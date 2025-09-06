"""
V2ポイント設定のキャッシュ管理
RedisまたはメモリキャッシュでDB負荷を削減
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

# Redisキャッシュの試行
try:
    from services.redis_cache import get_redis_cache
    redis_cache = get_redis_cache()
    REDIS_AVAILABLE = redis_cache.is_connected()
    if REDIS_AVAILABLE:
        logger.info("Redis available for V2 points config cache")
except:
    redis_cache = None
    REDIS_AVAILABLE = False
    logger.info("Redis not available, using memory cache for V2 points config")

class PointsConfigCache:
    """ポイント設定のキャッシュ（Redis優先、フォールバックでメモリ）"""
    
    def __init__(self, ttl_minutes: int = 60):
        self.memory_cache: Optional[Dict[str, Any]] = None
        self.last_updated: Optional[datetime] = None
        self.ttl = timedelta(minutes=ttl_minutes)
        self.ttl_seconds = ttl_minutes * 60
        self.redis_key = "v2:points_config"
        
    def get(self) -> Optional[Dict[str, Any]]:
        """キャッシュから設定を取得（Redis優先）"""
        # 1. Redisから取得を試みる
        if REDIS_AVAILABLE and redis_cache:
            try:
                cached_data = redis_cache.get(self.redis_key)
                if cached_data is not None:
                    logger.debug("Points config Redis cache hit")
                    return cached_data
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        # 2. メモリキャッシュから取得
        if self.memory_cache is None:
            return None
            
        if self.last_updated is None:
            return None
            
        # TTL確認
        if datetime.now() - self.last_updated > self.ttl:
            logger.info("Points config memory cache expired")
            self.memory_cache = None
            self.last_updated = None
            return None
            
        logger.debug("Points config memory cache hit")
        return self.memory_cache
        
    def set(self, config: Dict[str, Any]) -> None:
        """キャッシュに設定を保存（Redis + メモリ）"""
        # 1. Redisに保存
        if REDIS_AVAILABLE and redis_cache:
            try:
                redis_cache.set(self.redis_key, config, ttl=self.ttl_seconds)
                logger.info(f"Points config cached in Redis for {self.ttl_seconds} seconds")
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        # 2. メモリキャッシュにも保存（フォールバック）
        self.memory_cache = config
        self.last_updated = datetime.now()
        logger.info(f"Points config cached in memory until {self.last_updated + self.ttl}")
        
    def clear(self) -> None:
        """キャッシュをクリア（Redis + メモリ）"""
        # 1. Redisから削除
        if REDIS_AVAILABLE and redis_cache:
            try:
                redis_cache.delete(self.redis_key)
                logger.info("Points config Redis cache cleared")
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        # 2. メモリキャッシュもクリア
        self.memory_cache = None
        self.last_updated = None
        logger.info("Points config memory cache cleared")

# グローバルインスタンス
points_config_cache = PointsConfigCache(ttl_minutes=60)