"""
V2ポイント管理API
既存システムには一切影響しない
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
from datetime import datetime
import logging
from pydantic import BaseModel

from api.v2.auth import get_current_user
from services.v2.points_service import V2PointsService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/points", tags=["v2-points"])

class PointsResponse(BaseModel):
    """ポイント情報レスポンス"""
    current_points: int
    total_earned: int
    total_spent: int
    can_create_chat: bool

class TransactionRequest(BaseModel):
    """ポイント取引リクエスト"""
    transaction_type: str
    amount: int
    description: Optional[str] = None
    related_entity_id: Optional[str] = None

@router.get("/status", response_model=PointsResponse)
async def get_points_status(user_id: str = Depends(get_current_user)):
    """
    ユーザーのポイント状態を取得
    """
    try:
        service = V2PointsService()
        points_data = await service.get_user_points(user_id)
        
        return PointsResponse(
            current_points=points_data["current_points"],
            total_earned=points_data["total_earned"],
            total_spent=points_data["total_spent"],
            can_create_chat=points_data["current_points"] > 0
        )
    except Exception as e:
        logger.error(f"ポイント状態取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ポイント情報の取得に失敗しました")

@router.post("/use")
async def use_points(
    request: TransactionRequest,
    user_id: str = Depends(get_current_user)
):
    """
    ポイントを使用（チャット作成時など）
    """
    try:
        service = V2PointsService()
        
        # ポイント残高確認
        points_data = await service.get_user_points(user_id)
        if points_data["current_points"] < request.amount:
            raise HTTPException(status_code=400, detail="ポイントが不足しています")
        
        # ポイント使用処理
        transaction = await service.use_points(
            user_id=user_id,
            amount=request.amount,
            transaction_type=request.transaction_type,
            description=request.description,
            related_entity_id=request.related_entity_id
        )
        
        return {
            "success": True,
            "transaction_id": transaction["id"],
            "remaining_points": transaction["balance_after"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ポイント使用エラー: {e}")
        raise HTTPException(status_code=500, detail="ポイントの使用に失敗しました")

@router.post("/grant")
async def grant_points(
    request: TransactionRequest,
    user_id: str = Depends(get_current_user)
):
    """
    ポイントを付与（認証時、LINE連携時など）
    """
    try:
        service = V2PointsService()
        
        # ポイント付与処理
        transaction = await service.grant_points(
            user_id=user_id,
            amount=request.amount,
            transaction_type=request.transaction_type,
            description=request.description,
            related_entity_id=request.related_entity_id
        )
        
        return {
            "success": True,
            "transaction_id": transaction["id"],
            "new_balance": transaction["balance_after"]
        }
        
    except Exception as e:
        logger.error(f"ポイント付与エラー: {e}")
        raise HTTPException(status_code=500, detail="ポイントの付与に失敗しました")

@router.get("/transactions")
async def get_transactions(
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user)
):
    """
    ポイント取引履歴を取得
    """
    try:
        service = V2PointsService()
        transactions = await service.get_transactions(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "transactions": transactions,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"取引履歴取得エラー: {e}")
        raise HTTPException(status_code=500, detail="取引履歴の取得に失敗しました")