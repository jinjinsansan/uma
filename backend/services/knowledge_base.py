import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class KnowledgeBase:
    """ナレッジベース管理クラス"""
    
    def __init__(self):
        # データファイルのパス
        self.data_dir = Path(__file__).parent.parent / "data"
        self.knowledge_file = self.data_dir / "knowledgeBase.json"
        self._knowledge_data = None
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """ナレッジベースデータを読み込み"""
        try:
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                self._knowledge_data = json.load(f)
        except FileNotFoundError:
            print(f"警告: ナレッジベースファイルが見つかりません: {self.knowledge_file}")
            self._knowledge_data = self._get_default_knowledge_base()
        except json.JSONDecodeError as e:
            print(f"エラー: ナレッジベースファイルの読み込みに失敗: {e}")
            self._knowledge_data = self._get_default_knowledge_base()
    
    def _get_default_knowledge_base(self) -> Dict[str, Any]:
        """デフォルトのナレッジベースデータ"""
        return {
            "reference_horse": {
                "name": "ダンスインザダーク",
                "base_score": 100,
                "description": "Dロジック指数の基準馬"
            },
            "scoring_weights": {
                "distance_aptitude": 0.12,
                "bloodline_evaluation": 0.10,
                "jockey_compatibility": 0.08,
                "trainer_evaluation": 0.08,
                "track_aptitude": 0.10,
                "weather_aptitude": 0.06,
                "popularity_factor": 0.08,
                "weight_impact": 0.08,
                "horse_weight_impact": 0.08,
                "corner_specialist": 0.08,
                "margin_analysis": 0.08,
                "time_index": 0.06
            },
            "reference_data": {
                "distance_aptitude": {
                    "1400m": 75,
                    "1600m": 85,
                    "1800m": 95,
                    "2000m": 100,
                    "2200m": 90,
                    "2400m": 85
                },
                "bloodline_evaluation": {
                    "sunday_silence_line": 95,
                    "northern_dancer_line": 90,
                    "storm_cat_line": 85,
                    "other": 70
                },
                "jockey_compatibility": {
                    "top_jockey": 95,
                    "experienced_jockey": 85,
                    "average_jockey": 75,
                    "rookie_jockey": 65
                },
                "trainer_evaluation": {
                    "top_trainer": 90,
                    "experienced_trainer": 80,
                    "average_trainer": 70,
                    "new_trainer": 60
                },
                "track_aptitude": {
                    "turf_good": 100,
                    "turf_soft": 85,
                    "turf_heavy": 70,
                    "dirt_good": 80,
                    "dirt_soft": 75,
                    "dirt_heavy": 70
                },
                "weather_aptitude": {
                    "sunny": 100,
                    "cloudy": 95,
                    "light_rain": 85,
                    "heavy_rain": 75
                }
            },
            "calculation_parameters": {
                "confidence_thresholds": {
                    "high": 85,
                    "medium": 70,
                    "low": 0
                }
            }
        }
    
    def get_reference_horse(self) -> Dict[str, Any]:
        """基準馬（ダンスインザダーク）の情報を取得"""
        return self._knowledge_data.get("reference_horse", {})
    
    def get_scoring_weights(self) -> Dict[str, float]:
        """12項目の重み係数を取得"""
        return self._knowledge_data.get("scoring_weights", {})
    
    def get_reference_data(self, category: str) -> Dict[str, Any]:
        """指定カテゴリの参考データを取得"""
        reference_data = self._knowledge_data.get("reference_data", {})
        return reference_data.get(category, {})
    
    def get_confidence_thresholds(self) -> Dict[str, float]:
        """信頼度の閾値を取得"""
        params = self._knowledge_data.get("calculation_parameters", {})
        return params.get("confidence_thresholds", {"high": 85, "medium": 70, "low": 0})
    
    def get_display_settings(self) -> Dict[str, Any]:
        """表示設定を取得"""
        return self._knowledge_data.get("display_settings", {
            "user_facing_name": "Dロジック",
            "hide_reference_horse": True,
            "show_total_score_only": False,
            "decimal_places": 1
        })
    
    def update_knowledge_base(self, new_data: Dict[str, Any]) -> bool:
        """ナレッジベースを更新"""
        try:
            # 既存データとマージ
            self._knowledge_data.update(new_data)
            
            # ファイルに保存
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self._knowledge_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"ナレッジベース更新エラー: {e}")
            return False
    
    def get_d_logic_item_names(self) -> Dict[str, str]:
        """Dロジック12項目の名前一覧を取得"""
        return {
            "distance_aptitude": "距離適性",
            "bloodline_evaluation": "血統評価", 
            "jockey_compatibility": "騎手相性",
            "trainer_evaluation": "調教師評価",
            "track_aptitude": "馬場適性",
            "weather_aptitude": "天候適性",
            "popularity_factor": "人気度",
            "weight_impact": "斤量影響",
            "horse_weight_impact": "馬体重影響",
            "corner_specialist": "コーナー巧者度",
            "margin_analysis": "着差分析",
            "time_index": "タイム指数"
        }
    
    def validate_knowledge_base(self) -> Dict[str, bool]:
        """ナレッジベースの整合性をチェック"""
        validation_results = {
            "reference_horse_exists": "reference_horse" in self._knowledge_data,
            "scoring_weights_complete": len(self.get_scoring_weights()) == 12,
            "weights_sum_to_one": abs(sum(self.get_scoring_weights().values()) - 1.0) < 0.01,
            "reference_data_exists": "reference_data" in self._knowledge_data,
            "confidence_thresholds_valid": self._validate_confidence_thresholds()
        }
        
        return validation_results
    
    def _validate_confidence_thresholds(self) -> bool:
        """信頼度閾値の妥当性をチェック"""
        thresholds = self.get_confidence_thresholds()
        try:
            high = thresholds.get("high", 0)
            medium = thresholds.get("medium", 0)
            low = thresholds.get("low", 0)
            
            return high > medium > low and high <= 100 and low >= 0
        except (TypeError, ValueError):
            return False
    
    def get_sample_race_data(self) -> Dict[str, Any]:
        """サンプルレースデータを生成"""
        return {
            "race_id": "tokyo_3r_sample",
            "race_name": "東京3R",
            "race_conditions": {
                "distance": 1600,
                "track_type": "芝",
                "track_condition": "良",
                "weather": "晴",
                "course": "東京",
                "grade": None
            },
            "horses": [
                {
                    "name": "スピードスター",
                    "age": 4,
                    "sex": "牡", 
                    "weight": 498,
                    "jockey": "トップ騎手",
                    "trainer": "ベテラン調教師",
                    "recent_form": [1, 2, 1, 3, 2]
                },
                {
                    "name": "ダービーキング",
                    "age": 3,
                    "sex": "牡",
                    "weight": 502,
                    "jockey": "期待の若手",
                    "trainer": "名門厩舎",
                    "recent_form": [2, 1, 1, 1, 3]
                },
                {
                    "name": "エレガントクイーン",
                    "age": 5,
                    "sex": "牝",
                    "weight": 485,
                    "jockey": "女性騎手",
                    "trainer": "実績ある調教師",
                    "recent_form": [3, 2, 2, 1, 1]
                }
            ]
        }
    
    def reload_knowledge_base(self):
        """ナレッジベースを再読み込み"""
        self._load_knowledge_base()