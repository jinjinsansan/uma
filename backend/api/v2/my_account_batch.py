"""
V2マイアカウントのバッチAPI
複数のステータスを一括取得して高速化
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["v2_my_account"])

@router.get("/my-account/batch-status")
async def get_batch_status(
    email: str,
    user_id: Optional[str] = None
):
    """
    マイアカウントの全ステータスを一括取得
    - ポイント状態
    - LINE連携状態
    - 友達紹介状態
    - デイリーログイン状態
    """
    try:
        from api.v2.points import get_user_points_status
        from api.v2.line_referral import get_line_and_referral_status
        
        # 並列で全ステータスを取得
        tasks = []
        
        # 1. ポイント状態を取得
        async def get_points():
            try:
                # 既存のポイントAPIロジックを使用
                from services.supabase_service import get_supabase_client
                supabase = get_supabase_client()
                
                # ユーザー情報取得
                user_result = supabase.table("v2_users").select("*").eq("email", email).execute()
                if not user_result.data:
                    return {"points": 0, "error": "User not found"}
                
                user = user_result.data[0]
                user_id = user["id"]
                
                # ポイント取得
                points_result = supabase.table("v2_user_points").select("*").eq("user_id", user_id).execute()
                if points_result.data:
                    return {
                        "points": points_result.data[0]["points"],
                        "last_updated": points_result.data[0]["updated_at"]
                    }
                else:
                    return {"points": 0}
            except Exception as e:
                logger.error(f"ポイント取得エラー: {e}")
                return {"points": 0, "error": str(e)}
        
        # 2. LINE連携状態を取得
        async def get_line():
            try:
                from services.supabase_service import get_supabase_client
                supabase = get_supabase_client()
                
                # ユーザー情報取得
                user_result = supabase.table("v2_users").select("*").eq("email", email).execute()
                if not user_result.data:
                    return {"line_connected": False}
                
                user = user_result.data[0]
                return {
                    "line_connected": bool(user.get("line_user_id")),
                    "line_connected_at": user.get("line_connected_at")
                }
            except Exception as e:
                logger.error(f"LINE状態取得エラー: {e}")
                return {"line_connected": False, "error": str(e)}
        
        # 3. 友達紹介状態を取得
        async def get_referral():
            try:
                from services.supabase_service import get_supabase_client
                supabase = get_supabase_client()
                
                # ユーザー情報取得
                user_result = supabase.table("v2_users").select("*").eq("email", email).execute()
                if not user_result.data:
                    return {"referral_count": 0}
                
                user = user_result.data[0]
                user_id = user["id"]
                
                # 紹介数を取得
                referral_result = supabase.table("v2_referral_history")\
                    .select("id")\
                    .eq("referrer_id", user_id)\
                    .eq("status", "line_connected")\
                    .execute()
                
                return {
                    "referral_code": user.get("referral_code"),
                    "referral_count": len(referral_result.data) if referral_result.data else 0,
                    "has_used_referral": bool(user.get("referred_by"))
                }
            except Exception as e:
                logger.error(f"紹介状態取得エラー: {e}")
                return {"referral_count": 0, "error": str(e)}
        
        # 4. デイリーログイン状態を取得
        async def get_daily_login():
            try:
                from services.supabase_service import get_supabase_client
                from datetime import date
                supabase = get_supabase_client()
                
                # ユーザー情報取得
                user_result = supabase.table("v2_users").select("*").eq("email", email).execute()
                if not user_result.data:
                    return {"has_claimed_daily_login": False}
                
                user = user_result.data[0]
                user_id = user["id"]
                
                # 今日のログインボーナス取得状況
                today = date.today().isoformat()
                daily_result = supabase.table("v2_point_transactions")\
                    .select("id")\
                    .eq("user_id", user_id)\
                    .eq("transaction_type", "daily_login")\
                    .gte("created_at", f"{today}T00:00:00")\
                    .execute()
                
                return {
                    "has_claimed_daily_login": bool(daily_result.data)
                }
            except Exception as e:
                logger.error(f"デイリーログイン状態取得エラー: {e}")
                return {"has_claimed_daily_login": False, "error": str(e)}
        
        # 並列実行
        results = await asyncio.gather(
            get_points(),
            get_line(),
            get_referral(),
            get_daily_login(),
            return_exceptions=True
        )
        
        # 結果をまとめる
        response = {
            "email": email,
            "timestamp": datetime.now().isoformat(),
            "points": results[0] if not isinstance(results[0], Exception) else {"points": 0, "error": str(results[0])},
            "line": results[1] if not isinstance(results[1], Exception) else {"line_connected": False, "error": str(results[1])},
            "referral": results[2] if not isinstance(results[2], Exception) else {"referral_count": 0, "error": str(results[2])},
            "daily_login": results[3] if not isinstance(results[3], Exception) else {"has_claimed_daily_login": False, "error": str(results[3])}
        }
        
        # ポイント設定も追加
        from api.v2.config import v2_config
        response["points_config"] = v2_config.get_points_summary()
        
        return response
        
    except Exception as e:
        logger.error(f"バッチステータス取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))