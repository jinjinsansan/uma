#!/usr/bin/env python3
"""地方競馬版MetaLogic（メタ予想）エンジン V2"""

import logging
from datetime import datetime
from typing import Dict, Any, List

from .local_race_analysis_engine_v2 import local_race_analysis_engine_v2
from .local_viewlogic_engine_v2 import local_viewlogic_engine_v2
from .local_fast_dlogic_engine_v2 import local_fast_dlogic_engine_v2

logger = logging.getLogger(__name__)


class LocalMetaLogicEngineV2:
    """地方競馬版MetaLogicエンジン"""

    def __init__(self):
        self.engine_weight = 0.75
        self.odds_weight = 0.25
        self.dlogic_weight = 0.3
        self.ilogic_weight = 0.4
        self.viewlogic_weight = 0.3
        logger.info("🏇 地方競馬版MetaLogicエンジンV2初期化: D/I/View = 30/40/30")

    def _prepare_context(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'venue': race_data.get('venue', ''),
            'distance': race_data.get('distance', ''),
            'track_type': race_data.get('track_type', 'ダート'),
            'track_condition': race_data.get('track_condition', '良')
        }

    def _calculate_dlogic_scores(self, horses: List[str]) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        manager = local_fast_dlogic_engine_v2.raw_manager
        for horse in horses:
            score_data = manager.calculate_dlogic_realtime(horse)
            if score_data and score_data.get('data_available') and not score_data.get('error'):
                scores[horse] = round(score_data.get('total_score', 0.0), 1)
        return scores

    def _calculate_ilogic_scores(self, race_data: Dict[str, Any]) -> Dict[str, float]:
        analysis_result = local_race_analysis_engine_v2.analyze_race(race_data)
        if analysis_result.get('status') != 'success':
            return {}

        scores: Dict[str, float] = {}
        for item in analysis_result.get('results', []):
            if not isinstance(item, dict):
                continue
            horse = item.get('horse') or item.get('horse_name')
            total_score = item.get('total_score')
            if horse and total_score is not None and item.get('has_data'):
                scores[horse] = round(float(total_score), 1)
        return scores

    def _calculate_viewlogic_scores(self, race_data: Dict[str, Any]) -> Dict[str, float]:
        try:
            local_result = local_viewlogic_engine_v2.predict_race_flow_advanced(race_data)
            scores: Dict[str, float] = {}
            flow_matching = local_result.get('flow_matching', {}) if isinstance(local_result, dict) else {}
            for horse, score in flow_matching.items():
                try:
                    if score is not None:
                        scores[horse] = round(float(score), 1)
                except (TypeError, ValueError):
                    continue
            return scores
        except Exception as exc:
            logger.error("MetaLogic: ViewLogicスコア計算エラー (%s)", exc)
            return {}

    @staticmethod
    def _calculate_odds_factor(odds: float) -> float:
        if odds is None or odds <= 0:
            return 0.0
        return 100 / (1 + odds)

    def _calculate_meta_scores(
        self,
        horses: List[str],
        dlogic_scores: Dict[str, float],
        ilogic_scores: Dict[str, float],
        viewlogic_scores: Dict[str, float],
        odds: List[float]
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        for index, horse in enumerate(horses):
            d_score = dlogic_scores.get(horse)
            i_score = ilogic_scores.get(horse)
            v_score = viewlogic_scores.get(horse)

            scores = []
            weights = []

            if d_score is not None:
                scores.append(d_score)
                weights.append(self.dlogic_weight)
            if i_score is not None:
                scores.append(i_score)
                weights.append(self.ilogic_weight)
            if v_score is not None:
                scores.append(v_score)
                weights.append(self.viewlogic_weight)

            if not scores:
                continue

            total_weight = sum(weights)
            engine_avg = sum(score * weight for score, weight in zip(scores, weights)) / total_weight if total_weight > 0 else 0.0

            horse_odds = odds[index] if index < len(odds) else None
            odds_factor = self._calculate_odds_factor(horse_odds)

            meta_score = (engine_avg * self.engine_weight) + (odds_factor * self.odds_weight)

            results.append({
                'horse': horse,
                'meta_score': round(meta_score, 1),
                'details': {
                    'd_logic': d_score or 0.0,
                    'i_logic': i_score or 0.0,
                    'view_logic': v_score or 0.0,
                    'engine_avg': round(engine_avg, 1),
                    'odds': horse_odds or 0.0,
                    'odds_factor': round(odds_factor, 1),
                    'engine_count': len(scores)
                }
            })

        results.sort(key=lambda item: item['meta_score'], reverse=True)
        for idx, item in enumerate(results, 1):
            item['rank'] = idx
        return results[:5]

    def analyze_race(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        horses = race_data.get('horses', [])
        if not horses:
            return {'status': 'error', 'message': '馬データがありません'}

        context = self._prepare_context(race_data)

        logger.info("MetaLogic(local): D-Logic計算開始")
        d_scores = self._calculate_dlogic_scores(horses)

        logger.info("MetaLogic(local): I-Logic計算開始")
        i_scores = self._calculate_ilogic_scores({**race_data, **context})

        logger.info("MetaLogic(local): ViewLogic計算開始")
        v_scores = self._calculate_viewlogic_scores({**race_data, **context})

        logger.info("MetaLogic(local): メタスコア計算開始")
        rankings = self._calculate_meta_scores(
            horses,
            d_scores,
            i_scores,
            v_scores,
            race_data.get('odds', [])
        )

        return {
            'status': 'success',
            'type': 'metalogic',
            'rankings': rankings,
            'analyzed_at': datetime.now().isoformat()
        }


local_metalogic_engine_v2 = LocalMetaLogicEngineV2()
