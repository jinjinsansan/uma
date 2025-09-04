"""
V2コラムポイント消費API
コラム閲覧時のポイント消費と既読管理
作成日: 2025-09-04
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
from datetime import datetime
import logging
import os
from supabase import create_client, Client

from services.v2.points_service import V2PointsService, InsufficientPointsError
from api.v2.auth import get_current_user

logger = logging.getLogger(__name__)

# Supabase設定
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

router = APIRouter(prefix="/api/v2/column", tags=["v2-column"])

@router.post("/view/{column_id}")
async def view_column_with_points(
    column_id: str,
    user_data: Dict = Depends(get_current_user)
) -> Dict:
    """
    コラムを閲覧（ポイント消費処理付き）
    
    処理フロー:
    1. コラム情報を取得
    2. アクセスタイプを確認
    3. ポイント必要な場合は既読チェック
    4. 未読の場合はポイント消費
    5. 閲覧記録を保存
    6. コラム内容を返却
    """
    try:
        user_id = user_data.get("id")
        user_email = user_data.get("email")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="ユーザー認証が必要です")
        
        # 管理者チェック
        is_admin = user_email in ["goldbenchan@gmail.com", "kusanokiyoshi1@gmail.com"]
        
        logger.info(f"コラム閲覧リクエスト: column_id={column_id}, user_id={user_id}, is_admin={is_admin}")
        
        # 1. コラム情報取得
        column_response = supabase.table("v2_columns")\
            .select("*")\
            .eq("id", column_id)\
            .execute()
        
        if not column_response.data:
            logger.warning(f"コラムが見つかりません: {column_id}")
            raise HTTPException(status_code=404, detail="コラムが見つかりません")
        
        column = column_response.data[0]
        
        # 公開状態チェック（管理者は非公開でも閲覧可）
        if not column.get("is_published", False) and not is_admin:
            logger.warning(f"非公開コラムへのアクセス試行: {column_id}")
            raise HTTPException(status_code=403, detail="このコラムは現在公開されていません")
        
        # 2. アクセスタイプ確認
        access_type = column.get("access_type", "free")
        required_points = column.get("required_points", 0)
        
        logger.info(f"コラムアクセスタイプ: {access_type}, 必要ポイント: {required_points}")
        
        # 管理者は無料で閲覧可能
        if is_admin:
            logger.info(f"管理者アクセス: ポイント消費をスキップ")
            # 閲覧記録のみ保存
            await _record_column_view(column_id, user_id)
            return {
                "success": True,
                "column": column,
                "points_used": 0,
                "is_admin_access": True
            }
        
        # 3. ポイント消費が必要な場合
        if access_type == "point_required" and required_points > 0:
            # 既読チェック
            read_check_response = supabase.table("v2_column_reads")\
                .select("*")\
                .eq("column_id", column_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if read_check_response.data:
                # 既読の場合はポイント消費なし
                logger.info(f"既読コラム: ポイント消費なし")
                await _record_column_view(column_id, user_id)
                return {
                    "success": True,
                    "column": column,
                    "points_used": 0,
                    "already_read": True
                }
            
            # 未読の場合はポイント消費
            logger.info(f"未読コラム: {required_points}ポイント消費")
            points_service = V2PointsService()
            
            try:
                # ポイント消費（楽観的ロック付き）
                transaction = await points_service.use_points(
                    user_id=user_id,
                    amount=required_points,
                    transaction_type="column_view",
                    description=f"コラム閲覧: {column.get('title', 'タイトルなし')}",
                    related_entity_id=column_id
                )
                
                # 既読記録を保存
                read_record = {
                    "column_id": column_id,
                    "user_id": user_id,
                    "read_at": datetime.now().isoformat()
                }
                supabase.table("v2_column_reads").insert(read_record).execute()
                
                # 閲覧記録を保存
                await _record_column_view(column_id, user_id)
                
                logger.info(f"ポイント消費成功: {required_points}ポイント")
                
                return {
                    "success": True,
                    "column": column,
                    "points_used": required_points,
                    "balance_after": transaction.get("balance_after"),
                    "transaction_id": transaction.get("id")
                }
                
            except InsufficientPointsError as e:
                logger.warning(f"ポイント不足: {e}")
                
                # 現在のポイント残高を取得
                points_data = await points_service.get_user_points(user_id)
                current_points = points_data.get("current_points", 0)
                
                return {
                    "success": False,
                    "error": "insufficient_points",
                    "message": f"ポイントが不足しています",
                    "required_points": required_points,
                    "current_points": current_points,
                    "shortage": required_points - current_points
                }
        
        # 4. LINE連携必須の場合
        elif access_type == "line_linked":
            # LINE連携チェック
            user_response = supabase.table("v2_users")\
                .select("line_user_id")\
                .eq("id", user_id)\
                .execute()
            
            if not user_response.data or not user_response.data[0].get("line_user_id"):
                logger.warning(f"LINE未連携ユーザーのアクセス試行")
                return {
                    "success": False,
                    "error": "line_not_linked",
                    "message": "このコラムを閲覧するにはLINE連携が必要です"
                }
            
            # 閲覧記録を保存
            await _record_column_view(column_id, user_id)
            
            return {
                "success": True,
                "column": column,
                "points_used": 0
            }
        
        # 5. 無料コラムの場合
        else:
            # 閲覧記録を保存
            await _record_column_view(column_id, user_id)
            
            return {
                "success": True,
                "column": column,
                "points_used": 0
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"コラム閲覧エラー: {e}")
        raise HTTPException(status_code=500, detail="コラムの閲覧に失敗しました")

async def _record_column_view(column_id: str, user_id: str) -> None:
    """コラム閲覧記録を保存"""
    try:
        view_record = {
            "column_id": column_id,
            "user_id": user_id,
            "viewed_at": datetime.now().isoformat()
        }
        supabase.table("v2_column_views").insert(view_record).execute()
        
        # ビュー数を更新（非同期でも問題なし）
        supabase.rpc("increment_column_view_count", {"p_column_id": column_id}).execute()
        
    except Exception as e:
        # ビュー記録の失敗はエラーにしない（メイン処理には影響しない）
        logger.warning(f"ビュー記録失敗（非致命的）: {e}")

@router.get("/read-status/{column_id}")
async def get_column_read_status(
    column_id: str,
    user_data: Dict = Depends(get_current_user)
) -> Dict:
    """
    コラムの既読状態を確認
    """
    try:
        user_id = user_data.get("id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="ユーザー認証が必要です")
        
        # 既読チェック
        read_response = supabase.table("v2_column_reads")\
            .select("read_at, points_used")\
            .eq("column_id", column_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if read_response.data:
            return {
                "is_read": True,
                "read_at": read_response.data[0].get("read_at")
            }
        else:
            return {
                "is_read": False,
                "read_at": None
            }
            
    except Exception as e:
        logger.error(f"既読状態確認エラー: {e}")
        raise HTTPException(status_code=500, detail="既読状態の確認に失敗しました")

@router.get("/preview/{column_id}")
async def get_column_preview(column_id: str) -> Dict:
    """
    コラムのプレビュー情報を取得（ポイント消費なし）
    タイトル、サマリー、必要ポイントなど基本情報のみ
    """
    try:
        # コラム基本情報のみ取得（content以外）
        column_response = supabase.table("v2_columns")\
            .select("id, title, summary, featured_image, category_id, access_type, required_points, published_at, is_published")\
            .eq("id", column_id)\
            .execute()
        
        if not column_response.data:
            raise HTTPException(status_code=404, detail="コラムが見つかりません")
        
        column = column_response.data[0]
        
        # 非公開コラムは表示しない
        if not column.get("is_published", False):
            raise HTTPException(status_code=404, detail="コラムが見つかりません")
        
        return {
            "success": True,
            "preview": column
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"コラムプレビュー取得エラー: {e}")
        raise HTTPException(status_code=500, detail="プレビューの取得に失敗しました")