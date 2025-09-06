"""
Renderのコールドスタートを防ぐためのKeep-Aliveサービス
定期的にヘルスチェックエンドポイントを呼び出してインスタンスを温かく保つ
"""
import asyncio
import logging
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class KeepAliveService:
    """定期的にサービスを起こし続けるサービス"""
    
    def __init__(self):
        self.running = False
        # ローカルテスト用にlocalhostを使用
        import os
        if os.getenv("RENDER"):
            self.health_url = "https://uma-i30n.onrender.com/api/v2/health/"
        else:
            self.health_url = "http://localhost:8000/api/v2/health/"
        self.interval = 60  # テスト用に1分ごと（本番は300秒）
        
    async def start(self):
        """Keep-Aliveサービスを開始 - 無効化（パフォーマンス問題のため）"""
        logger.info("Keep-Alive service disabled (performance optimization)")
        return  # 完全に無効化
    
    async def _ping_health(self):
        """ヘルスチェックエンドポイントにリクエスト"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.health_url) as response:
                    if response.status == 200:
                        logger.info(f"✅ Keep-Alive ping successful at {datetime.now()}")
                    else:
                        logger.warning(f"Keep-Alive ping failed with status {response.status}")
        except Exception as e:
            logger.error(f"Keep-Alive ping error: {type(e).__name__}: {e}")
    
    def stop(self):
        """Keep-Aliveサービスを停止"""
        self.running = False
        logger.info("Keep-Alive service stopped")

# グローバルインスタンス
_keep_alive_service = None

def get_keep_alive_service():
    """Keep-Aliveサービスのシングルトンインスタンスを取得"""
    global _keep_alive_service
    if _keep_alive_service is None:
        _keep_alive_service = KeepAliveService()
    return _keep_alive_service