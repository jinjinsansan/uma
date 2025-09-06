"""
レート制限ミドルウェア
高負荷対策として、APIエンドポイントごとにレート制限を設定
"""
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

logger = logging.getLogger(__name__)

# レート制限の設定
# IPアドレスごとの制限
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]  # デフォルト: 1分間に100リクエスト
)

# エンドポイント別のレート制限設定
RATE_LIMITS = {
    # V2チャットAPI（重い処理）
    "/api/v2/chat/": "10 per minute",  # 1分間に10回まで
    "/api/v2/logic-chat": "10 per minute",
    
    # V1チャットAPI
    "/api/chat/d-logic": "20 per minute",
    "/api/chat/i-logic": "20 per minute",
    "/api/chat/my-logic": "20 per minute",
    
    # ヘルスチェック（高頻度OK）
    "/api/v2/health": "600 per minute",  # 1分間に600回（1秒10回）
    "/health": "600 per minute",
    
    # ポイント関連（軽い処理）
    "/api/v2/points/": "60 per minute",
    
    # デフォルト
    "*": "100 per minute"  # その他のエンドポイント
}

def get_rate_limit_for_path(path: str) -> str:
    """
    パスに応じたレート制限を取得
    """
    # 完全一致を優先
    if path in RATE_LIMITS:
        return RATE_LIMITS[path]
    
    # 部分一致を確認
    for pattern, limit in RATE_LIMITS.items():
        if pattern != "*" and pattern in path:
            logger.debug(f"レート制限適用: {path} -> {limit}")
            return limit
    
    # デフォルト
    return RATE_LIMITS.get("*", "100 per minute")

def create_rate_limit_middleware():
    """
    レート制限ミドルウェアを作成
    """
    async def rate_limit_middleware(request: Request, call_next):
        # パスに応じたレート制限を取得
        path = request.url.path
        rate_limit = get_rate_limit_for_path(path)
        
        # IPアドレスを取得
        client_ip = get_remote_address(request)
        
        # レート制限をチェック（実際の実装はslowapi側で行う）
        # ここではログ出力のみ
        if path.startswith("/api/"):
            logger.debug(f"リクエスト: {client_ip} -> {path} (制限: {rate_limit})")
        
        response = await call_next(request)
        return response
    
    return rate_limit_middleware