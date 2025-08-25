"""
V2チャット管理API
IMLogicとViewLogic（将来）を統合
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from datetime import datetime
import logging
from pydantic import BaseModel
import uuid

from api.v2.auth import get_current_user
from services.v2.points_service import V2PointsService
from services.v2.chat_service import V2ChatService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/chat", tags=["v2-chat"])

class CreateChatRequest(BaseModel):
    """チャット作成リクエスト"""
    race_id: str
    race_date: str
    venue: str
    race_number: int
    race_name: str
    horses: List[str]
    jockeys: Optional[List[str]] = []
    posts: Optional[List[int]] = []
    horse_numbers: Optional[List[int]] = []
    distance: Optional[int] = None
    course_type: Optional[str] = None
    weather: Optional[str] = None
    track_condition: Optional[str] = None
    imlogic_settings_id: Optional[str] = None

class ChatMessageRequest(BaseModel):
    """チャットメッセージリクエスト"""
    message: str
    ai_type: str  # 'imlogic' or 'viewlogic'

@router.post("/create")
async def create_chat(
    request: CreateChatRequest,
    user_id: str = Depends(get_current_user)
):
    """
    新しいチャットセッションを作成（1ポイント消費）
    """
    try:
        # ポイント確認
        points_service = V2PointsService()
        points_data = await points_service.get_user_points(user_id)
        
        if points_data["current_points"] < 1:
            raise HTTPException(status_code=400, detail="チャット作成にはポイントが必要です")
        
        # チャット作成
        chat_service = V2ChatService()
        chat_session = await chat_service.create_session(
            user_id=user_id,
            race_data={
                "race_id": request.race_id,
                "race_date": request.race_date,
                "venue": request.venue,
                "race_number": request.race_number,
                "race_name": request.race_name,
                "horses": request.horses,
                "jockeys": request.jockeys,
                "posts": request.posts,
                "horse_numbers": request.horse_numbers,
                "distance": request.distance,
                "course_type": request.course_type,
                "weather": request.weather,
                "track_condition": request.track_condition
            },
            imlogic_settings_id=request.imlogic_settings_id
        )
        
        # ポイント消費
        await points_service.use_points(
            user_id=user_id,
            amount=1,
            transaction_type="chat_create",
            description=f"{request.venue}{request.race_number}Rのチャット作成",
            related_entity_id=chat_session["id"]
        )
        
        return {
            "success": True,
            "chat_id": chat_session["id"],
            "remaining_points": points_data["current_points"] - 1
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"チャット作成エラー: {e}")
        raise HTTPException(status_code=500, detail="チャットの作成に失敗しました")

@router.get("/sessions")
async def get_chat_sessions(
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """
    ユーザーのチャットセッション一覧を取得
    """
    try:
        chat_service = V2ChatService()
        sessions = await chat_service.get_user_sessions(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "sessions": sessions,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"セッション一覧取得エラー: {e}")
        raise HTTPException(status_code=500, detail="セッション一覧の取得に失敗しました")

@router.get("/session/{session_id}")
async def get_chat_session(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    特定のチャットセッションを取得
    """
    try:
        chat_service = V2ChatService()
        session = await chat_service.get_session(session_id, user_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="チャットセッションが見つかりません")
        
        # 最終アクセス日時を更新
        await chat_service.update_last_accessed(session_id)
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"セッション取得エラー: {e}")
        raise HTTPException(status_code=500, detail="セッションの取得に失敗しました")

@router.post("/session/{session_id}/message")
async def send_message(
    session_id: str,
    request: ChatMessageRequest,
    user_id: str = Depends(get_current_user)
):
    """
    チャットにメッセージを送信
    """
    try:
        chat_service = V2ChatService()
        
        # セッション確認
        session = await chat_service.get_session(session_id, user_id)
        if not session:
            raise HTTPException(status_code=404, detail="チャットセッションが見つかりません")
        
        # AIタイプ確認
        if request.ai_type not in ["imlogic", "viewlogic"]:
            raise HTTPException(status_code=400, detail="無効なAIタイプです")
        
        # ViewLogicは未実装
        if request.ai_type == "viewlogic":
            # Phase 5完了後に実装
            return {
                "message": {
                    "id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": "ViewLogicは現在開発中です。2025年春頃の公開を予定しています。",
                    "ai_type": "viewlogic",
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        # IMLogicメッセージ処理
        response = await chat_service.process_message(
            session_id=session_id,
            message=request.message,
            ai_type=request.ai_type,
            session_data=session
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"メッセージ送信エラー: {e}")
        raise HTTPException(status_code=500, detail="メッセージの送信に失敗しました")