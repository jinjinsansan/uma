"""
騎手データAPI
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from services.jockey_data_manager import jockey_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/jockey-data/{jockey_name}")
async def get_jockey_data(jockey_name: str) -> Dict[str, Any]:
    """
    指定された騎手のデータを取得
    
    Args:
        jockey_name: 騎手名
    
    Returns:
        騎手データ
    """
    try:
        # 騎手データの存在確認
        if not jockey_manager.has_jockey_data(jockey_name):
            raise HTTPException(
                status_code=404,
                detail=f"騎手 {jockey_name} のデータが見つかりません"
            )
        
        # 騎手データ取得
        jockey_data = jockey_manager.jockey_data.get(jockey_name, {})
        
        return {
            "jockey_name": jockey_name,
            "data": jockey_data,
            "statistics": {
                "total_races": jockey_data.get("overall_stats", {}).get("total_races_analyzed", 0),
                "fukusho_rate": jockey_data.get("overall_stats", {}).get("overall_fukusho_rate", 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting jockey data: {e}")
        raise HTTPException(
            status_code=500,
            detail="騎手データの取得中にエラーが発生しました"
        )

@router.get("/jockey-list")
async def get_jockey_list() -> Dict[str, Any]:
    """
    利用可能な騎手リストを取得
    
    Returns:
        騎手リスト
    """
    try:
        jockey_names = list(jockey_manager.jockey_data.keys())
        
        return {
            "total": len(jockey_names),
            "jockeys": sorted(jockey_names)[:100]  # 最初の100名のみ返す
        }
        
    except Exception as e:
        logger.error(f"Error getting jockey list: {e}")
        raise HTTPException(
            status_code=500,
            detail="騎手リストの取得中にエラーが発生しました"
        )