"""
ViewLogic展開予想エンジン
脚質判定、ペース予測、展開シミュレーションを行う
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from statistics import mean, stdev
import math
from datetime import datetime

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
        # 各馬の脚質を判定
        style_distribution = {
            '逃げ': {'count': 0, 'horses': []},
            '先行': {'count': 0, 'horses': []},
            '差し': {'count': 0, 'horses': []},
            '追込': {'count': 0, 'horses': []},
            '不明': {'count': 0, 'horses': []}
        }
        
        detailed_escapes = {
            '超積極逃げ': [],
            '状況逃げ': [],
            '消極逃げ': []
        }
        
        for horse_data in all_horses_data:
            if 'races' not in horse_data:
                continue
            
            basic_style = self.style_analyzer.classify_basic_style(horse_data['races'])
            style_distribution[basic_style]['count'] += 1
            style_distribution[basic_style]['horses'].append(horse_data.get('horse_name', '不明'))
            
            # 逃げ馬の詳細分類
            if basic_style == '逃げ':
                _, sub_style = self.style_analyzer.classify_detailed_style(basic_style, horse_data['races'])
                detailed_escapes[sub_style].append(horse_data.get('horse_name', '不明'))
        
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
            'detailed_escapes': detailed_escapes
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
    """ViewLogic展開予想エンジンのメインクラス"""
    
    def __init__(self):
        self.predictor = RaceFlowPredictor()
        self.style_analyzer = RunningStyleAnalyzer()
        self.bayesian = BayesianCorrector()
        # ViewLogicデータマネージャーを初期化
        from services.viewlogic_data_manager import ViewLogicDataManager
        self.data_manager = ViewLogicDataManager()
    
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
        
        # 各馬のデータを取得
        horses_data = []
        for horse_name in horses:
            horse_data = self.data_manager.get_horse_data(horse_name)
            if horse_data:
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
                'disadvantaged_horses': analysis['advantages']['disadvantaged']
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
            'sample_size': course_stats.get('total_races', 0)
        }
    
    def analyze_daily_trend(self, date: str, venue: str) -> Dict[str, Any]:
        """
        当日傾向分析 - 開催日のリアルタイム傾向を提供
        
        Args:
            date: 開催日（YYYY-MM-DD形式）
            venue: 開催場
        
        Returns:
            当日傾向分析結果
        """
        # 当日の結果データを集計（実際の実装では結果DBから取得）
        daily_stats = self._calculate_daily_statistics(date, venue)
        
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
        """コース統計を計算（簡易実装）"""
        # 実際の実装ではナレッジデータを集計
        # ここでは仮のデータを返す
        venue_code_map = {
            '東京': '05', '中山': '06', '阪神': '09', '京都': '08',
            '中京': '07', '新潟': '04', '札幌': '02', '函館': '01',
            '福島': '03', '小倉': '10'
        }
        
        venue_code = venue_code_map.get(venue, '05')
        
        # 仮のデータ（実際はナレッジデータから集計）
        return {
            'jockey_stats': [
                {'name': 'ルメール', 'wins': 15, 'runs': 30, 'win_rate': 0.50, 'fukusho_rate': 0.70},
                {'name': '川田', 'wins': 12, 'runs': 28, 'win_rate': 0.43, 'fukusho_rate': 0.64},
                {'name': '武豊', 'wins': 10, 'runs': 25, 'win_rate': 0.40, 'fukusho_rate': 0.60},
                {'name': '横山武', 'wins': 8, 'runs': 22, 'win_rate': 0.36, 'fukusho_rate': 0.55},
                {'name': '戸崎', 'wins': 7, 'runs': 20, 'win_rate': 0.35, 'fukusho_rate': 0.50}
            ],
            'sire_stats': [
                {'name': 'ディープインパクト', 'fukusho_rate': 0.38, 'runs': 150},
                {'name': 'ハーツクライ', 'fukusho_rate': 0.35, 'runs': 80},
                {'name': 'キングカメハメハ', 'fukusho_rate': 0.32, 'runs': 90}
            ],
            'post_stats': {
                '内枠（1-4）': {'win_rate': 0.12, 'fukusho_rate': 0.25},
                '中枠（5-12）': {'win_rate': 0.18, 'fukusho_rate': 0.38},
                '外枠（13-18）': {'win_rate': 0.08, 'fukusho_rate': 0.20}
            },
            'style_stats': {
                '逃げ': {'win_rate': 0.15, 'fukusho_rate': 0.30},
                '先行': {'win_rate': 0.20, 'fukusho_rate': 0.40},
                '差し': {'win_rate': 0.12, 'fukusho_rate': 0.35},
                '追込': {'win_rate': 0.08, 'fukusho_rate': 0.25}
            },
            'total_races': 500
        }
    
    def _calculate_daily_statistics(self, date: str, venue: str) -> Dict:
        """当日統計を計算（簡易実装）"""
        # 実際の実装では当日の結果DBから集計
        # ここでは仮のデータを返す
        return {
            'style_performance': {
                '逃げ': {'wins': 3, 'runs': 6, 'win_rate': 0.50},
                '先行': {'wins': 5, 'runs': 18, 'win_rate': 0.28},
                '差し': {'wins': 3, 'runs': 24, 'win_rate': 0.13},
                '追込': {'wins': 1, 'runs': 12, 'win_rate': 0.08}
            },
            'hot_jockeys': [
                {'name': '武豊', 'wins': 2, 'runs': 3, 'fukusho_rate': 0.67},
                {'name': 'ルメール', 'wins': 2, 'runs': 2, 'fukusho_rate': 1.00},
                {'name': '川田', 'wins': 1, 'runs': 3, 'fukusho_rate': 0.33}
            ],
            'post_trend': {
                '1-2枠': {'fukusho_rate': 0.15},
                '3-6枠': {'fukusho_rate': 0.32},
                '7-8枠': {'fukusho_rate': 0.45}
            },
            'track_condition': '良',
            'track_bias': '外有利',
            'races_completed': 6
        }
    
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
