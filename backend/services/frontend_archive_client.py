"""
フロントエンドのアーカイブデータAPIクライアント
"""
import httpx
import logging
from typing import Dict, Any, List, Optional
import os

logger = logging.getLogger(__name__)

class FrontendArchiveClient:
    """フロントエンドのアーカイブデータを取得するクライアント"""
    
    def __init__(self):
        # 環境変数から取得、デフォルトは本番環境
        self.base_url = os.getenv("FRONTEND_URL", "https://www.dlogicai.in")
        self.timeout = 30.0  # タイムアウト30秒
        
    async def search_archive_races(self, venue: str, race_number: int, specific_date: Optional[str] = None) -> Dict[str, Any]:
        """
        フロントエンドのアーカイブからレースを検索
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/archive/search",
                    json={
                        "venue": venue,
                        "raceNumber": race_number,
                        "specificDate": specific_date
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "found": data.get("found", False),
                        "races": data.get("races", []),
                        "total_count": data.get("totalCount", 0),
                        "has_more": data.get("hasMore", False)
                    }
                else:
                    logger.error(f"Archive search failed: {response.status_code}")
                    return {
                        "found": False,
                        "races": [],
                        "total_count": 0,
                        "has_more": False
                    }
                    
        except Exception as e:
            logger.error(f"Archive search error: {e}")
            # エラー時はフォールバック（既存のローカルデータを使用）
            return {
                "found": False,
                "races": [],
                "total_count": 0,
                "has_more": False,
                "error": str(e)
            }
    
    async def get_race_data(self, date: str, venue: str, race_number: int) -> Optional[Dict[str, Any]]:
        """
        特定のレースの詳細データを取得
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/archive/get-race",
                    json={
                        "date": date,
                        "venue": venue,
                        "raceNumber": race_number
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("found"):
                        return data.get("raceData")
                    return None
                else:
                    logger.error(f"Get race data failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Get race data error: {e}")
            return None

# シングルトンインスタンス
frontend_archive_client = FrontendArchiveClient()