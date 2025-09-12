"""
フェア値計算エンジン
オッズと各種データから理論的な適正価格を算出
"""

from typing import Dict, List, Optional, Tuple
import math

class FairValueEngine:
    """フェア値計算エンジン"""
    
    def __init__(self):
        self.name = "FairValue"
        self.version = "1.0.0"
        
    def calculate(self, race_data: Dict) -> Dict[str, float]:
        """
        レースデータからフェア値を計算
        
        Args:
            race_data: {
                'horses': [{'name': str, 'odds': float, 'popularity': int, ...}],
                'predictions': {
                    'D-Logic': {...},
                    'I-Logic': {...},
                    'ViewLogic': {...}
                }
            }
        
        Returns:
            {'馬名': フェア値オッズ, ...}
        """
        horses = race_data.get('horses', [])
        predictions = race_data.get('predictions', {})
        
        fair_values = {}
        
        for horse in horses:
            # 1. 基礎確率の計算（人気順位ベース）
            base_prob = self._calculate_base_probability(
                horse['popularity'], 
                len(horses)
            )
            
            # 2. オッズ補正（市場の歪みを考慮）
            market_prob = self._calculate_market_probability(
                horse['odds'],
                horses
            )
            
            # 3. エンジン予想の統合
            engine_prob = self._integrate_engine_predictions(
                horse['name'],
                predictions
            )
            
            # 4. 総合確率の算出（加重平均）
            final_prob = (
                base_prob * 0.3 +      # 基礎確率 30%
                market_prob * 0.4 +    # 市場評価 40%
                engine_prob * 0.3      # AI予想 30%
            )
            
            # 5. フェア値オッズに変換
            if final_prob > 0:
                fair_value = 1.0 / final_prob
                fair_values[horse['name']] = round(fair_value, 1)
            else:
                fair_values[horse['name']] = 999.9
                
        return fair_values
    
    def _calculate_base_probability(self, popularity: int, total_horses: int) -> float:
        """人気順位から基礎確率を計算"""
        if popularity <= 0 or popularity > total_horses:
            return 0.01
            
        # 人気順位に基づく指数的減衰モデル
        # 1番人気を基準(1.0)として、順位が下がるごとに減衰
        decay_rate = 0.85  # 減衰率
        base_score = decay_rate ** (popularity - 1)
        
        # 正規化（確率の合計が1になるように）
        total_score = sum(decay_rate ** i for i in range(total_horses))
        probability = base_score / total_score
        
        return probability
    
    def _calculate_market_probability(self, odds: float, all_horses: List[Dict]) -> float:
        """オッズから市場確率を計算（控除率を考慮）"""
        if odds <= 0:
            return 0.01
            
        # JRA控除率（約25%）を除去
        TAKEOUT_RATE = 0.25
        
        # 全馬のオッズから控除率を逆算
        implied_probs = [1.0 / h['odds'] for h in all_horses if h['odds'] > 0]
        total_implied = sum(implied_probs)
        
        # 実際の控除率を計算
        actual_takeout = 1.0 - (1.0 / total_implied) if total_implied > 0 else TAKEOUT_RATE
        
        # 真の確率を計算
        raw_prob = 1.0 / odds
        adjusted_prob = raw_prob / (1.0 + actual_takeout)
        
        return adjusted_prob
    
    def _integrate_engine_predictions(self, horse_name: str, predictions: Dict) -> float:
        """各エンジンの予想を統合して確率化"""
        scores = []
        
        # 各エンジンから馬のスコアを取得
        for engine_name, engine_data in predictions.items():
            if horse_name in engine_data:
                score = engine_data[horse_name]
                scores.append(score)
        
        if not scores:
            return 0.1  # デフォルト値
            
        # スコアの平均を取得
        avg_score = sum(scores) / len(scores)
        
        # スコアを確率に変換（シグモイド関数）
        # スコア90点 → 約50%、100点 → 約73%
        probability = 1.0 / (1.0 + math.exp(-(avg_score - 90) / 10))
        
        return probability
    
    def calculate_expected_value(self, fair_value: float, actual_odds: float) -> float:
        """
        期待値を計算
        
        Args:
            fair_value: フェア値オッズ
            actual_odds: 実際のオッズ
            
        Returns:
            期待値（%）100を超えれば投資価値あり
        """
        if fair_value <= 0:
            return 0
            
        fair_prob = 1.0 / fair_value
        expected_value = fair_prob * actual_odds * 100
        
        return round(expected_value, 1)
    
    def find_value_bets(self, race_data: Dict, threshold: float = 110.0) -> List[Dict]:
        """
        投資価値のある馬を検出
        
        Args:
            race_data: レースデータ
            threshold: 期待値の閾値（デフォルト110%）
            
        Returns:
            [{'name': '馬名', 'fair_value': X.X, 'odds': Y.Y, 'expected_value': Z.Z}]
        """
        fair_values = self.calculate(race_data)
        value_bets = []
        
        for horse in race_data['horses']:
            name = horse['name']
            if name in fair_values:
                fair_value = fair_values[name]
                actual_odds = horse['odds']
                ev = self.calculate_expected_value(fair_value, actual_odds)
                
                if ev >= threshold:
                    value_bets.append({
                        'name': name,
                        'fair_value': fair_value,
                        'odds': actual_odds,
                        'expected_value': ev,
                        'popularity': horse['popularity']
                    })
        
        # 期待値の高い順にソート
        value_bets.sort(key=lambda x: x['expected_value'], reverse=True)
        
        return value_bets
    
    def format_response(self, race_data: Dict) -> str:
        """チャット用のレスポンスを生成"""
        fair_values = self.calculate(race_data)
        value_bets = self.find_value_bets(race_data)
        
        response = "【フェア値分析結果】\n\n"
        
        # 上位5頭のフェア値を表示
        sorted_horses = sorted(fair_values.items(), key=lambda x: x[1])[:5]
        response += "◆ フェア値ランキング TOP5\n"
        for i, (name, fair_value) in enumerate(sorted_horses, 1):
            # 実際のオッズを取得
            actual_odds = next((h['odds'] for h in race_data['horses'] if h['name'] == name), 0)
            ev = self.calculate_expected_value(fair_value, actual_odds)
            
            response += f"{i}. {name}\n"
            response += f"   フェア値: {fair_value:.1f}倍 / 実オッズ: {actual_odds:.1f}倍\n"
            response += f"   期待値: {ev:.1f}%"
            
            if ev > 110:
                response += " ⭐ 投資価値あり"
            response += "\n\n"
        
        # 投資価値のある馬を強調
        if value_bets:
            response += "\n◆ 推奨投資馬（期待値110%以上）\n"
            for bet in value_bets[:3]:  # 上位3頭まで
                response += f"🎯 {bet['name']} ({bet['popularity']}番人気)\n"
                response += f"   期待値: {bet['expected_value']:.1f}%\n"
                response += f"   フェア値 {bet['fair_value']:.1f}倍 < 実オッズ {bet['odds']:.1f}倍\n\n"
        else:
            response += "\n※ 期待値110%を超える投資価値のある馬は見つかりませんでした。\n"
        
        return response