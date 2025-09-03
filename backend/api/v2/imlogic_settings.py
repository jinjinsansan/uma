from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from api.v2.auth import verify_email_token

load_dotenv()

router = APIRouter(prefix="/api/v2/imlogic", tags=["IMLogic Settings"])

# Supabaseクライアント
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Supabase環境変数が設定されていません。SUPABASE_URLとSUPABASE_SERVICE_ROLE_KEYを確認してください。")

supabase: Client = create_client(supabase_url, supabase_key)

class ItemWeights(BaseModel):
    # 12項目の重み（キー名を文字列で定義）
    distance_aptitude: float = 8.33
    bloodline_evaluation: float = 8.33
    jockey_compatibility: float = 8.33
    trainer_evaluation: float = 8.33
    track_aptitude: float = 8.33
    weather_aptitude: float = 8.33
    popularity_factor: float = 8.33
    weight_impact: float = 8.33
    horse_weight_impact: float = 8.33
    corner_specialist: float = 8.33
    margin_analysis: float = 8.33
    time_index: float = 8.37
    
    def to_dict(self) -> Dict[str, float]:
        """フィールド名変換用の辞書に変換"""
        return {
            "1_distance_aptitude": self.distance_aptitude,
            "2_bloodline_evaluation": self.bloodline_evaluation,
            "3_jockey_compatibility": self.jockey_compatibility,
            "4_trainer_evaluation": self.trainer_evaluation,
            "5_track_aptitude": self.track_aptitude,
            "6_weather_aptitude": self.weather_aptitude,
            "7_popularity_factor": self.popularity_factor,
            "8_weight_impact": self.weight_impact,
            "9_horse_weight_impact": self.horse_weight_impact,
            "10_corner_specialist": self.corner_specialist,
            "11_margin_analysis": self.margin_analysis,
            "12_time_index": self.time_index
        }

class CreateSettingsRequest(BaseModel):
    name: str
    horse_weight: int  # 0-100 (10刻み)
    jockey_weight: int  # 0-100 (10刻み)
    item_weights: Dict[str, float]  # フロントからは"1_distance_aptitude"形式で来る

class UpdateSettingsRequest(BaseModel):
    name: Optional[str] = None
    horse_weight: Optional[int] = None
    jockey_weight: Optional[int] = None
    item_weights: Optional[Dict[str, float]] = None

@router.get("/settings")
async def get_user_settings(user_info: dict = Depends(verify_email_token)):
    """ユーザーの現在のIMLogic設定を取得（最新の1件）"""
    try:
        # V2認証システムからuser_idを取得
        user_id = user_info.get("user_id")
        
        # 最新の設定を取得（v2_imlogic_settingsテーブルから）
        result = supabase.table("v2_imlogic_settings") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()
        
        if result.data and len(result.data) > 0:
            data = result.data[0]
            return {
                "settings": {
                    "id": data["id"],
                    "name": data.get("settings_name", "カスタム設定"),
                    "horse_weight": data["horse_weight"],
                    "jockey_weight": data["jockey_weight"],
                    "item_weights": data["item_weights"],
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at")
                }
            }
        else:
            # デフォルト設定を返す（新規ユーザー用）
            return {
                "settings": {
                    "id": None,
                    "name": "デフォルト設定",
                    "horse_weight": 70,
                    "jockey_weight": 30,
                    "item_weights": {
                        "1_distance_aptitude": 8.33,
                        "2_bloodline_evaluation": 8.33,
                        "3_jockey_compatibility": 8.33,
                        "4_trainer_evaluation": 8.33,
                        "5_track_aptitude": 8.33,
                        "6_weather_aptitude": 8.33,
                        "7_popularity_factor": 8.33,
                        "8_weight_impact": 8.33,
                        "9_horse_weight_impact": 8.33,
                        "10_corner_specialist": 8.33,
                        "11_margin_analysis": 8.33,
                        "12_time_index": 8.37
                    },
                    "created_at": None,
                    "updated_at": None
                }
            }
            
    except Exception as e:
        print(f"設定取得エラー: {str(e)}")
        return {"settings": None}

@router.post("/settings")
async def save_user_settings(
    request: CreateSettingsRequest,
    user_info: dict = Depends(verify_email_token)
):
    """ユーザーのIMLogic設定を保存（POST /settings エンドポイント）"""
    # user_infoを渡してcreate_settingsを呼び出す
    return await create_settings(request, user_info)

@router.post("/create")
async def create_settings(
    request: CreateSettingsRequest,
    user_info: dict = Depends(verify_email_token)
):
    """新規IMLogic設定を作成（既存設定がある場合は更新）"""
    try:
        # V2認証システムからuser_idを取得
        user_id = user_info.get("user_id")
        
        # バリデーション
        if request.horse_weight + request.jockey_weight != 100:
            raise HTTPException(
                status_code=400, 
                detail=f"馬と騎手の重みの合計は100である必要があります（現在: {request.horse_weight + request.jockey_weight}）"
            )
        
        # 12項目の合計チェック
        weights_sum = sum(request.item_weights.values())
        if not (99.9 <= weights_sum <= 100.1):
            raise HTTPException(
                status_code=400,
                detail=f"12項目の重みの合計は100である必要があります（現在: {weights_sum:.2f}）"
            )
        
        # 既存設定があるか確認（UNIQUE制約により1ユーザー1設定）
        existing = supabase.table("v2_imlogic_settings").select("id").eq("user_id", user_id).execute()
        
        if existing.data:
            # 既存設定を更新
            result = supabase.table("v2_imlogic_settings").update({
                "settings_name": request.name,
                "horse_weight": request.horse_weight,
                "jockey_weight": request.jockey_weight,
                "item_weights": request.item_weights,
                "updated_at": datetime.now().isoformat()
            }).eq("user_id", user_id).execute()
            
            message = "IMLogic設定を更新しました"
        else:
            # 新規作成
            settings_id = str(uuid.uuid4())
            result = supabase.table("v2_imlogic_settings").insert({
                "id": settings_id,
                "user_id": user_id,
                "settings_name": request.name,
                "horse_weight": request.horse_weight,
                "jockey_weight": request.jockey_weight,
                "item_weights": request.item_weights
            }).execute()
            
            message = "IMLogic設定を作成しました"
        
        return {
            "id": settings_id,
            "message": "IMLogic設定を作成しました",
            "settings": result.data[0]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_settings():
    """ユーザーのIMLogic設定一覧を取得"""
    try:
        # TODO: 認証実装後にuser_idを取得
        user_id = "c73c78b2-c074-402e-be6e-8c9faa46d29a"  # 仮のユーザーID（goldbenchan@gmail.com）
        
        result = supabase.table("v2_imlogic_settings").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).execute()
        
        return {
            "settings": result.data,
            "count": len(result.data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{settings_id}")
async def get_settings(settings_id: str):
    """特定のIMLogic設定を取得"""
    try:
        # TODO: 認証実装後にuser_idを取得
        user_id = "c73c78b2-c074-402e-be6e-8c9faa46d29a"  # 仮のユーザーID（goldbenchan@gmail.com）
        
        if settings_id == "default":
            # デフォルト設定を返す
            return {
                "id": "default",
                "name": "デフォルト設定",
                "horse_weight": 70,
                "jockey_weight": 30,
                "item_weights": {
                    "1_distance_aptitude": 8.33,
                    "2_bloodline_evaluation": 8.33,
                    "3_jockey_compatibility": 8.33,
                    "4_trainer_evaluation": 8.33,
                    "5_track_aptitude": 8.33,
                    "6_weather_aptitude": 8.33,
                    "7_popularity_factor": 8.33,
                    "8_weight_impact": 8.33,
                    "9_horse_weight_impact": 8.33,
                    "10_corner_specialist": 8.33,
                    "11_margin_analysis": 8.33,
                    "12_time_index": 8.37
                },
                "is_default": True
            }
        
        result = supabase.table("v2_imlogic_settings").select("*").eq(
            "id", settings_id
        ).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="設定が見つかりません")
        
        return result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{settings_id}")
async def update_settings(settings_id: str, request: UpdateSettingsRequest):
    """IMLogic設定を更新"""
    try:
        # TODO: 認証実装後にuser_idを取得
        user_id = "c73c78b2-c074-402e-be6e-8c9faa46d29a"  # 仮のユーザーID（goldbenchan@gmail.com）
        
        # 既存設定の確認
        existing = supabase.table("v2_imlogic_settings").select("*").eq(
            "id", settings_id
        ).eq("user_id", user_id).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="設定が見つかりません")
        
        # 更新データの準備
        update_data = {
            "updated_at": datetime.now().isoformat()
        }
        
        if request.name is not None:
            update_data["settings_name"] = request.name
            
        if request.horse_weight is not None and request.jockey_weight is not None:
            if request.horse_weight + request.jockey_weight != 100:
                raise HTTPException(
                    status_code=400,
                    detail=f"馬と騎手の重みの合計は100である必要があります"
                )
            update_data["horse_weight"] = request.horse_weight
            update_data["jockey_weight"] = request.jockey_weight
            
        if request.item_weights is not None:
            weights_sum = sum(request.item_weights.values())
            if not (99.9 <= weights_sum <= 100.1):
                raise HTTPException(
                    status_code=400,
                    detail=f"12項目の重みの合計は100である必要があります（現在: {weights_sum:.2f}）"
                )
            update_data["item_weights"] = request.item_weights
        
        # 更新実行
        result = supabase.table("v2_imlogic_settings").update(update_data).eq(
            "id", settings_id
        ).execute()
        
        return {
            "message": "設定を更新しました",
            "settings": result.data[0]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{settings_id}")
async def delete_settings(settings_id: str):
    """IMLogic設定を削除"""
    try:
        # TODO: 認証実装後にuser_idを取得
        user_id = "c73c78b2-c074-402e-be6e-8c9faa46d29a"  # 仮のユーザーID（goldbenchan@gmail.com）
        
        # 削除実行
        result = supabase.table("v2_imlogic_settings").delete().eq(
            "id", settings_id
        ).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="設定が見つかりません")
        
        return {
            "message": "設定を削除しました",
            "deleted_id": settings_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{settings_id}/activate")
async def activate_settings(settings_id: str):
    """特定の設定をアクティブにする"""
    try:
        # TODO: 認証実装後にuser_idを取得
        user_id = "c73c78b2-c074-402e-be6e-8c9faa46d29a"  # 仮のユーザーID（goldbenchan@gmail.com）
        
        # 全ての設定を非アクティブに
        supabase.table("v2_imlogic_settings").update({
            "is_active": False
        }).eq("user_id", user_id).execute()
        
        # 指定された設定をアクティブに
        result = supabase.table("v2_imlogic_settings").update({
            "is_active": True,
            "updated_at": datetime.now().isoformat()
        }).eq("id", settings_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="設定が見つかりません")
        
        return {
            "message": "設定をアクティブにしました",
            "settings": result.data[0]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presets/list")
async def get_presets():
    """プリセット設定のリストを取得"""
    return {
        "presets": [
            {
                "id": "balanced",
                "name": "バランス型",
                "description": "全項目を均等に評価",
                "horse_weight": 70,
                "jockey_weight": 30,
                "item_weights": {
                    "1_distance_aptitude": 8.33,
                    "2_bloodline_evaluation": 8.33,
                    "3_jockey_compatibility": 8.33,
                    "4_trainer_evaluation": 8.33,
                    "5_track_aptitude": 8.33,
                    "6_weather_aptitude": 8.33,
                    "7_popularity_factor": 8.33,
                    "8_weight_impact": 8.33,
                    "9_horse_weight_impact": 8.33,
                    "10_corner_specialist": 8.33,
                    "11_margin_analysis": 8.33,
                    "12_time_index": 8.37
                }
            },
            {
                "id": "bloodline",
                "name": "血統重視型",
                "description": "血統評価に40%の重みを置く",
                "horse_weight": 80,
                "jockey_weight": 20,
                "item_weights": {
                    "1_distance_aptitude": 5.0,
                    "2_bloodline_evaluation": 40.0,
                    "3_jockey_compatibility": 5.0,
                    "4_trainer_evaluation": 5.0,
                    "5_track_aptitude": 5.0,
                    "6_weather_aptitude": 5.0,
                    "7_popularity_factor": 5.0,
                    "8_weight_impact": 5.0,
                    "9_horse_weight_impact": 5.0,
                    "10_corner_specialist": 5.0,
                    "11_margin_analysis": 5.0,
                    "12_time_index": 10.0
                }
            },
            {
                "id": "time",
                "name": "タイム重視型",
                "description": "タイムインデックスに50%の重み",
                "horse_weight": 90,
                "jockey_weight": 10,
                "item_weights": {
                    "1_distance_aptitude": 10.0,
                    "2_bloodline_evaluation": 5.0,
                    "3_jockey_compatibility": 3.0,
                    "4_trainer_evaluation": 3.0,
                    "5_track_aptitude": 5.0,
                    "6_weather_aptitude": 3.0,
                    "7_popularity_factor": 3.0,
                    "8_weight_impact": 3.0,
                    "9_horse_weight_impact": 3.0,
                    "10_corner_specialist": 5.0,
                    "11_margin_analysis": 7.0,
                    "12_time_index": 50.0
                }
            },
            {
                "id": "jockey",
                "name": "騎手重視型",
                "description": "騎手50%、騎手相性も重視",
                "horse_weight": 50,
                "jockey_weight": 50,
                "item_weights": {
                    "1_distance_aptitude": 8.0,
                    "2_bloodline_evaluation": 5.0,
                    "3_jockey_compatibility": 25.0,
                    "4_trainer_evaluation": 8.0,
                    "5_track_aptitude": 8.0,
                    "6_weather_aptitude": 5.0,
                    "7_popularity_factor": 5.0,
                    "8_weight_impact": 5.0,
                    "9_horse_weight_impact": 5.0,
                    "10_corner_specialist": 8.0,
                    "11_margin_analysis": 8.0,
                    "12_time_index": 10.0
                }
            }
        ]
    }