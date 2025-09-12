"""
F-Logic with built-in D-Logic
D-Logic計算を内蔵した独立動作可能なF-Logicエンジン
"""

import math
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class FLogicWithDLogicEngine:
    """D-Logic計算内蔵版F-Logicエンジン"""
    
    def __init__(self):
        self.name = "F-Logic"
        self.version = "2.0.0"
        self.description = "D-Logic内蔵型フェア値分析エンジン"
        
        # D-Logic基準値（簡易版）
        self.dlogic_base_scores = {
            # 有力馬の特徴パターン
            'top_class': 95,      # G1馬、重賞勝ち馬
            'high_class': 85,     # オープン、3勝クラス
            'mid_class': 75,      # 2勝クラス
            'low_class': 65,      # 1勝クラス
            'maiden': 55,         # 未勝利
            'debut': 50           # 新馬
        }
    
    def analyze(self, race_data: Dict) -> Dict:
        """
        F-Logic分析（D-Logic計算を内蔵）
        
        Args:
            race_data: {
                'horses': ['馬名1', '馬名2', ...],
                'odds': [3.5, 8.2, ...],
                'popularities': [1, 3, ...],
                'jockeys': ['騎手1', '騎手2', ...],
                'trainers': ['調教師1', '調教師2', ...],
                'horse_info': [  # オプション：馬の追加情報
                    {'class': 'high', 'wins': 3, ...},
                    ...
                ]
            }
        """
        try:
            horses = race_data.get('horses', [])
            odds = race_data.get('odds', [])
            popularities = race_data.get('popularities', [])
            jockeys = race_data.get('jockeys', [])
            trainers = race_data.get('trainers', [])
            horse_info = race_data.get('horse_info', [])
            
            if not horses or not odds:
                logger.warning("F-Logic: データ不足")
                return self._empty_result()
            
            # 1. 内蔵D-Logic計算で基礎能力スコアを算出
            dlogic_scores = self._calculate_dlogic_scores(
                horses, jockeys, trainers, horse_info
            )
            
            # 2. フェア値を計算（D-Logicスコア統合）
            fair_values = {}
            expected_values = {}
            scores = {}
            
            for i, horse in enumerate(horses):
                if i >= len(odds):
                    continue
                
                # 各確率要素を計算
                # a. 人気順位ベース確率（20%）
                pop = popularities[i] if i < len(popularities) else i + 1
                base_prob = self._calc_base_probability(pop, len(horses))
                
                # b. オッズベース市場確率（40%）
                market_prob = self._calc_market_probability(odds[i], odds)
                
                # c. D-Logic能力確率（40%） ← ここがポイント！
                dlogic_prob = self._calc_dlogic_probability(
                    dlogic_scores.get(horse, 50), 
                    dlogic_scores
                )
                
                # 統合確率（加重平均）
                final_prob = (
                    base_prob * 0.20 +      # 人気 20%
                    market_prob * 0.40 +    # オッズ 40%
                    dlogic_prob * 0.40      # D-Logic 40%
                )
                
                # フェア値オッズ
                if final_prob > 0.001:
                    fair_value = 1.0 / final_prob
                    fair_values[horse] = round(fair_value, 1)
                    
                    # 期待値
                    ev = (1.0 / fair_value) * odds[i] * 100
                    expected_values[horse] = round(ev, 1)
                    
                    # F-Logicスコア（期待値ベース）
                    score = min(100, max(0, 50 + (ev - 100) * 0.5))
                    scores[horse] = round(score, 1)
                else:
                    fair_values[horse] = 999.9
                    expected_values[horse] = 0
                    scores[horse] = 30.0
            
            # ランキング作成
            rankings = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            # 投資価値馬の検出
            value_bets = self._find_value_bets(
                horses, odds, fair_values, expected_values, popularities
            )
            
            return {
                'scores': scores,
                'rankings': rankings[:5],
                'fair_values': fair_values,
                'expected_values': expected_values,
                'value_bets': value_bets,
                'dlogic_scores': dlogic_scores  # 内部D-Logicスコアも返す
            }
            
        except Exception as e:
            logger.error(f"F-Logic分析エラー: {e}")
            return self._empty_result()
    
    def _calculate_dlogic_scores(self, horses: List[str], jockeys: List[str], 
                                 trainers: List[str], horse_info: List[Dict]) -> Dict[str, float]:
        """
        簡易D-Logic計算（馬名ベースの基礎能力評価）
        実際のD-Logicより簡略化されているが、高速で実用的
        """
        scores = {}
        
        for i, horse in enumerate(horses):
            base_score = 65.0  # デフォルトスコア
            
            # 馬名から推定（簡易版）
            # 実際はデータベースから過去成績を取得すべきだが、ここでは簡略化
            if any(keyword in horse for keyword in ['ディープ', 'オルフェ', 'キズナ']):
                base_score += 10  # 良血馬ボーナス
            
            # 騎手補正
            if i < len(jockeys):
                jockey = jockeys[i]
                if any(name in jockey for name in ['ルメール', 'デムーロ', 'クリストフ']):
                    base_score += 8
                elif any(name in jockey for name in ['川田', '福永', '松山']):
                    base_score += 5
            
            # 調教師補正
            if i < len(trainers):
                trainer = trainers[i]
                if any(name in trainer for name in ['藤沢', '音無', '友道']):
                    base_score += 5
            
            # 追加情報があれば活用
            if i < len(horse_info) and horse_info[i]:
                info = horse_info[i]
                # クラス補正
                if info.get('class') == 'G1':
                    base_score = max(base_score, 90)
                elif info.get('class') == 'G2':
                    base_score = max(base_score, 85)
                elif info.get('class') == 'G3':
                    base_score = max(base_score, 80)
                
                # 勝利数補正
                wins = info.get('wins', 0)
                base_score += min(wins * 2, 10)
            
            # スコアを正規化（0-100）
            scores[horse] = min(100, max(0, base_score))
        
        return scores
    
    def _calc_dlogic_probability(self, score: float, all_scores: Dict[str, float]) -> float:
        """D-Logicスコアから確率を計算"""
        if not all_scores:
            return 0.1
        
        # スコアを指数変換（高スコアほど確率が高くなる）
        exp_score = math.exp(score / 20)  # 20で割って調整
        
        # 全馬の指数合計
        total_exp = sum(math.exp(s / 20) for s in all_scores.values())
        
        # 確率化
        if total_exp > 0:
            probability = exp_score / total_exp
        else:
            probability = 1.0 / len(all_scores)
        
        return min(0.8, max(0.01, probability))
    
    def _calc_base_probability(self, popularity: int, total: int) -> float:
        """人気順位から基礎確率を計算"""
        if popularity <= 0 or popularity > total:
            return 0.01
        
        decay_rate = 0.80
        score = decay_rate ** (popularity - 1)
        total_score = sum(decay_rate ** i for i in range(total))
        
        return score / total_score if total_score > 0 else 0.01
    
    def _calc_market_probability(self, odds: float, all_odds: List[float]) -> float:
        """オッズから市場確率を計算"""
        if odds <= 0:
            return 0.01
        
        # 控除率推定
        implied_total = sum(1.0 / o for o in all_odds if o > 0)
        takeout = max(0, 1 - (1.0 / implied_total)) if implied_total > 0 else 0.25
        
        # 控除率除去
        raw_prob = 1.0 / odds
        adjusted_prob = raw_prob / (1 + takeout)
        
        return min(0.8, max(0.01, adjusted_prob))
    
    def _find_value_bets(self, horses: List[str], odds: List[float], 
                        fair_values: Dict[str, float], expected_values: Dict[str, float],
                        popularities: List[int]) -> List[Dict]:
        """投資価値のある馬を検出"""
        value_bets = []
        
        for i, horse in enumerate(horses):
            if i < len(odds) and horse in expected_values:
                ev = expected_values[horse]
                
                if ev >= 110:  # 期待値110%以上
                    value_bets.append({
                        'horse': horse,
                        'fair_value': fair_values[horse],
                        'actual_odds': odds[i],
                        'expected_value': ev,
                        'popularity': popularities[i] if i < len(popularities) else i + 1
                    })
        
        value_bets.sort(key=lambda x: x['expected_value'], reverse=True)
        return value_bets[:3]
    
    def _empty_result(self) -> Dict:
        """空の結果"""
        return {
            'scores': {},
            'rankings': [],
            'fair_values': {},
            'expected_values': {},
            'value_bets': [],
            'dlogic_scores': {}
        }
    
    def format_response(self, result: Dict) -> str:
        """チャット用レスポンス生成"""
        response = "【F-Logic フェア値分析】\n"
        response += "（D-Logic能力評価統合版）\n\n"
        
        rankings = result.get('rankings', [])
        value_bets = result.get('value_bets', [])
        dlogic_scores = result.get('dlogic_scores', {})
        
        if rankings:
            response += "◆ F-Logic TOP5\n"
            for i, (horse, score) in enumerate(rankings[:5], 1):
                ev = result['expected_values'].get(horse, 0)
                fv = result['fair_values'].get(horse, 0)
                dl = dlogic_scores.get(horse, 0)
                
                response += f"{i}. {horse} (F-Logic: {score:.1f}点)\n"
                response += f"   D-Logic能力: {dl:.0f}点 / フェア値: {fv:.1f}倍\n"
                response += f"   期待値: {ev:.1f}%"
                
                if ev >= 120:
                    response += " 🔥 激アツ"
                elif ev >= 110:
                    response += " ⭐ 投資価値あり"
                response += "\n\n"
        
        if value_bets:
            response += "\n◆ 投資推奨馬（期待値110%以上）\n"
            for bet in value_bets:
                response += f"🎯 {bet['horse']} ({bet['popularity']}番人気)\n"
                response += f"   期待値: {bet['expected_value']:.1f}%\n"
                response += f"   フェア値 {bet['fair_value']:.1f}倍 < 実オッズ {bet['actual_odds']:.1f}倍\n"
                response += "   → 市場が過小評価している可能性大\n\n"
        else:
            response += "\n※ 現在のオッズに投資価値のある馬は見つかりませんでした。\n"
        
        response += "\n💡 F-Logicは内蔵D-Logic能力評価とオッズ分析を統合した投資判断エンジンです。"
        
        return response