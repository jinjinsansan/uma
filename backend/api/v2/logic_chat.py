from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import json
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from .auth import get_current_user

load_dotenv()

router = APIRouter(prefix="/api/v2/logic-chat", tags=["Logic Chat V2"])

# Supabaseクライアント
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Supabase環境変数が設定されていません。SUPABASE_URLとSUPABASE_SERVICE_ROLE_KEYを確認してください。")

supabase: Client = create_client(supabase_url, supabase_key)

class CreateChatRequest(BaseModel):
    race_id: str
    venue: str
    race_number: int
    race_name: str
    horses: List[str]
    jockeys: List[str]
    posts: List[int]
    horse_numbers: List[int]

class AnalyzeRequest(BaseModel):
    chat_id: str
    engine_type: str  # 'imlogic', 'viewlogic'
    imlogic_settings_id: Optional[str] = None  # IMLogicの場合のみ
    message: str

@router.post("/create")
async def create_chat(request: CreateChatRequest, user_id: str = Depends(get_current_user)):
    """新規チャット作成（レース固定）"""
    try:
        
        # レースデータを固定
        locked_race_data = {
            "venue": request.venue,
            "race_number": request.race_number,
            "race_name": request.race_name,
            "horses": request.horses,
            "jockeys": request.jockeys,
            "posts": request.posts,
            "horse_numbers": request.horse_numbers,
            "locked_at": datetime.now().isoformat()
        }
        
        # Supabaseに保存
        chat_id = str(uuid.uuid4())
        
        # user_idがUUID形式でない場合（メールアドレスの場合）、usersテーブルから実際のIDを取得
        actual_user_id = user_id
        if '@' in str(user_id):
            user_result = supabase.table("users").select("id").eq("email", user_id).execute()
            if user_result.data and len(user_result.data) > 0:
                actual_user_id = user_result.data[0]["id"]
            else:
                # ユーザーが存在しない場合は作成
                new_user_result = supabase.table("users").insert({
                    "email": user_id,
                    "name": user_id.split("@")[0],
                    "google_id": "",
                    "avatar_url": ""
                }).execute()
                if new_user_result.data:
                    actual_user_id = new_user_result.data[0]["id"]
                else:
                    raise HTTPException(status_code=500, detail="ユーザー作成に失敗しました")
        
        result = supabase.table("logic_chats_v2").insert({
            "id": chat_id,
            "user_id": actual_user_id,
            "race_id": request.race_id,
            "locked_race_data": locked_race_data,
            "points_consumed": 1
        }).execute()
        
        return {
            "chat_id": chat_id,
            "race_data": locked_race_data,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze(request: AnalyzeRequest, user_id: str = Depends(get_current_user)):
    """分析実行（IMLogic/ViewLogic）"""
    try:
        
        # user_idがメールアドレスの場合、実際のUUIDを取得
        actual_user_id = user_id
        if '@' in str(user_id):
            user_result = supabase.table("users").select("id").eq("email", user_id).execute()
            if user_result.data and len(user_result.data) > 0:
                actual_user_id = user_result.data[0]["id"]
        
        # チャットの存在確認とレースデータ取得
        chat_result = supabase.table("logic_chats_v2").select("*").eq(
            "id", request.chat_id
        ).eq("user_id", actual_user_id).execute()
        
        if not chat_result.data:
            raise HTTPException(status_code=404, detail="チャットが見つかりません")
        
        chat = chat_result.data[0]
        locked_race_data = chat["locked_race_data"]
        
        # リクエストされた馬がレースに含まれているか検証
        horses_in_message = _extract_horses_from_message(request.message)
        locked_horses = locked_race_data.get("horses", [])
        
        for horse in horses_in_message:
            if horse not in locked_horses:
                raise HTTPException(
                    status_code=400, 
                    detail=f"「{horse}」はこのレースに出走していません。このチャットでは{locked_race_data['race_name']}の出走馬のみ分析できます。"
                )
        
        # エンジンタイプに応じて分析実行
        if request.engine_type == "imlogic":
            # IMLogicエンジンを使用
            result = await _analyze_imlogic(
                locked_race_data, 
                user_id,
                request.imlogic_settings_id
            )
            
        elif request.engine_type == "viewlogic":
            # ViewLogicエンジン（将来実装）
            result = {"message": "ViewLogicは開発中です"}
            
        else:
            raise HTTPException(status_code=400, detail="無効なエンジンタイプです。'imlogic'または'viewlogic'を指定してください。")
        
        # チャット履歴に追加
        await _add_to_chat_history(
            request.chat_id,
            request.message,
            result,
            request.engine_type
        )
        
        return {
            "analysis_result": result,
            "engine_type": request.engine_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _extract_horses_from_message(message: str) -> List[str]:
    """メッセージから馬名を抽出する（簡易版）"""
    # TODO: より高度な馬名抽出ロジックの実装
    # 現在は「」で囲まれた文字列を馬名として扱う
    import re
    horses = re.findall(r'「([^」]+)」', message)
    return horses

async def _analyze_imlogic(
    race_data: Dict[str, Any], 
    user_id: str,
    settings_id: Optional[str] = None
) -> Dict[str, Any]:
    """IMLogic分析実行"""
    try:
        # 設定を取得
        if settings_id and settings_id != "default":
            # user_idの形式を確認
            settings_user_id = user_id
            if '@' in str(user_id):
                user_result = supabase.table("users").select("id").eq("email", user_id).execute()
                if user_result.data and len(user_result.data) > 0:
                    settings_user_id = user_result.data[0]["id"]
            
            # ユーザーのカスタム設定を取得
            settings_result = supabase.table("v2_imlogic_settings").select("*").eq(
                "id", settings_id
            ).eq("user_id", settings_user_id).execute()
            
            if not settings_result.data:
                raise HTTPException(status_code=404, detail="指定された設定が見つかりません")
            
            settings = settings_result.data[0]
            # デバッグ：Supabaseから取得した設定を確認
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Supabaseから取得した設定: {settings}")
        else:
            # デフォルト設定を使用（フロントエンドと同じ番号付きキー）
            settings = {
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
            }
        
        # IMLogicエンジンを使用して分析
        from services.imlogic_engine import IMLogicEngine
        engine = IMLogicEngine()
        
        result = engine.analyze_race(
            race_data=race_data,
            horse_weight=settings["horse_weight"],
            jockey_weight=settings["jockey_weight"],
            item_weights=settings["item_weights"]
        )
        
        return result  # 既に適切な形式で返される
        
    except Exception as e:
        # エラーの場合
        import traceback
        traceback.print_exc()
        return {
            "type": "imlogic",
            "error": f"IMLogic分析エラー: {str(e)}",
            "settings_id": settings_id,
            "race_info": {
                "venue": race_data.get("venue"),
                "race_name": race_data.get("race_name"),
                "horses_count": len(race_data.get("horses", []))
            }
        }

async def _add_to_chat_history(
    chat_id: str,
    user_message: str,
    analysis_result: Dict[str, Any],
    engine_type: str
):
    """チャット履歴に追加"""
    # 現在のチャット履歴を取得
    chat_result = supabase.table("logic_chats_v2").select(
        "chat_history", "analyses_cache"
    ).eq("id", chat_id).execute()
    
    if not chat_result.data:
        return
    
    current_history = chat_result.data[0]["chat_history"] or []
    current_cache = chat_result.data[0]["analyses_cache"] or {}
    
    # 新しいエントリを追加
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_message": user_message,
        "engine_type": engine_type,
        "analysis_result": analysis_result
    }
    
    current_history.append(new_entry)
    current_cache[engine_type] = analysis_result
    
    # 更新
    supabase.table("logic_chats_v2").update({
        "chat_history": current_history,
        "analyses_cache": current_cache,
        "updated_at": datetime.now().isoformat()
    }).eq("id", chat_id).execute()

@router.get("/chat/{chat_id}")
async def get_chat(chat_id: str, user_id: str = Depends(get_current_user)):
    """チャット情報を取得"""
    try:
        # user_idがメールアドレスの場合、実際のUUIDを取得
        actual_user_id = user_id
        if '@' in str(user_id):
            user_result = supabase.table("users").select("id").eq("email", user_id).execute()
            if user_result.data and len(user_result.data) > 0:
                actual_user_id = user_result.data[0]["id"]
        
        chat_result = supabase.table("logic_chats_v2").select("*").eq(
            "id", chat_id
        ).eq("user_id", actual_user_id).execute()
        
        if not chat_result.data:
            raise HTTPException(status_code=404, detail="チャットが見つかりません")
        
        return chat_result.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))