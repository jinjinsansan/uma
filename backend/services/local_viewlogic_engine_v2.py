#!/usr/bin/env python3
"""
地方競馬版ViewLogic展開予想エンジン V2
ViewLogicの4つのサブエンジン機能を地方競馬版で実装:
1. 展開予想 (predict_race_flow_advanced)
2. 傾向分析 (analyze_course_trend)  
3. 推奨馬券 (recommend_betting_tickets)
4. 過去データ (get_horse_history/get_jockey_history)
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime
from statistics import mean, stdev
# from .viewlogic_engine import ViewLogicEngine  # 親クラスに依存しない独立実装
from .local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
from .local_jockey_data_manager import local_jockey_manager

logger = logging.getLogger(__name__)

# ユーティリティ関数（JRA版と同じ）
def safe_int(value, default=0):
    """安全に整数変換"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """安全に浮動小数点変換"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

# JRA版と全く同じRunningStyleAnalyzerクラス
class RunningStyleAnalyzer:
    """脚質判定と3段階分類を行うクラス"""
    
    def classify_basic_style(self, horse_races: List[Dict]) -> str:
        """基本4分類（逃げ/先行/差し/追込）を判定"""
        if not horse_races:
            return "不明"
        
        # 1コーナー通過順位の平均を計算
        corner1_positions = []
        for race in horse_races:
            if 'CORNER1_JUNI' in race:
                try:
                    corner1_pos = int(race['CORNER1_JUNI'])
                    if corner1_pos > 0:
                        corner1_positions.append(corner1_pos)
                except (ValueError, TypeError):
                    continue
        
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
            corner1 = safe_int(race.get('CORNER1_JUNI'), 99)
            corner2 = safe_int(race.get('CORNER2_JUNI'), 99)
            finish = safe_int(race.get('KAKUTEI_CHAKUJUN'), 99)
            
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
            corner1 = safe_int(race.get('CORNER1_JUNI'), 99)
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
            corner4 = safe_int(race.get('CORNER4_JUNI'), 99)
            finish = safe_int(race.get('KAKUTEI_CHAKUJUN'), 99)
            
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
            corner4 = safe_int(race.get('CORNER4_JUNI'), 99)
            finish = safe_int(race.get('KAKUTEI_CHAKUJUN'), 99)
            
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

class LocalViewLogicEngineV2:  # ViewLogicEngineを継承しない独立実装
    """地方競馬版ViewLogic展開予想エンジン V2"""
    
    def __init__(self):
        """初期化：地方競馬版マネージャーを使用"""
        # 地方競馬版マネージャー
        self.data_manager = local_dlogic_manager_v2
        self.jockey_manager = local_jockey_manager
        
        # JRA版と同じアナライザークラスを使用
        self.style_analyzer = RunningStyleAnalyzer()
        
        # 互換性メソッドを追加（安全な最小限修正）
        self._ensure_data_manager_compatibility()
        self._ensure_jockey_manager_compatibility()
        
        logger.info(f"地方競馬版ViewLogicエンジンV2初期化完了")
        horse_count = len(self.data_manager.knowledge_data.get('horses', {}))
        jockey_count = len(self.jockey_manager.knowledge_data.get('jockeys', {}))
        logger.info(f"馬データ: {horse_count}頭, 騎手データ: {jockey_count}騎手")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """エンジン情報を返す"""
        return {
            "engine_type": "LocalViewLogicEngineV2",
            "venue": "南関東4場",
            "knowledge_horses": len(self.data_manager.knowledge_data.get('horses', {})),
            "knowledge_jockeys": len(self.jockey_manager.knowledge_data.get('jockeys', {})),
            "manager_type": "V2",
            "subengines": [
                "展開予想 (predict_race_flow_advanced)",
                "傾向分析 (analyze_course_trend)",
                "推奨馬券 (recommend_betting_tickets)",
                "過去データ (horse/jockey history)"
            ]
        }
    
    def get_horse_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """馬データを取得（ViewLogicDataManagerとの互換性のため）"""
        return self.data_manager.get_horse_raw_data(horse_name)
    
    def get_horse_history(self, horse_name: str) -> Dict[str, Any]:
        """
        馬の過去データを取得（地方競馬版）
        JRA版と同じ形式で実装
        
        Returns:
            {
                'status': 'success' or 'error',
                'horse_name': str,
                'races': List[Dict],  # 直近5走のデータ
                'running_style': Dict,  # 脚質情報
                'message': str
            }
        """
        try:
            # 馬データを取得
            horse_data = self.data_manager.get_horse_raw_data(horse_name)
            
            if not horse_data:
                return {
                    'status': 'error',
                    'message': f'{horse_name}のデータベースにデータがありません'
                }
            
            # 直近5走のデータを取得
            races = horse_data.get('races', [])
            recent_races = races[:5] if len(races) >= 5 else races
            
            # 各レースの重要データのみ抽出
            formatted_races = []
            for race in recent_races:
                # レース名の取得
                race_name = race.get('KYOSOMEI_HONDAI', '') or race.get('レース名', '')
                if not race_name:
                    race_name = f"{race.get('RACE_BANGO', race.get('レース番号', ''))}R"
                
                # 着順の取得（複数のフィールド名に対応）
                finish_position = race.get('KAKUTEI_CHAKUJUN') or race.get('着順')
                
                formatted_race = {
                    'date': race.get('KAISAI_NEN', '') or race.get('開催年', ''),
                    'venue': race.get('KEIBAJO', '') or race.get('競馬場', ''),
                    'race_name': race_name,
                    'distance': race.get('KYORI', 0) or race.get('距離', 0),
                    'track_type': race.get('TRACK_CODE', '') or race.get('馬場', ''),
                    'finish': finish_position,
                    'horse_count': race.get('TOSU', 0) or race.get('頭数', 0),
                    'horse_number': race.get('UMA_BAN', 0) or race.get('馬番', 0),
                    'jockey': race.get('KISHU_MEI', '') or race.get('騎手名', ''),
                    'weight': race.get('FUTANZYURYO', 0) or race.get('斤量', 0),
                    'odds': race.get('TANSHO_ODDS', 0) or race.get('単勝オッズ', 0),
                    'popularity': race.get('NINKI_ZYUNI', 0) or race.get('人気', 0),
                    'corner1': race.get('CORNER1_JUNI', 0),
                    'corner4': race.get('CORNER4_JUNI', 0),
                    'time': race.get('RACE_TIME', '') or race.get('タイム', '')
                }
                formatted_races.append(formatted_race)
            
            # 脚質情報を取得（実データから判定）
            running_style_info = {}
            if recent_races:
                basic_style = self.style_analyzer.classify_basic_style(recent_races)
                _, detailed_style = self.style_analyzer.classify_detailed_style(basic_style, recent_races)
                running_style_info = {
                    'basic': basic_style,
                    'detailed': detailed_style,
                    'confidence': 0.7 if len(recent_races) >= 3 else 0.4
                }
            
            return {
                'status': 'success',
                'horse_name': horse_name,
                'races': formatted_races,
                'running_style': running_style_info,
                'race_count': len(formatted_races),
                'message': f'{horse_name}の直近{len(formatted_races)}走データ'
            }
            
        except Exception as e:
            logger.error(f"馬履歴取得エラー ({horse_name}): {e}")
            return {
                'status': 'error',
                'message': f'データ取得に失敗しました: {str(e)}'
            }
    
    def get_jockey_history(self, jockey_name: str) -> Dict[str, Any]:
        """
        騎手の過去データを取得（地方競馬版）
        JRA版と同じ形式で実装
        
        Returns:
            {
                'status': 'success' or 'error',
                'jockey_name': str,
                'recent_rides': List[Dict],  # 直近騎乗データ
                'statistics': Dict,  # 統計情報
                'message': str
            }
        """
        try:
            # 騎手データを取得
            jockey_data = self.jockey_manager.get_jockey_data(jockey_name)
            
            if not jockey_data:
                return {
                    'status': 'error',
                    'message': f'{jockey_name}のデータベースにデータがありません'
                }
            
            # 統計情報を取得
            statistics = {}
            if isinstance(jockey_data, dict):
                overall_stats = jockey_data.get('overall_stats', {})
                statistics = {
                    'total_races': overall_stats.get('total_races', 0),
                    'total_wins': overall_stats.get('total_wins', 0),
                    'win_rate': overall_stats.get('overall_win_rate', 0),
                    'place_rate': overall_stats.get('overall_fukusho_rate', 0),
                    'earnings': overall_stats.get('total_earnings', 0)
                }
                
                # 直近の騎乗データ（もしあれば）
                recent_rides = []
                if 'recent_races' in jockey_data:
                    for race in jockey_data['recent_races'][:10]:
                        recent_rides.append({
                            'date': race.get('date', ''),
                            'venue': race.get('venue', ''),
                            'horse_name': race.get('horse_name', ''),
                            'finish': race.get('finish', 0),
                            'horse_count': race.get('horse_count', 0)
                        })
            else:
                # データ構造が異なる場合
                statistics = {
                    'message': 'データ形式が異なるため詳細情報を取得できません'
                }
                recent_rides = []
            
            return {
                'status': 'success',
                'jockey_name': jockey_name,
                'recent_rides': recent_rides,
                'statistics': statistics,
                'message': f'{jockey_name}の騎乗データ'
            }
            
        except Exception as e:
            logger.error(f"騎手履歴取得エラー ({jockey_name}): {e}")
            return {
                'status': 'error',
                'message': f'データ取得に失敗しました: {str(e)}'
            }
    
    # ===== 互換性のためのプロキシメソッド（安全な最小限修正） =====
    
    def _ensure_data_manager_compatibility(self):
        """data_managerに必要なメソッドを追加（ViewLogicEngineとの互換性のため）"""
        # get_total_horsesメソッドが存在しない場合、プロキシを追加
        if not hasattr(self.data_manager, 'get_total_horses'):
            def get_total_horses_proxy():
                """総馬数を取得するプロキシメソッド"""
                if hasattr(self.data_manager, 'knowledge_data') and self.data_manager.knowledge_data:
                    horses = self.data_manager.knowledge_data.get('horses', {})
                    return len(horses)
                return 0
            self.data_manager.get_total_horses = get_total_horses_proxy
            
        # is_loadedメソッドが存在しない場合、プロキシを追加
        if not hasattr(self.data_manager, 'is_loaded'):
            def is_loaded_proxy():
                """データがロード済みか確認するプロキシメソッド"""
                return hasattr(self.data_manager, 'knowledge_data') and self.data_manager.knowledge_data is not None
            self.data_manager.is_loaded = is_loaded_proxy
    
    def _ensure_jockey_manager_compatibility(self):
        """jockey_managerに必要なメソッドを追加（ViewLogicEngineとの互換性のため）"""
        # get_jockey_post_position_fukusho_ratesメソッドが存在しない場合、プロキシを追加
        if not hasattr(self.jockey_manager, 'get_jockey_post_position_fukusho_rates'):
            def get_jockey_post_position_fukusho_rates_proxy(jockey_names: list):
                """騎手の枠順別複勝率を取得するプロキシメソッド"""
                result = {}
                for jockey_name in jockey_names:
                    # デフォルトの枠順別データを返す（データ不足として扱う）
                    result[jockey_name] = {
                        '内枠（1-6）': {'fukusho_rate': 0.0, 'race_count': 0},
                        '中枠（7-12）': {'fukusho_rate': 0.0, 'race_count': 0},
                        '外枠（13-18）': {'fukusho_rate': 0.0, 'race_count': 0}
                    }
                return result
            self.jockey_manager.get_jockey_post_position_fukusho_rates = get_jockey_post_position_fukusho_rates_proxy
    
    def predict_race_flow_advanced(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        高度な展開予想（地方競馬版）
        JRA版と全く同じロジックで実装
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
                horse_data['horse_name'] = horse_name
                horse_data['horse_number'] = race_data.get('horse_numbers', [])[idx-1] if idx-1 < len(race_data.get('horse_numbers', [])) else idx
                horses_data.append(horse_data)
        
        # データ不足の場合は誠実に報告
        if len(horses_data) == 0:
            return {
                'status': 'error',
                'message': 'データベースにデータがありません',
                'type': 'advanced_flow_prediction'
            }
        
        # JRA版と同じペース予測アルゴリズム
        pace_prediction = self._advanced_pace_prediction(horses_data)
        
        # 詳細な脚質分類（超積極逃げ、状況逃げなど）
        detailed_styles = self._classify_detailed_styles(horses_data)
        
        # 位置取り安定性指標の計算
        position_stability = self._calculate_position_stability_all(horses_data)
        
        # 展開適性マッチング
        flow_matching = self._calculate_flow_matching(horses_data, pace_prediction)
        
        # 展開シミュレーション
        race_simulation = self._simulate_race_positions(horses_data, pace_prediction)
        
        # 結果をまとめる（JRA版と同じ構造）
        result = {
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
        
        return result
    
    def analyze_course_trend(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        コース傾向分析（地方競馬版）
        JRA版と同じデータ構造を使用した実装
        
        Returns:
            コース傾向分析結果（3項目）:
            1. 出場する馬全ての開催場所での成績複勝率
            2. 騎手の枠順別複勝率  
            3. 騎手の開催場所での成績複勝率
        """
        try:
            venue = race_data.get('venue', '不明')
            distance = race_data.get('distance')
            
            # distanceが文字列の場合、数値に変換
            if isinstance(distance, str):
                distance_str = distance.replace('m', '').replace('M', '').strip()
                try:
                    distance = int(distance_str)
                except (ValueError, AttributeError):
                    distance = None
            
            track_type = race_data.get('course_type') or race_data.get('track_type', 'ダート')
            horses = race_data.get('horses', [])
            jockeys = race_data.get('jockeys', [])
            posts = race_data.get('posts', [])
            
            # データ検証
            if not isinstance(horses, list) or (horses and not isinstance(horses[0], str)):
                logger.warning(f"馬データが不正: {type(horses)}")
                horses = []
            
            if not isinstance(jockeys, list):
                jockeys = []
            
            if not isinstance(posts, list):
                posts = []
            else:
                posts = [int(p) if isinstance(p, (int, float, str)) else 0 for p in posts]
            
            course_key = f"{venue}{distance}m{track_type}" if distance else f"{venue}{track_type}"
            
            logger.info(f"地方競馬版傾向分析開始: {course_key}")
            logger.info(f"馬: {len(horses)}頭, 騎手: {len(jockeys)}名, 枠番: {len(posts)}")
            
            # 1. 出場馬の該当コース成績複勝率を分析
            horse_course_stats = self._analyze_horses_course_performance(horses, venue, distance, track_type)
            
            # 2. 騎手の枠順別複勝率分析
            jockey_post_stats = []
            if jockeys and posts and len(jockeys) == len(posts):
                jockey_post_stats = self._analyze_jockeys_post_performance(jockeys, posts)
            
            # 3. 騎手の該当コース成績複勝率分析
            jockey_course_stats = []
            if jockeys:
                jockey_course_stats = self._analyze_jockeys_course_performance(jockeys, venue, distance, track_type)
            
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
                    'horse_course_performance': horse_course_stats,
                    'jockey_post_performance': jockey_post_stats,
                    'jockey_course_performance': jockey_course_stats
                },
                'insights': self._generate_trend_insights(
                    horse_course_stats, jockey_post_stats, jockey_course_stats
                ),
                'data_period': '2023-2025',
                'sample_size': len(horses) + len(jockeys),
                'course_identifier': course_key
            }
            
            return result
            
        except Exception as e:
            logger.error(f"地方競馬版コース傾向分析エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'コース傾向分析に失敗しました: {str(e)}'
            }
    
    def recommend_betting_tickets(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        馬券推奨（地方競馬版）
        JRA版と完全に同じロジックで実装
        """
        try:
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
            
            # ViewLogic展開予想を実行して上位馬を取得
            flow_result = self.predict_race_flow_advanced(race_data)
            
            # 展開予想の上位馬を取得
            top_5_horses = []
            if flow_result and flow_result.get('status') == 'success':
                if 'race_simulation' in flow_result and 'finish' in flow_result['race_simulation']:
                    finish_order = flow_result['race_simulation']['finish']
                    for horse_info in finish_order[:5]:
                        horse_name = horse_info.get('horse_name')
                        if horse_name and horse_name in horses:
                            top_5_horses.append(horse_name)
            
            # 展開予想から取得できない場合はスコア計算
            if len(top_5_horses) < 3:
                horse_scores = self._calculate_horse_scores(race_data)
                sorted_horses = sorted(horse_scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
                top_5_horses = [h[0] for h in sorted_horses[:5] if h[1]['total_score'] >= 0]
            
            # データが不足している場合
            if len(top_5_horses) < 3:
                return {
                    'status': 'error',
                    'message': 'データ不足により推奨馬券を生成できません。データベースにデータがありません。'
                }
            
            # 推奨馬券を生成（JRA版と同じロジック）
            recommendations = []
            budget = 10000
            
            if len(top_5_horses) >= 2:
                # 本命馬券（上位2頭の馬連）
                top_horses = top_5_horses[:2]
                recommendations.append({
                    'type': '本命',
                    'ticket_type': '馬連',
                    'horses': top_horses,
                    'confidence': 85,
                    'investment': int(budget * 0.4),
                    'reason': f'{top_horses[0]} × {top_horses[1]}の鉄板構成'
                })
            
            if len(top_5_horses) >= 4:
                # 対抗馬券（1位軸の3連複）
                axis_horse = top_5_horses[0]
                target_horses = top_5_horses[1:4]
                recommendations.append({
                    'type': '対抗',
                    'ticket_type': '3連複',
                    'horses': [axis_horse] + target_horses,
                    'confidence': 65,
                    'investment': int(budget * 0.35),
                    'reason': f'{axis_horse}軸の手堅い組み合わせ'
                })
            
            return {
                'status': 'success',
                'type': 'betting_recommendation',
                'venue': venue,
                'total_horses': len(horses),
                'top_5_horses': top_5_horses,
                'recommendations': recommendations,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"地方競馬版馬券推奨生成エラー: {e}")
            return {
                'status': 'error',
                'message': f'馬券推奨の生成に失敗しました: {str(e)}'
            }

    
    # ===== ヘルパーメソッド（JRA版と同一ロジック） =====
    
    def _calculate_horse_scores(self, race_data: Dict[str, Any]) -> Dict[str, Dict]:
        """各馬のスコアを計算（JRA版と同一ロジック）"""
        horses = race_data.get('horses', [])
        jockeys = race_data.get('jockeys', [])
        posts = race_data.get('posts', [])
        
        horse_scores = {}
        
        for i, horse_name in enumerate(horses):
            try:
                # 馬のデータを取得
                horse_data = self.data_manager.get_horse_raw_data(horse_name)
                
                if not horse_data:
                    # データがない場合は-1でマーク（誠実な対応）
                    horse_scores[horse_name] = {
                        'total_score': -1,
                        'base_score': -1,
                        'jockey_bonus': 0,
                        'post_bonus': 0,
                        'error': 'データベースにデータがありません'
                    }
                    continue
                
                # ViewLogicベーススコア（馬の基本スコア）
                base_score = 50.0
                races = horse_data.get('races', [])
                
                if races:
                    # 実際のレースデータから計算
                    recent_races = races[:5]  # 直近5走
                    win_count = sum(1 for r in recent_races if r.get('着順') == 1)
                    place_count = sum(1 for r in recent_races if r.get('着順', 99) <= 3)
                    
                    win_rate = win_count / len(recent_races) if recent_races else 0
                    place_rate = place_count / len(recent_races) if recent_races else 0
                    
                    base_score = 50 + (win_rate * 30) + (place_rate * 20)
                
                # 騎手スコア加算
                jockey_bonus = 0
                if i < len(jockeys) and self.jockey_manager.is_loaded():
                    jockey_data = self.jockey_manager.get_jockey_data(jockeys[i])
                    if jockey_data and isinstance(jockey_data, dict):
                        overall_stats = jockey_data.get('overall_stats', {})
                        fukusho_rate = overall_stats.get('overall_fukusho_rate', 0)
                        jockey_bonus = (fukusho_rate / 100) * 20  # 最大20点加算
                
                # 枠順ボーナス（JRA版と同じ）
                post_bonus = 0
                if i < len(posts):
                    post = posts[i]
                    if 1 <= post <= 6:
                        post_bonus = 5
                    elif 7 <= post <= 12:
                        post_bonus = 2
                    # 外枠（13-18）は加算なし
                
                total_score = base_score + jockey_bonus + post_bonus
                
                horse_scores[horse_name] = {
                    'total_score': min(total_score, 100),  # 100点上限
                    'base_score': base_score,
                    'jockey_bonus': jockey_bonus,
                    'post_bonus': post_bonus
                }
                
            except Exception as e:
                logger.error(f"馬スコア計算エラー ({horse_name}): {e}")
                horse_scores[horse_name] = {
                    'total_score': -1,
                    'base_score': -1,
                    'jockey_bonus': 0,
                    'post_bonus': 0,
                    'error': str(e)
                }
        
        return horse_scores
    
    def _analyze_horses_course_performance(self, horses: List[str], venue: str, 
                                          distance: int, track_type: str) -> List[Dict]:
        """出場馬のコース成績を分析（実データのみ使用）"""
        performances = []
        
        for horse_name in horses:
            try:
                horse_data = self.data_manager.get_horse_raw_data(horse_name)
                
                if not horse_data:
                    performances.append({
                        'horse_name': horse_name,
                        'error': 'データベースにデータがありません'
                    })
                    continue
                
                races = horse_data.get('races', [])
                # 該当コースのレースを抽出
                course_races = []
                for race in races:
                    race_venue = race.get('競馬場', '') or race.get('KEIBAJO', '')
                    race_distance = race.get('距離', 0) or race.get('KYORI', 0)
                    if race_venue == venue and race_distance == distance:
                        course_races.append(race)
                
                if course_races:
                    wins = sum(1 for r in course_races if r.get('着順', r.get('KAKUTEI_CHAKUJUN', 99)) == 1)
                    places = sum(1 for r in course_races if r.get('着順', r.get('KAKUTEI_CHAKUJUN', 99)) <= 3)
                    total = len(course_races)
                    
                    performances.append({
                        'horse_name': horse_name,
                        'course_key': f"{venue}{distance}m",
                        'total_races': total,
                        'wins': wins,
                        'places': places,
                        'win_rate': (wins / total * 100) if total > 0 else 0,
                        'place_rate': (places / total * 100) if total > 0 else 0
                    })
                else:
                    performances.append({
                        'horse_name': horse_name,
                        'course_key': f"{venue}{distance}m",
                        'total_races': 0,
                        'wins': 0,
                        'places': 0,
                        'win_rate': 0,
                        'place_rate': 0,
                        'message': '該当コースの実績なし'
                    })
                    
            except Exception as e:
                logger.error(f"馬コース成績分析エラー ({horse_name}): {e}")
                performances.append({
                    'horse_name': horse_name,
                    'error': str(e)
                })
        
        return performances
    
    def _analyze_jockeys_post_performance(self, jockeys: List[str], posts: List[int]) -> List[Dict]:
        """騎手の枠順別成績を分析（実データのみ）"""
        performances = []
        
        for i, jockey_name in enumerate(jockeys):
            if i < len(posts):
                post = posts[i]
                try:
                    # 実際の騎手データを取得
                    jockey_data = self.jockey_manager.get_jockey_data(jockey_name)
                    
                    if not jockey_data:
                        performances.append({
                            'jockey_name': jockey_name,
                            'post': post,
                            'error': 'データベースにデータがありません'
                        })
                        continue
                    
                    # 枠順別データが存在する場合のみ使用
                    if 'post_position_stats' in jockey_data:
                        post_stats = jockey_data['post_position_stats']
                        post_category = '内枠' if post <= 6 else '中枠' if post <= 12 else '外枠'
                        
                        if post_category in post_stats:
                            performances.append({
                                'jockey_name': jockey_name,
                                'post': post,
                                'post_category': post_category,
                                'place_rate': post_stats[post_category].get('fukusho_rate', 0),
                                'race_count': post_stats[post_category].get('race_count', 0)
                            })
                        else:
                            performances.append({
                                'jockey_name': jockey_name,
                                'post': post,
                                'post_category': post_category,
                                'message': '枠順別データなし'
                            })
                    else:
                        performances.append({
                            'jockey_name': jockey_name,
                            'post': post,
                            'message': '枠順別データが利用できません'
                        })
                        
                except Exception as e:
                    logger.error(f"騎手枠順成績分析エラー ({jockey_name}): {e}")
                    performances.append({
                        'jockey_name': jockey_name,
                        'error': str(e)
                    })
        
        return performances
    
    def _analyze_jockeys_course_performance(self, jockeys: List[str], venue: str, 
                                           distance: int, track_type: str) -> List[Dict]:
        """騎手のコース成績を分析（実データのみ）"""
        performances = []
        course_key = f"{venue}_{distance}"
        
        for jockey_name in jockeys:
            try:
                jockey_data = self.jockey_manager.get_jockey_data(jockey_name)
                
                if not jockey_data:
                    performances.append({
                        'jockey_name': jockey_name,
                        'error': 'データベースにデータがありません'
                    })
                    continue
                
                # コース別データが存在する場合のみ使用
                if 'course_stats' in jockey_data and course_key in jockey_data['course_stats']:
                    course_stat = jockey_data['course_stats'][course_key]
                    performances.append({
                        'jockey_name': jockey_name,
                        'course_key': f"{venue}{distance}m",
                        'place_rate': course_stat.get('fukusho_rate', 0),
                        'race_count': course_stat.get('race_count', 0)
                    })
                else:
                    performances.append({
                        'jockey_name': jockey_name,
                        'course_key': f"{venue}{distance}m",
                        'message': '該当コースのデータなし'
                    })
                    
            except Exception as e:
                logger.error(f"騎手コース成績分析エラー ({jockey_name}): {e}")
                performances.append({
                    'jockey_name': jockey_name,
                    'error': str(e)
                })
        
        return performances
    
    def _generate_trend_insights(self, horse_stats: List[Dict], 
                                jockey_post_stats: List[Dict], 
                                jockey_course_stats: List[Dict]) -> List[str]:
        """傾向分析のインサイトを生成（実データベース）"""
        insights = []
        
        # 馬の実績から傾向を分析（実データのみ）
        if horse_stats:
            # エラーでない有効なデータのみ抽出
            valid_stats = [h for h in horse_stats if 'place_rate' in h and not h.get('error')]
            if valid_stats:
                high_performers = [h for h in valid_stats if h['place_rate'] >= 40]
                if high_performers:
                    horse_names = [h['horse_name'] for h in high_performers[:3]]
                    insights.append(f"好走実績馬: {', '.join(horse_names)}")
                
                # データがある馬の数を報告
                data_count = len(valid_stats)
                total_count = len(horse_stats)
                if data_count < total_count:
                    insights.append(f"{total_count}頭中{data_count}頭のデータあり")
        
        # 騎手の枠順傾向（実データのみ）
        if jockey_post_stats:
            valid_jockey_posts = [j for j in jockey_post_stats if 'place_rate' in j and not j.get('error')]
            if valid_jockey_posts:
                inner_high = [j for j in valid_jockey_posts if j.get('post_category') == '内枠' and j['place_rate'] >= 35]
                if inner_high:
                    insights.append(f"内枠好走騎手: {', '.join([j['jockey_name'] for j in inner_high])}")
        
        # 騎手のコース相性（実データのみ）
        if jockey_course_stats:
            valid_jockey_course = [j for j in jockey_course_stats if 'place_rate' in j and not j.get('error')]
            if valid_jockey_course:
                course_experts = [j for j in valid_jockey_course if j['place_rate'] >= 35]
                if course_experts:
                    insights.append(f"コース巧者: {', '.join([j['jockey_name'] for j in course_experts[:2]])}")
        
        # データ不足の場合は誠実に報告
        if not insights:
            error_count = sum(1 for h in horse_stats if h.get('error'))
            if error_count > len(horse_stats) / 2:
                insights.append("データ不足により傾向分析が限定的です")
            else:
                insights.append("標準的なレース展開が予想されます")
        
        return insights
    
    # ===== JRA版と同じ展開予想用ヘルパーメソッド =====
    
    def _normalize_3f_time(self, value) -> Optional[float]:
        """
        3Fタイムを秒単位に正規化
        実データ分析に基づく正規化ロジック（JRA版と同じ）
        """
        # 欠損値チェック
        if value == 0 or value == 999 or value == 999.0:
            return None
        
        # 100を境界にシンプルに判定
        # 前半3F: 34.3-38.7の範囲（全て100未満、既に秒単位）
        # 後半3F: 338-398の範囲（全て100以上、0.1秒単位×10）
        if value >= 100:
            return value / 10  # 後半3F用: 347.0 → 34.7秒
        else:
            return value  # 前半3F用: そのまま秒単位
    
    def _advanced_pace_prediction(self, horses_data: List[Dict]) -> Dict[str, Any]:
        """
        ペース予測アルゴリズム（JRA版と同じ）
        前半3F・後半3Fのデータを使用（正規化済み）
        """
        zenhan_times = []  # 前半3Fタイム（秒単位）
        kohan_times = []   # 後半3Fタイム（秒単位）
        
        for horse in horses_data:
            if 'races' not in horse:
                continue
            
            # 直近レースの前半3F・後半3Fを収集
            for race in horse['races'][:5]:  # 直近5レース
                # 前半3Fの正規化
                zenhan_raw = race.get('ZENHAN_3F')
                if zenhan_raw is not None:
                    zenhan_normalized = self._normalize_3f_time(float(zenhan_raw))
                    if zenhan_normalized is not None:
                        zenhan_times.append(zenhan_normalized)
                
                # 後半3Fの正規化
                kohan_raw = race.get('KOHAN_3F')
                if kohan_raw is not None:
                    kohan_normalized = self._normalize_3f_time(float(kohan_raw))
                    if kohan_normalized is not None:
                        kohan_times.append(kohan_normalized)
        
        if not zenhan_times:
            return {'pace': 'データ不足', 'confidence': 0, 'zenhan_avg': 0, 'kohan_avg': 0}
        
        # 平均タイムを計算
        zenhan_avg = mean(zenhan_times) if zenhan_times else 0
        kohan_avg = mean(kohan_times) if kohan_times else 0
        
        # ペース判定（JRA版と同じ基準）
        if zenhan_avg < 35.5:
            pace = "ハイペース"
            confidence = 85
        elif zenhan_avg < 36.5:
            pace = "ミドルペース"
            confidence = 75
        else:
            pace = "スローペース"
            confidence = 80
        
        return {
            'pace': pace,
            'confidence': confidence,
            'zenhan_avg': round(zenhan_avg, 1),
            'kohan_avg': round(kohan_avg, 1),
            'sample_size': len(zenhan_times)
        }
    
    def _classify_detailed_styles(self, horses_data: List[Dict]) -> Dict[str, Any]:
        """
        詳細な脚質分類（JRA版と同じ）
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
            
            # 基本脚質の判定（実データから）
            basic_style = self.style_analyzer.classify_basic_style(horse['races'])
            
            # 詳細分類（実データから）
            _, sub_style = self.style_analyzer.classify_detailed_style(basic_style, horse['races'])
            
            if basic_style in detailed_classification:
                if sub_style in detailed_classification[basic_style]:
                    detailed_classification[basic_style][sub_style].append(horse_name)
        
        return detailed_classification
    
    def _calculate_position_stability_all(self, horses_data: List[Dict]) -> Dict[str, float]:
        """位置取り安定性指標を全馬計算（JRA版と同じ）"""
        stability_scores = {}
        
        for horse in horses_data:
            horse_name = horse.get('horse_name', '不明')
            
            if 'races' not in horse:
                stability_scores[horse_name] = 0.0
                continue
            
            corner_positions = []
            for race in horse['races'][:5]:  # 直近5走
                corner1 = safe_int(race.get('CORNER1_JUNI'), 99)
                if corner1 < 99:
                    corner_positions.append(corner1)
            
            if len(corner_positions) > 1:
                # 標準偏差が小さいほど安定
                stability = 1 / (1 + stdev(corner_positions))
            elif len(corner_positions) == 1:
                stability = 0.5
            else:
                stability = 0.0
            
            stability_scores[horse_name] = round(stability, 2)
        
        return stability_scores
    
    def _calculate_flow_matching(self, horses_data: List[Dict], pace_prediction: Dict) -> Dict[str, float]:
        """展開適性マッチング（JRA版と同じ）"""
        flow_scores = {}
        pace = pace_prediction.get('pace', 'ミドルペース')
        
        for horse in horses_data:
            horse_name = horse.get('horse_name', '不明')
            
            if 'races' not in horse:
                flow_scores[horse_name] = 0.5
                continue
            
            basic_style = self.style_analyzer.classify_basic_style(horse['races'])
            
            # ペースと脚質の相性を評価
            if pace == "ハイペース":
                if basic_style in ["差し", "追込"]:
                    flow_scores[horse_name] = 0.8
                elif basic_style == "先行":
                    flow_scores[horse_name] = 0.6
                else:  # 逃げ
                    flow_scores[horse_name] = 0.4
            elif pace == "スローペース":
                if basic_style == "逃げ":
                    flow_scores[horse_name] = 0.8
                elif basic_style == "先行":
                    flow_scores[horse_name] = 0.7
                else:  # 差し、追込
                    flow_scores[horse_name] = 0.5
            else:  # ミドルペース
                flow_scores[horse_name] = 0.6  # 全脚質平等
        
        return flow_scores
    
    def _simulate_race_positions(self, horses_data: List[Dict], pace_prediction: Dict) -> Dict[str, Any]:
        """レース展開シミュレーション（JRA版と同じ）"""
        simulation = {
            'start': [],
            'middle': [],
            'finish': []
        }
        
        # 各馬の予想位置を計算
        for horse in horses_data:
            horse_name = horse.get('horse_name', '不明')
            horse_number = horse.get('horse_number', 0)
            
            if 'races' not in horse:
                continue
            
            basic_style = self.style_analyzer.classify_basic_style(horse['races'])
            
            # スタート位置（脚質による）
            if basic_style == "逃げ":
                position = 1
            elif basic_style == "先行":
                position = 3
            elif basic_style == "差し":
                position = 8
            else:  # 追込
                position = 12
            
            simulation['start'].append({
                'horse_name': horse_name,
                'horse_number': horse_number,
                'position': position,
                'style': basic_style
            })
        
        # スタート位置でソート
        simulation['start'].sort(key=lambda x: x['position'])
        
        # 中間とフィニッシュも同様に計算（簡略化）
        simulation['middle'] = simulation['start'].copy()
        simulation['finish'] = simulation['start'].copy()
        
        return simulation
    
    def _prepare_visualization_data(self, race_simulation: Dict) -> Dict[str, Any]:
        """視覚化用データの準備（JRA版と同じ）"""
        return {
            'position_chart': race_simulation,
            'format': 'position_transition'
        }

# グローバルインスタンス
local_viewlogic_engine_v2 = LocalViewLogicEngineV2()