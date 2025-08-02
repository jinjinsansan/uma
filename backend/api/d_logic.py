from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import json
import os
from datetime import datetime
import random

from models.d_logic_models import (
    DLogicScore, HorseData, RaceConditions, 
    DLogicAnalysis, RacePrediction, 
    ChatDLogicRequest, ChatDLogicResponse
)
from services.knowledge_base import KnowledgeBase

router = APIRouter()
kb = KnowledgeBase()

class DLogicEngine:
    """Dロジック12項目分析エンジン"""
    
    def __init__(self):
        self.knowledge_base = kb
        
    def calculate_d_logic_score(self, horse: HorseData, race_conditions: RaceConditions) -> DLogicScore:
        """12項目のDロジックスコアを計算"""
        
        # 1. 距離適性
        distance_aptitude = self._calculate_distance_aptitude(horse, race_conditions.distance)
        
        # 2. 血統評価
        bloodline_evaluation = self._calculate_bloodline_evaluation(horse)
        
        # 3. 騎手相性
        jockey_compatibility = self._calculate_jockey_compatibility(horse.jockey)
        
        # 4. 調教師評価
        trainer_evaluation = self._calculate_trainer_evaluation(horse.trainer)
        
        # 5. 馬場適性
        track_aptitude = self._calculate_track_aptitude(race_conditions)
        
        # 6. 天候適性
        weather_aptitude = self._calculate_weather_aptitude(race_conditions.weather)
        
        # 7. 人気度（サンプルデータ）
        popularity_factor = random.uniform(60, 95)
        
        # 8. 斤量影響（サンプルデータ）
        weight_impact = random.uniform(70, 90)
        
        # 9. 馬体重影響
        horse_weight_impact = self._calculate_horse_weight_impact(horse.weight)
        
        # 10. コーナー巧者度（サンプルデータ）
        corner_specialist = random.uniform(65, 90)
        
        # 11. 着差分析（サンプルデータ）
        margin_analysis = random.uniform(60, 95)
        
        # 12. タイム指数（サンプルデータ）
        time_index = random.uniform(70, 95)
        
        return DLogicScore(
            distance_aptitude=distance_aptitude,
            bloodline_evaluation=bloodline_evaluation,
            jockey_compatibility=jockey_compatibility,
            trainer_evaluation=trainer_evaluation,
            track_aptitude=track_aptitude,
            weather_aptitude=weather_aptitude,
            popularity_factor=popularity_factor,
            weight_impact=weight_impact,
            horse_weight_impact=horse_weight_impact,
            corner_specialist=corner_specialist,
            margin_analysis=margin_analysis,
            time_index=time_index
        )
    
    def _calculate_distance_aptitude(self, horse: HorseData, distance: int) -> float:
        """距離適性を計算"""
        distance_data = self.knowledge_base.get_reference_data("distance_aptitude")
        
        # 距離に基づく基準値を取得
        if distance <= 1400:
            base_score = distance_data.get("1400m", 75)
        elif distance <= 1600:
            base_score = distance_data.get("1600m", 85)
        elif distance <= 1800:
            base_score = distance_data.get("1800m", 95)
        elif distance <= 2000:
            base_score = distance_data.get("2000m", 100)
        elif distance <= 2200:
            base_score = distance_data.get("2200m", 90)
        else:
            base_score = distance_data.get("2400m", 85)
        
        # ランダムな調整を加える（実際のデータがない場合）
        adjustment = random.uniform(-10, 10)
        return max(0, min(100, base_score + adjustment))
    
    def _calculate_bloodline_evaluation(self, horse: HorseData) -> float:
        """血統評価を計算"""
        bloodline_data = self.knowledge_base.get_reference_data("bloodline_evaluation")
        
        # サンプル血統評価（実際は馬名から血統を推定）
        bloodline_types = list(bloodline_data.keys())
        selected_bloodline = random.choice(bloodline_types)
        base_score = bloodline_data[selected_bloodline]
        
        adjustment = random.uniform(-5, 5)
        return max(0, min(100, base_score + adjustment))
    
    def _calculate_jockey_compatibility(self, jockey: str) -> float:
        """騎手相性を計算"""
        jockey_data = self.knowledge_base.get_reference_data("jockey_compatibility")
        
        if not jockey:
            return jockey_data.get("average_jockey", 75)
        
        # サンプル騎手評価
        jockey_types = list(jockey_data.keys())
        selected_type = random.choice(jockey_types)
        base_score = jockey_data[selected_type]
        
        adjustment = random.uniform(-8, 8)
        return max(0, min(100, base_score + adjustment))
    
    def _calculate_trainer_evaluation(self, trainer: str) -> float:
        """調教師評価を計算"""
        trainer_data = self.knowledge_base.get_reference_data("trainer_evaluation")
        
        if not trainer:
            return trainer_data.get("average_trainer", 70)
        
        # サンプル調教師評価
        trainer_types = list(trainer_data.keys())
        selected_type = random.choice(trainer_types)
        base_score = trainer_data[selected_type]
        
        adjustment = random.uniform(-10, 10)
        return max(0, min(100, base_score + adjustment))
    
    def _calculate_track_aptitude(self, race_conditions: RaceConditions) -> float:
        """馬場適性を計算"""
        track_data = self.knowledge_base.get_reference_data("track_aptitude")
        
        # 馬場状態に基づくスコア
        track_key = f"{race_conditions.track_type.lower()}_{race_conditions.track_condition.lower()}"
        
        # マッピング
        if race_conditions.track_type == "芝":
            if race_conditions.track_condition == "良":
                base_score = track_data.get("turf_good", 100)
            elif race_conditions.track_condition in ["やや重", "重"]:
                base_score = track_data.get("turf_soft", 85)
            else:
                base_score = track_data.get("turf_heavy", 70)
        else:  # ダート
            if race_conditions.track_condition == "良":
                base_score = track_data.get("dirt_good", 80)
            elif race_conditions.track_condition in ["やや重", "重"]:
                base_score = track_data.get("dirt_soft", 75)
            else:
                base_score = track_data.get("dirt_heavy", 70)
        
        adjustment = random.uniform(-8, 8)
        return max(0, min(100, base_score + adjustment))
    
    def _calculate_weather_aptitude(self, weather: str) -> float:
        """天候適性を計算"""
        weather_data = self.knowledge_base.get_reference_data("weather_aptitude")
        
        weather_mapping = {
            "晴": "sunny",
            "曇": "cloudy", 
            "小雨": "light_rain",
            "雨": "heavy_rain"
        }
        
        weather_key = weather_mapping.get(weather, "sunny")
        base_score = weather_data.get(weather_key, 95)
        
        adjustment = random.uniform(-5, 5)
        return max(0, min(100, base_score + adjustment))
    
    def _calculate_horse_weight_impact(self, weight: int) -> float:
        """馬体重影響を計算"""
        if not weight:
            return 75  # デフォルト値
        
        # 理想的な馬体重を500kgとして計算
        ideal_weight = 500
        difference = abs(weight - ideal_weight)
        
        if difference <= 20:
            base_score = 90
        elif difference <= 40:
            base_score = 80
        elif difference <= 60:
            base_score = 70
        else:
            base_score = 60
        
        adjustment = random.uniform(-5, 5)
        return max(0, min(100, base_score + adjustment))
    
    def calculate_total_score(self, d_logic_score: DLogicScore) -> float:
        """ダンスインザダーク基準100点での総合スコアを計算"""
        weights = self.knowledge_base.get_scoring_weights()
        
        total = (
            d_logic_score.distance_aptitude * weights["distance_aptitude"] +
            d_logic_score.bloodline_evaluation * weights["bloodline_evaluation"] +
            d_logic_score.jockey_compatibility * weights["jockey_compatibility"] +
            d_logic_score.trainer_evaluation * weights["trainer_evaluation"] +
            d_logic_score.track_aptitude * weights["track_aptitude"] +
            d_logic_score.weather_aptitude * weights["weather_aptitude"] +
            d_logic_score.popularity_factor * weights["popularity_factor"] +
            d_logic_score.weight_impact * weights["weight_impact"] +
            d_logic_score.horse_weight_impact * weights["horse_weight_impact"] +
            d_logic_score.corner_specialist * weights["corner_specialist"] +
            d_logic_score.margin_analysis * weights["margin_analysis"] +
            d_logic_score.time_index * weights["time_index"]
        )
        
        return round(total, 1)
    
    def determine_confidence(self, score: float) -> str:
        """信頼度を決定"""
        thresholds = self.knowledge_base.get_confidence_thresholds()
        
        if score >= thresholds["high"]:
            return "high"
        elif score >= thresholds["medium"]:
            return "medium"
        else:
            return "low"
    
    def generate_analysis_details(self, d_logic_score: DLogicScore) -> Dict[str, str]:
        """分析詳細を生成"""
        return {
            "距離適性": f"{d_logic_score.distance_aptitude:.1f}点 - 距離への適応度",
            "血統評価": f"{d_logic_score.bloodline_evaluation:.1f}点 - 血統による能力評価",
            "騎手相性": f"{d_logic_score.jockey_compatibility:.1f}点 - 騎手との相性",
            "調教師評価": f"{d_logic_score.trainer_evaluation:.1f}点 - 調教師の実績",
            "馬場適性": f"{d_logic_score.track_aptitude:.1f}点 - 馬場状態への適応",
            "天候適性": f"{d_logic_score.weather_aptitude:.1f}点 - 天候条件への適応",
            "人気度": f"{d_logic_score.popularity_factor:.1f}点 - 市場評価",
            "斤量影響": f"{d_logic_score.weight_impact:.1f}点 - 負担重量の影響", 
            "馬体重影響": f"{d_logic_score.horse_weight_impact:.1f}点 - 馬体重の影響",
            "コーナー巧者度": f"{d_logic_score.corner_specialist:.1f}点 - コーナリング技術",
            "着差分析": f"{d_logic_score.margin_analysis:.1f}点 - 過去の着差パターン",
            "タイム指数": f"{d_logic_score.time_index:.1f}点 - タイム能力評価"
        }

# DLogicEngine インスタンス
d_logic_engine = DLogicEngine()

@router.post("/calculate", response_model=RacePrediction)
async def calculate_d_logic(race_data: Dict[str, Any]):
    """Dロジック指数を計算"""
    try:
        # レース条件の作成
        race_conditions = RaceConditions(**race_data["race_conditions"])
        
        # 馬データの処理
        horses_data = [HorseData(**horse_data) for horse_data in race_data["horses"]]
        
        # 各馬のDロジック分析
        analyses = []
        for horse_data in horses_data:
            # Dロジックスコア計算
            d_logic_score = d_logic_engine.calculate_d_logic_score(horse_data, race_conditions)
            
            # 総合スコア計算（ダンスインザダーク基準100点）
            total_score = d_logic_engine.calculate_total_score(d_logic_score)
            
            # 信頼度決定
            confidence = d_logic_engine.determine_confidence(total_score)
            
            # 分析詳細生成
            analysis_details = d_logic_engine.generate_analysis_details(d_logic_score)
            
            analysis = DLogicAnalysis(
                horse_name=horse_data.name,
                d_logic_score=d_logic_score,
                total_score=total_score,
                rank=0,  # 後でソート後に設定
                confidence=confidence,
                analysis_details=analysis_details
            )
            analyses.append(analysis)
        
        # スコアでソートしてランク付け
        analyses.sort(key=lambda x: x.total_score, reverse=True)
        for i, analysis in enumerate(analyses):
            analysis.rank = i + 1
        
        # 予想結果作成
        prediction = RacePrediction(
            race_id=race_data.get("race_id", "sample_race"),
            race_name=race_data.get("race_name", "サンプルレース"),
            race_conditions=race_conditions,
            horses=analyses,
            calculation_time=datetime.now()
        )
        
        return prediction
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dロジック計算エラー: {str(e)}")

@router.get("/sample")
async def get_sample_calculation():
    """サンプルDロジック計算（デモ用）"""
    
    sample_data = {
        "race_id": "sample_race_001",
        "race_name": "サンプルレース",
        "race_conditions": {
            "distance": 2000,
            "track_type": "芝",
            "track_condition": "良",
            "weather": "晴",
            "course": "東京",
            "grade": "G1"
        },
        "horses": [
            {
                "name": "サンプルホース1",
                "age": 4,
                "sex": "牡",
                "weight": 500,
                "jockey": "サンプル騎手1",
                "trainer": "サンプル調教師1",
                "recent_form": [1, 2, 1, 3, 1]
            },
            {
                "name": "サンプルホース2", 
                "age": 5,
                "sex": "牝",
                "weight": 480,
                "jockey": "サンプル騎手2",
                "trainer": "サンプル調教師2",
                "recent_form": [2, 1, 3, 1, 2]
            },
            {
                "name": "サンプルホース3",
                "age": 3,
                "sex": "牡",
                "weight": 520,
                "jockey": "サンプル騎手3", 
                "trainer": "サンプル調教師3",
                "recent_form": [3, 2, 1, 2, 1]
            }
        ]
    }
    
    return await calculate_d_logic(sample_data) 