"""
本日のレース情報を一時的に保存・管理するAPI
メモリベースで当日のみ有効
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

router = APIRouter(prefix="/api/today-races/ocr", tags=["Today Races OCR"])
logger = logging.getLogger(__name__)

# メモリ内でレース情報を管理（本番環境ではRedis等を推奨）
# 構造: {date: {race_id: race_data}}
race_storage: Dict[str, Dict[str, Any]] = {}

class RaceData(BaseModel):
    """レースデータのモデル"""
    race_date: str
    venue: str
    race_number: int
    race_name: str
    horses: List[str]

class RaceResponse(BaseModel):
    """レース情報レスポンス"""
    race_id: str
    race_date: str
    venue: str
    race_number: int
    race_name: str
    horses: List[str]
    created_at: str

@router.post("/")
async def save_race_data(race_data: RaceData):
    """OCRで取得したレース情報を保存"""
    try:
        # 日付のクリーンアップ（古いデータを削除）
        cleanup_old_races()
        
        # レースIDの生成（日付_競馬場_レース番号）
        race_id = f"{race_data.race_date}_{race_data.venue}_R{race_data.race_number}"
        
        # 日付をキーとして保存
        date_key = race_data.race_date
        if date_key not in race_storage:
            race_storage[date_key] = {}
        
        # レース情報を保存
        race_storage[date_key][race_id] = {
            "race_id": race_id,
            "race_date": race_data.race_date,
            "venue": race_data.venue,
            "race_number": race_data.race_number,
            "race_name": race_data.race_name,
            "horses": race_data.horses,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"レース情報を保存: {race_id}")
        
        return {
            "status": "success",
            "race_id": race_id,
            "message": "レース情報を保存しました"
        }
        
    except Exception as e:
        logger.error(f"Save race data error: {e}")
        raise HTTPException(
            status_code=500,
            detail="レース情報の保存に失敗しました"
        )

@router.get("/")
async def get_today_races(date: Optional[str] = None):
    """指定日（デフォルトは今日）のレース一覧を取得"""
    try:
        # 日付の指定がない場合は今日
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 古いデータをクリーンアップ
        cleanup_old_races()
        
        # 指定日のレース情報を取得
        races = race_storage.get(date, {})
        
        # レース番号順にソート
        sorted_races = sorted(
            races.values(),
            key=lambda x: (x["venue"], x["race_number"])
        )
        
        return {
            "status": "success",
            "date": date,
            "count": len(sorted_races),
            "races": sorted_races
        }
        
    except Exception as e:
        logger.error(f"Get today races error: {e}")
        raise HTTPException(
            status_code=500,
            detail="レース情報の取得に失敗しました"
        )

@router.get("/{race_id}")
async def get_race_detail(race_id: str):
    """特定のレース詳細を取得"""
    try:
        # race_idから日付を抽出
        date_part = race_id.split("_")[0]
        
        # レース情報を検索
        if date_part in race_storage and race_id in race_storage[date_part]:
            race_data = race_storage[date_part][race_id]
            return {
                "status": "success",
                "race": race_data
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="指定されたレースが見つかりません"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get race detail error: {e}")
        raise HTTPException(
            status_code=500,
            detail="レース詳細の取得に失敗しました"
        )

@router.delete("/{race_id}")
async def delete_race(race_id: str):
    """レース情報を削除"""
    try:
        # race_idから日付を抽出
        date_part = race_id.split("_")[0]
        
        # レース情報を削除
        if date_part in race_storage and race_id in race_storage[date_part]:
            del race_storage[date_part][race_id]
            
            # 日付のレースが空になったら日付エントリも削除
            if not race_storage[date_part]:
                del race_storage[date_part]
            
            logger.info(f"レース情報を削除: {race_id}")
            
            return {
                "status": "success",
                "message": "レース情報を削除しました"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="指定されたレースが見つかりません"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete race error: {e}")
        raise HTTPException(
            status_code=500,
            detail="レース情報の削除に失敗しました"
        )

def cleanup_old_races():
    """古いレース情報をクリーンアップ（前日以前のデータを削除）"""
    try:
        today = datetime.now().date()
        dates_to_remove = []
        
        for date_str in race_storage.keys():
            race_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if race_date < today:
                dates_to_remove.append(date_str)
        
        for date_str in dates_to_remove:
            del race_storage[date_str]
            logger.info(f"古いレース情報を削除: {date_str}")
            
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

@router.get("/status/info")
async def get_storage_status():
    """ストレージ状態を確認（デバッグ用）"""
    return {
        "status": "success",
        "storage_dates": list(race_storage.keys()),
        "total_races": sum(len(races) for races in race_storage.values()),
        "current_time": datetime.now().isoformat()
    }