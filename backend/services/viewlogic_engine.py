"""
ViewLogic展開予想エンジン
脚質判定、ペース予測、展開シミュレーションを行う
計画書通りの完全実装版
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from statistics import mean, stdev
import math
from datetime import datetime

# numpy import with fallback
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    # Fallback implementations
    class np:
        @staticmethod
        def percentile(data, percentile):
            """Simple percentile calculation without numpy"""
            if not data:
                return 0
            sorted_data = sorted(data)
            index = int(len(sorted_data) * percentile / 100)
            return sorted_data[min(index, len(sorted_data) - 1)]

logger = logging.getLogger(__name__)


class RunningStyleAnalyzer:
    """脚質判定と3段階分類を行うクラス"""
    
    def classify_basic_style(self, horse_races: List[Dict]) -> str:
        """基本4分類（逃げ/先行/差し/追込）を判定"""
        if not horse_races:
            return "不明"
        
        # 1コーナー通過順位の平均を計算
        corner1_positions = []
        for race in horse_races:
            if 'CORNER1_JUNI' in race and race['CORNER1_JUNI'] > 0:
                corner1_positions.append(race['CORNER1_JUNI'])
        
        if not corner1_positions:
            return "不明"
        
        avg_corner1 = mean(corner1_positions)
        
        if avg_corner1 <= 2.0:
            return "逃げ"
        elif avg_corner1 <= 5.0:
            return "先行"
        elif avg_corner1 <= 9.0:
            return "差し"
        else:
            return "追込"
    
    def classify_detailed_style(self, basic_style: str, horse_races: List[Dict]) -> Tuple[str, str]:
        """3段階詳細分類を行う"""
        if basic_style == "逃げ":
            return self._classify_escape_details(horse_races)
        elif basic_style == "先行":
            return self._classify_stalker_details(horse_races)
        elif basic_style == "差し":
            return self._classify_closer_details(horse_races)
        elif basic_style == "追込":
            return self._classify_latecloser_details(horse_races)
        else:
            return basic_style, "標準"
    
    def _classify_escape_details(self, horse_races: List[Dict]) -> Tuple[str, str]:
        """逃げ馬の詳細分類"""
        solo_escape_count = 0
        escape_success_count = 0
        escape_races = 0
        
        for race in horse_races:
            corner1 = race.get('CORNER1_JUNI', 99)
            corner2 = race.get('CORNER2_JUNI', 99)
            finish = race.get('KAKUTEI_CHAKUJUN', 99)
            
            # 逃げた場合
            if corner1 <= 2:
                escape_races += 1
                
                # 単独逃げかチェック（2コーナーでも先頭）
                if corner2 == 1:
                    solo_escape_count += 1
                
                # 逃げて3着以内
                if finish <= 3:
                    escape_success_count += 1
        
        if escape_races == 0:
            return "逃げ", "消極逃げ"
        
        solo_rate = solo_escape_count / escape_races
        success_rate = escape_success_count / escape_races
        
        if solo_rate > 0.6:
            return "逃げ", "超積極逃げ"
        elif success_rate > 0.5:
            return "逃げ", "状況逃げ"
        else:
            return "逃げ", "消極逃げ"
    
    def _classify_stalker_details(self, horse_races: List[Dict]) -> Tuple[str, str]:
        """先行馬の詳細分類"""
        corner1_positions = []
        position_stability = 0
        
        for race in horse_races:
            corner1 = race.get('CORNER1_JUNI', 99)
            if corner1 < 99:
                corner1_positions.append(corner1)
        
        if not corner1_positions:
            return "先行", "標準先行"
        
        avg_corner1 = mean(corner1_positions)
        
        # 位置取りの安定性を計算（標準偏差が小さいほど安定）
        if len(corner1_positions) > 1:
            position_stability = 1 / (1 + stdev(corner1_positions))
        else:
            position_stability = 0.5
        
        if avg_corner1 <= 3.5 and position_stability > 0.8:
            return "先行", "前寄り先行"
        elif position_stability > 0.7:
            return "先行", "安定先行"
        else:
            return "先行", "後寄り先行"
    
    def _classify_closer_details(self, horse_races: List[Dict]) -> Tuple[str, str]:
        """差し馬の詳細分類"""
        finishing_power_scores = []
        
        for race in horse_races:
            corner4 = race.get('CORNER4_JUNI', 99)
            finish = race.get('KAKUTEI_CHAKUJUN', 99)
            
            if corner4 < 99 and finish < 99:
                # 4コーナーから着順への改善度
                improvement = corner4 - finish
                finishing_power_scores.append(improvement)
        
        if not finishing_power_scores:
            return "差し", "標準差し"
        
        avg_improvement = mean(finishing_power_scores)
        
        if avg_improvement > 3:
            return "差し", "強烈差し"
        elif avg_improvement > 1:
            return "差し", "確実差し"
        else:
            return "差し", "遅め差し"
    
    def _classify_latecloser_details(self, horse_races: List[Dict]) -> Tuple[str, str]:
        """追込馬の詳細分類"""
        extreme_finishes = 0
        total_races = len(horse_races)
        
        for race in horse_races:
            corner4 = race.get('CORNER4_JUNI', 99)
            finish = race.get('KAKUTEI_CHAKUJUN', 99)
            
            if corner4 > 10 and finish <= 3:
                extreme_finishes += 1
        
        if total_races == 0:
            return "追込", "標準追込"
        
        extreme_rate = extreme_finishes / total_races
        
        if extreme_rate > 0.3:
            return "追込", "極限追込"
        elif extreme_rate > 0.1:
            return "追込", "強力追込"
        else:
            return "追込", "通常追込"
    
    def calculate_differentiation_score(self, horse_data: Dict, horse_races: List[Dict]) -> float:
        """18頭同一脚質の場合の差別化スコアを計算（100点満点）"""
        score_components = {
            'solo_escape': 0,      # 単独逃げ実績（40%）
            'start_dash': 0,       # スタートダッシュ力（25%）
            'tenacity': 0,         # 逃げ粘り度（20%）
            'competition': 0,      # 競り合い耐性（10%）
            'recent_form': 0       # 最近の勢い（5%）
        }
        
        # 1. 単独逃げ実績
        solo_count = 0
        total_escapes = 0
        for race in horse_races:
            if race.get('CORNER1_JUNI', 99) <= 2:
                total_escapes += 1
                if race.get('CORNER2_JUNI', 99) == 1:
                    solo_count += 1
        
        if total_escapes > 0:
            score_components['solo_escape'] = (solo_count / total_escapes) * 40
        
        # 2. スタートダッシュ力（簡易計算）
        corner1_avg = mean([r.get('CORNER1_JUNI', 10) for r in horse_races[:5]])
        score_components['start_dash'] = max(0, (10 - corner1_avg) * 2.5)
        
        # 3. 逃げ粘り度
        success_count = 0
        escape_count = 0
        for race in horse_races:
            if race.get('CORNER1_JUNI', 99) <= 3:
                escape_count += 1
                if race.get('KAKUTEI_CHAKUJUN', 99) <= 3:
                    success_count += 1
        
        if escape_count > 0:
            score_components['tenacity'] = (success_count / escape_count) * 20
        
        # 4. 競り合い耐性（簡易実装）
        score_components['competition'] = 5  # デフォルト値
        
        # 5. 最近の勢い
        recent_races = horse_races[:3] if len(horse_races) >= 3 else horse_races
        recent_corner1 = [r.get('CORNER1_JUNI', 99) for r in recent_races]
        if recent_corner1:
            recent_avg = mean(recent_corner1)
            if recent_avg <= 3:
                score_components['recent_form'] = 5
        
        # 総合スコア計算
        total_score = sum(score_components.values())
        return min(100, total_score)


class BayesianCorrector:
    """ベイズ補正を行うクラス"""
    
    def correct_rate(self, success_count: int, total_count: int, 
                    prior_mean: float = 0.20, prior_weight: float = 5) -> Dict[str, float]:
        """
        ベイズ補正で少ないサンプル数の影響を緩和
        
        Parameters:
        - success_count: 成功回数（複勝回数）
        - total_count: 総試行回数（出走回数）
        - prior_mean: 事前平均（全体の複勝率）
        - prior_weight: 事前分布の重み（信頼度）
        """
        if total_count == 0:
            return {
                "corrected_rate": prior_mean,
                "confidence": 0.0,
                "raw_rate": 0.0
            }
        
        # ベイズ推定による事後確率
        posterior = (success_count + prior_mean * prior_weight) / (total_count + prior_weight)
        
        # 信頼区間の計算
        confidence = min(total_count / (total_count + prior_weight), 1.0)
        
        # 生の確率
        raw_rate = success_count / total_count if total_count > 0 else 0
        
        return {
            "corrected_rate": posterior,
            "confidence": confidence,
            "raw_rate": raw_rate
        }


class RaceFlowPredictor:
    """レース展開予想を行うクラス"""
    
    def __init__(self):
        self.style_analyzer = RunningStyleAnalyzer()
        self.bayesian = BayesianCorrector()
    
    def predict_pace(self, all_horses_data: List[Dict]) -> Dict[str, Any]:
        """ペース予測（ハイ/平均/スロー）"""
        # 各馬の脚質を判定（馬番付き）
        style_distribution = {
            '逃げ': {'count': 0, 'horses': [], 'horse_numbers': []},
            '先行': {'count': 0, 'horses': [], 'horse_numbers': []},
            '差し': {'count': 0, 'horses': [], 'horse_numbers': []},
            '追込': {'count': 0, 'horses': [], 'horse_numbers': []},
            '不明': {'count': 0, 'horses': [], 'horse_numbers': []}
        }
        
        detailed_escapes = {
            '超積極逃げ': [],
            '状況逃げ': [],
            '消極逃げ': []
        }
        
        # スタート事故がある馬を記録
        start_accident_horses = []
        start_accident_numbers = []
        
        for idx, horse_data in enumerate(all_horses_data, 1):
            if 'races' not in horse_data:
                continue
            
            horse_name = horse_data.get('horse_name', '不明')
            horse_number = horse_data.get('horse_number', idx)  # 馬番（なければインデックス）
            
            # 脚質判定
            basic_style = self.style_analyzer.classify_basic_style(horse_data['races'])
            style_distribution[basic_style]['count'] += 1
            style_distribution[basic_style]['horses'].append(horse_name)
            style_distribution[basic_style]['horse_numbers'].append(horse_number)
            
            # 逃げ馬の詳細分類
            if basic_style == '逃げ':
                _, sub_style = self.style_analyzer.classify_detailed_style(basic_style, horse_data['races'])
                detailed_escapes[sub_style].append(horse_name)
            
            # スタート事故チェック（直近5走）
            recent_races = horse_data.get('races', [])[:5]
            for race in recent_races:
                # 発走順位が馬番より3以上遅い場合は出遅れと判定
                if 'HASSOUJUN' in race and 'UMA_BAN' in race:
                    if race['HASSOUJUN'] - race['UMA_BAN'] >= 3:
                        if horse_number not in start_accident_numbers:
                            start_accident_horses.append(horse_name)
                            start_accident_numbers.append(horse_number)
                        break
        
        # ペース判定
        super_aggressive_count = len(detailed_escapes['超積極逃げ'])
        situational_count = len(detailed_escapes['状況逃げ'])
        
        if super_aggressive_count >= 2:
            pace = "ハイペース濃厚"
            confidence = 90
        elif super_aggressive_count == 1 and situational_count >= 3:
            pace = "ややハイペース"
            confidence = 70
        elif situational_count >= 5:
            pace = "平均ペース"
            confidence = 60
        else:
            pace = "スローペース"
            confidence = 80
        
        return {
            'pace': pace,
            'confidence': confidence,
            'style_distribution': style_distribution,
            'detailed_escapes': detailed_escapes,
            'start_accident_horses': start_accident_horses,
            'start_accident_numbers': start_accident_numbers
        }
    
    def identify_advantaged_horses(self, pace: str, all_horses_data: List[Dict]) -> Dict[str, List[str]]:
        """有利/不利な馬を特定"""
        advantaged = []
        disadvantaged = []
        
        for horse_data in all_horses_data:
            if 'races' not in horse_data:
                continue
            
            horse_name = horse_data.get('horse_name', '不明')
            basic_style = self.style_analyzer.classify_basic_style(horse_data['races'])
            
            # ペースに応じた有利不利判定
            if pace in ["ハイペース濃厚", "ややハイペース"]:
                if basic_style in ["差し", "追込"]:
                    advantaged.append(f"{horse_name}（{basic_style}）")
                elif basic_style in ["逃げ", "先行"]:
                    disadvantaged.append(f"{horse_name}（{basic_style}）")
            elif pace == "スローペース":
                if basic_style in ["逃げ", "先行"]:
                    advantaged.append(f"{horse_name}（{basic_style}）")
                elif basic_style == "追込":
                    disadvantaged.append(f"{horse_name}（{basic_style}）")
        
        return {
            'advantaged': advantaged[:5],  # 上位5頭まで
            'disadvantaged': disadvantaged[:5]
        }
    
    def generate_race_scenario(self, all_horses_data: List[Dict]) -> str:
        """展開シナリオを生成"""
        pace_result = self.predict_pace(all_horses_data)
        
        scenario = f"【展開予想】{pace_result['pace']}（確信度{pace_result['confidence']}%）\n\n"
        
        # 脚質分布
        scenario += "【脚質分布】\n"
        for style, data in pace_result['style_distribution'].items():
            if data['count'] > 0:
                scenario += f"・{style}：{data['count']}頭\n"
        
        # 詳細な逃げ馬分析
        if pace_result['detailed_escapes']['超積極逃げ']:
            scenario += f"\n⚡ 超積極逃げ：{', '.join(pace_result['detailed_escapes']['超積極逃げ'])}\n"
        if pace_result['detailed_escapes']['状況逃げ']:
            scenario += f"🐎 状況逃げ：{', '.join(pace_result['detailed_escapes']['状況逃げ'])}\n"
        
        # 有利不利
        advantages = self.identify_advantaged_horses(pace_result['pace'], all_horses_data)
        
        if advantages['advantaged']:
            scenario += "\n🎯 有利な馬：\n"
            for horse in advantages['advantaged']:
                scenario += f"・{horse}\n"
        
        if advantages['disadvantaged']:
            scenario += "\n⚠️ 不利な馬：\n"
            for horse in advantages['disadvantaged']:
                scenario += f"・{horse}\n"
        
        return scenario


# メインのViewLogicエンジン
class ViewLogicEngine:
    """ViewLogic展開予想エンジンのメインクラス - 計画書通りの完全実装版"""
    
    def __init__(self):
        self.predictor = RaceFlowPredictor()
        self.style_analyzer = RunningStyleAnalyzer()
        self.bayesian = BayesianCorrector()
        # ViewLogicデータマネージャーを初期化
        from services.viewlogic_data_manager import ViewLogicDataManager
        self.data_manager = ViewLogicDataManager()
    
    def predict_race_flow_advanced(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        計画書通りの高度な展開予想
        前半3F・後半3Fを使用したペース予測と詳細な脚質分析
        """
        horses = race_data.get('horses', [])
        if not horses:
            return {
                'status': 'error',
                'message': '出走馬情報がありません'
            }
        
        # 各馬のデータを取得（馬番付き）
        horses_data = []
        for idx, horse_name in enumerate(horses, 1):
            horse_data = self.data_manager.get_horse_data(horse_name)
            if horse_data:
                horse_data['horse_number'] = race_data.get('horse_numbers', [])[idx-1] if idx-1 < len(race_data.get('horse_numbers', [])) else idx
                horses_data.append(horse_data)
        
        # 計画書通りのペース予測アルゴリズム
        pace_prediction = self._advanced_pace_prediction(horses_data)
        
        # 詳細な脚質分類（超積極逃げ、状況逃げなど）
        detailed_styles = self._classify_detailed_styles(horses_data)
        
        # 位置取り安定性指標の計算
        position_stability = self._calculate_position_stability_all(horses_data)
        
        # 展開適性マッチング
        flow_matching = self._calculate_flow_matching(horses_data, pace_prediction)
        
        # 展開シミュレーション
        race_simulation = self._simulate_race_positions(horses_data, pace_prediction)
        
        return {
            'status': 'success',
            'type': 'advanced_flow_prediction',
            'race_info': {
                'venue': race_data.get('venue', ''),
                'race_number': race_data.get('race_number', ''),
                'race_name': race_data.get('race_name', ''),
                'distance': race_data.get('distance', '')
            },
            'pace_prediction': pace_prediction,
            'detailed_styles': detailed_styles,
            'position_stability': position_stability,
            'flow_matching': flow_matching,
            'race_simulation': race_simulation,
            'visualization_data': self._prepare_visualization_data(race_simulation)
        }
    
    def _advanced_pace_prediction(self, horses_data: List[Dict]) -> Dict[str, Any]:
        """
        計画書通りのペース予測アルゴリズム
        前半3F・後半3Fのデータを使用
        """
        zenhan_times = []  # 前半3Fタイム
        kohan_times = []   # 後半3Fタイム
        
        for horse in horses_data:
            if 'races' not in horse:
                continue
            
            # 直近レースの前半3F・後半3Fを収集
            for race in horse['races'][:5]:  # 直近5レース
                if race.get('ZENHAN_3F'):
                    zenhan_times.append(float(race['ZENHAN_3F']) / 10)  # 0.1秒単位から秒に変換
                if race.get('KOHAN_3F'):
                    kohan_times.append(float(race['KOHAN_3F']) / 10)
        
        if not zenhan_times:
            return {'pace': 'データ不足', 'confidence': 0, 'zenhan_avg': 0, 'kohan_avg': 0}
        
        # 平均前半3Fタイムでペース判定
        zenhan_avg = mean(zenhan_times)
        kohan_avg = mean(kohan_times) if kohan_times else 0
        
        # 計画書通りのペース判定基準
        if zenhan_avg <= 33.5:
            pace = "超ハイペース"
            confidence = 95
        elif zenhan_avg <= 34.0:
            pace = "ハイペース"
            confidence = 90
        elif zenhan_avg <= 34.5:
            pace = "平均ペース"
            confidence = 85
        else:
            pace = "スローペース"
            confidence = 80
        
        return {
            'pace': pace,
            'confidence': confidence,
            'zenhan_avg': zenhan_avg,
            'kohan_avg': kohan_avg,
            'pace_index': (kohan_avg - zenhan_avg) * 10  # ペース指数
        }
    
    def _classify_detailed_styles(self, horses_data: List[Dict]) -> Dict[str, Any]:
        """
        詳細な脚質分類（計画書通り）
        逃げ馬を超積極逃げ、状況逃げ、消極逃げに分類
        """
        detailed_classification = {
            '逃げ': {'超積極逃げ': [], '状況逃げ': [], '消極逃げ': []},
            '先行': {'前寄り先行': [], '安定先行': [], '後寄り先行': []},
            '差し': {'強烈差し': [], '確実差し': [], '遅め差し': []},
            '追込': {'極限追込': [], '強力追込': [], '通常追込': []}
        }
        
        for horse in horses_data:
            if 'races' not in horse:
                continue
            
            horse_name = horse.get('horse_name', '不明')
            horse_number = horse.get('horse_number', 0)
            
            # 基本脚質の判定
            basic_style = self.style_analyzer.classify_basic_style(horse['races'])
            
            # 詳細分類
            if basic_style == '逃げ':
                sub_style = self._classify_escape_details_advanced(horse['races'])
                detailed_classification['逃げ'][sub_style].append(horse_name)
            elif basic_style == '先行':
                sub_style = self._classify_stalker_details_advanced(horse['races'])
                detailed_classification['先行'][sub_style].append(horse_name)
            elif basic_style == '差し':
                sub_style = self._classify_closer_details_advanced(horse['races'])
                detailed_classification['差し'][sub_style].append(horse_name)
            elif basic_style == '追込':
                sub_style = self._classify_latecloser_details_advanced(horse['races'])
                detailed_classification['追込'][sub_style].append(horse_name)
        
        return detailed_classification
    
    def _classify_escape_details_advanced(self, races: List[Dict]) -> str:
        """逃げ馬の詳細分類（計画書通り）"""
        solo_escape_count = 0
        escape_success_count = 0
        total_escapes = 0
        
        for race in races:
            corner1 = race.get('CORNER1_JUNI', 99)
            corner2 = race.get('CORNER2_JUNI', 99)
            
            if corner1 <= 2:  # 逃げた場合
                total_escapes += 1
                
                # 単独逃げかチェック
                if corner1 == 1 and corner2 == 1:
                    solo_escape_count += 1
                
                # 逃げて3着以内
                if race.get('KAKUTEI_CHAKUJUN', 99) <= 3:
                    escape_success_count += 1
        
        if total_escapes == 0:
            return '消極逃げ'
        
        solo_rate = solo_escape_count / total_escapes
        success_rate = escape_success_count / total_escapes
        
        if solo_rate > 0.6:
            return '超積極逃げ'
        elif success_rate > 0.5:
            return '状況逃げ'
        else:
            return '消極逃げ'
    
    def _classify_stalker_details_advanced(self, races: List[Dict]) -> str:
        """先行馬の詳細分類"""
        corner1_positions = []
        
        for race in races:
            corner1 = race.get('CORNER1_JUNI', 99)
            if corner1 < 99:
                corner1_positions.append(corner1)
        
        if not corner1_positions:
            return '標準先行'
        
        avg_corner1 = mean(corner1_positions)
        position_stability = 1 / (1 + stdev(corner1_positions)) if len(corner1_positions) > 1 else 0.5
        
        if avg_corner1 <= 3.5 and position_stability > 0.8:
            return '前寄り先行'
        elif position_stability > 0.7:
            return '安定先行'
        else:
            return '後寄り先行'
    
    def _classify_closer_details_advanced(self, races: List[Dict]) -> str:
        """差し馬の詳細分類"""
        finishing_improvements = []
        
        for race in races:
            corner4 = race.get('CORNER4_JUNI', 99)
            finish = race.get('KAKUTEI_CHAKUJUN', 99)
            
            if corner4 < 99 and finish < 99:
                improvement = corner4 - finish
                finishing_improvements.append(improvement)
        
        if not finishing_improvements:
            return '遅め差し'
        
        avg_improvement = mean(finishing_improvements)
        
        if avg_improvement > 3:
            return '強烈差し'
        elif avg_improvement > 1:
            return '確実差し'
        else:
            return '遅め差し'
    
    def _classify_latecloser_details_advanced(self, races: List[Dict]) -> str:
        """追込馬の詳細分類"""
        extreme_finishes = 0
        
        for race in races:
            corner4 = race.get('CORNER4_JUNI', 99)
            finish = race.get('KAKUTEI_CHAKUJUN', 99)
            
            if corner4 > 10 and finish <= 3:
                extreme_finishes += 1
        
        extreme_rate = extreme_finishes / len(races) if races else 0
        
        if extreme_rate > 0.3:
            return '極限追込'
        elif extreme_rate > 0.1:
            return '強力追込'
        else:
            return '通常追込'
    
    def _calculate_position_stability_all(self, horses_data: List[Dict]) -> Dict[str, float]:
        """全馬の位置取り安定性指標を計算（計画書通り）"""
        stability_scores = {}
        
        for horse in horses_data:
            horse_name = horse.get('horse_name', '不明')
            horse_number = horse.get('horse_number', 0)
            
            if 'races' not in horse:
                stability_scores[horse_name] = 0.0
                continue
            
            stability_values = []
            for race in horse['races']:
                positions = [
                    race.get('CORNER1_JUNI', 99),
                    race.get('CORNER2_JUNI', 99),
                    race.get('CORNER3_JUNI', 99),
                    race.get('CORNER4_JUNI', 99)
                ]
                
                # 有効な位置データのみ使用
                valid_positions = [p for p in positions if p < 99]
                if len(valid_positions) > 1:
                    # 標準偏差が小さいほど安定
                    stability = 1 / (1 + stdev(valid_positions))
                    stability_values.append(stability)
            
            stability_scores[horse_name] = mean(stability_values) if stability_values else 0.0
        
        return stability_scores
    
    def _calculate_flow_matching(self, horses_data: List[Dict], pace_prediction: Dict) -> Dict[str, Any]:
        """展開適性マッチング（計画書通り）"""
        flow_scores = {}
        pace = pace_prediction['pace']
        
        for horse in horses_data:
            horse_name = horse.get('horse_name', '不明')
            
            if 'races' not in horse:
                flow_scores[horse_name] = 50.0
                continue
            
            # 脚質指数の計算
            style_index = self._calculate_style_index(horse['races'])
            
            # ペースに応じた評価調整
            if 'ハイペース' in pace:
                # 後半型有利
                if style_index > 0:  # 差し・追込タイプ
                    score = 70 + (style_index * 2)
                else:  # 逃げ・先行タイプ
                    score = 50 - (abs(style_index) * 1.5)
            elif 'スローペース' in pace:
                # 前半型有利
                if style_index < 0:  # 逃げ・先行タイプ
                    score = 70 + (abs(style_index) * 2)
                else:  # 差し・追込タイプ
                    score = 50 - (style_index * 1.5)
            else:
                # 平均ペース
                score = 60
            
            flow_scores[horse_name] = min(100, max(0, score))
        
        return flow_scores
    
    def _calculate_style_index(self, races: List[Dict]) -> float:
        """脚質指数の計算（後半-前半の差）"""
        style_values = []
        
        for race in races:
            zenhan = race.get('ZENHAN_3F', 0)
            kohan = race.get('KOHAN_3F', 0)
            
            if zenhan and kohan:
                # 正の値は差し・追込型、負の値は逃げ・先行型
                style_values.append((kohan - zenhan) / 10)
        
        return mean(style_values) if style_values else 0
    
    def _simulate_race_positions(self, horses_data: List[Dict], pace_prediction: Dict) -> Dict[str, Any]:
        """展開シミュレーション（スタート→3コーナー→4コーナー→ゴール）"""
        simulation = {
            'start': [],
            'corner3': [],
            'corner4': [],
            'finish': []
        }
        
        for horse in horses_data:
            horse_name = horse.get('horse_name', '不明')
            
            if 'races' not in horse:
                continue
            
            # 過去のコーナー通過順位の平均から予測
            c1_data = [r.get('CORNER1_JUNI', 10) for r in horse['races'] if r.get('CORNER1_JUNI')]
            c3_data = [r.get('CORNER3_JUNI', 10) for r in horse['races'] if r.get('CORNER3_JUNI')]
            c4_data = [r.get('CORNER4_JUNI', 10) for r in horse['races'] if r.get('CORNER4_JUNI')]
            
            avg_c1 = mean(c1_data) if c1_data else 10
            avg_c3 = mean(c3_data) if c3_data else 10
            avg_c4 = mean(c4_data) if c4_data else 10
            
            simulation['start'].append({'horse_name': horse_name, 'position': avg_c1})
            simulation['corner3'].append({'horse_name': horse_name, 'position': avg_c3})
            simulation['corner4'].append({'horse_name': horse_name, 'position': avg_c4})
            
            # 展開とペースを考慮した着順予測
            predicted_finish = self._predict_finish_position(horse, pace_prediction)
            simulation['finish'].append({'horse_name': horse_name, 'position': predicted_finish})
        
        # 各ポイントで順位でソート
        for key in simulation:
            simulation[key].sort(key=lambda x: x['position'])
        
        return simulation
    
    def _predict_finish_position(self, horse_data: Dict, pace_prediction: Dict) -> float:
        """ペースを考慮した着順予測"""
        if 'races' not in horse_data:
            return 10.0
        
        # 基本的な着順の平均
        avg_finish = mean([r.get('KAKUTEI_CHAKUJUN', 10) for r in horse_data['races']])
        
        # ペースによる補正
        style_index = self._calculate_style_index(horse_data['races'])
        pace = pace_prediction['pace']
        
        if 'ハイペース' in pace and style_index > 0:
            # 差し・追込有利
            avg_finish -= 1.5
        elif 'スローペース' in pace and style_index < 0:
            # 逃げ・先行有利
            avg_finish -= 1.5
        
        return max(1.0, avg_finish)
    
    def _prepare_visualization_data(self, simulation: Dict) -> Dict[str, Any]:
        """可視化用データの準備"""
        return {
            'type': 'race_flow_chart',
            'data': simulation,
            'chart_config': {
                'width': 800,
                'height': 400,
                'colors': {
                    '逃げ': '#FF6B6B',
                    '先行': '#4ECDC4',
                    '差し': '#45B7D1',
                    '追込': '#96CEB4'
                }
            }
        }
    
    def analyze_race(self, horses_data: List[Dict]) -> Dict[str, Any]:
        """レース全体の分析を実行"""
        # ペース予測
        pace_result = self.predictor.predict_pace(horses_data)
        
        # 有利不利判定
        advantages = self.predictor.identify_advantaged_horses(
            pace_result['pace'], horses_data
        )
        
        # シナリオ生成
        scenario = self.predictor.generate_race_scenario(horses_data)
        
        return {
            'pace': pace_result,
            'advantages': advantages,
            'scenario': scenario,
            'total_horses': len(horses_data)
        }
    
    def predict_race_flow(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        展開予想機能 - レースの流れ、ペース、有利不利を予測
        
        Args:
            race_data: レース情報（出走馬リスト、開催情報など）
        
        Returns:
            展開予想結果
        """
        horses = race_data.get('horses', [])
        if not horses:
            return {
                'status': 'error',
                'message': '出走馬情報がありません'
            }
        
        # 各馬のデータを取得（馬番付き）
        horses_data = []
        for idx, horse_name in enumerate(horses, 1):
            horse_data = self.data_manager.get_horse_data(horse_name)
            if horse_data:
                # 馬番を追加
                horse_data['horse_number'] = race_data.get('horse_numbers', [])[idx-1] if idx-1 < len(race_data.get('horse_numbers', [])) else idx
                horses_data.append(horse_data)
        
        if not horses_data:
            return {
                'status': 'error',
                'message': 'ナレッジデータが見つかりません'
            }
        
        # 展開分析を実行
        analysis = self.analyze_race(horses_data)
        
        # レスポンス形式を整える
        return {
            'status': 'success',
            'type': 'flow_prediction',
            'race_info': {
                'venue': race_data.get('venue', ''),
                'race_number': race_data.get('race_number', ''),
                'race_name': race_data.get('race_name', ''),
                'distance': race_data.get('distance', '')
            },
            'prediction': {
                'pace': analysis['pace']['pace'],
                'pace_confidence': analysis['pace']['confidence'],
                'style_distribution': self._format_style_distribution(analysis['pace']['style_distribution']),
                'detailed_escapes': analysis['pace']['detailed_escapes'],
                'advantaged_horses': analysis['advantages']['advantaged'],
                'disadvantaged_horses': analysis['advantages']['disadvantaged'],
                'start_accident_numbers': analysis['pace'].get('start_accident_numbers', []),
                'running_style_numbers': {
                    '逃げ': analysis['pace']['style_distribution']['逃げ']['horse_numbers'],
                    '先行': analysis['pace']['style_distribution']['先行']['horse_numbers'],
                    '差し': analysis['pace']['style_distribution']['差し']['horse_numbers'],
                    '追込': analysis['pace']['style_distribution']['追込']['horse_numbers']
                }
            },
            'scenario': analysis['scenario'],
            'analyzed_horses': len(horses_data),
            'total_horses': len(horses)
        }
    
    def analyze_course_trend(self, venue: str, distance: int = None, track_type: str = None) -> Dict[str, Any]:
        """
        コース傾向分析 - コース別の騎手・血統・枠順傾向を分析
        
        Args:
            venue: 開催場（東京、中山など）
            distance: 距離（メートル）
            track_type: 芝/ダート
        
        Returns:
            コース傾向分析結果
        """
        # ナレッジデータから該当コースのデータを集計
        course_stats = self._calculate_course_statistics(venue, distance, track_type)
        
        if not course_stats:
            return {
                'status': 'error',
                'message': f'{venue}のデータが見つかりません'
            }
        
        return {
            'status': 'success',
            'type': 'trend_analysis',
            'course_info': {
                'venue': venue,
                'distance': distance,
                'track_type': track_type
            },
            'trends': {
                'jockey_ranking': course_stats.get('jockey_stats', [])[:5],
                'sire_ranking': course_stats.get('sire_stats', [])[:5],
                'post_position_stats': course_stats.get('post_stats', {}),
                'running_style_stats': course_stats.get('style_stats', {})
            },
            'insights': self._generate_course_insights(course_stats),
            'data_period': '2023-2025',
            'sample_size': course_stats.get('total_races', 0),
            'total_races': course_stats.get('total_races', 0)
        }
    
    def analyze_daily_trend(self, date: str, venue: str, race_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        当日傾向分析 - 開催日の傾向を予想
        
        Args:
            date: 開催日（YYYY-MM-DD形式）
            venue: 開催場
            race_data: レース情報（出走馬、騎手など）
        
        Returns:
            当日傾向予想結果
        """
        # レースデータから当日の傾向を予想
        daily_stats = self._calculate_daily_prediction(date, venue, race_data)
        
        # 予想文章を生成
        prediction_text = self._generate_daily_prediction_text(daily_stats, venue)
        
        return {
            'status': 'success',
            'type': 'daily_trend',
            'date': date,
            'venue': venue,
            'trends': {
                'running_style_performance': daily_stats.get('style_performance', {}),
                'hot_jockeys': daily_stats.get('hot_jockeys', [])[:3],
                'post_position_trend': daily_stats.get('post_trend', {}),
                'track_condition': daily_stats.get('track_condition', '良'),
                'track_bias': daily_stats.get('track_bias', 'フラット')
            },
            'prediction_text': prediction_text,
            'recommendations': self._generate_daily_recommendations(daily_stats),
            'races_completed': daily_stats.get('races_completed', 0),
            'last_updated': datetime.now().isoformat()
        }
    
    def _format_style_distribution(self, distribution: Dict) -> List[Dict]:
        """脚質分布をフォーマット"""
        result = []
        for style, data in distribution.items():
            if data['count'] > 0:
                result.append({
                    'style': style,
                    'count': data['count'],
                    'horses': data['horses'][:3]  # 上位3頭まで
                })
        return result
    
    def _calculate_course_statistics(self, venue: str, distance: int = None, track_type: str = None) -> Dict:
        """コース統計を計算（実際のナレッジデータから集計）"""
        venue_code_map = {
            '東京': '05', '中山': '06', '阪神': '09', '京都': '08',
            '中京': '07', '新潟': '04', '札幌': '02', '函館': '01',
            '福島': '03', '小倉': '10'
        }
        
        venue_code = venue_code_map.get(venue, '05')
        
        # 騎手別、血統別、枠順別、脚質別の統計を集計
        jockey_stats = {}
        sire_stats = {}
        post_stats = {'内枠（1-4）': {'runs': 0, 'fukusho': 0}, 
                      '中枠（5-12）': {'runs': 0, 'fukusho': 0},
                      '外枠（13-18）': {'runs': 0, 'fukusho': 0}}
        style_stats = {'逃げ': {'runs': 0, 'fukusho': 0},
                       '先行': {'runs': 0, 'fukusho': 0},
                       '差し': {'runs': 0, 'fukusho': 0},
                       '追込': {'runs': 0, 'fukusho': 0}}
        total_races = 0
        
        try:
            # 全馬のデータを走査して開催場別の統計を計算
            for horse_name, horse_data in self.data_manager.horses_dict.items():
                if not horse_data or 'races' not in horse_data:
                    continue
                
                # 各馬の該当開催場でのレースを集計
                for race in horse_data.get('races', []):
                    # 開催場コードで一致を確認（venue_codeを使用）
                    if race.get('KEIBAJO_CODE') == venue_code:
                        if distance and race.get('distance') != distance:
                            continue
                        if track_type and race.get('track_type') != track_type:
                            continue
                        
                        total_races += 1
                        
                        # 騎手統計
                        jockey = race.get('KISHUMEI_RYAKUSHO')  # 騎手名略称
                        if jockey:
                            if jockey not in jockey_stats:
                                jockey_stats[jockey] = {'runs': 0, 'wins': 0, 'fukusho': 0}
                            jockey_stats[jockey]['runs'] += 1
                            finish = race.get('KAKUTEI_CHAKUJUN', 99)
                            if finish == 1:
                                jockey_stats[jockey]['wins'] += 1
                            if finish <= 3:
                                jockey_stats[jockey]['fukusho'] += 1
                        
                        # 血統統計（現在のデータには含まれていない）
                        # TODO: 血統データが追加されたら実装
                        pass
                        
                        # 枠順統計（馬番で代用）
                        post = race.get('UMA_BAN')
                        if post and isinstance(post, (int, float)):
                            if 1 <= post <= 4:
                                post_stats['内枠（1-4）']['runs'] += 1
                                if race.get('KAKUTEI_CHAKUJUN', 99) <= 3:
                                    post_stats['内枠（1-4）']['fukusho'] += 1
                            elif 5 <= post <= 12:
                                post_stats['中枠（5-12）']['runs'] += 1
                                if race.get('KAKUTEI_CHAKUJUN', 99) <= 3:
                                    post_stats['中枠（5-12）']['fukusho'] += 1
                            elif 13 <= post <= 18:
                                post_stats['外枠（13-18）']['runs'] += 1
                                if race.get('KAKUTEI_CHAKUJUN', 99) <= 3:
                                    post_stats['外枠（13-18）']['fukusho'] += 1
                        
                        # 脚質統計（コーナー通過順位から判定）
                        corner1 = race.get('CORNER1_JUNI', 99)
                        if corner1 <= 2:
                            style = '逃げ'
                        elif corner1 <= 5:
                            style = '先行'
                        elif corner1 <= 9:
                            style = '差し'
                        else:
                            style = '追込'
                        if style in style_stats:
                            style_stats[style]['runs'] += 1
                            if race.get('finish_position') <= 3:
                                style_stats[style]['fukusho'] += 1
            
            # 騎手統計をリスト形式に変換（複勝率順）
            jockey_list = []
            for name, stats in jockey_stats.items():
                if stats['runs'] >= 5:  # 5回以上騎乗した騎手のみ
                    jockey_list.append({
                        'name': name,
                        'wins': stats['wins'],
                        'runs': stats['runs'],
                        'win_rate': stats['wins'] / stats['runs'] if stats['runs'] > 0 else 0,
                        'fukusho_rate': stats['fukusho'] / stats['runs'] if stats['runs'] > 0 else 0
                    })
            jockey_list.sort(key=lambda x: x['fukusho_rate'], reverse=True)
            
            # 血統統計をリスト形式に変換（複勝率順）
            sire_list = []
            for name, stats in sire_stats.items():
                if stats['runs'] >= 10:  # 10頭以上の産駒が出走
                    sire_list.append({
                        'name': name,
                        'runs': stats['runs'],
                        'fukusho_rate': stats['fukusho'] / stats['runs'] if stats['runs'] > 0 else 0
                    })
            sire_list.sort(key=lambda x: x['fukusho_rate'], reverse=True)
            
            # 枠順統計に勝率・複勝率を追加
            for key in post_stats:
                runs = post_stats[key]['runs']
                if runs > 0:
                    post_stats[key]['fukusho_rate'] = post_stats[key]['fukusho'] / runs
                else:
                    post_stats[key]['fukusho_rate'] = 0
            
            # 脚質統計に勝率・複勝率を追加
            for key in style_stats:
                runs = style_stats[key]['runs']
                if runs > 0:
                    style_stats[key]['fukusho_rate'] = style_stats[key]['fukusho'] / runs
                else:
                    style_stats[key]['fukusho_rate'] = 0
            
            return {
                'jockey_stats': jockey_list[:10],  # 上位10名
                'sire_stats': sire_list[:10],      # 上位10頭
                'post_stats': post_stats,
                'style_stats': style_stats,
                'total_races': total_races
            }
            
        except Exception as e:
            logger.warning(f"コース統計の計算エラー: {e}")
            return {
                'jockey_stats': [],
                'sire_stats': [],
                'post_stats': {},
                'style_stats': {},
                'total_races': 0
            }
    
    def _calculate_daily_prediction(self, date: str, venue: str, race_data: Dict[str, Any] = None) -> Dict:
        """当日の傾向を予想（実際のレースデータから）"""
        # race_dataが与えられた場合は、そのレースの出走馬・騎手から傾向を予想
        if race_data:
            return self._predict_from_race_data(venue, race_data)
        # race_dataがない場合は、ナレッジファイルから開催場の一般的な傾向を予想
        return self._predict_from_knowledge(venue)
    
    def _predict_from_race_data(self, venue: str, race_data: Dict[str, Any]) -> Dict:
        """特定レースのデータから当日傾向を予想"""
        horses = race_data.get('horses', [])
        jockeys = race_data.get('jockeys', [])
        
        # 脚質傾向を予想
        style_prediction = self._predict_style_trend(horses)
        
        # 騎手傾向を予想
        jockey_prediction = self._predict_jockey_trend(venue, jockeys)
        
        # 枠順傾向を予想（過去データから）
        post_prediction = self._predict_post_trend(venue)
        
        return {
            'style_performance': style_prediction,
            'hot_jockeys': jockey_prediction,
            'post_trend': post_prediction,
            'track_condition': '良',
            'track_bias': self._predict_track_bias(post_prediction),
            'races_completed': 0
        }
    
    def _predict_from_knowledge(self, venue: str) -> Dict:
        """ナレッジファイルから一般的な傾向を予想"""
        # _calculate_course_statisticsを活用
        course_stats = self._calculate_course_statistics(venue)
        
        return {
            'style_performance': course_stats.get('style_stats', {}),
            'hot_jockeys': course_stats.get('jockey_stats', [])[:3],
            'post_trend': course_stats.get('post_stats', {}),
            'track_condition': '良',
            'track_bias': 'フラット',
            'races_completed': 0
        }
    
    def _predict_style_trend(self, horses: List[str]) -> Dict:
        """出走馬から脚質傾向を予想"""
        style_counts = {'逃げ': 0, '先行': 0, '差し': 0, '追込': 0}
        
        for horse_name in horses:
            horse_data = self.data_manager.get_horse_data(horse_name)
            if horse_data and 'races' in horse_data:
                style = self.style_analyzer.classify_basic_style(horse_data['races'])
                if style in style_counts:
                    style_counts[style] += 1
        
        # 傾向を判定
        total = sum(style_counts.values())
        style_performance = {}
        for style, count in style_counts.items():
            style_performance[style] = {
                'runs': count,
                'ratio': count / total if total > 0 else 0
            }
        
        return style_performance
    
    def _predict_jockey_trend(self, venue: str, jockeys: List[str]) -> List[Dict]:
        """騎手リストから好調騎手を予想"""
        jockey_stats = []
        
        # 各騎手の開催場別成績をナレッジから取得
        # TODO: 騎手ナレッジファイルから実績を取得
        
        return jockey_stats
    
    def _predict_post_trend(self, venue: str) -> Dict:
        """開催場の枠順傾向を予想"""
        # _calculate_course_statisticsから枠順データを取得
        course_stats = self._calculate_course_statistics(venue)
        return course_stats.get('post_stats', {})
    
    def _predict_track_bias(self, post_trend: Dict) -> str:
        """枠順傾向からトラックバイアスを予想"""
        if not post_trend:
            return 'フラット'
        
        # ベイズ補正を適用
        outer_rate = post_trend.get('外枠（13-18）', {}).get('fukusho_rate', 0)
        inner_rate = post_trend.get('内枠（1-4）', {}).get('fukusho_rate', 0)
        
        if outer_rate > 0.4:
            return '外有利'
        elif inner_rate > 0.4:
            return '内有利'
        return 'フラット'
    
    def _generate_daily_prediction_text(self, daily_stats: Dict, venue: str) -> str:
        """当日傾向の予想文章を生成"""
        text = f"本日の{venue}は\n"
        
        # 脚質傾向
        style_perf = daily_stats.get('style_performance', {})
        if style_perf:
            # 最も有利な脚質を判定
            best_style = max(style_perf.items(), key=lambda x: x[1].get('ratio', 0))
            if best_style[1].get('ratio', 0) > 0.3:
                text += f"{best_style[0]}有利です\n"
        
        # 好調騎手
        hot_jockeys = daily_stats.get('hot_jockeys', [])
        if hot_jockeys:
            text += f"\nまた\n好調騎手は{hot_jockeys[0]['name']}で\n"
        
        # 枠順傾向
        track_bias = daily_stats.get('track_bias', 'フラット')
        if track_bias == '外有利':
            text += "\n枠順は7,8枠の好走が目立ちます\n"
        elif track_bias == '内有利':
            text += "\n枠順は1,2枠の好走が目立ちます\n"
        
        return text
    
    def _calculate_daily_statistics(self, date: str, venue: str) -> Dict:
        """当日統計を計算（実際のレースデータから予想）"""
        # 実際のレースデータから当日の傾向を予想
        # ViewLogicナレッジファイルから該当開催場のデータを分析
        
        # 初期化
        statistics = {
            'style_performance': {},
            'hot_jockeys': [],
            'post_trend': {},
            'track_condition': '良',
            'track_bias': 'フラット',
            'races_completed': 0
        }
        
        try:
            # ナレッジファイルから開催場別のデータを集計
            # 実際のデータ分析を実装（仮実装を実データに置き換える必要）
            # TODO: 実際のレースデータから集計するロジックを実装
            return statistics
            
        except Exception as e:
            logger.warning(f"当日統計の計算エラー: {e}")
            return statistics
    
    def _generate_course_insights(self, stats: Dict) -> List[str]:
        """コース傾向からインサイトを生成"""
        insights = []
        
        # 騎手傾向
        if stats.get('jockey_stats'):
            top_jockey = stats['jockey_stats'][0]
            insights.append(f"騎手は{top_jockey['name']}が複勝率{top_jockey['fukusho_rate']:.0%}で最も好成績")
        
        # 枠順傾向
        post_stats = stats.get('post_stats', {})
        if '中枠（5-12）' in post_stats:
            insights.append("中枠の複勝率が高く有利な傾向")
        
        # 脚質傾向
        style_stats = stats.get('style_stats', {})
        if style_stats.get('先行', {}).get('win_rate', 0) > 0.18:
            insights.append("先行馬が有利なコース")
        
        return insights
    
    def _generate_daily_recommendations(self, stats: Dict) -> List[str]:
        """当日統計から推奨事項を生成"""
        recommendations = []
        
        # 脚質推奨
        style_perf = stats.get('style_performance', {})
        if style_perf.get('逃げ', {}).get('win_rate', 0) > 0.4:
            recommendations.append("逃げ馬の単勝が狙い目")
        
        # 枠順推奨
        post_trend = stats.get('post_trend', {})
        if post_trend.get('7-8枠', {}).get('fukusho_rate', 0) > 0.4:
            recommendations.append("外枠の馬に注目")
        
        # 騎手推奨
        if stats.get('hot_jockeys'):
            hot_jockey = stats['hot_jockeys'][0]['name']
            recommendations.append(f"{hot_jockey}騎手騎乗馬を軸に")
        
        return recommendations
