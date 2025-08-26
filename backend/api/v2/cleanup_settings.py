"""
V2 IMLogic設定の自動クリーンアップAPI
古い設定を定期的に削除して、データベースの肥大化を防ぐ
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime, timedelta
import logging
from supabase import create_client, Client
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/cleanup", tags=["Cleanup"])

# Supabaseクライアント
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Supabase環境変数が設定されていません")

supabase: Client = create_client(supabase_url, supabase_key)

# クリーンアップ設定
SETTINGS_RETENTION_DAYS = 7  # 設定を保持する日数
MAX_SETTINGS_PER_USER = 50  # ユーザーごとの最大設定数
CHAT_MESSAGES_RETENTION_DAYS = 30  # チャットメッセージを保持する日数
CHAT_SESSIONS_RETENTION_DAYS = 30  # チャットセッションを保持する日数

async def cleanup_old_imlogic_settings():
    """古いIMLogic設定を削除"""
    try:
        cutoff_date = (datetime.now() - timedelta(days=SETTINGS_RETENTION_DAYS)).isoformat()
        
        # 古い設定を削除（最新の5件は常に保持）
        all_users = supabase.table("v2_imlogic_settings")\
            .select("user_id", count="exact")\
            .execute()
        
        unique_users = set([row['user_id'] for row in all_users.data])
        
        for user_id in unique_users:
            # ユーザーごとの設定を取得
            user_settings = supabase.table("v2_imlogic_settings")\
                .select("id, created_at")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            if len(user_settings.data) > MAX_SETTINGS_PER_USER:
                # 最大数を超える古い設定を削除
                to_delete = user_settings.data[MAX_SETTINGS_PER_USER:]
                for setting in to_delete:
                    supabase.table("v2_imlogic_settings")\
                        .delete()\
                        .eq("id", setting['id'])\
                        .execute()
                    logger.info(f"削除: IMLogic設定 {setting['id']} (user: {user_id})")
            
            # 保持期間を過ぎた設定を削除（最新5件は除く）
            if len(user_settings.data) > 5:
                old_settings = [s for s in user_settings.data[5:] if s['created_at'] < cutoff_date]
                for setting in old_settings:
                    supabase.table("v2_imlogic_settings")\
                        .delete()\
                        .eq("id", setting['id'])\
                        .execute()
                    logger.info(f"期限切れ削除: IMLogic設定 {setting['id']}")
        
        return {"deleted_settings": True}
        
    except Exception as e:
        logger.error(f"IMLogic設定クリーンアップエラー: {e}")
        return {"error": str(e)}

async def cleanup_old_chat_sessions():
    """古いチャットセッションとメッセージを削除"""
    try:
        cutoff_date = (datetime.now() - timedelta(days=CHAT_SESSIONS_RETENTION_DAYS)).isoformat()
        
        # 古いセッションを取得
        old_sessions = supabase.table("v2_chat_sessions")\
            .select("id")\
            .lt("last_accessed_at", cutoff_date)\
            .execute()
        
        for session in old_sessions.data:
            # 関連メッセージを削除
            supabase.table("v2_chat_messages")\
                .delete()\
                .eq("session_id", session['id'])\
                .execute()
            
            # セッションを削除
            supabase.table("v2_chat_sessions")\
                .delete()\
                .eq("id", session['id'])\
                .execute()
            
            logger.info(f"削除: チャットセッション {session['id']}")
        
        return {"deleted_sessions": len(old_sessions.data)}
        
    except Exception as e:
        logger.error(f"チャットセッションクリーンアップエラー: {e}")
        return {"error": str(e)}

@router.post("/run")
async def run_cleanup(background_tasks: BackgroundTasks):
    """手動でクリーンアップを実行"""
    background_tasks.add_task(cleanup_old_imlogic_settings)
    background_tasks.add_task(cleanup_old_chat_sessions)
    return {"message": "クリーンアップをバックグラウンドで開始しました"}

@router.get("/stats")
async def get_cleanup_stats() -> Dict[str, Any]:
    """クリーンアップ統計を取得"""
    try:
        # IMLogic設定の統計
        settings_count = supabase.table("v2_imlogic_settings")\
            .select("*", count="exact", head=True)\
            .execute()
        
        # チャットセッションの統計
        sessions_count = supabase.table("v2_chat_sessions")\
            .select("*", count="exact", head=True)\
            .execute()
        
        # メッセージの統計
        messages_count = supabase.table("v2_chat_messages")\
            .select("*", count="exact", head=True)\
            .execute()
        
        return {
            "imlogic_settings": settings_count.count,
            "chat_sessions": sessions_count.count,
            "chat_messages": messages_count.count,
            "retention_policy": {
                "settings_days": SETTINGS_RETENTION_DAYS,
                "max_settings_per_user": MAX_SETTINGS_PER_USER,
                "sessions_days": CHAT_SESSIONS_RETENTION_DAYS
            }
        }
    except Exception as e:
        logger.error(f"統計取得エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))