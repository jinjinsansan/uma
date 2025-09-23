"""
Redisキャッシュ管理 - V1/V2共通
高速キャッシングとセッション管理
"""

import redis
import json
import pickle
import hashlib
from typing import Any, Optional, Union
from datetime import timedelta
import logging
import os
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class RedisCache:
    """Redisキャッシュマネージャー"""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
        password: str = None,
        decode_responses: bool = False,
        connection_pool_kwargs: dict = None
    ):
        """
        Redisクライアントを初期化
        
        Args:
            host: Redisホスト（環境変数REDIS_HOSTからも取得可能）
            port: Redisポート（環境変数REDIS_PORTからも取得可能）
            db: データベース番号
            password: 認証パスワード（環境変数REDIS_PASSWORDからも取得可能）
            decode_responses: 文字列として返すか
            connection_pool_kwargs: 接続プールの追加設定
        """
        # REDIS_URL環境変数があれば優先的に使用
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            logger.info(f"Attempting to connect to Redis with URL: {redis_url.split('@')[0] if '@' in redis_url else redis_url}...")
            # URLから接続
            try:
                self.client = redis.from_url(
                    redis_url,
                    decode_responses=decode_responses,
                    max_connections=50,
                    socket_keepalive=True
                    # socket_keepalive_optionsは環境依存のため削除
                )
                # 接続テスト
                self.client.ping()
                # URLからhost/portを抽出（表示用）
                if '@' in redis_url:
                    self.host = redis_url.split('@')[1].split(':')[0]
                else:
                    self.host = redis_url.replace('redis://', '').split(':')[0]
                self.port = 6379  # デフォルトポート
                logger.info(f"Connected to Redis via URL: {self.host}:{self.port}")
                return
            except Exception as e:
                import traceback
                logger.error(f"Failed to connect via REDIS_URL: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                self.client = None
                # フォールバックのためhost/portを設定
                self.host = 'localhost'
                self.port = 6379
                return
        
        # 個別パラメータから設定を取得
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = port or int(os.getenv('REDIS_PORT', '6379'))
        self.password = password or os.getenv('REDIS_PASSWORD')
        
        # 接続プールの設定
        pool_kwargs = {
            'host': self.host,
            'port': self.port,
            'db': db,
            'decode_responses': decode_responses,
            'max_connections': 50,
            'socket_keepalive': True
            # socket_keepalive_optionsは環境依存のため削除
        }
        
        if self.password:
            pool_kwargs['password'] = self.password
        
        if connection_pool_kwargs:
            pool_kwargs.update(connection_pool_kwargs)
        
        # 接続プールを作成
        self.pool = redis.ConnectionPool(**pool_kwargs)
        self.client = None
        self._connect()
    
    def _connect(self):
        """Redis接続を確立"""
        try:
            self.client = redis.Redis(connection_pool=self.pool)
            # 接続テスト
            self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.warning(f"Failed to connect to Redis: {e}. Running without cache.")
            self.client = None
    
    def is_connected(self) -> bool:
        """Redis接続状態を確認"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """キャッシュキーを生成（正規化付き）"""
        import unicodedata
        
        # 引数を正規化して文字列化
        normalized_parts = []
        
        for arg in args:
            if isinstance(arg, str):
                # 全角を半角に、大文字に統一、余分なスペース除去
                arg = unicodedata.normalize('NFKC', arg).upper().strip()
                arg = ' '.join(arg.split())
            normalized_parts.append(str(arg))
        
        # kwargsも同様に正規化
        for k, v in sorted(kwargs.items()):
            if isinstance(v, str):
                v = unicodedata.normalize('NFKC', v).upper().strip()
                v = ' '.join(v.split())
            normalized_parts.append(f"{k}={v}")
        
        key_content = "_".join(normalized_parts)
        
        # 長いキーはハッシュ化
        if len(key_content) > 200:
            key_hash = hashlib.md5(key_content.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        
        return f"{prefix}:{key_content}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """キャッシュから値を取得"""
        if not self.client:
            return default
        
        try:
            value = self.client.get(key)
            if value is None:
                return default
            
            # JSONとして復元を試みる
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Pickleとして復元を試みる
                try:
                    return pickle.loads(value)
                except:
                    # 文字列として返す
                    return value.decode('utf-8') if isinstance(value, bytes) else value
                    
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None,
        use_pickle: bool = False
    ) -> bool:
        """キャッシュに値を保存"""
        if not self.client:
            return False
        
        try:
            # TTLを秒に変換
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            # 値をシリアライズ
            if use_pickle:
                serialized_value = pickle.dumps(value)
            else:
                try:
                    serialized_value = json.dumps(value, ensure_ascii=False)
                except (TypeError, ValueError):
                    # JSON化できない場合はPickleを使用
                    serialized_value = pickle.dumps(value)
            
            # Redisに保存
            if ttl:
                return self.client.setex(key, ttl, serialized_value)
            else:
                return self.client.set(key, serialized_value)
                
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """キャッシュから削除"""
        if not self.client:
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """キーの存在確認"""
        if not self.client:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """TTLを設定"""
        if not self.client:
            return False
        
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            return bool(self.client.expire(key, ttl))
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """パターンに一致するキーを削除"""
        if not self.client:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    @contextmanager
    def lock(self, key: str, timeout: int = 10, blocking: bool = True):
        """分散ロック"""
        if not self.client:
            yield
            return
        
        lock_key = f"lock:{key}"
        lock = self.client.lock(lock_key, timeout=timeout)
        
        try:
            acquired = lock.acquire(blocking=blocking)
            if acquired:
                yield
            else:
                raise redis.LockError(f"Could not acquire lock for {key}")
        finally:
            try:
                lock.release()
            except redis.LockNotOwnedError:
                pass
    
    def close(self):
        """接続を閉じる"""
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")


# グローバルインスタンス（遅延初期化）
_redis_cache: Optional[RedisCache] = None

def get_redis_cache() -> RedisCache:
    """Redisキャッシュインスタンスを取得"""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache


# キャッシュデコレーター
def cached(
    prefix: str,
    ttl: Union[int, timedelta] = 3600,
    key_func: Optional[callable] = None
):
    """
    関数の結果をキャッシュするデコレーター
    
    Args:
        prefix: キャッシュキーのプレフィックス
        ttl: キャッシュの有効期限（秒またはtimedelta）
        key_func: カスタムキー生成関数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_redis_cache()
            
            # キーを生成
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = cache.generate_key(prefix, *args, **kwargs)
            
            # キャッシュから取得を試みる
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {key}")
                return cached_value
            
            # 関数を実行
            result = func(*args, **kwargs)
            
            # 結果をキャッシュ
            cache.set(key, result, ttl=ttl)
            logger.debug(f"Cache set for {key}")
            
            return result
        
        return wrapper
    return decorator


# 使用例：D-Logic計算結果のキャッシュ
@cached(prefix="dlogic", ttl=timedelta(hours=1))
def get_cached_dlogic_score(horse_name: str, race_date: str, venue: str) -> dict:
    """D-Logicスコアをキャッシュ付きで取得"""
    from services.dlogic_engine import DLogicEngine
    engine = DLogicEngine()
    return engine.calculate_single(horse_name, race_date, venue)