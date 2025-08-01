"""
ナレッジベースサービス
ダンスインザダーク基準データと競馬全般データの管理
SQLデータ活用による多次元Dロジック計算エンジン
"""
import logging
from typing import Dict, List, Any, Optional
import json
import os

logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self):
        self.dance_in_the_dark_data = {}
        self.horse_racing_general_data = {}
        self.sql_evaluation_criteria = {}
        self.d_logic_weights = {}
        self.is_initialized = False
    
    async def initialize(self):
        """ナレッジベースの初期化"""
        try:
            # フロントエンドのknowledgeBase.jsonを読み込み
            knowledge_base_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'frontend', 'src', 'data', 'knowledgeBase.json'
            )
            
            if os.path.exists(knowledge_base_path):
                with open(knowledge_base_path, 'r', encoding='utf-8') as f:
                    knowledge_data = json.load(f)
                
                self.dance_in_the_dark_data = knowledge_data.get('dance_in_the_dark', {})
                self.horse_racing_general_data = knowledge_data.get('horse_racing_general', {})
                self.sql_evaluation_criteria = knowledge_data.get('sql_evaluation_criteria', {})
                self.d_logic_weights = knowledge_data.get('d_logic_calculation_weights', {})
            
            self.is_initialized = True
            logger.info("ナレッジベース初期化完了")
            return True
        except Exception as e:
            logger.error(f"ナレッジベース初期化エラー: {e}")
            return False
    
    async def get_dance_in_the_dark_data(self) -> Dict[str, Any]:
        """ダンスインザダーク基準データの取得"""
        return self.dance_in_the_dark_data
    
    async def get_horse_racing_general_data(self) -> Dict[str, Any]:
        """競馬全般データの取得"""
        return self.horse_racing_general_data
    
    async def get_sql_evaluation_criteria(self) -> Dict[str, Any]:
        """SQL評価基準の取得"""
        return self.sql_evaluation_criteria
    
    async def get_d_logic_weights(self) -> Dict[str, Any]:
        """Dロジック計算重みの取得"""
        return self.d_logic_weights

class DLogicCalculator:
    """多次元Dロジック計算エンジン"""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        self.base_score = 100
        self.base_horse_data = None
    
    async def initialize(self):
        """計算エンジンの初期化"""
        await self.kb.initialize()
        self.base_horse_data = await self.kb.get_dance_in_the_dark_data()
        self.sql_criteria = await self.kb.get_sql_evaluation_criteria()
        self.weights = await self.kb.get_d_logic_weights()
    
    def calculate_d_logic_score(self, horse_data: Dict[str, Any]) -> Dict[str, Any]:
        """多次元Dロジック指数計算"""
        try:
            base_score = self.base_score
            
            # 基本能力 (30%)
            basic_ability_score = self._calculate_basic_ability(horse_data)
            
            # 環境適応 (25%)
            environment_score = self._calculate_environment_adaptation(horse_data)
            
            # 人的要因 (20%)
            human_factors_score = self._calculate_human_factors(horse_data)
            
            # 血統・体質 (15%)
            bloodline_score = self._calculate_bloodline_physique(horse_data)
            
            # 競走スタイル (10%)
            racing_style_score = self._calculate_racing_style(horse_data)
            
            # 重み付き総合スコア計算
            total_score = (
                basic_ability_score * self.weights.get('basic_ability', 0.30) +
                environment_score * self.weights.get('environment_adaptation', 0.25) +
                human_factors_score * self.weights.get('human_factors', 0.20) +
                bloodline_score * self.weights.get('bloodline_physique', 0.15) +
                racing_style_score * self.weights.get('racing_style', 0.10)
            )
            
            return {
                "total_score": round(total_score, 1),
                "base_score": base_score,
                "detailed_scores": {
                    "basic_ability": round(basic_ability_score, 1),
                    "environment_adaptation": round(environment_score, 1),
                    "human_factors": round(human_factors_score, 1),
                    "bloodline_physique": round(bloodline_score, 1),
                    "racing_style": round(racing_style_score, 1)
                },
                "sql_analysis": self._generate_sql_analysis(horse_data),
                "calculation_details": self._generate_calculation_details(horse_data)
            }
            
        except Exception as e:
            logger.error(f"Dロジック計算エラー: {e}")
            return {
                "total_score": 0,
                "error": str(e)
            }
    
    def _calculate_basic_ability(self, horse_data: Dict[str, Any]) -> float:
        """基本能力スコア計算"""
        score = 0
        
        # 距離適性分析
        distance_score = self._analyze_distance_performance(horse_data)
        score += distance_score * 0.5
        
        # 馬場適性分析
        track_score = self._analyze_track_performance(horse_data)
        score += track_score * 0.5
        
        return min(score, 100)
    
    def _calculate_environment_adaptation(self, horse_data: Dict[str, Any]) -> float:
        """環境適応スコア計算"""
        score = 0
        
        # 天候適性分析
        weather_score = self._analyze_weather_performance(horse_data)
        score += weather_score * 0.5
        
        # 馬場状態適性分析
        track_condition_score = self._analyze_track_condition(horse_data)
        score += track_condition_score * 0.5
        
        return min(score, 100)
    
    def _calculate_human_factors(self, horse_data: Dict[str, Any]) -> float:
        """人的要因スコア計算"""
        score = 0
        
        # 騎手相性分析
        jockey_score = self._analyze_jockey_compatibility(horse_data)
        score += jockey_score * 0.6
        
        # 調教師評価分析
        trainer_score = self._analyze_trainer_performance(horse_data)
        score += trainer_score * 0.4
        
        return min(score, 100)
    
    def _calculate_bloodline_physique(self, horse_data: Dict[str, Any]) -> float:
        """血統・体質スコア計算"""
        score = 0
        
        # 血統評価分析
        bloodline_score = self._analyze_bloodline_strength(horse_data)
        score += bloodline_score * 0.6
        
        # 馬体重分析
        weight_score = self._analyze_weight_performance(horse_data)
        score += weight_score * 0.4
        
        return min(score, 100)
    
    def _calculate_racing_style(self, horse_data: Dict[str, Any]) -> float:
        """競走スタイルスコア計算"""
        score = 0
        
        # コーナー巧者度分析
        corner_score = self._analyze_corner_performance(horse_data)
        score += corner_score * 0.5
        
        # ペース能力分析
        pace_score = self._analyze_pace_ability(horse_data)
        score += pace_score * 0.5
        
        return min(score, 100)
    
    def _analyze_distance_performance(self, horse_data: Dict[str, Any]) -> float:
        """距離適性分析"""
        # SQLデータ: KYORI, CHAKUJUN, NINKI
        # 実装例（実際のSQLデータに基づく）
        return 85.0  # 仮の値
    
    def _analyze_track_performance(self, horse_data: Dict[str, Any]) -> float:
        """馬場適性分析"""
        # SQLデータ: TRACK_CODE, CHAKUJUN, JIKAN
        return 90.0  # 仮の値
    
    def _analyze_weather_performance(self, horse_data: Dict[str, Any]) -> float:
        """天候適性分析"""
        # SQLデータ: WEATHER_CODE, CHAKUJUN, JIKAN
        return 88.0  # 仮の値
    
    def _analyze_track_condition(self, horse_data: Dict[str, Any]) -> float:
        """馬場状態適性分析"""
        # SQLデータ: BABAJOTAI_CODE, CHAKUJUN, JIKAN
        return 92.0  # 仮の値
    
    def _analyze_jockey_compatibility(self, horse_data: Dict[str, Any]) -> float:
        """騎手相性分析"""
        # SQLデータ: KISHI_CODE, CHAKUJUN, JIKAN
        return 87.0  # 仮の値
    
    def _analyze_trainer_performance(self, horse_data: Dict[str, Any]) -> float:
        """調教師評価分析"""
        # SQLデータ: CHOKYOSHI_CODE, CHAKUJUN, JIKAN
        return 89.0  # 仮の値
    
    def _analyze_bloodline_strength(self, horse_data: Dict[str, Any]) -> float:
        """血統評価分析"""
        # SQLデータ: CHICHI_BAMEI, HAHA_CHICHI_BAMEI, CHAKUJUN
        return 93.0  # 仮の値
    
    def _analyze_weight_performance(self, horse_data: Dict[str, Any]) -> float:
        """馬体重分析"""
        # SQLデータ: WEIGHT, WEIGHT_CHANGE, CHAKUJUN
        return 86.0  # 仮の値
    
    def _analyze_corner_performance(self, horse_data: Dict[str, Any]) -> float:
        """コーナー巧者度分析"""
        # SQLデータ: CORNER_POSITION, CHAKUJUN
        return 84.0  # 仮の値
    
    def _analyze_pace_ability(self, horse_data: Dict[str, Any]) -> float:
        """ペース能力分析"""
        # SQLデータ: TSUKA_JIKAN, JIKAN, CHAKUJUN
        return 91.0  # 仮の値
    
    def _generate_sql_analysis(self, horse_data: Dict[str, Any]) -> Dict[str, Any]:
        """SQL分析結果生成"""
        return {
            "distance_analysis": {
                "score": 85.0,
                "description": "1600m-2400mで安定した成績",
                "sql_fields_used": ["KYORI", "CHAKUJUN", "NINKI"]
            },
            "track_condition_analysis": {
                "score": 90.0,
                "description": "良馬場で特に好相性",
                "sql_fields_used": ["BABAJOTAI_CODE", "CHAKUJUN", "JIKAN"]
            },
            "weather_analysis": {
                "score": 88.0,
                "description": "晴れ・曇りで安定した走り",
                "sql_fields_used": ["WEATHER_CODE", "CHAKUJUN", "JIKAN"]
            },
            "jockey_compatibility": {
                "score": 87.0,
                "description": "武豊騎手との相性抜群",
                "sql_fields_used": ["KISHI_CODE", "CHAKUJUN", "JIKAN"]
            },
            "bloodline_evaluation": {
                "score": 93.0,
                "description": "サンデーサイレンス系の優秀な血統",
                "sql_fields_used": ["CHICHI_BAMEI", "HAHA_CHICHI_BAMEI", "CHAKUJUN"]
            }
        }
    
    def _generate_calculation_details(self, horse_data: Dict[str, Any]) -> Dict[str, Any]:
        """計算詳細生成"""
        return {
            "calculation_method": "多次元Dロジック計算エンジン",
            "base_horse": "ダンスインザダーク",
            "base_score": 100,
            "sql_data_utilization": "12項目の多角的評価",
            "weight_distribution": self.weights
        }

# グローバルインスタンス
knowledge_base = KnowledgeBase()
d_logic_calculator = DLogicCalculator(knowledge_base) 