"""
Supabase クライアント設定
アーカイブレースデータへのアクセス用
"""
import os
from typing import Optional
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabaseクライアントのシングルトン"""
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            supabase_url = os.getenv("SUPABASE_URL")
            # SERVICE_KEYまたはSERVICE_ROLE_KEYの両方を試す
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                logger.warning("Supabase環境変数が設定されていません")
                self._client = None
            else:
                try:
                    self._client = create_client(supabase_url, supabase_key)
                    logger.info("Supabaseクライアントを初期化しました")
                except Exception as e:
                    logger.error(f"Supabaseクライアントの初期化に失敗: {e}")
                    self._client = None
    
    @property
    def client(self) -> Optional[Client]:
        """Supabaseクライアントを取得"""
        return self._client
    
    def is_available(self) -> bool:
        """Supabaseが利用可能かチェック"""
        return self._client is not None

# シングルトンインスタンス
supabase_client = SupabaseClient()