from fastapi import APIRouter, HTTPException
import logging
from services.cache_service import cache_service

router = APIRouter(prefix="/api/admin/cache", tags=["Admin Cache"])
logger = logging.getLogger(__name__)

@router.delete("/clear/{prefix}")
async def clear_cache_prefix(prefix: str):
    """特定のプレフィックスのキャッシュをクリア"""
    try:
        valid_prefixes = ['chat_response', 'dlogic_analysis', 'weather_analysis', 'faq_response', 'race_analysis']
        
        if prefix not in valid_prefixes:
            raise HTTPException(status_code=400, detail=f"Invalid prefix. Valid prefixes: {valid_prefixes}")
        
        cache_service.clear_prefix(prefix)
        
        return {
            "status": "success",
            "message": f"Cleared cache for prefix: {prefix}",
            "stats": cache_service.get_stats()
        }
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear-all")
async def clear_all_cache():
    """すべてのキャッシュをクリア"""
    try:
        cache_service.cache.clear()
        cache_service.hit_count = 0
        cache_service.miss_count = 0
        
        return {
            "status": "success",
            "message": "All cache cleared",
            "stats": cache_service.get_stats()
        }
    except Exception as e:
        logger.error(f"Cache clear all error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_cache_stats():
    """キャッシュ統計情報を取得"""
    try:
        return cache_service.get_stats()
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))