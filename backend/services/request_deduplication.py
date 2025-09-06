"""
リクエスト重複排除サービス
同一ユーザーからの重複リクエストを防ぐ
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)

class RequestDeduplication:
    """リクエストの重複を排除するサービス"""
    
    def __init__(self, ttl_seconds: int = 2):
        """
        Args:
            ttl_seconds: 重複とみなす時間窓（デフォルト2秒）
        """
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.ttl = ttl_seconds
        
    def _generate_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """リクエストのユニークキーを生成"""
        # エンドポイントとパラメータからハッシュを生成
        key_str = f"{endpoint}:{str(sorted(params.items()))}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def deduplicate(self, endpoint: str, params: Dict[str, Any], func):
        """
        重複リクエストを排除して関数を実行
        
        Args:
            endpoint: APIエンドポイント
            params: リクエストパラメータ
            func: 実行する非同期関数
            
        Returns:
            関数の実行結果（重複の場合は最初のリクエストの結果）
        """
        key = self._generate_key(endpoint, params)
        
        # 既に同じリクエストが処理中の場合
        if key in self.pending_requests:
            logger.info(f"重複リクエストを検出: {endpoint} - 既存の結果を待機")
            try:
                # 既存のリクエストの結果を待つ
                result = await self.pending_requests[key]
                return result
            except Exception as e:
                logger.error(f"重複リクエストの待機中にエラー: {e}")
                # エラーの場合は新規実行を許可
                pass
        
        # 新規リクエストの場合
        future = asyncio.create_future()
        self.pending_requests[key] = future
        
        try:
            # 実際の処理を実行
            result = await func()
            future.set_result(result)
            
            # TTL後にキャッシュから削除
            asyncio.create_task(self._cleanup_after_ttl(key))
            
            return result
            
        except Exception as e:
            future.set_exception(e)
            # エラーの場合は即座に削除
            if key in self.pending_requests:
                del self.pending_requests[key]
            raise
    
    async def _cleanup_after_ttl(self, key: str):
        """TTL後にキャッシュから削除"""
        await asyncio.sleep(self.ttl)
        if key in self.pending_requests:
            del self.pending_requests[key]
            logger.debug(f"重複排除キャッシュから削除: {key}")

# グローバルインスタンス
request_dedup = RequestDeduplication(ttl_seconds=2)