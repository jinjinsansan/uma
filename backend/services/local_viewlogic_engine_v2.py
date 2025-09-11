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
    
    def get_horse_history(self, horse_name: str, limit: int = 5) -> Dict[str, Any]:
        """
        馬の過去データを取得（地方競馬版）
        JRA版と同じ形式で実装
        
        Args:
            horse_name: 馬名
            limit: 取得するレース数（デフォルト5）
        
        Returns:
            {
                'status': 'success' or 'error',
                'horse_name': str,
                'races': List[Dict],  # 直近limit走のデータ
                'running_style': Dict,  # 脚質情報
                'message': str
            }
        """
        try:
            # 馬データを取得
            horse_data = self.data_manager.get_horse_data(horse_name)
            
            if not horse_data:
                return {
                    'status': 'error',
                    'message': f'{horse_name}のデータベースにデータがありません'
                }
            
            races = horse_data.get('races', [])
            
            # 直近limit走のデータを取得
            recent_races = races[:limit] if len(races) >= limit else races
            
            # 各レースの重要データのみ抽出
            formatted_races = []
            for race in recent_races:
                # レース名の取得（RACE_NAMEフィールドを使用）
                actual_race_name = race.get('RACE_NAME', '').strip() if race.get('RACE_NAME') else ''
                grade_code = race.get('GRADE_CODE', '').strip() if race.get('GRADE_CODE') else ''
                
                # レース名の組み立て（グレードがある場合は追加）
                if actual_race_name:
                    if grade_code and grade_code not in ['', '00', '0']:
                        # グレード表示を追加
                        grade_display = f"【{grade_code}】" if grade_code in ['A', 'B', 'S', 'P'] else f"({grade_code})"
                        race_name = f"{actual_race_name} {grade_display}"
                    else:
                        race_name = actual_race_name
                else:
                    # RACE_NAMEがない場合は従来通りレース番号で表示
                    race_name = f"{race.get('RACE_BANGO', '')}R" if race.get('RACE_BANGO') else '不明'
                
                # 着順の取得（フォーマット付き）
                raw_finish = race.get('KAKUTEI_CHAKUJUN', '')
                # 着順を整数に変換してフォーマット
                try:
                    finish_num = int(raw_finish) if raw_finish and raw_finish != '00' else 0
                    finish_position = f"{finish_num}着" if finish_num > 0 else ''
                except:
                    finish_position = ''
                
                # 競馬場名の取得（track_nameフィールドを使用）
                venue = race.get('track_name', '') or race.get('KEIBAJO_CODE', '')
                
                formatted_race = {
                    # フォーマッターが期待する絵文字付きキーを使用
                    '📅 開催日': f"{race.get('KAISAI_NEN', '')}年{race.get('KAISAI_GAPPI', '')[:2]}月{race.get('KAISAI_GAPPI', '')[2:]}日" if race.get('KAISAI_GAPPI') else '不明',
                    '🏟️ 競馬場': venue if venue else '不明',
                    '🏁 レース': race_name,
                    '📏 距離': f"{race.get('KYORI', 0)}m" if race.get('KYORI') else '不明',
                    '🌤️ 馬場': 'ダート' if race.get('TRACK_CODE') in ['21','22','23','24','25','26','27','28','29'] else '芝',
                    '🥇 着順': finish_position if finish_position else '',
                    '📊 人気': f"{race.get('TANSHO_NINKIJUN', '')}番人気" if race.get('TANSHO_NINKIJUN') else '',
                    '⏱️ タイム': race.get('SOHA_TIME', '') if race.get('SOHA_TIME') else '',
                    '🏃 上り': race.get('KOHAN_3F_TIME', '') if race.get('KOHAN_3F_TIME') else '',
                    '🏇 騎手': race.get('KISHUMEI_RYAKUSHO', '') if race.get('KISHUMEI_RYAKUSHO') else '',
                    # 互換性のため通常のキーも保持
                    'date': f"{race.get('KAISAI_NEN', '')}年{race.get('KAISAI_GAPPI', '')[:2]}月{race.get('KAISAI_GAPPI', '')[2:]}日" if race.get('KAISAI_GAPPI') else '',
                    'venue': venue,
                    'race_name': race_name,
                    'distance': f"{race.get('KYORI', 0)}m",
                    'track_type': 'ダート' if race.get('TRACK_CODE') in ['21','22','23','24','25','26','27','28','29'] else '芝',
                    'finish': finish_position,
                    'horse_count': race.get('TOSU', 0),
                    'horse_number': race.get('UMA_BAN', 0),
                    'jockey': race.get('KISHUMEI_RYAKUSHO', ''),
                    'weight': race.get('FUTAN_JURYO', 0),
                    'odds': float(race.get('TANSHO_ODDS', 0)) / 10 if race.get('TANSHO_ODDS') else 0,
                    'popularity': race.get('TANSHO_NINKIJUN', 0),
                    'corner1': race.get('CORNER1_JUNI', 0),
                    'corner4': race.get('CORNER4_JUNI', 0),
                    'time': f"{race.get('SOHA_TIME', '')[:2]}.{race.get('SOHA_TIME', '')[2:]}" if race.get('SOHA_TIME') else '',
                    # ペース予測で使用するフィールドを追加
                    'ZENHAN_3F': race.get('ZENHAN_3F_TIME'),  # 正しいフィールド名
                    'KOHAN_3F': race.get('KOHAN_3F_TIME'),    # 正しいフィールド名
                    'KYORI': race.get('KYORI'),
                    'KAISAI_NEN': race.get('KAISAI_NEN'),
                    'KAKUTEI_CHAKUJUN': race.get('KAKUTEI_CHAKUJUN')
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
        # get_horse_dataメソッドが存在しない場合、プロキシを追加（最重要）
        if not hasattr(self.data_manager, 'get_horse_data'):
            def get_horse_data_proxy(horse_name):
                """馬データを取得するプロキシメソッド（get_horse_raw_dataを呼び出す）"""
                return self.data_manager.get_horse_raw_data(horse_name)
            self.data_manager.get_horse_data = get_horse_data_proxy
            
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
        horse_numbers = race_data.get('horse_numbers') or []  # Noneの場合は空リスト
        for idx, horse_name in enumerate(horses, 1):
            horse_data = self.data_manager.get_horse_data(horse_name)
            if horse_data:
                horse_data['horse_name'] = horse_name
                # horse_numbersがNoneや空の場合は連番を使用
                if horse_numbers and idx-1 < len(horse_numbers):
                    horse_data['horse_number'] = horse_numbers[idx-1]
                else:
                    horse_data['horse_number'] = idx
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
            logger.info(f"馬コース成績分析結果: {len(horse_course_stats)}件")
            
            # 2. 騎手の枠順別複勝率分析
            jockey_post_stats = []
            jockey_post_stats_dict = {}  # ai_handler.py用の辞書形式
            if jockeys and posts and len(jockeys) == len(posts):
                jockey_post_stats = self._analyze_jockeys_post_performance(jockeys, posts)
                
                # リスト形式から辞書形式に変換（JRA版と同じ形式）
                for stat in jockey_post_stats:
                    if 'jockey_name' in stat:
                        jockey_name = stat['jockey_name']
                        if jockey_name not in jockey_post_stats_dict:
                            jockey_post_stats_dict[jockey_name] = {}
                        
                        # エラーがない場合のみデータを追加
                        if 'place_rate' in stat and 'post_category' in stat:
                            post_category = stat['post_category']
                            jockey_post_stats_dict[jockey_name][post_category] = {
                                'fukusho_rate': stat['place_rate'],
                                'race_count': stat.get('race_count', 0),
                                'post': stat.get('post', 0)
                            }
            
            # 3. 騎手の該当コース成績複勝率分析
            jockey_course_stats = []
            if jockeys:
                jockey_course_stats = self._analyze_jockeys_course_performance(jockeys, venue, distance, track_type)
            
            # フォーマッター向けの結果形式変換
            horse_results = {}
            jockey_results = {}
            
            # 実績があった馬のみhorse_resultsに含める
            for horse_stat in horse_course_stats:
                if horse_stat.get('status') == 'found' and horse_stat.get('total_runs', 0) > 0:
                    horse_name = horse_stat['horse_name']
                    horse_results[horse_name] = {
                        'score': horse_stat.get('place_rate', 0),
                        'fukusho_rate': horse_stat.get('fukusho_rate', 0),
                        'total_runs': horse_stat.get('total_runs', 0),
                        'places': horse_stat.get('places', 0),
                        'status': 'success'
                    }
            
            # 実績があった騎手のみjockey_resultsに含める
            for jockey_stat in jockey_course_stats:
                if jockey_stat.get('status') == 'found' and jockey_stat.get('total_runs', 0) > 0:
                    jockey_name = jockey_stat['jockey_name']
                    jockey_results[jockey_name] = {
                        'score': jockey_stat.get('place_rate', 0),
                        'fukusho_rate': jockey_stat.get('fukusho_rate', 0),
                        'total_runs': jockey_stat.get('total_runs', 0),
                        'places': jockey_stat.get('places', 0),
                        'status': 'success'
                    }
            
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
                # フォーマッターとの互換性のため両方のキーを追加
                'trend_analysis': {
                    'horse_course_stats': horse_course_stats,
                    'jockey_post_stats': jockey_post_stats_dict,  # 辞書形式に変更
                    'jockey_course_stats': jockey_course_stats,
                    'course_trend': {
                        'favorable_style': '先行〜差し',
                        'favorable_post': '内〜中枠'
                    }
                },
                # フォーマッター向けキー（実績がある場合のみ含まれる）
                'horse_results': horse_results,
                'jockey_results': jockey_results,
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
        
        # 競馬場コード変換マップ（地方競馬）
        venue_code_map = {
            '川崎': ['川崎', '43', 43],
            '大井': ['大井', '44', 44],
            '船橋': ['船橋', '45', 45],
            '浦和': ['浦和', '46', 46]
        }
        
        # 比較用の競馬場リストを作成
        venue_variations = venue_code_map.get(venue, [venue])
        
        logger.info(f"🔍 馬コース成績分析開始: {venue}{distance}m{track_type}")
        logger.info(f"   対象馬: {horses}")
        logger.info(f"   競馬場変換: {venue} → {venue_variations}")
        
        for horse_name in horses:
            try:
                horse_data = self.get_horse_data(horse_name)
                logger.info(f"📊 {horse_name}: データ取得{'成功' if horse_data else '失敗'}")
                
                if not horse_data:
                    performances.append({
                        'horse_name': horse_name,
                        'error': 'データベースにデータがありません'
                    })
                    continue
                
                races = horse_data.get('races', [])
                logger.info(f"   レース総数: {len(races)}")
                
                # 該当コースのレースを抽出
                course_races = []
                debug_count = 0
                for race in races:
                    race_venue = race.get('venue', '') or race.get('KEIBAJO_CODE', '') or race.get('競馬場', '')
                    race_distance_str = race.get('distance', '') or str(race.get('KYORI', ''))
                    
                    # 最初の5レースだけデバッグ出力
                    if debug_count < 5:
                        logger.info(f"   レース{debug_count+1}: 競馬場={race_venue} 距離={race_distance_str}")
                        debug_count += 1
                    
                    # 距離を数値に変換
                    try:
                        race_distance = int(race_distance_str.replace('m', '').replace('M', '').strip()) if race_distance_str else 0
                    except (ValueError, AttributeError):
                        race_distance = 0
                    
                    # distanceも整数に変換して比較（文字列の場合に対応）
                    try:
                        distance_int = int(distance) if isinstance(distance, (str, int)) else 0
                    except (ValueError, TypeError):
                        distance_int = 0
                    
                    # 競馬場コードの比較（数字または文字列）
                    venue_match = False
                    if isinstance(race_venue, (int, str)):
                        venue_match = str(race_venue) in [str(v) for v in venue_variations]
                    
                    if venue_match and race_distance == distance_int:
                        course_races.append(race)
                
                logger.info(f"   → {venue}{distance}m該当レース: {len(course_races)}件")
                
                if course_races:
                    # 着順を整数に変換して比較
                    def get_finish_as_int(race):
                        finish = race.get('finish', race.get('KAKUTEI_CHAKUJUN', 99))
                        try:
                            return int(finish) if finish else 99
                        except (ValueError, TypeError):
                            return 99
                    
                    wins = sum(1 for r in course_races if get_finish_as_int(r) == 1)
                    places = sum(1 for r in course_races if get_finish_as_int(r) <= 3)
                    total = len(course_races)
                    
                    performances.append({
                        'horse_name': horse_name,
                        'course_key': f"{venue}{distance}m",
                        'status': 'found',  # フォーマッターが期待するキー
                        'total_runs': total,  # フォーマッターが期待するキー名
                        'total_races': total,  # 互換性のため残す
                        'wins': wins,
                        'places': places,
                        'win_rate': (wins / total * 100) if total > 0 else 0,
                        'place_rate': (places / total * 100) if total > 0 else 0,
                        'fukusho_rate': (places / total * 100) if total > 0 else 0  # フォーマッターが期待するキー
                    })
                else:
                    performances.append({
                        'horse_name': horse_name,
                        'course_key': f"{venue}{distance}m",
                        'status': 'not_found',  # フォーマッターが期待するキー
                        'total_runs': 0,  # フォーマッターが期待するキー名
                        'total_races': 0,  # 互換性のため残す
                        'wins': 0,
                        'places': 0,
                        'win_rate': 0,
                        'place_rate': 0,
                        'fukusho_rate': 0,  # フォーマッターが期待するキー
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
                        
                        # 枠番号のキーを探す（「枠1」〜「枠18」形式）
                        post_key = f'枠{post}'
                        
                        if post_key in post_stats:
                            # 該当枠のデータが存在する場合
                            performances.append({
                                'jockey_name': jockey_name,
                                'post': post,
                                'post_category': f'枠{post}',
                                'place_rate': post_stats[post_key].get('fukusho_rate', 0),
                                'race_count': post_stats[post_key].get('race_count', 0)
                            })
                        else:
                            # カテゴリ別に集計（内枠、中枠、外枠）
                            post_category = '内枠' if post <= 6 else '中枠' if post <= 12 else '外枠'
                            
                            # 該当カテゴリの枠を集計
                            total_races = 0
                            fukusho_count = 0
                            
                            if post_category == '内枠':
                                target_posts = [f'枠{i}' for i in range(1, 7)]
                            elif post_category == '中枠':
                                target_posts = [f'枠{i}' for i in range(7, 13)]
                            else:  # 外枠
                                target_posts = [f'枠{i}' for i in range(13, 19)]
                            
                            for target_post in target_posts:
                                if target_post in post_stats:
                                    stats = post_stats[target_post]
                                    race_count = stats.get('race_count', 0)
                                    fukusho_rate = stats.get('fukusho_rate', 0)
                                    total_races += race_count
                                    fukusho_count += int(race_count * fukusho_rate / 100)
                            
                            if total_races > 0:
                                performances.append({
                                    'jockey_name': jockey_name,
                                    'post': post,
                                    'post_category': post_category,
                                    'place_rate': (fukusho_count / total_races) * 100,
                                    'race_count': total_races
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
        # 騎手データのキー形式に合わせる（例：川崎_1500m）
        course_key = f"{venue}_{distance}m"
        
        logger.info(f"🏇 騎手コース成績分析開始: {venue}{distance}m{track_type}")
        logger.info(f"   対象騎手: {jockeys}")
        logger.info(f"   検索キー: {course_key}")
        
        for jockey_name in jockeys:
            try:
                jockey_data = self.jockey_manager.get_jockey_data(jockey_name)
                logger.info(f"🏇 {jockey_name}: データ取得{'成功' if jockey_data else '失敗'}")
                
                if not jockey_data:
                    performances.append({
                        'jockey_name': jockey_name,
                        'status': 'not_found',  # フォーマッターが期待するキー
                        'total_runs': 0,  # フォーマッターが期待するキー
                        'race_count': 0,
                        'win_rate': 0,
                        'place_rate': 0,
                        'fukusho_rate': 0,  # フォーマッターが期待するキー
                        'error': 'データベースにデータがありません'
                    })
                    continue
                
                # データ構造の確認
                if 'venue_course_stats' in jockey_data:
                    available_keys = list(jockey_data['venue_course_stats'].keys())
                    logger.info(f"   利用可能コース: {available_keys[:5]}")  # 最初の5つのキーのみ表示
                else:
                    logger.info(f"   venue_course_statsキーが存在しません")
                
                # 地方競馬版：venue_course_statsキーを使用
                if 'venue_course_stats' in jockey_data and course_key in jockey_data['venue_course_stats']:
                    course_stat = jockey_data['venue_course_stats'][course_key]
                    # 地方競馬データ形式：resultsとfukusho_rateがある
                    results = course_stat.get('results', [])
                    race_count = course_stat.get('race_count', len(results))
                    fukusho_rate = course_stat.get('fukusho_rate', 0)
                    
                    # 勝利数を計算
                    wins = sum(1 for r in results if r.get('position', 99) == 1)
                    win_rate = (wins / race_count * 100) if race_count > 0 else 0
                    
                    logger.info(f"   → {course_key}実績: {race_count}戦 複勝率{fukusho_rate}%")
                    
                    performances.append({
                        'jockey_name': jockey_name,
                        'course_key': f"{venue}{distance}m",
                        'status': 'found',  # フォーマッターが期待するキー
                        'total_runs': race_count,  # フォーマッターが期待するキー
                        'race_count': race_count,  # 互換性のため残す
                        'wins': wins,
                        'win_rate': win_rate,
                        'place_rate': fukusho_rate,
                        'fukusho_rate': fukusho_rate  # フォーマッターが期待するキー
                    })
                else:
                    logger.info(f"   → {course_key}実績: 0戦 (データなし)")
                    
                    performances.append({
                        'jockey_name': jockey_name,
                        'course_key': f"{venue}{distance}m",
                        'status': 'not_found',  # フォーマッターが期待するキー
                        'total_runs': 0,  # フォーマッターが期待するキー
                        'race_count': 0,
                        'win_rate': 0,
                        'place_rate': 0,
                        'fukusho_rate': 0,  # フォーマッターが期待するキー
                        'message': '該当コースのデータなし'
                    })
                    
            except Exception as e:
                logger.error(f"騎手コース成績分析エラー ({jockey_name}): {e}")
                performances.append({
                    'jockey_name': jockey_name,
                    'error': str(e)
                })
        
        logger.info(f"騎手コース成績分析結果: {len(performances)}件")
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
                zenhan_raw = race.get('ZENHAN_3F_TIME')  # 正しいフィールド名に修正
                if zenhan_raw is not None:
                    zenhan_normalized = self._normalize_3f_time(float(zenhan_raw))
                    if zenhan_normalized is not None:
                        zenhan_times.append(zenhan_normalized)
                
                # 後半3Fの正規化
                kohan_raw = race.get('KOHAN_3F_TIME')  # 正しいフィールド名に修正
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