"""
V2 キャッシュマネージャー
頻繁にアクセスされるデータをメモリに保持して高速化
"""
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """キャッシュを管理するクラス"""
    
    def __init__(self):
        # キャッシュストレージ
        self.cache: Dict[str, Dict[str, Any]] = {}
        
        # キャッシュ設定（秒単位）
        self.ttl_settings = {
            'race_analysis': 300,      # 5分
            'imlogic_result': 60,      # 1分（設定が変わる可能性があるため短め）
            'user_settings': 30,       # 30秒
            'session_data': 120,       # 2分
            'default': 60              # デフォルト1分
        }
        
        # キャッシュ統計
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
    
    def get(self, key: str, cache_type: str = 'default') -> Optional[Any]:
        """キャッシュから値を取得"""
        if key in self.cache:
            entry = self.cache[key]
            
            # 有効期限チェック
            if datetime.now() < entry['expires']:
                self.stats['hits'] += 1
                logger.debug(f"キャッシュヒット: {key[:20]}...")
                return entry['value']
            else:
                # 期限切れエントリを削除
                del self.cache[key]
                self.stats['evictions'] += 1
        
        self.stats['misses'] += 1
        return None
    
    def set(self, key: str, value: Any, cache_type: str = 'default', ttl: Optional[int] = None) -> None:
        """キャッシュに値を設定"""
        # TTLを決定
        if ttl is None:
            ttl = self.ttl_settings.get(cache_type, self.ttl_settings['default'])
        
        expires = datetime.now() + timedelta(seconds=ttl)
        
        # メモリ制限チェック（簡易版: 1000エントリまで）
        if len(self.cache) >= 1000:
            self._evict_oldest()
        
        self.cache[key] = {
            'value': value,
            'expires': expires,
            'cache_type': cache_type
        }
        self.stats['sets'] += 1
        logger.debug(f"キャッシュ設定: {key[:20]}... (TTL: {ttl}秒)")
    
    def delete(self, key: str) -> bool:
        """キャッシュからエントリを削除"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear_expired(self) -> int:
        """期限切れエントリをすべて削除"""
        now = datetime.now()
        expired_keys = [k for k, v in self.cache.items() if now >= v['expires']]
        
        for key in expired_keys:
            del self.cache[key]
            self.stats['evictions'] += 1
        
        return len(expired_keys)
    
    def _evict_oldest(self) -> None:
        """最も古いエントリを削除（LRU的な動作）"""
        if not self.cache:
            return
        
        # 期限が最も近いエントリを削除
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['expires'])
        del self.cache[oldest_key]
        self.stats['evictions'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'entries': len(self.cache),
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'evictions': self.stats['evictions'],
            'hit_rate': f"{hit_rate:.1f}%",
            'memory_entries': len(self.cache)
        }
    
    @staticmethod
    def generate_cache_key(*args, **kwargs) -> str:
        """引数からキャッシュキーを生成"""
        # 引数を文字列に変換してハッシュ化
        key_source = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_source.encode()).hexdigest()

# グローバルインスタンス
cache_manager = CacheManager()