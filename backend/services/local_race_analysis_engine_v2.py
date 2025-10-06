#!/usr/bin/env python3
"""
地方競馬版I-Logic（レース分析）エンジン V2
JRA版と完全に同じロジックで実装
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from .local_fast_dlogic_engine_v2 import LocalFastDLogicEngineV2
from .local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
from .local_jockey_data_manager import local_jockey_manager

logger = logging.getLogger(__name__)

class LocalRaceAnalysisEngineV2:
    """地方競馬版I-Logic（レース分析）エンジン V2 - JRA版と同一実装"""
    
    # 馬と騎手の重み付け（JRA版と同じ）
    HORSE_WEIGHT = 0.7    # 70%
    JOCKEY_WEIGHT = 0.3   # 30%
    
    def __init__(self):
        """初期化：地方競馬版V2エンジンを使用"""
        # 地方競馬版V2エンジンを使用
        self.dlogic_engine = LocalFastDLogicEngineV2()
        
        # 地方競馬版マネージャー
        self.raw_manager = local_dlogic_manager_v2
        self.jockey_manager = local_jockey_manager
        
        # modern_engineも同じ参照（互換性のため）
        self.modern_engine = self.dlogic_engine
        
        # 基準馬（イクイノックス）
        self.baseline_horse = "イクイノックス"
        
        logger.info(f"🏇 地方競馬版I-Logic分析エンジンV2初期化完了")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """エンジン情報を返す"""
        if hasattr(self.raw_manager, 'get_total_horses'):
            horse_count = self.raw_manager.get_total_horses()
        else:
            horses = getattr(self.raw_manager, 'knowledge_data', {}).get('horses', {})
            horse_count = len(horses) if isinstance(horses, dict) else 0

        return {
            "engine_type": "LocalRaceAnalysisEngineV2",
            "venue": "南関東4場",
            "baseline_horse": self.baseline_horse,
            "knowledge_horses": horse_count,
            "manager_type": "V2"
        }
    
    def analyze_race(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レース全体を分析（JRA版と同じ実装）
        
        Args:
            race_data: レース情報
        
        Returns:
            分析結果
        """
        try:
            # 入力検証
            if not self._validate_race_data(race_data):
                return {
                    'error': 'レースデータが不正です',
                    'analysis_type': 'race_analysis_v2'
                }
            
            # レース情報の準備
            context = {
                'venue': race_data.get('venue', ''),
                'grade': race_data.get('grade', ''),
                'distance': race_data.get('distance', ''),
                'track_condition': race_data.get('track_condition', '良')
            }
            
            # デフォルトの12項目重み付け（JRA版と同じ）
            default_item_weights = {
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
                '12_time_index': 8.37  # 合計100になるよう調整
            }
            
            # 各馬の分析
            results = []
            horses = race_data.get('horses', [])
            jockeys = race_data.get('jockeys', [])
            posts = race_data.get('posts') or []  # Noneの場合は空リスト
            horse_numbers = race_data.get('horse_numbers') or []  # Noneの場合は空リスト
            
            for i in range(len(horses)):
                try:
                    horse_name = horses[i]
                    jockey_name = jockeys[i] if jockeys and i < len(jockeys) else ''
                    post = posts[i] if posts and i < len(posts) else i + 1
                    horse_number = horse_numbers[i] if horse_numbers and i < len(horse_numbers) else i + 1
                    
                    # 馬のスコアを計算（12項目重み付け）
                    horse_score, has_data, horse_details = self._calculate_horse_score_with_weights(
                        horse_name=horse_name,
                        context=context,
                        item_weights=default_item_weights
                    )
                    
                    # 騎手の評価
                    jockey_context = {
                        'venue': context['venue'],
                        'post': post,
                        'sire': horse_details.get('sire')
                    }
                    jockey_score, jockey_breakdown = self._calculate_jockey_score(
                        jockey_name,
                        jockey_context
                    )
                    
                    # 総合評価（馬70%、騎手30%）
                    if not has_data:
                        # データなしの馬は0点（JRA版と同様）
                        total_score = 0
                        logger.info(f"{horse_name}: データなしのため0点")
                    else:
                        total_score = (
                            horse_score * self.HORSE_WEIGHT +
                            jockey_score * self.JOCKEY_WEIGHT
                        )
                    
                    estimation_method = horse_details.get('estimation_method', 'local_unknown')
                    data_status = horse_details.get('data_status', 'full_data' if has_data else 'no_data')

                    results.append({
                        'rank': 0,  # 後でソート
                        'horse_number': horse_number,
                        'post': post,
                        'horse': horse_name,
                        'jockey': jockey_name,
                        'total_score': round(total_score, 1),
                        'horse_score': round(horse_score, 1),
                        'jockey_score': round(jockey_score, 1),
                        'has_data': has_data,
                        'estimation_method': estimation_method,
                        'horse_details': horse_details,
                        'jockey_details': {
                            'venue': round(jockey_breakdown.get('venue_score', 0.0), 1),
                            'post': round(jockey_breakdown.get('post_score', 0.0), 1),
                            'sire': round(jockey_breakdown.get('sire_score', 0.0), 1)
                        },
                        'data_status': data_status
                    })
                    
                except Exception as e:
                    logger.error(f"馬の分析エラー（{horses[i]}）: {e}")
                    results.append({
                        'rank': 999,
                        'horse_number': horse_numbers[i] if horse_numbers and i < len(horse_numbers) else i + 1,
                        'post': posts[i] if posts and i < len(posts) else i + 1,
                        'horse': horses[i],
                        'jockey': jockeys[i] if jockeys and i < len(jockeys) else '',
                        'total_score': -1,
                        'horse_score': -1,
                        'jockey_score': 0,
                        'has_data': False,
                        'estimation_method': 'local_error',
                        'horse_details': {
                            'has_knowledge_data': False,
                            'data_status': 'error',
                            'venue_distance_bonus': 0.0,
                            'track_bonus': 0.0,
                            'class_factor': 1.0,
                            'venue_history': {'wins': 0, 'total': 0, 'place_rate': 0.0, 'average_finish': None},
                            'distance_history': {'total': 0, 'average_finish': None},
                            'recent_form': {'finishes': [], 'average_finish': None},
                            'd_logic_scores': {},
                            'd_logic_total': 0.0,
                            'sire': None
                        },
                        'jockey_details': {
                            'venue': 0.0,
                            'post': 0.0,
                            'sire': 0.0
                        },
                        'data_status': 'error',
                        'error': str(e)
                    })
            
            # データがある馬のみでソート（-1を除外）
            valid_results = [r for r in results if r['has_data']]
            invalid_results = [r for r in results if not r['has_data']]
            
            # スコア順にソート
            valid_results.sort(key=lambda x: x['total_score'], reverse=True)
            
            # 順位付け
            for i, result in enumerate(valid_results):
                result['rank'] = i + 1
            
            # データなしの馬を最後に追加
            for result in invalid_results:
                result['rank'] = len(valid_results) + 1
            
            # 全結果を結合
            all_results = valid_results + invalid_results
            
            # 分析サマリーの作成
            summary = self._create_analysis_summary(all_results, context)
            
            return {
                'race_info': {
                    'venue': race_data.get('venue', ''),
                    'race_number': race_data.get('race_number', ''),
                    'race_name': race_data.get('race_name', ''),
                    'grade': race_data.get('grade', ''),
                    'distance': race_data.get('distance', ''),
                    'track_condition': race_data.get('track_condition', '良')
                },
                'results': all_results,
                'summary': summary,
                'analysis_type': 'race_analysis_v2',
                'base_horse': 'イクイノックス基準（12項目均等重み）',
                'weights': {
                    'horse': self.HORSE_WEIGHT,
                    'jockey': self.JOCKEY_WEIGHT
                },
                'item_weights': default_item_weights,
                'status': 'success',
                'scores': all_results,
                'top_horses': [r['horse'] for r in valid_results[:5]]
            }
            
        except Exception as e:
            logger.error(f"レース分析エラー: {e}")
            return {
                'error': f'分析中にエラーが発生しました: {str(e)}',
                'analysis_type': 'race_analysis_v2',
                'status': 'error'
            }
    
    def _validate_race_data(self, race_data: Dict[str, Any]) -> bool:
        """レースデータの検証（JRA版と同じ）"""
        required_fields = ['horses']
        for field in required_fields:
            if field not in race_data or not race_data[field]:
                logger.warning(f"必須フィールドが不足: {field}")
                return False
        
        # 馬と騎手の数が一致しているか
        horses = race_data.get('horses', [])
        jockeys = race_data.get('jockeys', [])
        if jockeys and len(horses) != len(jockeys):
            logger.warning(f"馬と騎手の数が不一致: 馬{len(horses)}頭、騎手{len(jockeys)}人")
            return False
        
        return True
    
    def _parse_distance_value(self, distance: Any) -> Optional[int]:
        """距離表現を整数(m)に変換"""
        if distance is None:
            return None
        if isinstance(distance, (int, float)):
            return int(distance)
        if isinstance(distance, str):
            digits = ''.join(ch for ch in distance if ch.isdigit())
            if digits:
                try:
                    return int(digits)
                except ValueError:
                    return None
        return None

    def _compute_context_stats(
        self,
        horse_name: str,
        raw_data: Dict[str, Any],
        score_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """開催場・距離に基づく追加統計を算出"""
        races: List[Dict[str, Any]] = raw_data.get('races') or raw_data.get('race_history') or []
        venue = context.get('venue', '')
        distance_value = self._parse_distance_value(context.get('distance'))

        venue_finishes: List[int] = []
        venue_distance_finishes: List[int] = []
        distance_finishes: List[int] = []
        recent_finishes: List[int] = []
        all_finishes: List[int] = []

        wins_at_venue = 0
        place_at_venue = 0

        sire = raw_data.get('sire')
        if not sire and races:
            sire = races[0].get('sire')

        for idx, race in enumerate(races):
            finish_raw = race.get('KAKUTEI_CHAKUJUN') or race.get('finish')
            try:
                finish = int(finish_raw)
            except (TypeError, ValueError):
                continue

            track_name = race.get('track_name') or race.get('venue') or ''
            race_distance = race.get('KYORI') or race.get('distance')
            try:
                race_distance_val = int(race_distance)
            except (TypeError, ValueError):
                race_distance_val = None

            same_venue = bool(venue) and track_name == venue
            same_distance = distance_value is None or (
                race_distance_val is not None and abs(race_distance_val - distance_value) <= 100
            )

            if same_venue:
                venue_finishes.append(finish)
                if finish == 1:
                    wins_at_venue += 1
                if finish <= 3:
                    place_at_venue += 1

            if same_distance:
                distance_finishes.append(finish)

            if same_venue and same_distance:
                venue_distance_finishes.append(finish)

            if idx < 5:
                recent_finishes.append(finish)

            all_finishes.append(finish)

        def _calc_bonus(finishes: List[int]) -> float:
            if not finishes:
                return 0.0
            avg_finish = sum(finishes) / len(finishes)
            bonus = max(0.0, (3.5 - avg_finish) * 5.0)
            return round(min(15.0, bonus), 1)

        venue_distance_bonus = _calc_bonus(venue_distance_finishes)

        track_score = score_data.get('d_logic_scores', {}).get('5_track_aptitude')
        if track_score is None:
            track_score = score_data.get('total_score', 50.0)
        track_bonus = round((track_score - 50.0) * 0.2, 1)

        overall_finishes = venue_finishes or distance_finishes
        if not overall_finishes:
            overall_finishes = all_finishes
        if overall_finishes:
            avg_finish = sum(overall_finishes) / len(overall_finishes)
            class_factor = 1.0 + max(-0.3, min(0.3, (3.0 - avg_finish) * 0.05))
        else:
            class_factor = 1.0
        class_factor = max(0.85, min(1.15, class_factor))

        race_count = raw_data.get('race_count') or len(races)
        if race_count >= 8:
            estimation_method = 'local_full'
            data_status = 'full_data'
        elif race_count >= 3:
            estimation_method = 'local_bayesian'
            data_status = 'bayesian'
        elif race_count > 0:
            estimation_method = 'local_sparse'
            data_status = 'partial_data'
        else:
            estimation_method = 'local_default'
            data_status = 'no_data'

        venue_history = {
            'wins': wins_at_venue,
            'total': len(venue_finishes),
            'place_rate': round((place_at_venue / len(venue_finishes)) * 100, 1) if venue_finishes else 0.0,
            'average_finish': round(sum(venue_finishes) / len(venue_finishes), 2) if venue_finishes else None
        }

        distance_history = {
            'total': len(distance_finishes),
            'average_finish': round(sum(distance_finishes) / len(distance_finishes), 2) if distance_finishes else None
        }

        recent_form = {
            'finishes': recent_finishes,
            'average_finish': round(sum(recent_finishes) / len(recent_finishes), 2) if recent_finishes else None
        }

        return {
            'has_knowledge_data': bool(score_data.get('data_available', True)),
            'data_status': data_status,
            'estimation_method': estimation_method,
            'venue_distance_bonus': venue_distance_bonus,
            'track_bonus': track_bonus,
            'class_factor': round(class_factor, 3),
            'venue_history': venue_history,
            'distance_history': distance_history,
            'recent_form': recent_form,
            'race_count': race_count,
            'sire': sire
        }

    def _calculate_horse_score_with_weights(
        self,
        horse_name: str,
        context: Dict[str, Any],
        item_weights: Dict[str, float]
    ) -> Tuple[float, bool, Dict[str, Any]]:
        """馬のスコアを12項目重み付けで計算し、補助情報を添えて返す"""
        try:
            score_data = self.raw_manager.calculate_dlogic_realtime(horse_name)

            if score_data.get('error') or not score_data.get('data_available'):
                details = {
                    'has_knowledge_data': False,
                    'data_status': 'no_data',
                    'estimation_method': 'local_default',
                    'venue_distance_bonus': 0.0,
                    'track_bonus': 0.0,
                    'class_factor': 1.0,
                    'venue_history': {'wins': 0, 'total': 0, 'place_rate': 0.0, 'average_finish': None},
                    'distance_history': {'total': 0, 'average_finish': None},
                    'recent_form': {'finishes': [], 'average_finish': None},
                    'd_logic_scores': {},
                    'd_logic_total': 0.0,
                    'sire': None
                }
                return 0.0, False, details

            raw_data = self.raw_manager.get_horse_raw_data(horse_name) or {}
            context_stats = self._compute_context_stats(horse_name, raw_data, score_data, context)

            item_scores = score_data.get('d_logic_scores', {})
            weighted_sum = 0.0
            weight_sum = 0.0

            for item_key, weight in item_weights.items():
                score = item_scores.get(item_key)
                if score is None:
                    score = score_data.get('total_score', 50.0)
                weighted_sum += score * weight
                weight_sum += weight

            if weight_sum > 0:
                base_score = weighted_sum / weight_sum
            else:
                base_score = score_data.get('total_score', 50.0)

            final_score = base_score + context_stats['venue_distance_bonus'] + context_stats['track_bonus']
            final_score *= context_stats['class_factor']

            # 騎手指標も保存（互換用）
            context_stats['d_logic_total'] = score_data.get('total_score', base_score)
            context_stats['d_logic_scores'] = score_data.get('d_logic_scores', {})

            return float(round(final_score, 1)), True, context_stats

        except Exception as e:
            logger.error(f"馬スコア計算エラー（{horse_name}）: {e}")
            details = {
                'has_knowledge_data': False,
                'data_status': 'error',
                'estimation_method': 'local_error',
                'venue_distance_bonus': 0.0,
                'track_bonus': 0.0,
                'class_factor': 1.0,
                'venue_history': {'wins': 0, 'total': 0, 'place_rate': 0.0, 'average_finish': None},
                'distance_history': {'total': 0, 'average_finish': None},
                'recent_form': {'finishes': [], 'average_finish': None},
                'd_logic_scores': {},
                'd_logic_total': 0.0,
                'sire': None
            }
            return 0.0, False, details
    
    def _calculate_jockey_score(self, jockey_name: str, context: Dict[str, Any]) -> Tuple[float, Dict[str, float]]:
        """騎手スコアと内訳を計算"""
        try:
            if not jockey_name:
                return 0.0, {'venue_score': 0.0, 'post_score': 0.0, 'sire_score': 0.0}

            jockey_analysis = self.jockey_manager.calculate_jockey_score(
                jockey_name,
                context
            )

            jockey_score = max(-10, min(10, jockey_analysis.get('total_score', 0.0)))

            return jockey_score, {
                'venue_score': jockey_analysis.get('venue_score', 0.0),
                'post_score': jockey_analysis.get('post_score', 0.0),
                'sire_score': jockey_analysis.get('sire_score', 0.0)
            }

        except Exception as e:
            logger.error(f"騎手スコア計算エラー（{jockey_name}）: {e}")
            return 0.0, {'venue_score': 0.0, 'post_score': 0.0, 'sire_score': 0.0}
    
    def _create_analysis_summary(self, results: List[Dict], context: Dict) -> Dict[str, Any]:
        """分析サマリーを作成（JRA版と同じ）"""
        try:
            valid_results = [r for r in results if r.get('has_data')]
            
            if not valid_results:
                return {
                    'top_3': [],
                    'data_quality': 'データなし',
                    'confidence': 0
                }
            
            return {
                'top_3': [r['horse'] for r in valid_results[:3]],
                'data_quality': '完全' if len(valid_results) == len(results) else '部分的',
                'confidence': min(95, 50 + len(valid_results) * 5),
                'total_horses': len(results),
                'analyzed_horses': len(valid_results)
            }
            
        except Exception as e:
            logger.error(f"サマリー作成エラー: {e}")
            return {
                'top_3': [],
                'data_quality': 'エラー',
                'confidence': 0
            }

# グローバルインスタンス
local_race_analysis_engine_v2 = LocalRaceAnalysisEngineV2()