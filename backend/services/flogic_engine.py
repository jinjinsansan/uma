"""
F-Logic（Fair Value Logic）エンジン
I-Logicの計算式を組み込んだ公正価値計算システム
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import math

logger = logging.getLogger(__name__)

class FLogicEngine:
    """F-Logic計算エンジン（公正価値計算）"""
    
    def __init__(self):
        """初期化"""
        # I-Logicエンジンを内部で使用
        self._modern_engine = None
        # 騎手データマネージャー
        self._jockey_manager = None
        # 騎手名正規化関数
        self._normalize_jockey_name = None
        
        logger.info("F-Logicエンジンを初期化しました")
    
    @property
    def modern_engine(self):
        """ModernDLogicEngineの遅延初期化（I-Logic計算用）"""
        if self._modern_engine is None:
            from services.fast_dlogic_engine import fast_engine_instance
            from services.modern_dlogic_engine import ModernDLogicEngine
            self._modern_engine = ModernDLogicEngine(fast_engine_instance)
            logger.info("I-Logic計算エンジンを初期化しました")
        return self._modern_engine
    
    @property
    def jockey_manager(self):
        """騎手データマネージャーの遅延初期化"""
        if self._jockey_manager is None:
            from services.jockey_data_manager import jockey_manager
            self._jockey_manager = jockey_manager
            logger.info("騎手データマネージャーを初期化しました")
        return self._jockey_manager
    
    @property
    def normalize_jockey_name(self):
        """騎手名正規化関数の遅延初期化"""
        if self._normalize_jockey_name is None:
            from services.jockey_name_mapper import normalize_jockey_name
            self._normalize_jockey_name = normalize_jockey_name
        return self._normalize_jockey_name
    
    def calculate_ilogic_scores(
        self,
        race_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        I-Logic計算を実行して各馬のスコアを取得
        
        Args:
            race_data: レースデータ（馬、騎手、開催場等）
        
        Returns:
            馬名 -> I-Logicスコアのマッピング
        """
        try:
            # レース情報の準備
            context = {
                'venue': race_data.get('venue', ''),
                'grade': self._extract_grade(race_data.get('race_name', '')),
                'distance': race_data.get('distance', ''),
                'track_condition': race_data.get('track_condition', '良')
            }
            
            # 各馬のI-Logicスコアを計算
            ilogic_scores = {}
            horses = race_data.get('horses', [])
            jockeys = race_data.get('jockeys', [])
            posts = race_data.get('posts', [])
            
            for i in range(len(horses)):
                horse_name = horses[i]
                raw_jockey_name = jockeys[i] if i < len(jockeys) else ''
                jockey_name = self.normalize_jockey_name(raw_jockey_name)
                post = posts[i] if i < len(posts) else 1
                
                # 馬の評価（I-Logicベース）
                horse_result = self.modern_engine.calculate_horse_score(
                    horse_name=horse_name,
                    context=context,
                    enable_bayesian=True
                )
                
                # データがない馬はスキップ
                if horse_result.get('estimation_method') == 'default' and \
                   horse_result.get('data_confidence') == 'none':
                    logger.info(f"{horse_name}: ナレッジデータなし")
                    continue
                
                # 基本スコア（イクイノックス基準）
                base_score = horse_result.get('base_score', 50.0)
                venue_bonus = horse_result.get('venue_distance_bonus', 0)
                track_bonus = horse_result.get('track_bonus', 0)
                class_factor = horse_result.get('class_factor', 1.0)
                
                # 馬のスコア（70%）
                horse_score = (base_score + venue_bonus + track_bonus) * class_factor
                
                # 騎手の評価（30%）
                jockey_context = {
                    'venue': context['venue'],
                    'post': post,
                    'sire': None
                }
                jockey_analysis = self.jockey_manager.calculate_jockey_score(
                    jockey_name,
                    jockey_context
                )
                jockey_score = jockey_analysis.get('total_score', 0)
                
                # I-Logic総合評価（馬70% + 騎手30%）
                total_score = (horse_score * 0.7) + (jockey_score * 0.3)
                ilogic_scores[horse_name] = round(total_score, 2)
            
            return ilogic_scores
            
        except Exception as e:
            logger.error(f"I-Logicスコア計算エラー: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def calculate_fair_odds(
        self,
        ilogic_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        I-Logicスコアから公正オッズを計算
        
        Args:
            ilogic_scores: 馬名 -> I-Logicスコアのマッピング
        
        Returns:
            馬名 -> 公正オッズのマッピング
        """
        if not ilogic_scores:
            return {}
        
        try:
            # スコアを勝率に変換（ソフトマックス関数使用）
            # 温度パラメータで調整（低いほど差が大きくなる）
            temperature = 10.0
            
            # スコアの指数を計算
            exp_scores = {}
            for horse, score in ilogic_scores.items():
                exp_scores[horse] = math.exp(score / temperature)
            
            # 合計
            total_exp = sum(exp_scores.values())
            
            # 勝率計算
            win_probabilities = {}
            for horse, exp_score in exp_scores.items():
                win_probabilities[horse] = exp_score / total_exp
            
            # オッズ計算（控除率を考慮: JRAは約20%）
            payout_rate = 0.80  # 払戻率80%
            fair_odds = {}
            for horse, prob in win_probabilities.items():
                if prob > 0:
                    # オッズ = (払戻率 / 勝率)
                    odds = payout_rate / prob
                    fair_odds[horse] = round(odds, 1)
                else:
                    fair_odds[horse] = 999.9  # 最大オッズ
            
            return fair_odds
            
        except Exception as e:
            logger.error(f"公正オッズ計算エラー: {e}")
            return {}
    
    def calculate_expected_value(
        self,
        fair_odds: Dict[str, float],
        market_odds: Dict[str, float]
    ) -> Dict[str, Dict[str, Any]]:
        """
        期待値を計算して投資価値を判定（最適化版）
        
        Args:
            fair_odds: 公正オッズ（F-Logic計算値）
            market_odds: 市場オッズ（実際のオッズ）
        
        Returns:
            馬名 -> {
                'fair_odds': 公正オッズ,
                'market_odds': 市場オッズ,
                'win_probability': 勝率,
                'expected_value': 期待値,
                'value_rating': 価値評価,
                'kelly_criterion': ケリー基準での推奨賭け率,
                'roi_estimate': 推定ROI
            }
        """
        results = {}
        
        # 控除率を考慮した実効払戻率
        payout_rate = 0.80  # JRA控除率約20%
        
        for horse in fair_odds:
            if horse not in market_odds:
                continue
            
            fair = fair_odds[horse]
            market = market_odds[horse]
            
            # 勝率計算（公正オッズから逆算）
            win_probability = payout_rate / fair if fair > 0 else 0
            
            # 期待値 = (市場オッズ × 勝率) - 1
            # 1より大きければプラス期待値
            if win_probability > 0:
                expected_value = (market * win_probability) - 1
            else:
                expected_value = -1
            
            # ケリー基準での最適賭け率計算
            # f = (p × b - q) / b
            # p: 勝率, b: オッズ-1, q: 敗率(1-p)
            kelly_fraction = 0
            if market > 1 and win_probability > 0:
                b = market - 1
                p = win_probability
                q = 1 - p
                kelly_numerator = (p * b) - q
                if kelly_numerator > 0:
                    kelly_fraction = kelly_numerator / b
                    # 安全マージン（1/4ケリー）
                    kelly_fraction = min(kelly_fraction * 0.25, 0.10)  # 最大10%
            
            # 推定ROI計算
            roi_estimate = expected_value * 100  # パーセント表示
            
            # オッズ乖離率（市場オッズ ÷ フェア値）
            # 1より大きい = 割安（買い）
            # 1より小さい = 割高（見送り）
            odds_divergence = (market / fair) if fair > 0 else 0
            
            # 価値評価（オッズ乖離率ベース）
            if odds_divergence >= 2.0:
                value_rating = 'excellent'  # フェア値の2倍以上 = 非常に割安
                investment_signal = '強い買い'
            elif odds_divergence >= 1.5:
                value_rating = 'good'       # フェア値の1.5倍以上 = 割安
                investment_signal = '買い'
            elif odds_divergence >= 1.2:
                value_rating = 'fair'       # フェア値の1.2倍以上 = やや割安
                investment_signal = 'やや買い'
            elif odds_divergence >= 1.0:
                value_rating = 'neutral'    # フェア値とほぼ同じ
                investment_signal = '中立'
            else:
                value_rating = 'poor'       # フェア値より低い = 割高
                investment_signal = '見送り'
            
            results[horse] = {
                'fair_odds': fair,
                'market_odds': market,
                'win_probability': round(win_probability, 4),
                'expected_value': round(expected_value, 3),
                'value_rating': value_rating,
                'investment_signal': investment_signal,
                'kelly_criterion': round(kelly_fraction, 4),
                'roi_estimate': round(roi_estimate, 1),
                'odds_divergence': round(odds_divergence, 2)
            }
        
        return results
    
    def analyze_race(
        self,
        race_data: Dict[str, Any],
        market_odds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        レース全体のF-Logic分析を実行
        
        Args:
            race_data: レースデータ
            market_odds: 市場オッズ（オプション）
        
        Returns:
            F-Logic分析結果
        """
        try:
            # Step 1: I-Logicスコア計算
            logger.info("Step 1: I-Logicスコアを計算中...")
            ilogic_scores = self.calculate_ilogic_scores(race_data)
            
            if not ilogic_scores:
                return {
                    'status': 'error',
                    'message': 'I-Logicスコアの計算に失敗しました'
                }
            
            # Step 2: 公正オッズ計算
            logger.info("Step 2: 公正オッズを計算中...")
            fair_odds = self.calculate_fair_odds(ilogic_scores)
            
            # Step 3: 期待値計算（市場オッズがある場合）
            expected_values = {}
            if market_odds:
                logger.info("Step 3: 期待値を計算中...")
                expected_values = self.calculate_expected_value(fair_odds, market_odds)
            
            # 結果をランキング形式で整理
            rankings = []
            for horse, score in sorted(ilogic_scores.items(), key=lambda x: x[1], reverse=True):
                ranking_data = {
                    'horse': horse,
                    'ilogic_score': score,
                    'fair_odds': fair_odds.get(horse, 0)
                }
                
                # 期待値情報があれば追加
                if horse in expected_values:
                    ranking_data.update(expected_values[horse])
                
                rankings.append(ranking_data)
            
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
                'has_market_odds': market_odds is not None,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"F-Logic分析エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'分析中にエラーが発生しました: {str(e)}'
            }
    
    def _extract_grade(self, race_name: str) -> str:
        """レース名からグレードを抽出"""
        if 'G1' in race_name or 'GⅠ' in race_name:
            return 'G1'
        elif 'G2' in race_name or 'GⅡ' in race_name:
            return 'G2'
        elif 'G3' in race_name or 'GⅢ' in race_name:
            return 'G3'
        elif 'オープン' in race_name or 'OP' in race_name:
            return 'オープン'
        elif 'リステッド' in race_name or 'L' in race_name:
            return 'L'
        elif '3勝' in race_name:
            return '3勝'
        elif '2勝' in race_name:
            return '2勝'
        elif '1勝' in race_name:
            return '1勝'
        elif '未勝利' in race_name:
            return '未勝利'
        elif '新馬' in race_name:
            return '新馬'
        else:
            return ''

# グローバルインスタンス
flogic_engine = FLogicEngine()