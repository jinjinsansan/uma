from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class DLogicScore(BaseModel):
    """Dロジック12項目スコア"""
    distance_aptitude: float  # 距離適性
    bloodline_evaluation: float  # 血統評価
    jockey_compatibility: float  # 騎手相性
    trainer_evaluation: float  # 調教師評価
    track_aptitude: float  # 馬場適性
    weather_aptitude: float  # 天候適性
    popularity_factor: float  # 人気度
    weight_impact: float  # 斤量影響
    horse_weight_impact: float  # 馬体重影響
    corner_specialist: float  # コーナー巧者度
    margin_analysis: float  # 着差分析
    time_index: float  # タイム指数

class HorseData(BaseModel):
    """馬データ"""
    name: str
    age: int
    sex: str  # 牡, 牝, セン
    weight: Optional[int] = None
    jockey: Optional[str] = None
    trainer: Optional[str] = None
    recent_form: Optional[List[int]] = None  # 最近の着順

class RaceConditions(BaseModel):
    """レース条件"""
    distance: int
    track_type: str  # 芝, ダート
    track_condition: str  # 良, 重, やや重, 不良
    weather: str  # 晴, 曇, 雨
    course: str  # 東京, 中山, 阪神など
    grade: Optional[str] = None  # G1, G2, G3など

class DLogicAnalysis(BaseModel):
    """Dロジック分析結果"""
    horse_name: str
    d_logic_score: DLogicScore
    total_score: float  # ダンスインザダーク基準100点
    rank: int
    confidence: str  # high, medium, low
    analysis_details: Dict[str, str]  # 各項目の詳細説明

class RacePrediction(BaseModel):
    """レース予想結果"""
    race_id: str
    race_name: str
    race_conditions: RaceConditions
    horses: List[DLogicAnalysis]
    calculation_time: datetime
    base_reference: str = "ダンスインザダーク基準"  # 内部基準（ユーザーには表示しない）

class ChatDLogicRequest(BaseModel):
    """チャット用Dロジックリクエスト"""
    message: str
    race_info: Optional[Dict] = None
    request_type: str = "d_logic"  # d_logic, race_info, general

class ChatDLogicResponse(BaseModel):
    """チャット用Dロジック応答"""
    message: str
    type: str  # text, d_logic, race_selection
    data: Optional[Dict] = None
    show_d_logic_button: bool = False 