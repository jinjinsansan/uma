#!/usr/bin/env python3
"""地方競馬版F-Logic（Fair Value Logic）エンジン V2"""

import logging
import math
from datetime import datetime
from typing import Dict, Any, Optional

from .local_race_analysis_engine_v2 import local_race_analysis_engine_v2

logger = logging.getLogger(__name__)


class LocalFLogicEngineV2:
    """地方競馬版F-Logicエンジン（公正価値計算）"""

    def __init__(self):
        self._race_engine = local_race_analysis_engine_v2
        logger.info("🏇 地方競馬版F-LogicエンジンV2初期化")

    @staticmethod
    def _filter_valid_scores(results: list) -> Dict[str, float]:
        """LocalRaceAnalysisEngineの結果から有効なI-Logicスコアを抽出"""
        scores: Dict[str, float] = {}
        if not isinstance(results, list):
            return scores

        for item in results:
            if not isinstance(item, dict):
                continue

            horse_name = item.get('horse') or item.get('horse_name')
            total_score = item.get('total_score')
            has_data = item.get('has_data', True)

            if not horse_name:
                continue

            if has_data and total_score is not None:
                try:
                    scores[horse_name] = float(total_score)
                except (TypeError, ValueError):
                    logger.debug("F-Logic: 無効なスコア値 %s (%s)", total_score, horse_name)

        return scores

    def calculate_ilogic_scores(self, race_data: Dict[str, Any]) -> Dict[str, float]:
        """地方版I-Logicスコアを取得"""
        analysis_result = self._race_engine.analyze_race(race_data)

        if analysis_result.get('status') != 'success':
            logger.warning("F-Logic: I-Logic結果を取得できませんでした (%s)", analysis_result.get('error'))
            return {}

        return self._filter_valid_scores(analysis_result.get('results', []))

    @staticmethod
    def calculate_fair_odds(ilogic_scores: Dict[str, float]) -> Dict[str, float]:
        """I-Logicスコアからフェア値（理論オッズ）を計算"""
        if not ilogic_scores:
            return {}

        temperature = 10.0  # ソフトマックス温度パラメータ
        exp_scores: Dict[str, float] = {}

        for horse, score in ilogic_scores.items():
            try:
                exp_scores[horse] = math.exp(float(score) / temperature)
            except (TypeError, ValueError, OverflowError):
                exp_scores[horse] = 0.0

        total_exp = sum(exp_scores.values())
        if total_exp <= 0:
            return {}

        payout_rate = 0.80  # 地方競馬の控除率をJRA相当で仮置き
        fair_odds: Dict[str, float] = {}

        for horse, exp_value in exp_scores.items():
            probability = exp_value / total_exp if total_exp else 0.0
            if probability > 0:
                odds = payout_rate / probability
                fair_odds[horse] = round(odds, 1)
            else:
                fair_odds[horse] = 999.9

        return fair_odds

    @staticmethod
    def calculate_expected_value(
        fair_odds: Dict[str, float],
        market_odds: Dict[str, float]
    ) -> Dict[str, Dict[str, Any]]:
        """市場オッズとの比較による期待値計算"""
        results: Dict[str, Dict[str, Any]] = {}
        payout_rate = 0.80

        for horse, fair in fair_odds.items():
            market = market_odds.get(horse)
            if market is None or market <= 0:
                continue

            fair = fair or 0.0
            if fair <= 0:
                continue

            win_probability = payout_rate / fair
            expected_value = (market * win_probability) - 1 if win_probability > 0 else -1

            kelly_fraction = 0.0
            if market > 1 and win_probability > 0:
                b = market - 1
                p = win_probability
                q = 1 - p
                numerator = (p * b) - q
                if numerator > 0:
                    kelly_fraction = min((numerator / b) * 0.25, 0.10)

            odds_divergence = (market / fair) if fair > 0 else 0.0
            if odds_divergence >= 2.0:
                value_rating = 'excellent'
                investment_signal = '強い買い'
            elif odds_divergence >= 1.5:
                value_rating = 'good'
                investment_signal = '買い'
            elif odds_divergence >= 1.2:
                value_rating = 'fair'
                investment_signal = 'やや買い'
            elif odds_divergence >= 1.0:
                value_rating = 'neutral'
                investment_signal = '中立'
            else:
                value_rating = 'poor'
                investment_signal = '見送り'

            results[horse] = {
                'fair_odds': round(fair, 1),
                'market_odds': round(market, 1),
                'win_probability': round(win_probability, 4),
                'expected_value': round(expected_value, 3),
                'value_rating': value_rating,
                'investment_signal': investment_signal,
                'kelly_criterion': round(kelly_fraction, 4),
                'roi_estimate': round(expected_value * 100, 1),
                'odds_divergence': round(odds_divergence, 2)
            }

        return results

    def analyze_race(
        self,
        race_data: Dict[str, Any],
        market_odds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """F-Logic分析メイン処理"""
        ilogic_scores = self.calculate_ilogic_scores(race_data)
        if not ilogic_scores:
            return {
                'status': 'error',
                'message': '地方I-Logicスコアを取得できませんでした'
            }

        fair_odds = self.calculate_fair_odds(ilogic_scores)
        expected_values: Dict[str, Dict[str, Any]] = {}

        if market_odds:
            expected_values = self.calculate_expected_value(fair_odds, market_odds)

        rankings = []
        for horse, score in sorted(ilogic_scores.items(), key=lambda item: item[1], reverse=True):
            entry = {
                'horse': horse,
                'ilogic_score': round(score, 2),
                'fair_odds': fair_odds.get(horse, 0)
            }

            if horse in expected_values:
                entry.update(expected_values[horse])

            rankings.append(entry)

        return {
            'status': 'success',
            'type': 'flogic',
            'race_info': {
                'venue': race_data.get('venue'),
                'race_number': race_data.get('race_number'),
                'race_name': race_data.get('race_name'),
                'horses_count': len(race_data.get('horses', []))
            },
            'rankings': rankings,
            'has_market_odds': bool(market_odds),
            'analyzed_at': datetime.now().isoformat()
        }


# グローバルインスタンス
local_flogic_engine_v2 = LocalFLogicEngineV2()
