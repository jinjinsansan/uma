"""
Dロジック用データ構造
ダンスインザダーク基準100点の指数計算に必要なデータモデル
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class HorseData(BaseModel):
    """馬の基本データ"""
    horse_id: str
    horse_name: str
    jockey_name: str
    trainer_name: str
    weight: float
    weight_change: float
    odds: Optional[float] = None

class RaceData(BaseModel):
    """レース基本データ"""
    race_code: str
    keibajo_name: str
    race_bango: str
    kyosomei_hondai: str
    kyori: str
    track_condition: str
    weather: str
    hasso_jikoku: str
    shusso_tosu: int
    horses: List[HorseData]

class DLogicCalculationRequest(BaseModel):
    """Dロジック計算リクエスト"""
    race_data: RaceData
    calculation_type: str = "dance_in_the_dark_based"

class DLogicCalculationResult(BaseModel):
    """Dロジック計算結果"""
    race_code: str
    calculation_time: datetime
    horses: List[Dict[str, Any]]  # 馬ごとの指数
    base_horse: str = "ダンスインザダーク"
    base_score: int = 100
    status: str = "success"
    message: str = ""

class KnowledgeBaseData(BaseModel):
    """ナレッジベースデータ"""
    dance_in_the_dark_data: Dict[str, Any]
    horse_racing_general_data: Dict[str, Any]
    last_updated: datetime 