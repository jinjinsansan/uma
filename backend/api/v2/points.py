"""
V2ポイント管理API
既存システムには一切影響しない
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Optional
from datetime import datetime
import logging
from pydantic import BaseModel

from api.v2.auth import get_current_user, verify_email_token
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

class GrantPointsRequest(BaseModel):
    """ポイント付与リクエスト（管理者用）"""
    amount: int = 10
    description: Optional[str] = None


class ReferralMilestoneRequest(BaseModel):
    """紹介マイルストーンボーナス受取リクエスト"""
    milestone: int

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

@router.post("/grant")
async def grant_test_points(
    request: GrantPointsRequest,
    user_info: dict = Depends(verify_email_token)
):
    """
    管理者用テストポイント付与
    """
    try:
        user_id = user_info["user_id"]
        user_email = user_info.get("email", "")
        
        # 管理者チェック
        if user_email != "goldbenchan@gmail.com":
            raise HTTPException(status_code=403, detail="管理者権限が必要です")
        
        service = V2PointsService()
        
        # ポイント付与
        transaction = await service.add_points(
            user_id=user_id,
            amount=request.amount,
            transaction_type="admin_grant",
            description=request.description or "管理者テスト用ポイント付与"
        )
        
        # 現在のポイント取得
        points_data = await service.get_user_points(user_id)
        
        return {
            "success": True,
            "current_points": points_data["current_points"],
            "added_points": request.amount
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"管理者ポイント付与エラー: {e}")
        raise HTTPException(status_code=500, detail="ポイント付与に失敗しました")

@router.post("/reset")
async def reset_points(
    user_info: dict = Depends(verify_email_token)
):
    """
    管理者用ポイントリセット（0に戻す）
    """
    try:
        user_id = user_info["user_id"]
        user_email = user_info.get("email", "")
        
        # 管理者チェック
        if user_email != "goldbenchan@gmail.com":
            raise HTTPException(status_code=403, detail="管理者権限が必要です")
        
        service = V2PointsService()
        
        # 現在のポイントを取得
        points_data = await service.get_user_points(user_id)
        current_points = points_data["current_points"]
        
        # 現在のポイントを全て消費
        if current_points > 0:
            await service.use_points(
                user_id=user_id,
                amount=current_points,
                transaction_type="admin_reset",
                description="管理者によるポイントリセット"
            )
        
        return {
            "success": True,
            "message": "ポイントを0にリセットしました"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ポイントリセットエラー: {e}")
        raise HTTPException(status_code=500, detail="ポイントリセットに失敗しました")

@router.post("/daily-login")
async def claim_daily_login(user_id: str = Depends(get_current_user)):
    """
    デイリーログインボーナスを取得
    """
    try:
        service = V2PointsService()
        
        # 今日既にログインボーナスを受け取っているかチェック
        today = datetime.now().date()
        existing_login = await service.check_daily_login_exists(user_id, today)
        
        if existing_login:
            raise HTTPException(status_code=400, detail="今日のログインボーナスは既に受け取り済みです")
        
        # デイリーログインポイント付与
        daily_points = 2  # デイリーログインボーナス: 2ポイント
        transaction = await service.grant_points(
            user_id=user_id,
            amount=daily_points,
            transaction_type="daily_login",
            description="デイリーログインボーナス"
        )
        
        return {
            "points_granted": daily_points,
            "message": f"デイリーログインボーナス {daily_points}ポイント を獲得しました！",
            "new_balance": transaction["balance_after"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"デイリーログインボーナス取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ログインボーナスの取得に失敗しました")

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
@router.post("/referral-milestone-bonus")
async def claim_referral_milestone_bonus(
    payload: Optional[ReferralMilestoneRequest] = Body(default=None),
    milestone: Optional[int] = None,
    user_id: str = Depends(get_current_user)
):
    """
    紹介マイルストーンボーナスを取得
    milestone: 2, 5, または 10
    """
    try:
        from supabase import create_client, Client
        import os
        
        # リクエストボディ優先でマイルストーンを決定
        milestone_value: Optional[int] = payload.milestone if payload else milestone

        if milestone_value is None:
            raise HTTPException(status_code=422, detail="milestone is required")

        # マイルストーンの検証
        if milestone_value not in [2, 5, 10]:
            raise HTTPException(status_code=400, detail="無効なマイルストーンです")
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # ユーザーの紹介数を取得
        referral_result = supabase.table("v2_referrals").select("id").eq("referrer_id", user_id).eq("status", "completed").execute()
        referral_count = len(referral_result.data) if referral_result.data else 0
        
        # マイルストーンに達しているか確認
        if referral_count < milestone_value:
            raise HTTPException(
                status_code=400, 
                detail=f"紹介{milestone_value}名に達していません（現在: {referral_count}名）"
            )
        
        # 既に受け取り済みか確認
        transaction_type = f"referral_milestone_{milestone_value}"
        service = V2PointsService()
        
        existing = supabase.table("v2_point_transactions").select("id").eq("user_id", user_id).eq("transaction_type", transaction_type).execute()
        
        if existing.data:
            raise HTTPException(status_code=400, detail="このマイルストーンボーナスは既に受け取り済みです")
        
        # ボーナスポイントを付与（マイルストーンと同じポイント数）
        transaction = await service.grant_points(
            user_id=user_id,
            amount=milestone_value,
            transaction_type=transaction_type,
            description=f"紹介{milestone_value}名達成デイリーボーナス"
        )
        
        return {
            "points_granted": milestone_value,
            "message": f"紹介{milestone_value}名達成！デイリーボーナス+{milestone_value}Pを獲得しました",
            "new_balance": transaction["balance_after"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"紹介マイルストーンボーナス取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ボーナスの取得に失敗しました")
