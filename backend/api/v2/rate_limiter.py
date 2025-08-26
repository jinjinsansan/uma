"""
V2 レート制限ミドルウェア
APIの過負荷を防ぎ、2800人のユーザーに安定したサービスを提供
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """レート制限を管理するクラス"""
    
    def __init__(self):
        # ユーザーごとのリクエスト履歴
        self.request_history: Dict[str, list] = defaultdict(list)
        
        # レート制限設定
        self.limits = {
            'chat_message': {'max_requests': 30, 'window_seconds': 60},  # 1分間に30メッセージまで
            'settings_save': {'max_requests': 10, 'window_seconds': 60},  # 1分間に10回の設定保存まで
            'session_create': {'max_requests': 5, 'window_seconds': 60},  # 1分間に5セッションまで
            'default': {'max_requests': 60, 'window_seconds': 60}  # デフォルト: 1分間に60リクエスト
        }
        
        # 最終クリーンアップ時刻
        self.last_cleanup = time.time()
        
    def is_allowed(self, user_id: str, endpoint_type: str = 'default') -> tuple[bool, Optional[int]]:
        """
        リクエストが許可されるかチェック
        
        Returns:
            (is_allowed, retry_after_seconds)
        """
        current_time = time.time()
        
        # 定期的なメモリクリーンアップ（10分ごと）
        if current_time - self.last_cleanup > 600:
            self._cleanup_old_entries()
            self.last_cleanup = current_time
        
        # エンドポイントタイプの制限を取得
        limit_config = self.limits.get(endpoint_type, self.limits['default'])
        max_requests = limit_config['max_requests']
        window_seconds = limit_config['window_seconds']
        
        # ユーザーの履歴を取得
        user_history = self.request_history[user_id]
        
        # 時間窓内のリクエストをフィルタ
        window_start = current_time - window_seconds
        recent_requests = [t for t in user_history if t > window_start]
        
        # 履歴を更新
        self.request_history[user_id] = recent_requests
        
        # 制限チェック
        if len(recent_requests) >= max_requests:
            # 最も古いリクエストから時間窓が過ぎるまでの秒数を計算
            retry_after = int(recent_requests[0] + window_seconds - current_time) + 1
            return False, retry_after
        
        # リクエストを記録
        self.request_history[user_id].append(current_time)
        return True, None
    
    def _cleanup_old_entries(self):
        """古いエントリをメモリから削除"""
        current_time = time.time()
        max_window = max(limit['window_seconds'] for limit in self.limits.values())
        cutoff_time = current_time - max_window - 60  # 余裕を持って削除
        
        # 空のユーザーまたは古いエントリのみのユーザーを削除
        users_to_delete = []
        for user_id, history in self.request_history.items():
            recent_history = [t for t in history if t > cutoff_time]
            if not recent_history:
                users_to_delete.append(user_id)
            else:
                self.request_history[user_id] = recent_history
        
        for user_id in users_to_delete:
            del self.request_history[user_id]
        
        if users_to_delete:
            logger.info(f"レート制限履歴クリーンアップ: {len(users_to_delete)}ユーザー分削除")

# グローバルインスタンス
rate_limiter = RateLimiter()

def check_rate_limit(user_id: str, endpoint_type: str = 'default') -> tuple[bool, Optional[int]]:
    """レート制限をチェックする関数"""
    return rate_limiter.is_allowed(user_id, endpoint_type)