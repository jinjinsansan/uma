"""
V2システムヘルスチェックAPI
"""
from fastapi import APIRouter, HTTPException
from typing import Dict
import logging
import os
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/health", tags=["v2-health"])

@router.get("/")
async def health_check() -> Dict:
    """V2システムのヘルスチェック"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0",
        "services": {}
    }
    
    # Supabase接続チェック
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if supabase_url and supabase_key:
            supabase = create_client(supabase_url, supabase_key)
            # テストクエリ
            result = supabase.table("v2_user_points").select("count", count="exact").execute()
            health_status["services"]["supabase"] = {
                "status": "connected",
                "v2_user_points_count": result.count or 0
            }
        else:
            health_status["services"]["supabase"] = {
                "status": "no_credentials",
                "message": "Supabase環境変数が設定されていません"
            }
    except Exception as e:
        health_status["services"]["supabase"] = {
            "status": "error",
            "error": str(e)
        }
    
    # IMLogicエンジンチェック
    try:
        from services.imlogic_engine import get_imlogic_engine
        engine = get_imlogic_engine()
        health_status["services"]["imlogic"] = {
            "status": "ready",
            "jockey_data_loaded": hasattr(engine, 'jockey_manager'),
            "dlogic_data_loaded": hasattr(engine, 'dlogic_manager')
        }
    except Exception as e:
        health_status["services"]["imlogic"] = {
            "status": "error",
            "error": str(e)
        }
    
    # 全体のステータス判定
    all_services_healthy = all(
        service.get("status") in ["connected", "ready"] 
        for service in health_status["services"].values()
    )
    
    if not all_services_healthy:
        health_status["status"] = "degraded"
    
    return health_status

@router.get("/ready")
async def readiness_check() -> Dict:
    """準備状態チェック"""
    health = await health_check()
    
    if health["status"] == "healthy":
        return {"ready": True, "message": "V2システムは準備完了です"}
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "ready": False,
                "message": "V2システムは準備中です",
                "services": health["services"]
            }
        )

@router.get("/stats")
async def system_stats() -> Dict:
    """システム統計情報を取得"""
    stats = {
        "timestamp": datetime.now().isoformat(),
        "rate_limiter": {},
        "cache": {},
        "cleanup": {}
    }
    
    # レート制限統計
    try:
        from api.v2.rate_limiter import rate_limiter
        stats["rate_limiter"] = {
            "active_users": len(rate_limiter.request_history),
            "limits": rate_limiter.limits
        }
    except Exception as e:
        stats["rate_limiter"]["error"] = str(e)
    
    # キャッシュ統計
    try:
        from services.v2.cache_manager import cache_manager
        stats["cache"] = cache_manager.get_stats()
    except Exception as e:
        stats["cache"]["error"] = str(e)
    
    # クリーンアップ統計（Supabase経由）
    try:
        from api.v2.cleanup_settings import get_cleanup_stats
        stats["cleanup"] = await get_cleanup_stats()
    except Exception as e:
        stats["cleanup"]["error"] = str(e)
    
    return stats