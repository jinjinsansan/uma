#!/usr/bin/env python3
"""
キャッシュサービス
OpenAI APIとD-Logic分析結果をキャッシュして負荷軽減
Redis統合版 - Redisが利用可能な場合は優先的に使用
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import hashlib
import json
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Redisキャッシュをインポート（利用可能な場合）
try:
    from services.redis_cache import get_redis_cache, RedisCache
    REDIS_AVAILABLE = True
    logger.info("Redis cache module loaded successfully")
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis cache not available, using memory cache only")

class CacheService:
    """メモリベースのキャッシュサービス"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.hit_count = 0
        self.miss_count = 0
        
        # Redisクライアントを初期化（利用可能な場合）
        self.redis_cache: Optional[RedisCache] = None
        if REDIS_AVAILABLE:
            try:
                self.redis_cache = get_redis_cache()
                if self.redis_cache.is_connected():
                    logger.info("Redis cache connected successfully")
                else:
                    logger.warning("Redis cache not connected, using memory cache")
                    self.redis_cache = None
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {e}")
                self.redis_cache = None
        
        # TTL設定（用途別）
        self.ttl_settings = {
            'chat_response': timedelta(hours=48),      # チャット応答: 48時間（増加）
            'dlogic_analysis': timedelta(hours=72),    # D-Logic分析: 72時間（増加）
            'imlogic_analysis': timedelta(hours=72),   # IMLogic分析: 72時間
            'weather_analysis': timedelta(hours=24),   # 天候適性: 24時間（増加）
            'faq_response': timedelta(days=14),        # FAQ: 14日間（増加）
            'race_analysis': timedelta(hours=12),      # レース分析: 12時間（増加）
            'horse_data': timedelta(days=7),           # 馬データ: 7日間
            'jockey_data': timedelta(days=7),          # 騎手データ: 7日間
        }
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """キャッシュキーを生成（正規化付き）"""
        # データの正規化
        if isinstance(data, dict):
            # 辞書の値を正規化
            normalized_data = {}
            for k, v in data.items():
                # 正規化を削除し、そのまま使用
                normalized_data[k] = v
            data_str = json.dumps(normalized_data, sort_keys=True, ensure_ascii=False)
        elif isinstance(data, list):
            # リストの場合はそのままソート
            data_str = json.dumps(sorted(data) if all(isinstance(x, str) for x in data) else data, ensure_ascii=False)
        else:
            # 文字列の場合はそのまま使用
            data_str = str(data)
        
        # MD5ハッシュでキーを生成
        hash_obj = hashlib.md5(data_str.encode('utf-8'))
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, prefix: str, data: Any) -> Optional[Any]:
        """キャッシュから取得（Redis優先）"""
        key = self._generate_key(prefix, data)
        
        # Redisから取得を試みる
        if self.redis_cache and self.redis_cache.is_connected():
            try:
                redis_key = f"dlogic:{key}"
                value = self.redis_cache.get(redis_key)
                if value is not None:
                    self.hit_count += 1
                    logger.debug(f"Redis cache hit for {redis_key}")
                    return value
            except Exception as e:
                logger.warning(f"Redis get failed: {e}, falling back to memory cache")
        
        # メモリキャッシュから取得
        if key in self.cache:
            entry = self.cache[key]
            # 有効期限チェック
            if datetime.now() < entry['expires_at']:
                self.hit_count += 1
                print(f"📋 キャッシュヒット: {prefix} (ヒット率: {self.get_hit_rate():.1f}%)")
                return entry['value']
            else:
                # 期限切れは削除
                del self.cache[key]
        
        self.miss_count += 1
        return None
    
    def set(self, prefix: str, data: Any, value: Any, ttl_override: Optional[timedelta] = None) -> None:
        """キャッシュに保存（Redis優先）"""
        key = self._generate_key(prefix, data)
        
        # TTL決定
        ttl = ttl_override or self.ttl_settings.get(prefix, timedelta(hours=24))
        
        # Redisに保存を試みる
        if self.redis_cache and self.redis_cache.is_connected():
            try:
                redis_key = f"dlogic:{key}"
                ttl_seconds = int(ttl.total_seconds())
                success = self.redis_cache.set(redis_key, value, ttl=ttl_seconds)
                if success:
                    logger.debug(f"Saved to Redis cache: {redis_key}")
            except Exception as e:
                logger.warning(f"Redis set failed: {e}, saving to memory cache")
        
        # メモリキャッシュにも保存（フォールバック）
        self.cache[key] = {
            'value': value,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + ttl,
            'prefix': prefix
        }
        
        # メモリ管理（最大1000エントリ）
        if len(self.cache) > 1000:
            self._cleanup_old_entries()
    
    def _cleanup_old_entries(self):
        """古いエントリを削除"""
        now = datetime.now()
        # 期限切れを削除
        expired_keys = [k for k, v in self.cache.items() if v['expires_at'] < now]
        for key in expired_keys:
            del self.cache[key]
        
        # それでも多い場合は古い順に削除
        if len(self.cache) > 800:
            sorted_items = sorted(
                self.cache.items(),
                key=lambda x: x[1]['created_at']
            )
            for key, _ in sorted_items[:200]:
                del self.cache[key]
    
    def clear_prefix(self, prefix: str):
        """特定のプレフィックスのキャッシュをクリア"""
        keys_to_delete = [k for k, v in self.cache.items() if v.get('prefix') == prefix]
        for key in keys_to_delete:
            del self.cache[key]
        print(f"🗑️ {prefix}のキャッシュをクリア: {len(keys_to_delete)}件")
    
    def get_hit_rate(self) -> float:
        """キャッシュヒット率を取得"""
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return (self.hit_count / total) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計情報を取得"""
        stats = {
            'total_entries': len(self.cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': self.get_hit_rate(),
            'memory_usage_mb': self._estimate_memory_usage(),
            'entries_by_prefix': {}
        }
        
        # プレフィックス別の統計
        for key, entry in self.cache.items():
            prefix = entry.get('prefix', 'unknown')
            if prefix not in stats['entries_by_prefix']:
                stats['entries_by_prefix'][prefix] = 0
            stats['entries_by_prefix'][prefix] += 1
        
        return stats
    
    def _estimate_memory_usage(self) -> float:
        """メモリ使用量を推定（MB）"""
        # 簡易的な推定
        total_size = 0
        for key, entry in self.cache.items():
            # キーのサイズ
            total_size += len(key.encode('utf-8'))
            # 値のサイズ（JSON化して推定）
            try:
                value_str = json.dumps(entry, ensure_ascii=False)
                total_size += len(value_str.encode('utf-8'))
            except:
                total_size += 1000  # エラー時は1KBと仮定
        
        return total_size / (1024 * 1024)  # MB変換


# グローバルインスタンス（全インスタンスで共有）
def prewarm_cache():
    """キャッシュをプリウォーミング（G1レース用）"""
    logger.info("Starting cache prewarming for G1 races...")
    
    # G1レースでよく使われる馬名リスト（例）
    popular_horses = [
        "イクイノックス", "ドウデュース", "リバティアイランド",
        "ソダシ", "ジオグリフ", "スターズオンアース"
    ]
    
    # 主要競馬場
    major_venues = ["東京", "中山", "京都", "阪神"]
    
    try:
        from services.fast_dlogic_engine import FastDLogicEngine
        engine = FastDLogicEngine()
        
        warmed = 0
        for horse_name in popular_horses:
            for venue in major_venues:
                # キャッシュキー生成用のデータ
                cache_data = {
                    'horse_name': horse_name,
                    'venue': venue,
                    'analysis_type': 'dlogic'
                }
                
                # キャッシュチェック
                key = cache_service._generate_key('dlogic_analysis', cache_data)
                
                # Redisキャッシュに存在しない場合のみ計算
                if cache_service.redis_cache and cache_service.redis_cache.is_connected():
                    redis_key = f"dlogic:{key}"
                    if not cache_service.redis_cache.exists(redis_key):
                        # D-Logic分析を実行（実際の計算）
                        try:
                            result = engine.analyze_single_horse(horse_name)
                            # 長めのTTLでキャッシュに保存
                            cache_service.set(
                                'dlogic_analysis',
                                cache_data,
                                result,
                                ttl_override=timedelta(days=3)  # G1用に3日間保持
                            )
                            warmed += 1
                            logger.debug(f"Prewarmed cache for {horse_name} at {venue}")
                        except Exception as e:
                            logger.warning(f"Failed to prewarm {horse_name}: {e}")
        
        logger.info(f"Cache prewarming completed. Warmed {warmed} entries.")
        return warmed
        
    except Exception as e:
        logger.error(f"Cache prewarming failed: {e}")
        return 0


def schedule_cache_prewarm():
    """定期的なキャッシュプリウォーミングをスケジュール"""
    import threading
    import time
    
    def prewarm_worker():
        while True:
            try:
                # 毎朝4時にプリウォーミング実行
                now = datetime.now()
                next_run = now.replace(hour=4, minute=0, second=0, microsecond=0)
                if next_run < now:
                    next_run += timedelta(days=1)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"Next cache prewarm scheduled in {wait_seconds/3600:.1f} hours")
                time.sleep(wait_seconds)
                
                # プリウォーミング実行
                prewarm_cache()
                
            except Exception as e:
                logger.error(f"Prewarm scheduler error: {e}")
                time.sleep(3600)  # エラー時は1時間後に再試行
    
    # バックグラウンドスレッドで実行
    thread = threading.Thread(target=prewarm_worker, daemon=True)
    thread.start()
    logger.info("Cache prewarm scheduler started")


# グローバルインスタンス（全インスタンスで共有）
cache_service = CacheService()


# デコレータ関数
def cached(prefix: str, ttl: Optional[timedelta] = None):
    """キャッシュデコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # キャッシュキー用のデータ
            cache_data = {
                'args': args,
                'kwargs': kwargs
            }
            
            # キャッシュチェック
            cached_value = cache_service.get(prefix, cache_data)
            if cached_value is not None:
                return cached_value
            
            # 実行してキャッシュ
            result = func(*args, **kwargs)
            cache_service.set(prefix, cache_data, result, ttl)
            return result
        
        return wrapper
    return decorator