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

class RaceUpdateData(BaseModel):
    """レース更新データのモデル"""
    race_name: Optional[str] = None
    horses: Optional[List[str]] = None

class VisibilityData(BaseModel):
    """表示設定データのモデル"""
    is_visible: bool

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
            "is_visible": True,  # デフォルトで表示
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
async def get_today_races(date: Optional[str] = None, include_hidden: bool = False):
    """指定日（デフォルトは今日）のレース一覧を取得"""
    try:
        # 日付の指定がない場合は今日
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 古いデータをクリーンアップ
        cleanup_old_races()
        
        # 指定日のレース情報を取得
        races = race_storage.get(date, {})
        
        # 表示設定に基づいてフィルタリング（include_hidden=Trueの場合は全て含む）
        if not include_hidden:
            filtered_races = {k: v for k, v in races.items() if v.get("is_visible", True)}
        else:
            filtered_races = races
        
        # レース番号順にソート
        sorted_races = sorted(
            filtered_races.values(),
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

@router.put("/{race_id}")
async def update_race(race_id: str, update_data: RaceUpdateData):
    """レース情報を更新"""
    try:
        # race_idから日付を抽出
        date_part = race_id.split("_")[0]
        
        # レース情報を検索
        if date_part in race_storage and race_id in race_storage[date_part]:
            race_data = race_storage[date_part][race_id]
            
            # 更新するフィールドのみ適用
            if update_data.race_name is not None:
                race_data["race_name"] = update_data.race_name
            if update_data.horses is not None:
                race_data["horses"] = update_data.horses
            
            logger.info(f"レース情報を更新: {race_id}")
            
            return {
                "status": "success",
                "message": "レース情報を更新しました",
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
        logger.error(f"Update race error: {e}")
        raise HTTPException(
            status_code=500,
            detail="レース情報の更新に失敗しました"
        )

@router.put("/{race_id}/visibility")
async def toggle_race_visibility(race_id: str, visibility_data: VisibilityData):
    """レースの表示/非表示を切り替え"""
    try:
        # race_idから日付を抽出
        date_part = race_id.split("_")[0]
        
        # レース情報を検索
        if date_part in race_storage and race_id in race_storage[date_part]:
            race_data = race_storage[date_part][race_id]
            race_data["is_visible"] = visibility_data.is_visible
            
            logger.info(f"レース表示設定を更新: {race_id} -> {visibility_data.is_visible}")
            
            return {
                "status": "success",
                "message": f"レースを{'表示' if visibility_data.is_visible else '非表示'}に設定しました",
                "is_visible": visibility_data.is_visible
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="指定されたレースが見つかりません"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Toggle visibility error: {e}")
        raise HTTPException(
            status_code=500,
            detail="表示設定の更新に失敗しました"
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