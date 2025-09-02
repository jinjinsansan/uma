"""
V2 IMLogic設定管理API
ユーザーのIMLogic設定の保存・取得・更新を管理
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
import logging
import uuid
from datetime import datetime
from supabase import create_client, Client
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/imlogic-settings", tags=["IMLogic Settings"])

# Supabaseクライアント初期化
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def get_user_uuid_from_email(email_or_uuid: str) -> str:
    """
    emailまたはUUIDからユーザーIDを取得
    UUIDフォーマットの場合はそのまま返す
    emailの場合はv2_usersテーブルから検索
    """
    try:
        # UUID形式かチェック
        try:
            uuid.UUID(email_or_uuid)
            return email_or_uuid  # 既にUUID形式
        except ValueError:
            pass  # email形式として処理を続ける
        
        # emailでユーザーを検索
        result = supabase.table("v2_users").select("id").eq("email", email_or_uuid).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]["id"]
        else:
            logger.error(f"ユーザーが見つかりません: {email_or_uuid}")
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ユーザーID取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"ユーザー情報の取得に失敗しました: {str(e)}")

class IMLogicSettingsRequest(BaseModel):
    """IMLogic設定リクエスト"""
    user_id: str
    settings_name: str = "カスタム設定"
    horse_weight: int  # 馬の重み（0-100）
    jockey_weight: int  # 騎手の重み（0-100）
    item_weights: Dict[str, float]  # 12項目の重み

class IMLogicSettingsResponse(BaseModel):
    """IMLogic設定レスポンス"""
    id: str
    user_id: str
    settings_name: str
    horse_weight: int
    jockey_weight: int
    item_weights: Dict[str, float]
    is_active: bool
    created_at: str
    updated_at: str

@router.post("/save")
async def save_imlogic_settings(request: IMLogicSettingsRequest) -> IMLogicSettingsResponse:
    """
    IMLogic設定を保存（ユーザーの最新設定として）
    古い設定は自動的に非アクティブになる
    """
    try:
        # emailからUUIDを取得
        user_uuid = get_user_uuid_from_email(request.user_id)
        
        # 既存の設定を非アクティブ化
        supabase.table("v2_imlogic_settings").update({
            "is_active": False
        }).eq("user_id", user_uuid).execute()
        
        # 新しい設定を保存
        new_settings = {
            "id": str(uuid.uuid4()),
            "user_id": user_uuid,
            "settings_name": request.settings_name,
            "horse_weight": request.horse_weight,
            "jockey_weight": request.jockey_weight,
            "item_weights": request.item_weights,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("v2_imlogic_settings").insert(new_settings).execute()
        
        if result.data:
            logger.info(f"IMLogic設定を保存しました: user_id={request.user_id}")
            return IMLogicSettingsResponse(**result.data[0])
        else:
            raise HTTPException(status_code=500, detail="設定の保存に失敗しました")
            
    except Exception as e:
        logger.error(f"IMLogic設定保存エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current/{user_id}")
async def get_current_imlogic_settings(user_id: str) -> Optional[IMLogicSettingsResponse]:
    """
    ユーザーの現在のIMLogic設定を取得
    """
    try:
        # emailからUUIDを取得
        user_uuid = get_user_uuid_from_email(user_id)
        
        result = supabase.table("v2_imlogic_settings")\
            .select("*")\
            .eq("user_id", user_uuid)\
            .eq("is_active", True)\
            .single()\
            .execute()
        
        if result.data:
            return IMLogicSettingsResponse(**result.data)
        else:
            # デフォルト設定を返す
            return IMLogicSettingsResponse(
                id="default",
                user_id=user_uuid,
                settings_name="標準設定",
                horse_weight=70,
                jockey_weight=30,
                item_weights={
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
                is_active=True,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
    except Exception as e:
        logger.error(f"IMLogic設定取得エラー: {e}")
        # エラー時もデフォルト設定を返す
        return None

@router.put("/update")
async def update_imlogic_settings(request: IMLogicSettingsRequest) -> IMLogicSettingsResponse:
    """
    既存のIMLogic設定を更新
    """
    try:
        # emailからUUIDを取得
        user_uuid = get_user_uuid_from_email(request.user_id)
        
        # 現在のアクティブな設定を更新
        result = supabase.table("v2_imlogic_settings")\
            .update({
                "settings_name": request.settings_name,
                "horse_weight": request.horse_weight,
                "jockey_weight": request.jockey_weight,
                "item_weights": request.item_weights,
                "updated_at": datetime.now().isoformat()
            })\
            .eq("user_id", user_uuid)\
            .eq("is_active", True)\
            .execute()
        
        if result.data:
            logger.info(f"IMLogic設定を更新しました: user_id={request.user_id}")
            return IMLogicSettingsResponse(**result.data[0])
        else:
            # 設定が存在しない場合は新規作成
            return await save_imlogic_settings(request)
            
    except Exception as e:
        logger.error(f"IMLogic設定更新エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reset/{user_id}")
async def reset_imlogic_settings(user_id: str) -> Dict[str, str]:
    """
    ユーザーのIMLogic設定をデフォルトにリセット
    """
    try:
        # emailからUUIDを取得
        user_uuid = get_user_uuid_from_email(user_id)
        
        # すべての設定を非アクティブ化
        supabase.table("v2_imlogic_settings")\
            .update({"is_active": False})\
            .eq("user_id", user_uuid)\
            .execute()
        
        logger.info(f"IMLogic設定をリセットしました: user_id={user_id}")
        return {"message": "設定をデフォルトにリセットしました"}
        
    except Exception as e:
        logger.error(f"IMLogic設定リセットエラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))