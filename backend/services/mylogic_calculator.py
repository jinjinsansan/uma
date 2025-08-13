#!/usr/bin/env python3
"""
MyLogic計算エンジン
ユーザーカスタマイズの重み付けでD-Logic計算を行う
既存のFastDLogicEngineを利用して、重み付けだけ変更
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# 既存のD-Logic計算エンジンをインポート
from .fast_dlogic_engine import FastDLogicEngine

logger = logging.getLogger(__name__)

class MyLogicCalculator:
    """MyLogic計算エンジン - 既存のD-Logicエンジンを拡張"""
    
    # D-Logicスコアのキー名（マッピング不要、同じキーを使用）
    # MyLogicでもD-Logicと同じ項目名を使用する
    D_LOGIC_KEYS = [
        "1_distance_aptitude",          # 距離適性
        "2_bloodline_evaluation",       # 血統評価
        "3_jockey_compatibility",       # 騎手相性
        "4_trainer_evaluation",         # 調教師評価
        "5_track_aptitude",            # トラック適性
        "6_weather_aptitude",          # 天候適性
        "7_popularity_factor",         # 人気要因
        "8_weight_impact",             # 斤量影響
        "9_horse_weight_impact",       # 馬体重影響
        "10_corner_specialist_degree",  # コーナー巧者度
        "11_margin_analysis",           # 着差分析
        "12_time_index"                 # タイム指数
    ]
    
    def __init__(self):
        # 既存のD-Logic計算エンジンを使用
        self.dlogic_engine = FastDLogicEngine()
        logger.info("MyLogic計算エンジン初期化完了")
    
    def calculate_with_custom_weights(
        self, 
        horse_name: str, 
        weights: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        カスタム重み付けでD-Logic計算を実行
        
        Args:
            horse_name: 馬名
            weights: カスタム重み付け (各項目0-100、合計100)
        
        Returns:
            分析結果
        """
        try:
            # 1. 標準D-Logic分析を実行
            standard_result = self.dlogic_engine.analyze_single_horse(horse_name)
            
            if not standard_result or "total_score" not in standard_result:
                logger.warning(f"馬 {horse_name} の標準分析に失敗")
                return {
                    "horse_name": horse_name,
                    "standard_score": 0,
                    "mylogic_score": 0,
                    "score_difference": 0,
                    "error": "分析データが見つかりません"
                }
            
            # 2. D-Logicの各項目スコアを取得
            d_logic_scores = standard_result.get("d_logic_scores", {})
            
            # 3. カスタム重み付けで再計算
            mylogic_score = self._calculate_mylogic_score(d_logic_scores, weights)
            
            # デバッグ用: 各項目の貢献度を記録
            individual_contributions = {}
            for d_logic_key, score in d_logic_scores.items():
                mylogic_key = "_".join(d_logic_key.split("_")[1:])
                if mylogic_key in weights:
                    weight = weights[mylogic_key]
                    contribution = score * weight / 100
                    individual_contributions[mylogic_key] = {
                        "original_score": score,
                        "weight": weight,
                        "contribution": round(contribution, 2)
                    }
            
            # 4. 結果を返す
            standard_score = standard_result["total_score"]
            score_difference = round(mylogic_score - standard_score, 1)
            
            return {
                "horse_name": horse_name,
                "standard_score": standard_score,
                "mylogic_score": mylogic_score,
                "score_difference": score_difference,
                "grade": self._get_grade(mylogic_score),
                "individual_scores": d_logic_scores,  # デバッグ用
                "individual_contributions": individual_contributions  # 各項目の貢献度
            }
            
        except Exception as e:
            logger.error(f"MyLogic計算エラー: {str(e)}")
            return {
                "horse_name": horse_name,
                "standard_score": 0,
                "mylogic_score": 0,
                "score_difference": 0,
                "error": str(e)
            }
    
    def _calculate_mylogic_score(
        self, 
        d_logic_scores: Dict[str, float], 
        weights: Dict[str, int]
    ) -> float:
        """
        D-Logicの個別スコアとカスタム重み付けから総合スコアを計算
        
        Args:
            d_logic_scores: D-Logicの各項目スコア
            weights: カスタム重み付け
        
        Returns:
            MyLogicスコア (0-100)
        """
        # 重み付けの正規化（合計が100でない場合に備えて）
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 50.0  # デフォルト値
        
        mylogic_score = 0.0
        weight_sum = 0.0
        
        # 各D-Logicスコアにカスタム重み付けを適用
        for d_logic_key, score in d_logic_scores.items():
            # D-Logicのキー名からMyLogicのキー名に変換（番号を除去）
            # 例: "1_distance_aptitude" -> "distance_aptitude"
            mylogic_key = "_".join(d_logic_key.split("_")[1:])
            
            if mylogic_key in weights:
                weight = weights[mylogic_key] / total_weight * 100
                contribution = score * weight / 100
                mylogic_score += contribution
                weight_sum += weight
                
                logger.debug(f"{d_logic_key} ({mylogic_key}): {score} × {weight}% = {contribution}")
        
        # 重み付けの合計が100%にならない場合の調整
        if weight_sum > 0:
            mylogic_score = mylogic_score * 100 / weight_sum
        
        # 0-100の範囲に収める
        return round(max(0, min(100, mylogic_score)), 1)
    
    def _get_grade(self, score: float) -> str:
        """スコアからグレードを判定"""
        if score >= 95:
            return "SS"
        elif score >= 90:
            return "S"
        elif score >= 85:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 55:
            return "D+"
        elif score >= 50:
            return "D"
        else:
            return "E"
    
    def analyze_multiple_horses(
        self, 
        horse_names: List[str], 
        weights: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """
        複数馬をカスタム重み付けで分析
        
        Args:
            horse_names: 馬名リスト
            weights: カスタム重み付け
        
        Returns:
            分析結果リスト（MyLogicスコア降順）
        """
        results = []
        
        for horse_name in horse_names[:20]:  # 最大20頭まで
            result = self.calculate_with_custom_weights(horse_name, weights)
            results.append(result)
        
        # MyLogicスコアで降順ソート
        results.sort(key=lambda x: x.get("mylogic_score", 0), reverse=True)
        
        return results