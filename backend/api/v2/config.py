"""
V2システムの設定
環境変数から柔軟にポイント設定を読み込む
"""
import os
from dotenv import load_dotenv

load_dotenv()

class V2Config:
    """V2システムの設定"""
    
    # ポイント付与設定（環境変数から読み込み、デフォルト値を設定）
    POINTS_GOOGLE_AUTH = int(os.getenv("V2_POINTS_GOOGLE_AUTH", "2"))
    POINTS_LINE_CONNECT = int(os.getenv("V2_POINTS_LINE_CONNECT", "12"))
    POINTS_REFERRAL = int(os.getenv("V2_POINTS_REFERRAL", "22"))
    POINTS_DAILY_LOGIN = int(os.getenv("V2_POINTS_DAILY_LOGIN", "1"))
    POINTS_PER_CHAT = int(os.getenv("V2_POINTS_PER_CHAT", "1"))
    
    # その他の設定
    MAX_CHATS_PER_DAY = int(os.getenv("V2_MAX_CHATS_PER_DAY", "50"))  # 1日の最大チャット数
    
    @classmethod
    def get_points_summary(cls):
        """現在のポイント設定のサマリーを取得"""
        return {
            "google_auth": cls.POINTS_GOOGLE_AUTH,
            "line_connect": cls.POINTS_LINE_CONNECT,
            "referral": cls.POINTS_REFERRAL,
            "daily_login": cls.POINTS_DAILY_LOGIN,
            "per_chat": cls.POINTS_PER_CHAT,
            "max_total": cls.POINTS_GOOGLE_AUTH + cls.POINTS_LINE_CONNECT + cls.POINTS_REFERRAL
        }

# シングルトンインスタンス
v2_config = V2Config()