"""
V2ポイント設定のキャッシュ管理
設定は頻繁に変更されないため、メモリキャッシュで十分
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PointsConfigCache:
    """ポイント設定のシンプルなメモリキャッシュ"""
    
    def __init__(self, ttl_minutes: int = 60):
        self.cache: Optional[Dict[str, Any]] = None
        self.last_updated: Optional[datetime] = None
        self.ttl = timedelta(minutes=ttl_minutes)
        
    def get(self) -> Optional[Dict[str, Any]]:
        """キャッシュから設定を取得"""
        if self.cache is None:
            return None
            
        if self.last_updated is None:
            return None
            
        # TTL確認
        if datetime.now() - self.last_updated > self.ttl:
            logger.info("Points config cache expired")
            self.cache = None
            self.last_updated = None
            return None
            
        logger.debug("Points config cache hit")
        return self.cache
        
    def set(self, config: Dict[str, Any]) -> None:
        """キャッシュに設定を保存"""
        self.cache = config
        self.last_updated = datetime.now()
        logger.info(f"Points config cached until {self.last_updated + self.ttl}")
        
    def clear(self) -> None:
        """キャッシュをクリア"""
        self.cache = None
        self.last_updated = None
        logger.info("Points config cache cleared")

# グローバルインスタンス
points_config_cache = PointsConfigCache(ttl_minutes=60)