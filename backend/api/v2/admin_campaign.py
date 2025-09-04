"""
管理者用キャンペーン管理API
全ユーザーへの一括ポイント付与機能
作成日: 2025-09-04
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional, Literal
from datetime import datetime, timedelta
import logging
import os
import asyncio
from supabase import create_client, Client

from services.v2.points_service import V2PointsService
from api.v2.auth import get_current_user

logger = logging.getLogger(__name__)

# Supabase設定
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

router = APIRouter(prefix="/api/v2/admin/campaign", tags=["v2-admin-campaign"])

class CampaignRequest(BaseModel):
    amount: int
    description: str
    target_users: Literal["all", "active", "new"] = "all"

@router.post("/grant-points")
async def grant_campaign_points(
    request: CampaignRequest,
    user_data: Dict = Depends(get_current_user)
) -> Dict:
    """
    キャンペーン：全ユーザーへの一括ポイント付与
    
    Parameters:
    - amount: 付与するポイント数（1-100）
    - description: キャンペーンの説明
    - target_users: 対象ユーザー（all/active/new）
    """
    try:
        # 管理者権限チェック
        user_email = user_data.get("email", "")
        admin_emails = ["goldbenchan@gmail.com", "kusanokiyoshi1@gmail.com"]
        
        if user_email not in admin_emails:
            raise HTTPException(status_code=403, detail="管理者権限が必要です")
        
        # バリデーション
        if request.amount < 1 or request.amount > 100:
            raise HTTPException(status_code=400, detail="ポイント数は1〜100の範囲で指定してください")
        
        if not request.description.strip():
            raise HTTPException(status_code=400, detail="キャンペーン説明を入力してください")
        
        logger.info(f"キャンペーン開始: {request.description} ({request.amount}P) - 対象: {request.target_users}")
        
        # 対象ユーザーを取得
        users_query = supabase.table("v2_users").select("id, email, created_at, last_login_at")
        
        if request.target_users == "active":
            # アクティブユーザー（30日以内にログイン）
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
            users_query = users_query.gte("last_login_at", cutoff_date)
        elif request.target_users == "new":
            # 新規ユーザー（7日以内に登録）
            cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
            users_query = users_query.gte("created_at", cutoff_date)
        
        # ユーザーリスト取得
        users_response = users_query.execute()
        target_users = users_response.data
        
        if not target_users:
            return {
                "success": False,
                "message": "対象ユーザーが見つかりません",
                "processed": 0,
                "failed": 0
            }
        
        logger.info(f"対象ユーザー数: {len(target_users)}人")
        
        # ポイントサービス初期化
        points_service = V2PointsService()
        
        # 一括付与処理
        processed = 0
        failed = 0
        failed_users = []
        
        # バッチサイズを設定（大量処理時のメモリ対策）
        batch_size = 10
        
        for i in range(0, len(target_users), batch_size):
            batch = target_users[i:i + batch_size]
            tasks = []
            
            for user in batch:
                # 各ユーザーへのポイント付与を非同期タスクとして作成
                task = grant_points_to_user(
                    points_service,
                    user["id"],
                    request.amount,
                    f"キャンペーン: {request.description}",
                    user.get("email", "unknown")
                )
                tasks.append(task)
            
            # バッチ内のタスクを並列実行
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 結果を集計
            for result, user in zip(results, batch):
                if isinstance(result, Exception):
                    failed += 1
                    failed_users.append(user.get("email", "unknown"))
                    logger.error(f"ポイント付与失敗: {user.get('email')}: {result}")
                elif result:
                    processed += 1
                else:
                    failed += 1
                    failed_users.append(user.get("email", "unknown"))
        
        # キャンペーン履歴を記録
        campaign_record = {
            "campaign_name": request.description,
            "target_type": request.target_users,
            "points_granted": request.amount,
            "users_processed": processed,
            "users_failed": failed,
            "executed_by": user_email,
            "executed_at": datetime.now().isoformat()
        }
        
        try:
            supabase.table("v2_campaign_history").insert(campaign_record).execute()
        except Exception as e:
            logger.warning(f"キャンペーン履歴の記録失敗: {e}")
        
        # 結果を返す
        success = processed > 0
        
        if success:
            message = f"キャンペーンが完了しました。{processed}人にポイントを付与しました。"
            if failed > 0:
                message += f" （{failed}人は失敗）"
        else:
            message = "キャンペーンの実行に失敗しました。"
        
        logger.info(f"キャンペーン完了: 成功={processed}, 失敗={failed}")
        
        return {
            "success": success,
            "message": message,
            "processed": processed,
            "failed": failed,
            "failed_users": failed_users[:10] if failed_users else []  # 最初の10件のみ返す
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"キャンペーン実行エラー: {e}")
        raise HTTPException(status_code=500, detail=f"キャンペーンの実行中にエラーが発生しました: {str(e)}")

async def grant_points_to_user(
    points_service: V2PointsService,
    user_id: str,
    amount: int,
    description: str,
    user_email: str
) -> bool:
    """
    個別ユーザーへのポイント付与
    """
    try:
        await points_service.grant_points(
            user_id=user_id,
            amount=amount,
            transaction_type="campaign",
            description=description
        )
        logger.debug(f"ポイント付与成功: {user_email} ({amount}P)")
        return True
    except Exception as e:
        logger.error(f"ポイント付与エラー ({user_email}): {e}")
        return False

@router.get("/history")
async def get_campaign_history(
    limit: int = 20,
    user_data: Dict = Depends(get_current_user)
) -> Dict:
    """
    キャンペーン履歴を取得
    """
    try:
        # 管理者権限チェック
        user_email = user_data.get("email", "")
        admin_emails = ["goldbenchan@gmail.com", "kusanokiyoshi1@gmail.com"]
        
        if user_email not in admin_emails:
            raise HTTPException(status_code=403, detail="管理者権限が必要です")
        
        # キャンペーン履歴を取得
        history_response = supabase.table("v2_campaign_history")\
            .select("*")\
            .order("executed_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return {
            "success": True,
            "history": history_response.data
        }
        
    except Exception as e:
        logger.error(f"キャンペーン履歴取得エラー: {e}")
        raise HTTPException(status_code=500, detail="履歴の取得に失敗しました")