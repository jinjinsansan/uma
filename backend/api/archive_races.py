"""
アーカイブレース検索API
フロントエンドのアーカイブデータを検索して返す
"""
from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# アーカイブレースのメタデータ（フロントエンドと同期）
# 本来はデータベースで管理すべきだが、現状はハードコード
ARCHIVE_RACES_METADATA = [
    {
        "date": "2025-08-16",
        "venue": "新潟",
        "races": [
            {"race_number": 6, "race_name": "中郷T (15:10発走) [1勝クラス]"},
            {"race_number": 7, "race_name": "糸魚川特別 (15:45発走) [2勝クラス]"},
            {"race_number": 8, "race_name": "3歳以上1勝クラス (16:15発走) [定量]"},
            {"race_number": 9, "race_name": "村上特別 (16:50発走) [3勝クラス]"}
        ]
    },
    {
        "date": "2025-08-16",
        "venue": "中京",
        "races": [
            {"race_number": 6, "race_name": "知立T (15:10発走) [1勝クラス]"},
            {"race_number": 7, "race_name": "3歳以上1勝クラス (15:45発走) [定量]"},
            {"race_number": 8, "race_name": "3歳以上2勝クラス (16:15発走) [ハンデ]"}
        ]
    },
    {
        "date": "2025-08-16",
        "venue": "札幌",
        "races": [
            {"race_number": 9, "race_name": "富良野特別 (17:00発走) [2勝クラス]"},
            {"race_number": 10, "race_name": "十勝岳T (17:30発走) [3勝クラス]"},
            {"race_number": 11, "race_name": "札幌記念 (18:05発走) [G2]", "grade": "G2"},
            {"race_number": 12, "race_name": "大雪H (18:45発走) [OP・L]"}
        ]
    }
]

@router.get("/api/archive-races/search")
async def search_archive_races(
    venue: Optional[str] = Query(None, description="開催場（例: 新潟）"),
    race_number: Optional[int] = Query(None, description="レース番号（例: 7）"),
    date: Optional[str] = Query(None, description="日付（例: 2025-08-16）"),
    race_name: Optional[str] = Query(None, description="レース名（部分一致）")
) -> Dict[str, Any]:
    """
    アーカイブレースを検索
    
    Returns:
        {
            "matches": [
                {
                    "date": "2025-08-16",
                    "venue": "新潟",
                    "race_number": 7,
                    "race_name": "糸魚川特別",
                    "archive_url": "/archive/2025-08-16",
                    "has_jockey_data": true
                }
            ],
            "count": 1
        }
    """
    try:
        matches = []
        
        for archive in ARCHIVE_RACES_METADATA:
            # 日付フィルタ
            if date and archive["date"] != date:
                continue
            
            # 開催場フィルタ
            if venue and archive["venue"] != venue:
                continue
            
            # レース検索
            for race in archive["races"]:
                # レース番号フィルタ
                if race_number and race["race_number"] != race_number:
                    continue
                
                # レース名フィルタ（部分一致）
                if race_name and race_name not in race["race_name"]:
                    continue
                
                # 条件に合致したレースを追加
                matches.append({
                    "date": archive["date"],
                    "venue": archive["venue"],
                    "race_number": race["race_number"],
                    "race_name": race["race_name"],
                    "archive_url": f"/archive/{archive['date']}",
                    "has_jockey_data": archive["date"] == "2025-08-16" and archive["venue"] == "札幌" and race["race_number"] == 11,
                    "grade": race.get("grade", "")
                })
        
        # 日付とレース番号でソート
        matches.sort(key=lambda x: (x["date"], x["race_number"]))
        
        return {
            "matches": matches,
            "count": len(matches)
        }
        
    except Exception as e:
        logger.error(f"アーカイブレース検索エラー: {e}")
        return {
            "matches": [],
            "count": 0,
            "error": str(e)
        }

@router.get("/api/archive-races/dates")
async def get_archive_dates() -> Dict[str, Any]:
    """
    アーカイブが存在する日付リストを取得
    """
    try:
        dates = list(set(archive["date"] for archive in ARCHIVE_RACES_METADATA))
        dates.sort(reverse=True)  # 新しい日付順
        
        return {
            "dates": dates,
            "count": len(dates)
        }
        
    except Exception as e:
        logger.error(f"アーカイブ日付取得エラー: {e}")
        return {
            "dates": [],
            "count": 0,
            "error": str(e)
        }