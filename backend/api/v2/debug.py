"""
デバッグ用エンドポイント
本番環境での設定値確認用
"""
from fastapi import APIRouter
from api.v2.config import v2_config
from api.v2.config_cache import points_config_cache
import os

router = APIRouter()

@router.get("/config-check")
async def check_config():
    """現在の設定値を確認"""

    # キャッシュの状態を確認
    cached_config = points_config_cache.get()

    # 環境変数を確認
    env_value = os.getenv("V2_POINTS_PER_CHAT")

    # データベース設定を確認
    db_config = v2_config._get_db_config()

    return {
        "current_POINTS_PER_CHAT": v2_config.POINTS_PER_CHAT,
        "env_V2_POINTS_PER_CHAT": env_value,
        "db_chat_cost_points": db_config.get("chat_cost_points") if db_config else None,
        "cache_exists": cached_config is not None,
        "cached_value": cached_config.get("chat_cost_points") if cached_config else None,
        "message": "0ポイントで動作するはずの値" if v2_config.POINTS_PER_CHAT == 0 else f"⚠️ {v2_config.POINTS_PER_CHAT}ポイント必要"
    }

@router.post("/clear-cache")
async def clear_cache():
    """キャッシュを強制クリア"""
    points_config_cache.clear()
    v2_config._config_cache = None
    v2_config._last_cache_update = None

    # クリア後の値を確認
    new_value = v2_config.POINTS_PER_CHAT

    return {
        "message": "キャッシュをクリアしました",
        "new_POINTS_PER_CHAT": new_value,
        "status": "success" if new_value == 0 else "warning"
    }