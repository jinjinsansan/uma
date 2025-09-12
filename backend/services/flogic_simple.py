"""
簡易版F-Logic（Simple F-Logic）
他エンジンに依存せず、オッズと人気データのみで高速計算
サーバー負荷を最小限に抑えた実装
"""

import math
from typing import Dict, List, Optional

class SimpleFLogicEngine:
    """簡易版F-Logicエンジン（独立動作版）"""
    
    def __init__(self):
        self.name = "F-Logic (Simple)"
        self.version = "1.0.0"
        self.description = "オッズベースの高速フェア値分析"
    
    def analyze(self, race_data: Dict) -> Dict:
        """
        オッズと人気のみでフェア値を計算（他エンジン不要）
        
        Args:
            race_data: {
                'horses': ['馬名1', '馬名2', ...],
                'odds': [3.5, 8.2, ...],
                'popularities': [1, 3, ...]
            }
        """
        horses = race_data.get('horses', [])
        odds = race_data.get('odds', [])
        popularities = race_data.get('popularities', [])
        
        if not horses or not odds:
            return self._empty_result()
        
        fair_values = {}
        expected_values = {}
        scores = {}
        
        for i, horse in enumerate(horses):
            if i >= len(odds):
                continue
                
            # 1. 人気順位から基礎確率（40%）
            pop = popularities[i] if i < len(popularities) else i + 1
            base_prob = self._calc_base_probability(pop, len(horses))
            
            # 2. オッズから市場確率（60%）
            market_prob = self._calc_market_probability(odds[i], odds)
            
            # 3. 統合確率（エンジン予想なし版）
            final_prob = base_prob * 0.4 + market_prob * 0.6
            
            # 4. フェア値計算
            if final_prob > 0.001:
                fair_value = 1.0 / final_prob
                fair_values[horse] = round(fair_value, 1)
                
                # 5. 期待値計算
                ev = (1.0 / fair_value) * odds[i] * 100
                expected_values[horse] = round(ev, 1)
                
                # 6. スコア化（期待値ベース）
                # 期待値100% = 50点、150% = 75点
                score = min(100, max(0, 50 + (ev - 100) * 0.5))
                scores[horse] = round(score, 1)
            else:
                fair_values[horse] = 999.9
                expected_values[horse] = 0
                scores[horse] = 30.0
        
        # ランキング作成
        rankings = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # 投資価値馬の検出
        value_bets = []
        for i, horse in enumerate(horses):
            if i < len(odds) and horse in expected_values:
                ev = expected_values[horse]
                if ev >= 110:
                    value_bets.append({
                        'horse': horse,
                        'fair_value': fair_values[horse],
                        'actual_odds': odds[i],
                        'expected_value': ev,
                        'popularity': popularities[i] if i < len(popularities) else i + 1
                    })
        
        value_bets.sort(key=lambda x: x['expected_value'], reverse=True)
        
        return {
            'scores': scores,
            'rankings': rankings[:5],
            'fair_values': fair_values,
            'expected_values': expected_values,
            'value_bets': value_bets[:3]
        }
    
    def _calc_base_probability(self, popularity: int, total: int) -> float:
        """人気順位から基礎確率を計算"""
        if popularity <= 0 or popularity > total:
            return 0.01
        
        # より急峻な減衰（人気馬重視）
        decay_rate = 0.75
        score = decay_rate ** (popularity - 1)
        
        # 正規化
        total_score = sum(decay_rate ** i for i in range(total))
        return score / total_score if total_score > 0 else 0.01
    
    def _calc_market_probability(self, odds: float, all_odds: List[float]) -> float:
        """オッズから市場確率を計算"""
        if odds <= 0:
            return 0.01
        
        # 控除率の推定（JRA約25%）
        implied_total = sum(1.0 / o for o in all_odds if o > 0)
        takeout = max(0, 1 - (1.0 / implied_total)) if implied_total > 0 else 0.25
        
        # 控除率除去
        raw_prob = 1.0 / odds
        adjusted_prob = raw_prob / (1 + takeout)
        
        return min(0.8, max(0.01, adjusted_prob))
    
    def _empty_result(self) -> Dict:
        """空の結果"""
        return {
            'scores': {},
            'rankings': [],
            'fair_values': {},
            'expected_values': {},
            'value_bets': []
        }
    
    def format_response(self, result: Dict) -> str:
        """チャット用レスポンス生成"""
        response = "【F-Logic 簡易版フェア値分析】\n\n"
        
        rankings = result.get('rankings', [])
        value_bets = result.get('value_bets', [])
        
        if rankings:
            response += "◆ フェア値 TOP5\n"
            for i, (horse, score) in enumerate(rankings[:5], 1):
                ev = result['expected_values'].get(horse, 0)
                fv = result['fair_values'].get(horse, 0)
                
                response += f"{i}. {horse} (スコア: {score:.1f})\n"
                response += f"   フェア値: {fv:.1f}倍 / 期待値: {ev:.1f}%"
                
                if ev >= 120:
                    response += " 🔥"
                elif ev >= 110:
                    response += " ⭐"
                response += "\n\n"
        
        if value_bets:
            response += "\n◆ 投資推奨馬（期待値110%以上）\n"
            for bet in value_bets:
                response += f"🎯 {bet['horse']} ({bet['popularity']}番人気)\n"
                response += f"   期待値: {bet['expected_value']:.1f}%\n"
                response += f"   {bet['fair_value']:.1f}倍 → {bet['actual_odds']:.1f}倍\n\n"
        
        response += "\n※ 簡易版はオッズと人気のみで計算（高速処理）"
        
        return response