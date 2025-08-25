"""
V2サービスパッケージ
既存システムとは完全に独立
"""
from .points_service import V2PointsService
from .chat_service import V2ChatService

__all__ = [
    "V2PointsService",
    "V2ChatService"
]