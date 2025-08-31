"""
ViewLogic展開予想エンジン
脚質判定、ペース予測、展開シミュレーションを行う
計画書通りの完全実装版
"""

import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from statistics import mean, stdev
import math
import hashlib
import time
from datetime import datetime, timedelta
from .jockey_knowledge_manager import get_jockey_knowledge_manager

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
        # ViewLogicデータマネージャーを初期化（シングルトンインスタンスを使用）
        from services.viewlogic_data_manager import get_viewlogic_data_manager
        self.data_manager = get_viewlogic_data_manager()
        # 騎手ナレッジマネージャーを初期化
        self.jockey_manager = get_jockey_knowledge_manager()
        
        # メモリキャッシュ（4GBメモリ活用）
        self.trend_cache = {}
        self.cache_ttl = 1800  # 30分間キャッシュ
        self.max_cache_size = 100  # 最大100レース分
    
    def _generate_cache_key(self, race_data: Dict[str, Any]) -> str:
        """レースデータからキャッシュキーを生成"""
        # 重要な要素のみでキーを作成（順序無視）
        horses = sorted(race_data.get('horses', []))
        jockeys = sorted(race_data.get('jockeys', []))
        posts = sorted(race_data.get('posts', []))
        
        key_data = {
            'venue': race_data.get('venue', ''),
            'distance': race_data.get('distance', ''),
            'course_type': race_data.get('course_type', '芝'),
            'horses': horses,
            'jockeys': jockeys,
            'posts': posts
        }
        
        # ハッシュ化してキーにする
        key_string = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def _get_cached_trend(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """キャッシュから傾向分析結果を取得"""
        if cache_key in self.trend_cache:
            cache_entry = self.trend_cache[cache_key]
            # TTL チェック
            if time.time() - cache_entry['timestamp'] < self.cache_ttl:
                logger.info(f"キャッシュヒット: {cache_key[:8]}...")
                return cache_entry['data']
            else:
                # 期限切れのキャッシュを削除
                del self.trend_cache[cache_key]
                logger.info(f"キャッシュ期限切れ: {cache_key[:8]}...")
        return None
    
    def _cache_trend_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """傾向分析結果をキャッシュに保存"""
        # キャッシュサイズ制限
        if len(self.trend_cache) >= self.max_cache_size:
            # 最も古いエントリを削除
            oldest_key = min(self.trend_cache.keys(), 
                           key=lambda k: self.trend_cache[k]['timestamp'])
            del self.trend_cache[oldest_key]
            logger.info(f"キャッシュサイズ制限により削除: {oldest_key[:8]}...")
        
        self.trend_cache[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }
        logger.info(f"キャッシュに保存: {cache_key[:8]}... (合計: {len(self.trend_cache)}件)")
    
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
    
    def analyze_course_trend(self, race_data: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """
        コース傾向分析（実際の出場馬・騎手の該当コース成績に基づく3項目分析）
        
        Args:
            race_data: レース情報（出場馬・騎手含む）
            progress_callback: プログレス報告用コールバック関数
        
        Returns:
            コース傾向分析結果（3項目）:
            1. 出場する馬全ての開催場所（開催場+距離+コース種別）での成績複勝率
            2. 騎手の枠順別複勝率  
            3. 騎手の開催場所（開催場+距離+コース種別）での成績複勝率
        """
        try:
            # キャッシュチェック
            cache_key = self._generate_cache_key(race_data)
            cached_result = self._get_cached_trend(cache_key)
            if cached_result:
                if progress_callback:
                    progress_callback("キャッシュから結果を取得しました", 100)
                return cached_result
            
            venue = race_data.get('venue', '不明')
            distance = race_data.get('distance')
            
            # distanceが文字列の場合、数値に変換
            if isinstance(distance, str):
                # "1200m" -> 1200 のような変換
                distance_str = distance.replace('m', '').replace('M', '').strip()
                try:
                    distance = int(distance_str)
                except (ValueError, AttributeError):
                    distance = None
            
            # track_typeはcourse_typeまたはtrack_conditionから取得
            track_type = race_data.get('course_type') or race_data.get('track_type', '芝')
            if track_type not in ['芝', 'ダート']:
                # デフォルトは芝
                track_type = '芝'
            
            horses = race_data.get('horses', [])
            jockeys = race_data.get('jockeys', [])
            posts = race_data.get('posts', [])  # 枠番データを取得
            
            # horsesが整数や辞書の場合の処理
            if horses and not isinstance(horses[0], str):
                logger.error(f"horses配列の要素が文字列ではありません: type={type(horses[0])}, value={horses[0]}")
                # horsesが数値の配列の場合、空配列に置き換える
                horses = []
            
            # jockeysのデータ型チェック
            if jockeys:
                # jockeysが文字列のリストであることを確認
                if not isinstance(jockeys, list):
                    logger.error(f"jockeysがリストではありません: type={type(jockeys)}")
                    jockeys = []
                else:
                    # 各要素が文字列であることを確認
                    valid_jockeys = []
                    for j in jockeys:
                        if isinstance(j, str):
                            valid_jockeys.append(j)
                        else:
                            logger.error(f"騎手名が文字列ではありません: type={type(j)}, value={j}")
                    jockeys = valid_jockeys
            
            # postsのデータ型チェック
            if posts:
                # postsが数値のリストであることを確認
                if not isinstance(posts, list):
                    logger.error(f"postsがリストではありません: type={type(posts)}")
                    posts = []
                else:
                    # 各要素が数値であることを確認
                    valid_posts = []
                    for p in posts:
                        if isinstance(p, (int, float)):
                            valid_posts.append(int(p))
                        elif isinstance(p, str):
                            # 文字列の場合は数値に変換を試みる
                            try:
                                valid_posts.append(int(p))
                            except (ValueError, TypeError):
                                logger.error(f"枠番が数値に変換できません: type={type(p)}, value={p}")
                        else:
                            logger.error(f"枠番が不正な型です: type={type(p)}, value={p}")
                    posts = valid_posts
            
            # コース識別子（例: "新潟1800m芝"）
            course_key = f"{venue}{distance}m{track_type}" if distance else f"{venue}{track_type}"
            
            logger.info(f"傾向分析開始（実出場データ）: {course_key}")
            logger.info(f"venue: {venue}, distance: {distance} (type: {type(distance)}), track_type: {track_type}")
            logger.info(f"出場馬 ({len(horses)}頭): {horses[:5] if horses else []}")  # 最初の5頭のみログ
            logger.info(f"騎手 ({len(jockeys)}名): {jockeys[:5] if jockeys else []}")  # 最初の5名のみログ
            logger.info(f"枠番 ({len(posts)}): {posts[:5] if posts else []}")  # 最初の5枠のみログ
            
            # プログレス報告: 分析開始
            if progress_callback:
                progress_callback("ViewLogic傾向分析を開始しています...", 10)
            
            # 1. 出場馬の該当コース成績複勝率を分析（ViewLogicナレッジファイル使用）
            if progress_callback:
                progress_callback(f"出場馬の{course_key}での成績を分析中...", 30)
            horse_course_stats = self._analyze_horses_course_performance(horses, venue, distance, track_type)
            
            # 2. 騎手の枠順別複勝率分析（騎手ナレッジファイル使用）
            if progress_callback:
                progress_callback("騎手の枠順別成績を分析中...", 50)
            jockey_post_stats = []
            if jockeys and posts and len(jockeys) == len(posts):
                jockey_post_stats = self._analyze_jockeys_post_performance(jockeys, posts)
            
            # 3. 騎手の該当コース成績複勝率分析（騎手ナレッジファイル使用）
            if progress_callback:
                progress_callback(f"騎手の{course_key}での成績を分析中...", 70)
            jockey_course_stats = []
            if jockeys:
                jockey_course_stats = self._analyze_jockeys_course_performance(jockeys, venue, distance, track_type)
            
            # プログレス報告: 分析完了
            if progress_callback:
                progress_callback("分析結果をまとめています...", 95)
            
            result = {
                'status': 'success',
                'type': 'trend_analysis',
                'course_info': {
                    'venue': venue,
                    'distance': distance,
                    'track_type': track_type,
                    'course_key': course_key
                },
                'trends': {
                    'horse_course_performance': horse_course_stats,      # 1. 出場馬の該当コース成績
                    'jockey_post_performance': jockey_post_stats,        # 2. 騎手の枠順別成績
                    'jockey_course_performance': jockey_course_stats     # 3. 騎手の該当コース成績
                },
                'insights': self._generate_trend_insights_from_real_data(
                    horse_course_stats, jockey_post_stats, jockey_course_stats
                ),
                'data_period': '2023-2025',
                'sample_size': len(horses) + len(jockeys),
                'course_identifier': course_key
            }
            
            # 結果をキャッシュに保存
            self._cache_trend_result(cache_key, result)
            
            if progress_callback:
                progress_callback("分析完了！", 100)
                
            return result
            
        except Exception as e:
            logger.error(f"コース傾向分析エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'コース傾向分析に失敗しました: {str(e)}'
            }
    
    def recommend_betting_tickets(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        馬券推奨機能 - ViewLogic展開予想の上位5頭を基に推奨馬券を生成
        
        Args:
            race_data: レース情報（出走馬、騎手、枠番など）
        
        Returns:
            推奨馬券情報
        """
        try:
            # 基本情報を取得
            venue = race_data.get('venue', '不明')
            horses = race_data.get('horses', [])
            jockeys = race_data.get('jockeys', [])
            posts = race_data.get('posts', [])
            
            # データ検証
            if not horses or len(horses) < 3:
                return {
                    'status': 'error',
                    'message': '推奨馬券の生成には最低3頭の出走馬が必要です。'
                }
            
            # まずViewLogic展開予想を実行して上位5頭を取得
            flow_result = self.predict_race_flow_advanced(race_data)
            
            # 展開予想の上位5頭を取得（race_simulationのfinishから取得）
            top_5_horses = []
            if flow_result and flow_result.get('status') == 'success':
                # race_simulationのfinishから上位5頭を取得
                if 'race_simulation' in flow_result and 'finish' in flow_result['race_simulation']:
                    finish_order = flow_result['race_simulation']['finish']
                    logger.info(f"展開予想結果（finish）: {finish_order[:5]}")
                    # 既にpositionでソート済みなので、先頭から5頭取得
                    for horse_info in finish_order[:5]:
                        horse_name = horse_info.get('horse_name')
                        if horse_name and horse_name in horses:
                            top_5_horses.append(horse_name)
                    logger.info(f"展開予想上位5頭: {top_5_horses}")
                            
                # もし上記で取得できなければ、旧形式を試す（後方互換性のため）
                elif 'prediction' in flow_result and 'predicted_result' in flow_result['prediction']:
                    logger.info("旧形式での展開予想結果取得を試行")
                    for rank_info in flow_result['prediction']['predicted_result']:
                        if '位' in rank_info:
                            parts = rank_info.split(':')
                            if len(parts) >= 2:
                                horse_part = parts[1].strip()
                                horse_name = horse_part.split('(')[0].strip()
                                if horse_name in horses:
                                    top_5_horses.append(horse_name)
                                    if len(top_5_horses) >= 5:
                                        break
            
            # 上位馬が取得できない場合は従来の方法にフォールバック
            if len(top_5_horses) < 3:
                logger.warning("展開予想から十分な上位馬を取得できませんでした。従来の方法にフォールバック")
                recommendations = self._generate_betting_recommendations(race_data)
            else:
                # 展開予想の上位5頭から具体的な買い目を生成
                recommendations = self._generate_betting_recommendations_from_top5(
                    top_5_horses, race_data, flow_result
                )
            
            return {
                'status': 'success',
                'type': 'betting_recommendation',
                'venue': venue,
                'total_horses': len(horses),
                'top_5_horses': top_5_horses[:5],  # 上位5頭を含める
                'recommendations': recommendations,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"馬券推奨生成エラー: {e}")
            return {
                'status': 'error',
                'message': f'馬券推奨の生成に失敗しました: {str(e)}'
            }
    
    def _generate_betting_recommendations(self, race_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """馬券推奨を生成"""
        try:
            # 各馬のスコアを計算
            horse_scores = self._calculate_horse_scores(race_data)
            
            # スコア順にソート
            sorted_horses = sorted(horse_scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
            
            # 推奨馬券を生成
            recommendations = []
            budget = 10000  # デフォルト予算1万円
            
            if len(sorted_horses) >= 2:
                # 本命馬券（上位2頭の馬連）
                top_horses = [sorted_horses[0][0], sorted_horses[1][0]]
                recommendations.append({
                    'type': '本命',
                    'ticket_type': '馬連',
                    'horses': top_horses,
                    'confidence': 85,
                    'investment': int(budget * 0.4),
                    'reason': f'{top_horses[0]} × {top_horses[1]}の鉄板構成'
                })
                
            if len(sorted_horses) >= 4:
                # 対抗馬券（1位軸の3連複）
                axis_horse = sorted_horses[0][0]
                target_horses = [sorted_horses[i][0] for i in range(1, 4)]
                recommendations.append({
                    'type': '対抗',
                    'ticket_type': '3連複',
                    'horses': [axis_horse] + target_horses,
                    'confidence': 65,
                    'investment': int(budget * 0.35),
                    'reason': f'{axis_horse}軸の手堅い組み合わせ'
                })
                
            # 穴狙い馬券（特殊条件の馬を探す）
            surprise_candidate = self._find_surprise_candidate(sorted_horses, race_data)
            if surprise_candidate and len(sorted_horses) >= 3:
                surprise_horse = surprise_candidate['horse']
                surprise_reason = surprise_candidate['reason']
                recommendations.append({
                    'type': '穴狙い',
                    'ticket_type': '馬連',
                    'horses': [sorted_horses[0][0], surprise_horse],
                    'confidence': 25,
                    'investment': int(budget * 0.25),
                    'reason': f'{surprise_horse}は{surprise_reason}'
                })
            
            # 予算が余った場合の調整
            total_invested = sum(rec['investment'] for rec in recommendations)
            if total_invested < budget:
                remaining = budget - total_invested
                if recommendations:
                    recommendations[-1]['investment'] += remaining
            
            return recommendations
            
        except Exception as e:
            logger.error(f"馬券推奨生成エラー: {e}")
            return []
    
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
                        # distanceのチェック（KYORIフィールドを使用）
                        if distance:
                            race_distance = race.get('KYORI')
                            if race_distance:
                                # 文字列の場合は数値に変換
                                if isinstance(distance, str):
                                    distance_num = int(distance.replace('m', ''))
                                else:
                                    distance_num = distance
                                if abs(int(race_distance) - distance_num) > 100:  # 100m以上の差があれば除外
                                    continue
                        
                        # track_typeのチェック（TRACK_CODEフィールドを使用）
                        if track_type:
                            track_code = race.get('TRACK_CODE', '')
                            # トラックコードから芝/ダートを判定
                            # 11-19: 芝, 21-29: ダート
                            if track_type == '芝' and not (11 <= int(track_code) <= 19 if track_code else False):
                                continue
                            if track_type == 'ダート' and not (21 <= int(track_code) <= 29 if track_code else False):
                                continue
                        
                        total_races += 1
                        
                        # 騎手統計
                        jockey = race.get('KISHUMEI_RYAKUSHO')  # 騎手名略称
                        if jockey:
                            if jockey not in jockey_stats:
                                jockey_stats[jockey] = {'runs': 0, 'wins': 0, 'fukusho': 0}
                            jockey_stats[jockey]['runs'] += 1
                            finish = race.get('KAKUTEI_CHAKUJUN')
                            if finish is not None:
                                if finish == 1:
                                    jockey_stats[jockey]['wins'] += 1
                                if finish <= 3:
                                    jockey_stats[jockey]['fukusho'] += 1
                        
                        # 血統統計（現在のデータには含まれていない）
                        # TODO: 血統データが追加されたら実装
                        pass
                        
                        # 枠順統計（Phase 4データが欠落しているため、スキップ）
                        # 騎手の枠順別複勝率は後で騎手ナレッジから取得
                        
                        # 脚質統計（コーナー通過順位から判定）
                        corner1 = race.get('CORNER1_JUNI')
                        if corner1 is not None:
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
                                finish_pos = race.get('KAKUTEI_CHAKUJUN')
                                if finish_pos is not None and finish_pos <= 3:
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
            
            # 騎手ナレッジから枠順別複勝率を取得（上位騎手のみ）
            top_jockeys = [j['name'] for j in jockey_list[:10]]
            if top_jockeys:
                jockey_post_stats = self.jockey_manager.get_jockey_post_position_fukusho_rates(top_jockeys)
                
                # 集計して平均を計算
                aggregated_post_stats = {
                    '内枠（1-6）': {'fukusho_rate': 0, 'race_count': 0, 'jockey_count': 0},
                    '中枠（7-12）': {'fukusho_rate': 0, 'race_count': 0, 'jockey_count': 0},
                    '外枠（13-18）': {'fukusho_rate': 0, 'race_count': 0, 'jockey_count': 0}
                }
                
                for jockey_name, jockey_post_data in jockey_post_stats.items():
                    for category, stats in jockey_post_data.items():
                        if stats['race_count'] > 0:
                            prev_count = aggregated_post_stats[category]['race_count']
                            prev_rate = aggregated_post_stats[category]['fukusho_rate']
                            new_count = stats['race_count']
                            new_rate = stats['fukusho_rate']
                            
                            # 重み付き平均
                            total_count = prev_count + new_count
                            if total_count > 0:
                                aggregated_post_stats[category]['fukusho_rate'] = (
                                    (prev_rate * prev_count + new_rate * new_count) / total_count
                                )
                                aggregated_post_stats[category]['race_count'] = total_count
                                aggregated_post_stats[category]['jockey_count'] += 1
                
                # post_statsを騎手ナレッジベースに置き換え
                post_stats = aggregated_post_stats
            
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
        
        # 枠順傾向を予想（騎手ナレッジを活用）
        post_prediction = self._predict_post_trend(venue, jockeys)
        
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
        
        if not jockeys or not self.jockey_manager.is_loaded():
            return jockey_stats
        
        # 各騎手の成績を取得（正規化してから検索）
        for jockey_name in jockeys:
            # 騎手名を正規化
            normalized_name = self._normalize_jockey_name(jockey_name)
            jockey_data = self.jockey_manager.get_jockey_data(normalized_name)
            
            # jockey_dataがdictであることを確認
            if jockey_data and isinstance(jockey_data, dict):
                # 騎手の総合成績を取得
                overall_stats = jockey_data.get('overall_stats', {})
                if overall_stats:
                    jockey_stats.append({
                        'name': jockey_name,  # 元の名前を表示用に使用
                        'results': f"{overall_stats.get('total_races_analyzed', 0)}戦",
                        'fukusho_rate': overall_stats.get('overall_fukusho_rate', 0) / 100,  # パーセントを小数に
                        'venue_course_stats': jockey_data.get('venue_course_stats', {})
                    })
            else:
                logger.warning(f"騎手データが見つからない、または無効: {jockey_name} → {normalized_name}")
        
        # 複勝率順にソート
        jockey_stats.sort(key=lambda x: x['fukusho_rate'], reverse=True)
        
        return jockey_stats
    
    def _predict_post_trend(self, venue: str, jockeys: List[str] = None) -> Dict:
        """開催場の枠順傾向を予想（騎手ナレッジを活用）"""
        if jockeys and self.jockey_manager.is_loaded():
            # 騎手名を正規化してから枠順別複勝率を取得
            normalized_jockeys = [self._normalize_jockey_name(j) for j in jockeys]
            jockey_post_stats = self.jockey_manager.get_jockey_post_position_fukusho_rates(normalized_jockeys)
            
            # 集計
            aggregated_stats = {
                '内枠（1-6）': {'fukusho_rate': 0, 'race_count': 0},
                '中枠（7-12）': {'fukusho_rate': 0, 'race_count': 0},
                '外枠（13-18）': {'fukusho_rate': 0, 'race_count': 0}
            }
            
            for jockey_name, jockey_data in jockey_post_stats.items():
                for category, stats in jockey_data.items():
                    if stats['race_count'] > 0:
                        prev_count = aggregated_stats[category]['race_count']
                        prev_rate = aggregated_stats[category]['fukusho_rate']
                        new_count = stats['race_count']
                        new_rate = stats['fukusho_rate']
                        
                        total_count = prev_count + new_count
                        if total_count > 0:
                            aggregated_stats[category]['fukusho_rate'] = (
                                (prev_rate * prev_count + new_rate * new_count) / total_count
                            )
                            aggregated_stats[category]['race_count'] = total_count
            
            return aggregated_stats
        else:
            # 騎手データがない場合は従来の方法
            course_stats = self._calculate_course_statistics(venue)
            return course_stats.get('post_stats', {})
    
    def _predict_track_bias(self, post_trend: Dict) -> str:
        """枠順傾向からトラックバイアスを予想"""
        if not post_trend:
            return 'フラット'
        
        # ベイズ補正を適用（内枠は1-6、外枠は13-18）
        outer_rate = post_trend.get('外枠（13-18）', {}).get('fukusho_rate', 0)
        inner_rate = post_trend.get('内枠（1-6）', {}).get('fukusho_rate', 0)
        
        if outer_rate > 0.4:
            return '外有利'
        elif inner_rate > 0.4:
            return '内有利'
        return 'フラット'
    
    def _generate_daily_prediction_text(self, daily_stats: Dict, venue: str) -> str:
        """当日傾向の詳細な予想文章を生成"""
        lines = []
        lines.append(f"## 本日の{venue}傾向予想")
        lines.append("")
        
        # 脚質傾向の詳細分析
        style_perf = daily_stats.get('style_performance', {})
        if style_perf:
            lines.append("### 脚質別予想")
            # 統計を整理
            sorted_styles = sorted(style_perf.items(), key=lambda x: x[1].get('ratio', 0), reverse=True)
            
            for style, data in sorted_styles:
                if data.get('runs', 0) > 0:
                    ratio = data.get('ratio', 0)
                    lines.append(f"- **{style}**: {data['runs']}頭 (構成比 {ratio*100:.1f}%)")
            
            # 最も有利な脚質を判定
            best_style = max(style_perf.items(), key=lambda x: x[1].get('ratio', 0))
            if best_style[1].get('ratio', 0) > 0.3:
                lines.append("")
                lines.append(f"**予想**: {best_style[0]}馬が{best_style[1]['runs']}頭と多く、ペースが{'速く' if best_style[0] in ['逃げ', '先行'] else '落ち着いた展開に'}なりそうです。")
        
        lines.append("")
        
        # 好調騎手の詳細
        hot_jockeys = daily_stats.get('hot_jockeys', [])
        if hot_jockeys:
            lines.append("### 注目騎手")
            for i, jockey in enumerate(hot_jockeys[:3], 1):
                lines.append(f"{i}. **{jockey['name']}** - 複勝率 {jockey['fukusho_rate']*100:.1f}% ({jockey.get('results', 'データなし')})")
            
            if hot_jockeys[0]['fukusho_rate'] > 0.5:
                lines.append("")
                lines.append(f"特に**{hot_jockeys[0]['name']}騎手**は複勝率{hot_jockeys[0]['fukusho_rate']*100:.1f}%と絶好調です。")
        
        lines.append("")
        
        # 枠順傾向の詳細
        lines.append("### 枠順傾向")
        post_trend = daily_stats.get('post_trend', {})
        if post_trend:
            for position, stats in post_trend.items():
                fukusho_rate = stats.get('fukusho_rate', 0)
                race_count = stats.get('race_count', 0)
                if race_count > 0:
                    lines.append(f"- {position}: 複勝率 **{fukusho_rate:.1f}%** ({race_count}レース)")
        
        # トラックバイアス判定
        track_bias = daily_stats.get('track_bias', 'フラット')
        lines.append("")
        if track_bias == '外有利':
            lines.append("**バイアス**: 外枠有利 - 外回りコースで差し馬が台頭しやすい傾向")
        elif track_bias == '内有利':
            lines.append("**バイアス**: 内枠有利 - 内ラチ沿いが伸びる馬場状態")
        else:
            lines.append("**バイアス**: フラット - 枠順による有利不利は少ない")
        
        lines.append("")
        lines.append("---")
        
        return "\n".join(lines)
    
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
        
        # 騎手推奨
        hot_jockeys = stats.get('hot_jockeys', [])
        if hot_jockeys:
            top_jockey = hot_jockeys[0]
            recommendations.append(f"{top_jockey['name']}騎手の騎乗馬は要注目")
        
        # 脚質推奨
        style_stats = stats.get('style_stats', {})
        best_style = max(style_stats.items(), key=lambda x: x[1].get('fukusho_rate', 0), default=None)
        if best_style and best_style[1].get('fukusho_rate', 0) > 0.3:
            recommendations.append(f"{best_style[0]}馬中心の馬券構成")
        
        return recommendations
    
    def _calculate_horse_scores(self, race_data: Dict[str, Any]) -> Dict[str, Dict]:
        """各馬のスコアを計算"""
        horses = race_data.get('horses', [])
        jockeys = race_data.get('jockeys', [])
        posts = race_data.get('posts', [])
        venue = race_data.get('venue', '')
        
        horse_scores = {}
        
        for i, horse_name in enumerate(horses):
            try:
                # ViewLogicベーススコア（馬の基本スコア）
                horse_data = self.data_manager.get_horse_data(horse_name)
                base_score = 50.0  # デフォルトスコア
                
                if horse_data and 'running_style' in horse_data:
                    style_data = horse_data['running_style']
                    # スタイル評価から基本点を算出
                    if isinstance(style_data, dict):
                        confidence = style_data.get('confidence', 0.5)
                        base_score = 50 + (confidence * 30)  # 50-80点の範囲
                
                # 騎手スコア加算
                jockey_bonus = 0
                if i < len(jockeys) and self.jockey_manager.is_loaded():
                    jockey_name = self._normalize_jockey_name(jockeys[i])
                    jockey_data = self.jockey_manager.get_jockey_data(jockey_name)
                    if jockey_data and isinstance(jockey_data, dict):
                        overall_stats = jockey_data.get('overall_stats', {})
                        fukusho_rate = overall_stats.get('overall_fukusho_rate', 0)
                        jockey_bonus = (fukusho_rate / 100) * 20  # 最大20点加算
                
                # 枠順ボーナス（内枠有利など）
                post_bonus = 0
                if i < len(posts):
                    post = posts[i]
                    if 1 <= post <= 6:
                        post_bonus = 5
                    elif 7 <= post <= 12:
                        post_bonus = 2
                    # 外枠（13-18）は加算なし
                
                # 最終スコア
                total_score = base_score + jockey_bonus + post_bonus
                
                horse_scores[horse_name] = {
                    'total_score': min(total_score, 100),  # 100点上限
                    'base_score': base_score,
                    'jockey_bonus': jockey_bonus,
                    'post_bonus': post_bonus,
                    'jockey': jockeys[i] if i < len(jockeys) else '不明',
                    'post': posts[i] if i < len(posts) else 0
                }
                
            except Exception as e:
                logger.error(f"馬{horse_name}のスコア計算エラー: {e}")
                horse_scores[horse_name] = {
                    'total_score': 50.0,
                    'base_score': 50.0,
                    'jockey_bonus': 0,
                    'post_bonus': 0,
                    'jockey': jockeys[i] if i < len(jockeys) else '不明',
                    'post': posts[i] if i < len(posts) else 0
                }
        
        return horse_scores
    
    def _find_surprise_candidate(self, sorted_horses: List, race_data: Dict[str, Any]) -> Dict:
        """穴馬候補を探す"""
        if len(sorted_horses) < 6:
            return None
            
        # 中位から下位の馬（4-8位）で特殊条件のある馬を探す
        candidates = sorted_horses[3:8] if len(sorted_horses) >= 8 else sorted_horses[3:]
        
        for horse_name, horse_data in candidates:
            # 騎手が好調
            jockey = horse_data.get('jockey', '')
            if self._is_hot_jockey(jockey):
                return {
                    'horse': horse_name,
                    'reason': f'{jockey}騎手の好調'
                }
            
            # 内枠で逃げ・先行
            if horse_data.get('post', 0) <= 6:
                horse_viewlogic_data = self.data_manager.get_horse_data(horse_name)
                if horse_viewlogic_data and 'running_style' in horse_viewlogic_data:
                    style_data = horse_viewlogic_data['running_style']
                    if isinstance(style_data, dict) and style_data.get('style') in ['逃げ', '先行']:
                        return {
                            'horse': horse_name,
                            'reason': f'内枠{horse_data["post"]}番からの{style_data["style"]}'
                        }
        
        # 該当なしの場合は6位の馬を返す
        if len(sorted_horses) >= 6:
            return {
                'horse': sorted_horses[5][0],
                'reason': '中穴候補'
            }
        
        return None
    
    def _get_surprise_reason(self, horse_name: str, race_data: Dict[str, Any]) -> str:
        """穴馬の理由を取得"""
        horse_viewlogic_data = self.data_manager.get_horse_data(horse_name)
        if horse_viewlogic_data and 'running_style' in horse_viewlogic_data:
            style_data = horse_viewlogic_data['running_style']
            if isinstance(style_data, dict):
                return f"{style_data.get('style', '不明')}タイプの穴馬"
        return "データ不足による穴馬"
    
    def _is_hot_jockey(self, jockey_name: str) -> bool:
        """騎手が好調かどうか判定"""
        if not jockey_name or not self.jockey_manager.is_loaded():
            return False
            
        normalized_name = self._normalize_jockey_name(jockey_name)
        jockey_data = self.jockey_manager.get_jockey_data(normalized_name)
        
        if jockey_data and isinstance(jockey_data, dict):
            overall_stats = jockey_data.get('overall_stats', {})
            fukusho_rate = overall_stats.get('overall_fukusho_rate', 0)
            return fukusho_rate > 40  # 40%以上を好調とみなす
        
        return False
    
    def _generate_betting_recommendations_from_top5(
        self, 
        top_5_horses: List[str], 
        race_data: Dict[str, Any],
        flow_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        展開予想の上位5頭から実践的な馬券買い目を生成
        
        Args:
            top_5_horses: 展開予想の上位5頭
            race_data: レース情報
            flow_result: 展開予想結果
        
        Returns:
            推奨馬券リスト
        """
        try:
            recommendations = []
            budget = 10000  # デフォルト予算1万円
            
            # 最低3頭は必要
            if len(top_5_horses) < 3:
                return []
            
            # 1. 単勝（1位の馬）
            if len(top_5_horses) >= 1:
                recommendations.append({
                    'type': '単勝',
                    'ticket_type': '単勝',
                    'horses': [top_5_horses[0]],
                    'confidence': 75,
                    'investment': int(budget * 0.2),  # 20%
                    'reason': f'ViewLogic展開予想1位の{top_5_horses[0]}',
                    'buy_type': 'ストレート'
                })
            
            # 2. 馬連BOX（上位3頭）
            if len(top_5_horses) >= 3:
                box_horses = top_5_horses[:3]
                recommendations.append({
                    'type': '馬連BOX',
                    'ticket_type': '馬連',
                    'horses': box_horses,
                    'confidence': 65,
                    'investment': int(budget * 0.25),  # 25%
                    'reason': f'上位3頭（{", ".join(box_horses)}）のBOX買い',
                    'buy_type': 'BOX',
                    'combinations': 3  # 3頭BOXは3通り
                })
            
            # 3. 3連単1着流し（1位軸、2-3位から2着、4-5位から3着）
            if len(top_5_horses) >= 4:
                first = top_5_horses[0]
                second_candidates = top_5_horses[1:3]  # 2-3位
                third_candidates = top_5_horses[2:min(5, len(top_5_horses))]  # 3-5位
                
                recommendations.append({
                    'type': '3連単流し',
                    'ticket_type': '3連単',
                    'horses': {
                        '1着': [first],
                        '2着': second_candidates,
                        '3着': third_candidates
                    },
                    'confidence': 45,
                    'investment': int(budget * 0.25),  # 25%
                    'reason': f'{first}の1着固定、2-3着流し',
                    'buy_type': '流し',
                    'combinations': len(second_candidates) * len(third_candidates)
                })
            
            # 4. ワイド（1位と2-3位の組み合わせ）
            if len(top_5_horses) >= 3:
                axis = top_5_horses[0]
                partners = top_5_horses[1:3]
                recommendations.append({
                    'type': 'ワイド',
                    'ticket_type': 'ワイド',
                    'horses': {
                        '軸': axis,
                        '相手': partners
                    },
                    'confidence': 80,
                    'investment': int(budget * 0.15),  # 15%
                    'reason': f'{axis}軸のワイド、確実性重視',
                    'buy_type': '軸流し',
                    'combinations': len(partners)
                })
            
            # 5. 3連複（上位4頭BOX）- 穴狙い
            if len(top_5_horses) >= 4:
                box_horses = top_5_horses[:4]
                recommendations.append({
                    'type': '3連複BOX',
                    'ticket_type': '3連複',
                    'horses': box_horses,
                    'confidence': 55,
                    'investment': int(budget * 0.15),  # 15%
                    'reason': f'上位4頭のBOX、配当狙い',
                    'buy_type': 'BOX',
                    'combinations': 4  # 4頭から3頭選ぶ組み合わせ
                })
            
            # ペース判定を追加情報として付与
            pace_info = ""
            if flow_result and 'pace' in flow_result:
                pace_data = flow_result['pace']
                if 'predicted_pace' in pace_data:
                    pace_info = f"（予想ペース: {pace_data['predicted_pace']}）"
            
            # 各推奨にペース情報を追加
            for rec in recommendations:
                if pace_info and '理由' in rec:
                    rec['reason'] += pace_info
            
            return recommendations
            
        except Exception as e:
            logger.error(f"展開予想ベースの馬券生成エラー: {e}")
            import traceback
            traceback.print_exc()
            # エラー時は従来の方法にフォールバック
            return self._generate_betting_recommendations(race_data)

    # =====================================
    # ViewLogic傾向分析：4項目分析メソッド群
    # =====================================

    def _analyze_horses_course_performance(self, horses: List[str], venue: str, distance: int, track_type: str) -> List[Dict]:
        """
        1. 出場する馬全ての開催場所（開催場+距離+コース種別）での成績複勝率を分析
        
        Args:
            horses: 出場馬名リスト
            venue: 開催場（新潟、東京など）
            distance: 距離（1800など）
            track_type: コース種別（芝、ダートなど）
            
        Returns:
            出場馬の該当コース成績リスト
        """
        horse_performances = []
        
        # horsesパラメータの型をチェック
        logger.info(f"_analyze_horses_course_performance called with horses type: {type(horses)}, value: {horses}")
        if not isinstance(horses, list):
            logger.error(f"horses パラメータがリストではありません: type={type(horses)}")
            return []
        
        course_key = f"{venue}{distance}m{track_type}" if distance else f"{venue}{track_type}"
        
        # 開催場コードマッピング
        venue_codes = {
            '札幌': '01', '函館': '02', '福島': '03', '新潟': '04',
            '東京': '05', '中山': '06', '中京': '07', '京都': '08',
            '阪神': '09', '小倉': '10'
        }
        venue_code = venue_codes.get(venue, '')
        
        try:
            logger.info(f"馬の該当コース成績分析開始: {len(horses)}頭, venue_code={venue_code}, distance={distance}")
            logger.info(f"data_manager loaded: {self.data_manager.is_loaded()}, total_horses: {self.data_manager.get_total_horses()}")
            
            for item in horses:
                # itemが文字列（馬名）でない場合の処理
                if not isinstance(item, str):
                    logger.error(f"馬名が文字列ではありません: type={type(item)}, value={item}")
                    continue
                    
                horse_name = item
                horse_data = self.data_manager.get_horse_data(horse_name)
                
                # horse_dataの型をチェック
                if not isinstance(horse_data, dict):
                    logger.error(f"馬 {horse_name} のデータが辞書ではありません: type={type(horse_data)}, value={horse_data}")
                    horse_performances.append({
                        'horse_name': horse_name,
                        'course_key': course_key,
                        'total_runs': 0,
                        'fukusho_count': 0,
                        'fukusho_rate': 0.0,
                        'status': 'invalid_data_type'
                    })
                    continue
                
                if not horse_data or 'races' not in horse_data:
                    logger.debug(f"馬データなし: {horse_name}")
                    # データがない場合は記録しておく
                    horse_performances.append({
                        'horse_name': horse_name,
                        'course_key': course_key,
                        'total_runs': 0,
                        'fukusho_count': 0,
                        'fukusho_rate': 0.0,
                        'status': 'no_data'
                    })
                    continue
                
                # 該当コースのレースを集計
                course_runs = 0
                course_fukusho = 0
                
                races_data = horse_data.get('races', [])
                # racesが正しい形式かチェック
                if not isinstance(races_data, list):
                    logger.error(f"馬 {horse_name} のracesデータが配列ではない: {type(races_data)}")
                    continue
                    
                for race in races_data:
                    # raceが辞書かチェック
                    if not isinstance(race, dict):
                        logger.error(f"馬 {horse_name} のレースデータが辞書ではない: {type(race)} = {race}")
                        continue
                        
                    # 開催場チェック
                    if race.get('KEIBAJO_CODE') != venue_code:
                        continue
                    
                    # 距離チェック（±100m許容）
                    if distance:
                        race_distance = race.get('KYORI')
                        if race_distance:
                            try:
                                if abs(int(race_distance) - distance) > 100:
                                    continue
                            except (ValueError, TypeError):
                                continue
                    
                    # コース種別チェック（簡易版：トラックコードから推定）
                    track_code = race.get('TRACK_CODE', '')
                    if track_code:
                        try:
                            track_code_num = int(track_code)
                            # 11-19: 芝, 21-29: ダート
                            if track_type == '芝' and not (11 <= track_code_num <= 19):
                                continue
                            if track_type == 'ダート' and not (21 <= track_code_num <= 29):
                                continue
                        except (ValueError, TypeError):
                            pass
                    
                    course_runs += 1
                    
                    # 複勝判定（3着以内）
                    finish = race.get('KAKUTEI_CHAKUJUN')
                    if finish is not None:
                        try:
                            if int(finish) <= 3:
                                course_fukusho += 1
                        except (ValueError, TypeError):
                            pass
                
                # 成績をまとめる
                if course_runs > 0:
                    fukusho_rate = course_fukusho / course_runs
                    logger.info(f"馬の該当コース成績あり: {horse_name}, {course_runs}戦, 複勝率{fukusho_rate:.1%}")
                    horse_performances.append({
                        'horse_name': horse_name,
                        'course_key': course_key,
                        'total_runs': course_runs,
                        'fukusho_count': course_fukusho,
                        'fukusho_rate': fukusho_rate,
                        'status': 'found'
                    })
                else:
                    horse_performances.append({
                        'horse_name': horse_name,
                        'course_key': course_key,
                        'total_runs': 0,
                        'fukusho_count': 0,
                        'fukusho_rate': 0.0,
                        'status': 'no_course_data'
                    })
            
            # 複勝率順にソート
            horse_performances.sort(key=lambda x: x['fukusho_rate'], reverse=True)
            
            logger.info(f"馬の該当コース成績分析完了: {len(horse_performances)}頭, course={course_key}")
            return horse_performances
            
        except Exception as e:
            logger.error(f"馬のコース成績分析エラー: {e}")
            return []

    def _analyze_jockeys_post_performance(self, jockeys: List[str], posts: List[int] = None) -> Dict[str, Dict]:
        """
        2. 騎手の枠順別複勝率を分析（騎手ナレッジファイル使用）
        
        Args:
            jockeys: 騎手名リスト
            posts: 枠番リスト（オプション）
            
        Returns:
            騎手別枠順成績辞書
        """
        jockey_post_performances = {}
        
        # jockeysパラメータの型をチェック
        logger.info(f"_analyze_jockeys_post_performance called with jockeys type: {type(jockeys)}, posts type: {type(posts)}")
        if not isinstance(jockeys, list):
            logger.error(f"jockeys パラメータがリストではありません: type={type(jockeys)}, value={jockeys}")
            return {}
        
        # postsパラメータの型をチェック（Noneでない場合）
        if posts is not None and not isinstance(posts, list):
            logger.error(f"posts パラメータがリストではありません: type={type(posts)}, value={posts}")
            return {}
        
        # 騎手データの検証
        if not jockeys:
            logger.warning("騎手データが空です")
            return {}
        
        # 各要素の型チェックとNone値やempty stringを除外
        valid_jockeys = []
        for i, item in enumerate(jockeys):
            if not isinstance(item, str):
                logger.error(f"騎手名[{i}]が文字列ではありません: type={type(item)}, value={item}")
                continue
            if item and item.strip():
                valid_jockeys.append(item)
            else:
                logger.warning(f"騎手名[{i}]が空文字列です")
        
        if not valid_jockeys:
            logger.warning(f"有効な騎手データがありません: {jockeys}")
            return {}
        
        if not self.jockey_manager.is_loaded():
            logger.warning("騎手ナレッジファイルが読み込まれていません")
            return {}
        
        try:
            # postsの要素もチェック（提供されている場合）
            valid_posts = None
            if posts is not None:
                valid_posts = []
                for i, post in enumerate(posts):
                    if not isinstance(post, (int, float)):
                        logger.error(f"枠番[{i}]が数値ではありません: type={type(post)}, value={post}")
                        # 不正な値は0として扱う
                        valid_posts.append(0)
                    else:
                        # floatの場合はintに変換
                        valid_posts.append(int(post))
                logger.info(f"検証後の枠番リスト: {valid_posts}")
            
            # 騎手名を正規化（騎手ナレッジファイルの形式に合わせる）
            normalized_jockeys = []
            logger.info(f"傾向分析に使用する騎手名（元データ）: {valid_jockeys}")
            for jockey in valid_jockeys:
                jockey_normalized = self._normalize_jockey_name(jockey)
                normalized_jockeys.append(jockey_normalized)
            
            logger.info(f"正規化後の騎手名: {normalized_jockeys}")
            
            # 騎手ナレッジから枠順別複勝率を取得
            jockey_post_stats = self.jockey_manager.get_jockey_post_position_fukusho_rates(normalized_jockeys)
            
            # jockey_post_statsの型チェック
            if not isinstance(jockey_post_stats, dict):
                logger.error(f"jockey_post_statsが辞書ではありません: type={type(jockey_post_stats)}, value={jockey_post_stats}")
                return {}
            
            # 元の騎手名をキーとして返す（枠番情報も含む）
            for i, original_jockey in enumerate(valid_jockeys):
                if i < len(normalized_jockeys):
                    normalized = normalized_jockeys[i]
                    result_data = {}
                    
                    # 枠番が提供されている場合は、その枠番での成績を取得
                    if valid_posts and i < len(valid_posts):
                        post_num = valid_posts[i]
                        # 枠番カテゴリーを判定
                        if post_num <= 6:
                            category = '内枠（1-6）'
                        elif post_num <= 12:
                            category = '中枠（7-12）'
                        else:
                            category = '外枠（13-18）'
                        
                        result_data['assigned_post'] = post_num
                        result_data['post_category'] = category
                    
                    if normalized in jockey_post_stats:
                        # jockey_post_stats[normalized]の型チェック
                        jockey_stats = jockey_post_stats[normalized]
                        if not isinstance(jockey_stats, dict):
                            logger.error(f"騎手 {normalized} のpost_statsが辞書ではありません: type={type(jockey_stats)}, value={jockey_stats}")
                            result_data['all_post_stats'] = {
                                '内枠（1-6）': {'race_count': 0, 'fukusho_rate': 0.0, 'status': 'error'},
                                '中枠（7-12）': {'race_count': 0, 'fukusho_rate': 0.0, 'status': 'error'},
                                '外枠（13-18）': {'race_count': 0, 'fukusho_rate': 0.0, 'status': 'error'}
                            }
                        else:
                            # 全枠順データを保持
                            result_data['all_post_stats'] = jockey_stats
                            
                            # 該当枠番での成績を特別に抽出
                            if 'post_category' in result_data:
                                category = result_data['post_category']
                                if category in jockey_stats:
                                    category_stats = jockey_stats[category]
                                    # category_statsの型チェック
                                    if not isinstance(category_stats, dict):
                                        logger.error(f"騎手 {normalized} のカテゴリー {category} データが辞書ではありません: type={type(category_stats)}")
                                    else:
                                        result_data['assigned_post_stats'] = category_stats
                    else:
                        # データがない場合
                        result_data['all_post_stats'] = {
                            '内枠（1-6）': {'race_count': 0, 'fukusho_rate': 0.0, 'status': 'no_data'},
                            '中枠（7-12）': {'race_count': 0, 'fukusho_rate': 0.0, 'status': 'no_data'},
                            '外枠（13-18）': {'race_count': 0, 'fukusho_rate': 0.0, 'status': 'no_data'}
                        }
                        
                    jockey_post_performances[original_jockey] = result_data
            
            logger.info(f"騎手の枠順別成績分析完了: {len(jockey_post_performances)}名")
            return jockey_post_performances
            
        except Exception as e:
            logger.error(f"騎手の枠順別成績分析エラー: {e}")
            return {}

    def _analyze_jockeys_course_performance(self, jockeys: List[str], venue: str, distance: int, track_type: str) -> List[Dict]:
        """
        3. 騎手の開催場所（開催場+距離+コース種別）での成績複勝率を分析
        ViewLogicナレッジファイルのracesデータから騎手別に集計
        
        Args:
            jockeys: 騎手名リスト
            venue: 開催場
            distance: 距離
            track_type: コース種別
            
        Returns:
            騎手の該当コース成績リスト
        """
        jockey_course_performances = []
        course_key = f"{venue}{distance}m{track_type}" if distance else f"{venue}{track_type}"
        
        # jockeysパラメータの型をチェック
        logger.info(f"_analyze_jockeys_course_performance called with jockeys type: {type(jockeys)}")
        if not isinstance(jockeys, list):
            logger.error(f"jockeys パラメータがリストではありません（コース成績）: type={type(jockeys)}, value={jockeys}")
            return []
        
        # 騎手データの検証
        if not jockeys:
            logger.warning("騎手データが空です（コース成績分析）")
            return []
        
        # 各要素の型チェックとNone値やempty stringを除外
        valid_jockeys = []
        for i, item in enumerate(jockeys):
            if not isinstance(item, str):
                logger.error(f"騎手名[{i}]が文字列ではありません（コース成績）: type={type(item)}, value={item}")
                continue
            if item and item.strip():
                valid_jockeys.append(item)
            else:
                logger.warning(f"騎手名[{i}]が空文字列です（コース成績）")
        
        if not valid_jockeys:
            logger.warning(f"有効な騎手データがありません（コース成績分析）: {jockeys}")
            return []
        
        if not self.data_manager.is_loaded():
            logger.warning("ViewLogicナレッジファイルが読み込まれていません")
            return []
        
        try:
            # 各騎手について、ViewLogicの全馬データから該当コースでの騎乗成績を集計
            for jockey_name in valid_jockeys:
                wins = 0
                fukusho = 0
                total_runs = 0
                
                # 全馬のデータを検索
                for horse_name, horse_data in self.data_manager.horses_dict.items():
                    if 'races' not in horse_data:
                        continue
                    
                    # 該当馬のレースデータから騎手の成績を集計
                    for race in horse_data['races']:
                        # ViewLogicのフィールド名を使用
                        race_jockey = race.get('KISHUMEI_RYAKUSHO', '')
                        race_venue_code = race.get('KEIBAJO_CODE', '')
                        race_distance = race.get('KYORI', 0)
                        race_track_code = race.get('TRACK_CODE', '')
                        
                        # 会場コードを会場名に変換
                        venue_map = {
                            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
                            '05': '東京', '06': '中山', '07': '中京', '08': '京都',
                            '09': '阪神', '10': '小倉'
                        }
                        race_venue = venue_map.get(race_venue_code, '')
                        
                        # トラックコードをコース種別に変換（11-29は芝、それ以外はダート）
                        race_track = '芝' if 11 <= int(race_track_code) <= 29 else 'ダート'
                        
                        # 騎手名の正規化（スペースや記号の違いを吸収）
                        if self._normalize_jockey_name(race_jockey) == self._normalize_jockey_name(jockey_name):
                            # コース条件の一致確認
                            if race_venue == venue and race_track == track_type:
                                if not distance or race_distance == distance:
                                    total_runs += 1
                                    place = race.get('KAKUTEI_CHAKUJUN', 99)
                                    if place == 1:
                                        wins += 1
                                    if place <= 3:
                                        fukusho += 1
                
                # 成績データを追加
                if total_runs > 0:
                    jockey_course_performances.append({
                        'jockey_name': jockey_name,
                        'course_key': course_key,
                        'total_runs': total_runs,
                        'wins': wins,
                        'fukusho_count': fukusho,
                        'win_rate': wins / total_runs if total_runs > 0 else 0.0,
                        'fukusho_rate': fukusho / total_runs if total_runs > 0 else 0.0,
                        'status': 'found'
                    })
                else:
                    jockey_course_performances.append({
                        'jockey_name': jockey_name,
                        'course_key': course_key,
                        'total_runs': 0,
                        'wins': 0,
                        'fukusho_count': 0,
                        'win_rate': 0.0,
                        'fukusho_rate': 0.0,
                        'status': 'no_course_data'
                    })
            
            # 複勝率順にソート
            jockey_course_performances.sort(key=lambda x: x['fukusho_rate'], reverse=True)
            
            logger.info(f"騎手の該当コース成績分析完了: {len(jockey_course_performances)}名, course={course_key}")
            return jockey_course_performances
            
        except Exception as e:
            logger.error(f"騎手のコース成績分析エラー: {e}")
            return []

    def _analyze_course_bloodline_performance(self, venue: str, distance: int, track_type: str) -> List[Dict]:
        """
        4. 開催場所（開催場+距離+コース種別）の血統成績上位順を分析
        
        Args:
            venue: 開催場
            distance: 距離
            track_type: コース種別
            
        Returns:
            血統成績上位順リスト
        """
        bloodline_performances = {}
        course_key = f"{venue}{distance}m{track_type}" if distance else f"{venue}{track_type}"
        
        # 開催場コードマッピング
        venue_codes = {
            '札幌': '01', '函館': '02', '福島': '03', '新潟': '04',
            '東京': '05', '中山': '06', '中京': '07', '京都': '08',
            '阪神': '09', '小倉': '10'
        }
        venue_code = venue_codes.get(venue, '')
        
        try:
            # 全馬のデータを走査して血統別成績を集計
            # 注：現在のViewLogicナレッジには血統情報がないため、代替案として騎手統計を使用
            # 将来的に血統データが追加されたら修正する
            
            logger.warning("血統データは現在のナレッジファイルに含まれていません")
            
            # 暫定的に空リストを返す
            return []
            
        except Exception as e:
            logger.error(f"血統成績分析エラー: {e}")
            return []

    def _normalize_jockey_name(self, name: str) -> str:
        """騎手名を騎手ナレッジファイルの形式に正規化"""
        if not name:
            return ""
        
        # 既存のスペースを削除
        name_clean = name.strip().replace(' ', '').replace('　', '')
        
        # jockey_managerが利用可能で、データがロードされている場合
        if self.jockey_manager and self.jockey_manager.is_loaded():
            # 動的に騎手名を検索
            # 完全一致を最初に試す
            for full_name in self.jockey_manager.jockey_data.keys():
                clean_full = full_name.strip().replace('　', '').replace(' ', '')
                if clean_full == name_clean:
                    return full_name
            
            # 部分一致（姓のみ等）を試す
            # 2-3文字の場合は姓として扱う
            if len(name_clean) <= 3:
                candidates = []
                for full_name in self.jockey_manager.jockey_data.keys():
                    clean_full = full_name.strip().replace('　', '').replace(' ', '')
                    if clean_full.startswith(name_clean):
                        candidates.append(full_name)
                
                # 候補が1つだけなら確定
                if len(candidates) == 1:
                    return candidates[0]
                # 複数候補がある場合は、より一般的な騎手を優先
                # （ここでは最初の候補を返す）
                elif candidates:
                    return candidates[0]
        
        # フォールバック: 静的マッピング
        special_mappings = {
            'ルメール': 'ルメール',
            'Cルメール': 'ルメール',
            'C.ルメール': 'ルメール',
            '武豊': '武豊　　',
            '川田': '川田将雅',
            '福永': '福永祐一',
            '横山武': '横山武史',
            '横山和': '横山和生',
            '松山': '松山弘平',
            '戸崎': '戸崎圭太',
            '岩田康': '岩田康誠',
            '岩田望': '岩田望来',
            '田辺': '田辺裕信',
            '藤岡佑': '藤岡佑介',
            '藤岡康': '藤岡康太',
            '吉田豊': '吉田豊　',
            '吉田隼': '吉田隼人',
            '津村': '津村明秀',
            '古川': '古川吉洋',
            '大野': '大野拓弥',
            '石川': '石川裕紀',  # 石川裕紀人の可能性が高い
            '野中': '野中悠太',
            '菅原': '菅原明良',
            '木幡': '木幡初也',
            '柴田': '柴田大知',
            '坂井': '坂井瑠星',
            '佐々木': '佐々木大',  # 佐々木大輔の可能性
            '丸山': '丸山元気',
            '石橋': '石橋脩　',
            '菊沢': '菊沢一樹',
            '水沼': '水沼元輝',
            '遠藤': '遠藤健太',
            '石田': '石田拓郎',
        }
        
        # マッピングから探す
        if name_clean in special_mappings:
            return special_mappings[name_clean]
        
        # 見つからない場合は元の名前を4文字に正規化
        if len(name_clean) < 4:
            # 全角スペースで4文字に埋める
            normalized = name_clean + '　' * (4 - len(name_clean))
        elif len(name_clean) > 4:
            # 4文字を超える場合は最初の4文字
            normalized = name_clean[:4]
        else:
            normalized = name_clean
        
        return normalized
    
    def _generate_trend_insights_from_real_data(self, horse_course_stats: List[Dict], jockey_post_stats: Dict, 
                                               jockey_course_stats: List[Dict]) -> List[str]:
        """
        実データに基づく傾向分析のインサイトを生成
        
        Args:
            horse_course_stats: 馬のコース成績
            jockey_post_stats: 騎手の枠順別成績
            jockey_course_stats: 騎手のコース成績  
            bloodline_stats: 血統成績
            
        Returns:
            インサイト文言リスト
        """
        insights = []
        
        try:
            # 1. 馬のコース適性インサイト
            strong_horses = [h for h in horse_course_stats if h['fukusho_rate'] > 0.5 and h['total_runs'] >= 3]
            if strong_horses:
                top_horse = strong_horses[0]
                insights.append(f"{top_horse['horse_name']}は当コースで複勝率{top_horse['fukusho_rate']:.1%}と高適性")
            
            # 2. 騎手の枠順傾向インサイト  
            if jockey_post_stats:
                # 内枠・中枠・外枠の平均複勝率を計算
                position_averages = {'内枠（1-6）': 0, '中枠（7-12）': 0, '外枠（13-18）': 0}
                position_counts = {'内枠（1-6）': 0, '中枠（7-12）': 0, '外枠（13-18）': 0}
                
                for jockey_name, post_data in jockey_post_stats.items():
                    # 新しいデータ構造に対応
                    if 'assigned_post_stats' in post_data:
                        # 個別の騎手の該当枠での成績
                        category = post_data.get('post_category')
                        stats = post_data['assigned_post_stats']
                        if category and stats.get('race_count', 0) > 0:
                            position_averages[category] += stats['fukusho_rate']
                            position_counts[category] += 1
                    elif 'all_post_stats' in post_data:
                        # 全枠順データを使用
                        for position, stats in post_data['all_post_stats'].items():
                            if stats.get('race_count', 0) > 0:
                                position_averages[position] += stats['fukusho_rate']
                                position_counts[position] += 1
                
                for position in position_averages:
                    if position_counts[position] > 0:
                        position_averages[position] /= position_counts[position]
                
                # 最も有利な枠順を判定
                best_position = max(position_averages.items(), key=lambda x: x[1])
                if best_position[1] > 40:  # 40%以上
                    insights.append(f"枠順は{best_position[0]}が複勝率{best_position[1]:.1f}%で有利")
            
            # 3. 騎手のコース適性インサイト
            strong_jockeys = [j for j in jockey_course_stats if j['fukusho_rate'] > 0.4 and j['total_runs'] >= 5]
            if strong_jockeys:
                top_jockey = strong_jockeys[0]
                insights.append(f"{top_jockey['jockey_name']}は当コースで複勝率{top_jockey['fukusho_rate']*100:.1f}%の好成績")
            
            return insights[:3]  # 最大3つのインサイト
            
        except Exception as e:
            logger.error(f"傾向インサイト生成エラー: {e}")
            return ["実データに基づく傾向分析を実施"]
