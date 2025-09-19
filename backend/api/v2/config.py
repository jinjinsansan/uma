"""
V2システムの設定
環境変数から柔軟にポイント設定を読み込む
管理者パネルからの変更にも対応
"""
import os
from dotenv import load_dotenv
from typing import Optional
from supabase import create_client, Client
import json
import logging
from .config_cache import points_config_cache

load_dotenv()
logger = logging.getLogger(__name__)

class V2Config:
    """V2システムの設定（動的に更新可能）"""
    
    def __init__(self):
        self._config_cache = None
        self._last_cache_update = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Supabaseクライアントの初期化"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if supabase_url and supabase_key:
                self.supabase: Client = create_client(supabase_url, supabase_key)
            else:
                self.supabase = None
        except Exception as e:
            logger.warning(f"Supabase初期化失敗: {e}")
            self.supabase = None
    
    def _get_db_config(self) -> Optional[dict]:
        """データベースから設定を取得（キャンペーン設定優先）"""
        # まずキャッシュを確認
        cached = points_config_cache.get()
        if cached is not None:
            return cached
            
        if not self.supabase:
            return None
        
        try:
            # v2_points_configテーブルから最新の設定を取得
            result = self.supabase.table("v2_points_config")\
                .select("*")\
                .eq("is_active", True)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                config = result.data[0]
                # キャッシュに保存
                points_config_cache.set(config)
                return config
        except Exception as e:
            logger.debug(f"DB設定取得失敗（正常）: {e}")
        
        return None
    
    def get_points_value(self, key: str, default: int) -> int:
        """ポイント値を取得（DB > 環境変数 > デフォルト）"""
        # カラム名マッピング（config.py の key -> DBのカラム名）
        column_mapping = {
            "per_chat": "chat_cost_points",
            "google_auth": "google_auth_points",
            "line_connect": "line_connect_points",
            "daily_login": "daily_login_points",
            "referral_received": "referral_points"
        }

        # 1. データベースから取得を試みる
        db_config = self._get_db_config()
        if db_config:
            # マッピングされたカラム名で探す
            db_column = column_mapping.get(key, key)
            if db_column in db_config and db_config[db_column] is not None:
                return int(db_config[db_column])

        # 2. 環境変数から取得
        env_key = f"V2_POINTS_{key.upper()}"
        env_value = os.getenv(env_key)
        if env_value:
            return int(env_value)

        # 3. デフォルト値を返す
        return default
    
    # 基本ポイント設定
    @property
    def POINTS_GOOGLE_AUTH(self):
        return self.get_points_value("google_auth", 2)
    
    @property
    def POINTS_LINE_CONNECT(self):
        return self.get_points_value("line_connect", 24)
    
    @property
    def POINTS_DAILY_LOGIN(self):
        return self.get_points_value("daily_login", 2)
    
    @property
    def POINTS_PER_CHAT(self):
        return self.get_points_value("per_chat", 0)
    
    # 友達紹介ポイント（被紹介者）
    @property
    def POINTS_REFERRAL_RECEIVED(self):
        return self.get_points_value("referral_received", 10)
    
    # 友達紹介ポイント（紹介者 - 段階的）
    @property
    def POINTS_REFERRAL_1(self):
        return self.get_points_value("referral_1", 30)
    
    @property
    def POINTS_REFERRAL_2(self):
        return self.get_points_value("referral_2", 40)
    
    @property
    def POINTS_REFERRAL_3(self):
        return self.get_points_value("referral_3", 50)
    
    @property
    def POINTS_REFERRAL_4(self):
        return self.get_points_value("referral_4", 60)
    
    @property
    def POINTS_REFERRAL_5(self):
        return self.get_points_value("referral_5", 100)
    
    def get_referral_points_for_count(self, count: int) -> int:
        """紹介人数に応じたポイントを取得"""
        if count <= 0:
            return 0
        elif count == 1:
            return self.POINTS_REFERRAL_1
        elif count == 2:
            return self.POINTS_REFERRAL_2
        elif count == 3:
            return self.POINTS_REFERRAL_3
        elif count == 4:
            return self.POINTS_REFERRAL_4
        elif count >= 5:
            return self.POINTS_REFERRAL_5
        return 0
    
    def get_points_summary(self):
        """現在のポイント設定のサマリーを取得"""
        return {
            "google_auth": self.POINTS_GOOGLE_AUTH,
            "line_connect": self.POINTS_LINE_CONNECT,
            "daily_login": self.POINTS_DAILY_LOGIN,
            "referral_received": self.POINTS_REFERRAL_RECEIVED,
            "referral_levels": {
                "1": self.POINTS_REFERRAL_1,
                "2": self.POINTS_REFERRAL_2,
                "3": self.POINTS_REFERRAL_3,
                "4": self.POINTS_REFERRAL_4,
                "5": self.POINTS_REFERRAL_5
            },
            "per_chat": self.POINTS_PER_CHAT
        }

# シングルトンインスタンス
v2_config = V2Config()