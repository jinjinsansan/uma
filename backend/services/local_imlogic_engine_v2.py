#!/usr/bin/env python3
"""
地方競馬版IMLogic統合エンジン V2
JRA版と同じ構造の分析結果を生成
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from .local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
from .local_jockey_data_manager import local_jockey_manager
from .local_fast_dlogic_engine_v2 import LocalFastDLogicEngineV2
from .local_race_analysis_engine_v2 import LocalRaceAnalysisEngineV2

logger = logging.getLogger(__name__)

class LocalIMLogicEngineV2:
    """地方競馬版IMLogic統合エンジン V2 - JRA版と同一実装"""
    
    # デフォルトの重み（JRA版と同じ）
    DEFAULT_HORSE_WEIGHT = 70    # 70%
    DEFAULT_JOCKEY_WEIGHT = 30   # 30%
    
    def __init__(self):
        """初期化：地方競馬版V2マネージャーとエンジンを使用"""
        # 地方競馬版マネージャーを設定
        self.dlogic_manager = local_dlogic_manager_v2
        self.jockey_manager = local_jockey_manager
        
        # 地方競馬版エンジンを設定
        self.dlogic_engine = LocalFastDLogicEngineV2()
        self.ilogic_engine = LocalRaceAnalysisEngineV2()
        
        # 現在のAIモード
        self.current_ai_mode = "IMLogic"
        
        # 初期化完了メッセージ
        horse_count = len(self.dlogic_manager.knowledge_data.get('horses', {}))
        jockey_count = len(self.jockey_manager.knowledge_data.get('jockeys', {}))
        logger.info(f"🏇 地方競馬版IMLogic統合エンジンV2初期化完了")
        logger.info(f"   馬データ: {horse_count}頭, 騎手データ: {jockey_count}騎手")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """エンジン情報を返す"""
        return {
            "engine_type": "LocalIMLogicEngineV2",
            "venue": "南関東4場",
            "current_ai_mode": self.current_ai_mode,
            "knowledge_horses": len(self.dlogic_manager.knowledge_data.get('horses', {})),
            "knowledge_jockeys": len(self.jockey_manager.knowledge_data.get('jockeys', {})),
            "manager_type": "V2"
        }
    
    def switch_ai_mode(self, mode: str) -> bool:
        """AIモード切り替え"""
        valid_modes = ["D-Logic", "I-Logic", "IMLogic", "ViewLogic"]
        if mode in valid_modes:
            self.current_ai_mode = mode
            logger.info(f"🔄 地方競馬版AIモード切替: {mode}")
            return True
        return False
    
    def analyze_race(
        self,
        race_data: Dict[str, Any],
        horse_weight: int = None,
        jockey_weight: int = None,
        item_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """地方競馬版のIMLogic分析を実行し、JRA版と同じ構造の結果を返す"""

        # デフォルト重み
        horse_weight = float(self.DEFAULT_HORSE_WEIGHT if horse_weight is None else horse_weight)
        jockey_weight = float(self.DEFAULT_JOCKEY_WEIGHT if jockey_weight is None else jockey_weight)

        total_weight = horse_weight + jockey_weight
        if total_weight <= 0:
            horse_weight = float(self.DEFAULT_HORSE_WEIGHT)
            jockey_weight = float(self.DEFAULT_JOCKEY_WEIGHT)
            total_weight = horse_weight + jockey_weight

        if abs(total_weight - 100.0) > 1e-6:
            horse_ratio = horse_weight / total_weight
            jockey_ratio = jockey_weight / total_weight
            horse_weight = round(horse_ratio * 100.0, 2)
            jockey_weight = round(jockey_ratio * 100.0, 2)

        normalized_item_weights = self._normalize_item_weights(item_weights)

        if not self.ilogic_engine._validate_race_data(race_data):
            return {
                'status': 'error',
                'message': 'レースデータが不正です',
                'analysis_type': 'imlogic'
            }

        context = {
            'venue': race_data.get('venue', ''),
            'grade': race_data.get('grade', ''),
            'distance': race_data.get('distance', ''),
            'track_condition': race_data.get('track_condition', '良')
        }

        horses = race_data.get('horses', []) or []
        jockeys = race_data.get('jockeys', []) or []
        posts = race_data.get('posts', []) or []
        horse_numbers = race_data.get('horse_numbers') or []

        results: List[Dict[str, Any]] = []

        for idx, horse_name in enumerate(horses):
            try:
                jockey_name = jockeys[idx] if idx < len(jockeys) else ''
                post = posts[idx] if idx < len(posts) else idx + 1
                horse_number = horse_numbers[idx] if idx < len(horse_numbers) else idx + 1

                horse_score, has_data, horse_details = self.ilogic_engine._calculate_horse_score_with_weights(
                    horse_name=horse_name,
                    context=context,
                    item_weights=normalized_item_weights
                )

                jockey_score, jockey_breakdown = self.ilogic_engine._calculate_jockey_score(
                    jockey_name,
                    {
                        'venue': context['venue'],
                        'post': post,
                        'sire': horse_details.get('sire')
                    }
                )

                if not has_data:
                    results.append({
                        'rank': 0,
                        'horse_number': horse_number,
                        'post': post,
                        'horse': horse_name,
                        'jockey': jockey_name,
                        'total_score': None,
                        'horse_score': None,
                        'jockey_score': None,
                        'horse_weight_pct': horse_weight,
                        'jockey_weight_pct': jockey_weight,
                        'data_status': 'no_data'
                    })
                    continue

                total_score = round(
                    horse_score * (horse_weight / 100.0) +
                    jockey_score * (jockey_weight / 100.0),
                    1
                )

                results.append({
                    'rank': 0,
                    'horse_number': horse_number,
                    'post': post,
                    'horse': horse_name,
                    'jockey': jockey_name,
                    'total_score': total_score,
                    'horse_score': round(horse_score, 1),
                    'jockey_score': round(jockey_score, 1),
                    'horse_weight_pct': horse_weight,
                    'jockey_weight_pct': jockey_weight,
                    'data_status': 'ok'
                })

            except Exception as exc:
                logger.error(f"IMLogic地方版分析エラー ({horse_name}): {exc}")
                results.append({
                    'rank': 0,
                    'horse_number': horse_numbers[idx] if idx < len(horse_numbers) else idx + 1,
                    'post': posts[idx] if idx < len(posts) else idx + 1,
                    'horse': horse_name,
                    'jockey': jockeys[idx] if idx < len(jockeys) else '',
                    'total_score': None,
                    'horse_score': None,
                    'jockey_score': None,
                    'horse_weight_pct': horse_weight,
                    'jockey_weight_pct': jockey_weight,
                    'data_status': 'no_data'
                })

        valid_results = [r for r in results if r['total_score'] is not None]
        invalid_results = [r for r in results if r['total_score'] is None]

        valid_results.sort(key=lambda x: x['total_score'], reverse=True)

        for pos, result in enumerate(valid_results, start=1):
            result['rank'] = pos

        for offset, result in enumerate(invalid_results, start=1):
            result['rank'] = len(valid_results) + offset

        ordered_results = valid_results + invalid_results

        response = {
            'status': 'success',
            'type': 'imlogic',
            'analysis_type': 'imlogic',
            'mode': 'IMLogic',
            'race_info': {
                'venue': race_data.get('venue', ''),
                'race_number': race_data.get('race_number', ''),
                'race_name': race_data.get('race_name', ''),
                'grade': race_data.get('grade', ''),
                'distance': race_data.get('distance', ''),
                'track_condition': race_data.get('track_condition', '良'),
                'horses_count': len(horses)
            },
            'settings': {
                'horse_weight': horse_weight,
                'jockey_weight': jockey_weight,
                'item_weights': normalized_item_weights
            },
            'results': ordered_results,
            'scores': ordered_results,
            'analyzed_at': datetime.now().isoformat()
        }

        return response
    
    def _normalize_item_weights(self, raw_weights: Optional[Dict[str, float]]) -> Dict[str, float]:
        """番号付き12項目の重みを正規化して返す"""
        default_weights = {
            '1_distance_aptitude': 8.33,
            '2_bloodline_evaluation': 8.33,
            '3_jockey_compatibility': 8.33,
            '4_trainer_evaluation': 8.33,
            '5_track_aptitude': 8.33,
            '6_weather_aptitude': 8.33,
            '7_popularity_factor': 8.33,
            '8_weight_impact': 8.33,
            '9_horse_weight_impact': 8.33,
            '10_corner_specialist': 8.33,
            '11_margin_analysis': 8.33,
            '12_time_index': 8.37
        }

        if not raw_weights:
            return default_weights.copy()

        numbered_keys = set(default_weights.keys())
        contains_numbered = any(key in numbered_keys for key in raw_weights.keys())

        weights: Dict[str, float] = {}

        if contains_numbered:
            for key, default_value in default_weights.items():
                try:
                    weights[key] = float(raw_weights.get(key, default_value))
                except (TypeError, ValueError):
                    weights[key] = default_value
        else:
            plain_mapping = {
                '1_distance_aptitude': 'distance_aptitude',
                '2_bloodline_evaluation': 'bloodline_evaluation',
                '3_jockey_compatibility': 'jockey_compatibility',
                '4_trainer_evaluation': 'trainer_evaluation',
                '5_track_aptitude': 'track_aptitude',
                '6_weather_aptitude': 'weather_aptitude',
                '7_popularity_factor': 'popularity_factor',
                '8_weight_impact': 'weight_impact',
                '9_horse_weight_impact': 'horse_weight_impact',
                '10_corner_specialist': 'corner_specialist',
                '11_margin_analysis': 'margin_analysis',
                '12_time_index': 'time_index'
            }

            for numbered_key, plain_key in plain_mapping.items():
                try:
                    weights[numbered_key] = float(raw_weights.get(plain_key, default_weights[numbered_key]))
                except (TypeError, ValueError):
                    weights[numbered_key] = default_weights[numbered_key]

        total = sum(weights.values())
        if total <= 0:
            return default_weights.copy()

        if abs(total - 100.0) > 1e-6:
            scale = 100.0 / total
            for key in weights:
                weights[key] = round(weights[key] * scale, 2)

        return weights

    def analyze_for_chat(
        self, 
        horses: List[str], 
        race_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        チャット用分析（JRA版と同じ実装）
        """
        logger.info(f"📊 {self.current_ai_mode}モードで{len(horses)}頭を分析")
        
        # レース情報の準備
        if race_info is None:
            race_info = {}
        
        race_data = {
            'horses': horses,
            'jockeys': race_info.get('jockeys', []),
            'venue': race_info.get('venue', '川崎'),
            'race_name': race_info.get('race_name', 'レース'),
            'race_number': race_info.get('race_number', 1),
            'grade': race_info.get('grade', ''),
            'distance': race_info.get('distance', ''),
            'track_condition': race_info.get('track_condition', '良')
        }
        
        if self.current_ai_mode == "D-Logic":
            # D-Logic分析（12項目の詳細分析）
            results = []
            for horse in horses:
                score_data = self.dlogic_manager.calculate_dlogic_realtime(horse)
                if not score_data.get('error') and score_data.get('data_available'):
                    results.append({
                        'name': horse,
                        'total_score': score_data.get('total_score', 0),
                        'grade': score_data.get('grade', 'N/A'),
                        'd_logic_scores': score_data.get('d_logic_scores', {})
                    })
                else:
                    results.append({
                        'name': horse,
                        'total_score': -1,  # データなしマーカー
                        'grade': 'データなし',
                        'error': score_data.get('error', 'データが見つかりません')
                    })
            
            # スコア順にソート（-1を除く）
            valid_results = [r for r in results if r['total_score'] >= 0]
            invalid_results = [r for r in results if r['total_score'] < 0]
            valid_results.sort(key=lambda x: x['total_score'], reverse=True)
            
            return {
                'mode': 'D-Logic',
                'rankings': valid_results + invalid_results,
                'response': f"D-Logic（12項目評価）で{len(horses)}頭を分析しました",
                'analysis_type': 'd_logic',
                'total_horses': len(horses),
                'analyzed_horses': len(valid_results)
            }
        
        elif self.current_ai_mode == "I-Logic":
            # I-Logic分析（レース全体分析）
            result = self.ilogic_engine.analyze_race(race_data)
            
            if result.get('status') == 'success':
                return {
                    'mode': 'I-Logic',
                    'rankings': result.get('results', []),
                    'response': f"I-Logic（馬70%・騎手30%）で{len(horses)}頭を分析しました",
                    'analysis_type': 'i_logic',
                    'race_info': result.get('race_info', {}),
                    'summary': result.get('summary', {}),
                    'weights': result.get('weights', {})
                }
            else:
                return {
                    'mode': 'I-Logic',
                    'rankings': [],
                    'response': f"分析エラー: {result.get('error', '不明なエラー')}",
                    'analysis_type': 'i_logic',
                    'error': result.get('error')
                }
        
        else:
            # IMLogic（統合分析）
            result = self.analyze_race(race_data)
            
            if result.get('status') == 'success':
                return {
                    'mode': 'IMLogic',
                    'rankings': result.get('rankings', []),
                    'response': f"IMLogic（統合分析）で{len(horses)}頭を分析しました",
                    'analysis_type': 'imlogic',
                    'race_info': result.get('race_info', {}),
                    'summary': result.get('summary', {}),
                    'weights': {
                        'horse': result.get('horse_weight', 70),
                        'jockey': result.get('jockey_weight', 30)
                    },
                    'item_weights': result.get('item_weights', {})
                }
            else:
                return {
                    'mode': 'IMLogic',
                    'rankings': [],
                    'response': f"分析エラー: {result.get('error', '不明なエラー')}",
                    'analysis_type': 'imlogic',
                    'error': result.get('error')
                }
    
    def calculate_custom_weights(
        self,
        race_data: Dict[str, Any],
        custom_weights: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        カスタム重み付けで分析（JRA版と同じ）
        
        Args:
            race_data: レース情報
            custom_weights: {
                'horse': 馬の重み（0-100）,
                'jockey': 騎手の重み（0-100）,
                'items': 12項目の個別重み（オプション）
            }
        """
        horse_weight = custom_weights.get('horse', self.DEFAULT_HORSE_WEIGHT)
        jockey_weight = custom_weights.get('jockey', self.DEFAULT_JOCKEY_WEIGHT)
        item_weights = custom_weights.get('items', None)
        
        return self.analyze_race(
            race_data=race_data,
            horse_weight=horse_weight,
            jockey_weight=jockey_weight,
            item_weights=item_weights
        )
    
    def get_analysis_details(self, horse_name: str) -> Dict[str, Any]:
        """
        特定の馬の詳細分析情報を取得（JRA版と同じ）
        """
        # D-Logic詳細スコア
        dlogic_data = self.dlogic_manager.calculate_dlogic_realtime(horse_name)
        
        # 騎手データ（もしあれば）
        jockey_data = {}
        
        return {
            'horse_name': horse_name,
            'dlogic': {
                'total_score': dlogic_data.get('total_score', 0),
                'grade': dlogic_data.get('grade', 'N/A'),
                'scores': dlogic_data.get('d_logic_scores', {}),
                'data_available': dlogic_data.get('data_available', False)
            },
            'jockey': jockey_data,
            'analysis_type': 'detailed'
        }

# グローバルインスタンス
local_imlogic_engine_v2 = LocalIMLogicEngineV2()