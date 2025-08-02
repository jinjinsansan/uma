#!/usr/bin/env python3
"""
Phase D統合: MySQL完全活用D-Logic計算エンジン
959,620レコードから瞬時にD-Logic指数を計算
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from services.advanced_d_logic_analyzer import AdvancedDLogicAnalyzer
from services.enhanced_knowledge_base import enhanced_knowledge_base

logger = logging.getLogger(__name__)

class IntegratedDLogicCalculator:
    """統合D-Logic計算エンジン"""
    
    def __init__(self):
        self.analyzer = None
        self.knowledge_base = enhanced_knowledge_base
        self.is_initialized = False
        
        print("🚀 統合D-Logic計算エンジン初期化")
    
    async def initialize(self):
        """非同期初期化"""
        if not self.is_initialized:
            try:
                # MySQL分析エンジン初期化
                self.analyzer = AdvancedDLogicAnalyzer()
                self.is_initialized = True
                print("✅ MySQL分析エンジン初期化完了")
            except Exception as e:
                logger.error(f"D-Logic計算エンジン初期化エラー: {e}")
                self.is_initialized = False
    
    def calculate_d_logic_score(self, horse_data: Dict[str, Any]) -> Dict[str, Any]:
        """馬のD-Logicスコア計算"""
        try:
            # 馬名取得
            horse_name = horse_data.get("horse_name") or horse_data.get("bamei") or horse_data.get("name", "")
            
            if not horse_name:
                return self._create_default_score("馬名が不明です")
            
            # Phase D伝説馬データから検索
            legendary_horses = self.knowledge_base.get_legendary_horses()
            
            if horse_name in legendary_horses:
                # 伝説馬の場合、Phase Dデータを使用
                horse_analysis = legendary_horses[horse_name]
                return self._format_legendary_horse_result(horse_analysis)
            
            # MySQL完全分析実行（初期化済みの場合）
            if self.is_initialized and self.analyzer:
                try:
                    analysis_result = self.analyzer.analyze_horse_complete_profile(horse_name)
                    if "error" not in analysis_result:
                        return self._format_mysql_analysis_result(analysis_result)
                except Exception as e:
                    logger.warning(f"MySQL分析エラー ({horse_name}): {e}")
            
            # フォールバック: 簡易計算
            return self._calculate_fallback_score(horse_data)
            
        except Exception as e:
            logger.error(f"D-Logic計算エラー: {e}")
            return self._create_default_score(f"計算エラー: {str(e)}")
    
    def _format_legendary_horse_result(self, horse_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """伝説馬データのフォーマット"""
        d_logic_scores = horse_analysis.get("d_logic_scores", {})
        total_score = horse_analysis.get("dance_in_the_dark_total_score", 0)
        grade = horse_analysis.get("performance_grade", "C (平均)")
        
        # 12項目スコアを日本語名に変換
        formatted_scores = {}
        item_names = {
            "1_distance_aptitude": "距離適性",
            "2_bloodline_evaluation": "血統評価",
            "3_jockey_compatibility": "騎手相性",
            "4_trainer_evaluation": "調教師評価",
            "5_track_aptitude": "馬場適性",
            "6_weather_aptitude": "天候適性",
            "7_popularity_factor": "人気度",
            "8_weight_impact": "斤量影響",
            "9_horse_weight_impact": "馬体重影響",
            "10_corner_specialist_degree": "コーナー巧者度",
            "11_margin_analysis": "着差分析",
            "12_time_index": "タイム指数"
        }
        
        for key, score in d_logic_scores.items():
            japanese_name = item_names.get(key, key)
            formatted_scores[japanese_name] = round(score, 1)
        
        # 詳細統計
        stats = horse_analysis.get("detailed_stats", {})
        
        return {
            "total_score": round(total_score, 1),
            "grade": grade,
            "detailed_scores": formatted_scores,
            "analysis_source": "Phase D 伝説馬データベース",
            "horse_stats": {
                "total_races": stats.get("total_races", 0),
                "wins": stats.get("wins", 0),
                "win_rate": round(stats.get("win_rate", 0) * 100, 1),
                "career_span": stats.get("career_span", {}).get("span", "不明")
            },
            "confidence_level": "最高 (Phase D完全分析済み)",
            "calculation_method": "ダンスインザダーク基準100点・MySQL完全分析",
            "specialties": self._extract_specialties_from_scores(formatted_scores)
        }
    
    def _format_mysql_analysis_result(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """MySQL分析結果のフォーマット"""
        d_logic_scores = analysis_result.get("d_logic_scores", {})
        total_score = analysis_result.get("dance_in_the_dark_total_score", 0)
        grade = analysis_result.get("performance_grade", "C (平均)")
        
        # 項目名変換
        formatted_scores = {}
        for key, score in d_logic_scores.items():
            japanese_name = key.split('_', 1)[1].replace('_', ' ').title() if '_' in key else key
            formatted_scores[japanese_name] = round(score, 1)
        
        stats = analysis_result.get("detailed_stats", {})
        
        return {
            "total_score": round(total_score, 1),
            "grade": grade,
            "detailed_scores": formatted_scores,
            "analysis_source": "MySQL完全分析 (959,620レコード)",
            "horse_stats": {
                "total_races": stats.get("total_races", 0),
                "wins": stats.get("wins", 0),
                "win_rate": round(stats.get("win_rate", 0) * 100, 1),
                "career_span": stats.get("career_span", {}).get("span", "不明")
            },
            "confidence_level": "高 (MySQL完全分析)",
            "calculation_method": "ダンスインザダーク基準100点・12項目D-Logic",
            "specialties": self._extract_specialties_from_scores(formatted_scores)
        }
    
    def _calculate_fallback_score(self, horse_data: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバック簡易計算"""
        # 基本データから簡易スコア算出
        base_score = 50.0  # デフォルト
        
        # 利用可能なデータから推定
        recent_form = horse_data.get("recent_form", [])
        if recent_form:
            # 最近5走の平均着順から推定
            avg_finish = sum(recent_form) / len(recent_form)
            base_score = max(0, 100 - (avg_finish - 1) * 10)
        
        # 簡易12項目スコア
        simple_scores = {
            "距離適性": base_score + (hash(str(horse_data.get("name", ""))) % 20 - 10),
            "血統評価": base_score + (hash(str(horse_data.get("age", 4))) % 15 - 7),
            "騎手相性": base_score + (hash(str(horse_data.get("jockey", ""))) % 25 - 12),
            "調教師評価": base_score + (hash(str(horse_data.get("trainer", ""))) % 20 - 10),
            "馬場適性": base_score,
            "天候適性": base_score,
            "人気度": base_score,
            "斤量影響": base_score,
            "馬体重影響": base_score,
            "コーナー巧者度": base_score,
            "着差分析": base_score,
            "タイム指数": base_score
        }
        
        # 範囲調整
        for key in simple_scores:
            simple_scores[key] = max(0, min(100, simple_scores[key]))
        
        total_score = sum(simple_scores.values()) / len(simple_scores)
        
        return {
            "total_score": round(total_score, 1),
            "grade": self._determine_grade(total_score),
            "detailed_scores": {k: round(v, 1) for k, v in simple_scores.items()},
            "analysis_source": "簡易計算 (データ不足)",
            "horse_stats": {
                "total_races": 0,
                "wins": 0,
                "win_rate": 0,
                "career_span": "データなし"
            },
            "confidence_level": "低 (簡易推定)",
            "calculation_method": "基本データからの推定計算",
            "specialties": []
        }
    
    def _extract_specialties_from_scores(self, scores: Dict[str, float]) -> List[str]:
        """スコアから特徴抽出"""
        specialties = []
        
        for item, score in scores.items():
            if score > 85:
                specialties.append(f"{item}優秀 ({score})")
        
        return specialties[:3]  # 上位3つ
    
    def _determine_grade(self, score: float) -> str:
        """グレード判定"""
        if score >= 90:
            return "SS (伝説級)"
        elif score >= 80:
            return "S (超一流)"
        elif score >= 70:
            return "A (一流)"
        elif score >= 60:
            return "B (良馬)"
        elif score >= 50:
            return "C (平均)"
        else:
            return "D (要改善)"
    
    def _create_default_score(self, error_message: str) -> Dict[str, Any]:
        """デフォルトスコア作成"""
        return {
            "total_score": 50.0,
            "grade": "C (平均)",
            "detailed_scores": {},
            "analysis_source": "デフォルト",
            "horse_stats": {
                "total_races": 0,
                "wins": 0,
                "win_rate": 0,
                "career_span": "不明"
            },
            "confidence_level": "低",
            "calculation_method": "デフォルト値",
            "error": error_message,
            "specialties": []
        }
    
    async def batch_calculate_race(self, race_horses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """レース全馬一括計算"""
        if not self.is_initialized:
            await self.initialize()
        
        results = []
        
        for i, horse_data in enumerate(race_horses):
            try:
                horse_result = self.calculate_d_logic_score(horse_data)
                
                # 結果にメタ情報追加
                horse_result.update({
                    "horse_id": horse_data.get("horse_id", f"horse_{i+1}"),
                    "horse_name": horse_data.get("horse_name") or horse_data.get("name", f"馬{i+1}"),
                    "umaban": horse_data.get("umaban", i+1),
                    "calculation_timestamp": datetime.now().isoformat()
                })
                
                results.append(horse_result)
                
            except Exception as e:
                logger.error(f"馬 {i+1} 計算エラー: {e}")
                results.append(self._create_default_score(f"計算エラー: {str(e)}"))
        
        # スコア順にソート
        results.sort(key=lambda x: x.get("total_score", 0), reverse=True)
        
        return results
    
    def get_calculation_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算サマリー作成"""
        if not results:
            return {}
        
        scores = [r.get("total_score", 0) for r in results]
        
        return {
            "total_horses": len(results),
            "average_score": round(sum(scores) / len(scores), 1),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "legendary_horses_count": len([r for r in results if "Phase D 伝説馬" in r.get("analysis_source", "")]),
            "mysql_analysis_count": len([r for r in results if "MySQL完全分析" in r.get("analysis_source", "")]),
            "calculation_timestamp": datetime.now().isoformat(),
            "top_3_horses": [
                {
                    "name": r.get("horse_name", ""),
                    "score": r.get("total_score", 0),
                    "grade": r.get("grade", "")
                }
                for r in results[:3]
            ]
        }

# グローバルインスタンス
d_logic_calculator = IntegratedDLogicCalculator()

if __name__ == "__main__":
    # テスト実行
    async def test_calculator():
        print("🧪 統合D-Logic計算エンジンテスト")
        
        # 初期化
        await d_logic_calculator.initialize()
        
        # テスト馬データ
        test_horses = [
            {"horse_name": "エフワンライデン", "umaban": 1},
            {"horse_name": "ブライアンズロマン", "umaban": 2},
            {"horse_name": "テスト馬", "name": "テスト馬", "umaban": 3, "recent_form": [1, 2, 1]}
        ]
        
        # 一括計算テスト
        results = await d_logic_calculator.batch_calculate_race(test_horses)
        
        print(f"📊 計算結果: {len(results)}頭")
        for i, result in enumerate(results, 1):
            print(f"  {i}位: {result.get('horse_name')} - スコア{result.get('total_score')} ({result.get('grade')})")
            print(f"       情報源: {result.get('analysis_source')}")
        
        # サマリー作成
        summary = d_logic_calculator.get_calculation_summary(results)
        print(f"\n📈 サマリー:")
        print(f"  平均スコア: {summary.get('average_score')}")
        print(f"  伝説馬: {summary.get('legendary_horses_count')}頭")
        print(f"  MySQL分析: {summary.get('mysql_analysis_count')}頭")
        
        print("\n✅ 統合D-Logic計算エンジンテスト完了!")
    
    # 非同期実行
    asyncio.run(test_calculator())