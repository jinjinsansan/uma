#!/usr/bin/env python3
"""
高速D-Logic計算エンジン
生データナレッジからリアルタイム計算（0.1秒目標）
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import mysql.connector
from .dlogic_raw_data_manager import dlogic_manager

class FastDLogicEngine:
    """高速D-Logic計算エンジン"""
    
    def __init__(self):
        # グローバルインスタンスを使用（ナレッジの重複読み込みを回避）
        self.raw_manager = dlogic_manager
        self.mysql_config = {
            'host': '172.25.160.1',
            'port': 3306,
            'user': 'root',
            'password': '04050405Aoi-',
            'database': 'mykeibadb',
            'charset': 'utf8mb4'
        }
        print(f"⚡ 高速D-Logic計算エンジン初期化完了 (ナレッジ: {len(self.raw_manager.knowledge_data.get('horses', {}))}頭)")
    
    def analyze_single_horse(self, horse_name: str) -> Dict[str, Any]:
        """単体馬分析（目標: 0.1秒以内）"""
        start_time = datetime.now()
        
        # ダンスインザダークは基準馬なので特別扱い
        if horse_name == "ダンスインザダーク":
            calc_time = (datetime.now() - start_time).total_seconds()
            return {
                "total_score": 100.0,
                "grade": "SS",
                "d_logic_scores": {
                    "1_distance_aptitude": 100.0,
                    "2_bloodline_evaluation": 100.0,
                    "3_jockey_compatibility": 100.0,
                    "4_trainer_evaluation": 100.0,
                    "5_track_aptitude": 100.0,
                    "6_weather_aptitude": 100.0,
                    "7_popularity_factor": 100.0,
                    "8_weight_impact": 100.0,
                    "9_horse_weight_impact": 100.0,
                    "10_corner_specialist_degree": 100.0,
                    "11_margin_analysis": 100.0,
                    "12_time_index": 100.0
                },
                "data_source": "baseline_horse",
                "calculation_time_seconds": calc_time,
                "horse_name": horse_name
            }
        
        # 1. ナレッジから生データ取得（高速）
        raw_data = self.raw_manager.get_horse_raw_data(horse_name)
        
        if raw_data:
            # ナレッジヒット - リアルタイム計算
            result = self.raw_manager.calculate_dlogic_realtime(horse_name)
            result['data_source'] = 'knowledge_base'
        else:
            # ナレッジ未登録 - MySQLフォールバック
            result = self._calculate_from_mysql(horse_name)
            result['data_source'] = 'mysql_fallback'
        
        # 計算時間記録
        calc_time = (datetime.now() - start_time).total_seconds()
        result['calculation_time_seconds'] = calc_time
        
        return result
    
    def analyze_single_horse_weather(self, horse_name: str, baba_condition: int) -> Dict[str, Any]:
        """単体馬の天候適性分析
        
        Args:
            horse_name: 馬名
            baba_condition: 馬場状態 (1=良, 2=稍重, 3=重, 4=不良)
        
        Returns:
            天候適性を考慮したD-Logic分析結果
        """
        start_time = datetime.now()
        
        # ダンスインザダークは基準馬なので特別扱い
        if horse_name == "ダンスインザダーク":
            calc_time = (datetime.now() - start_time).total_seconds()
            result = {
                "total_score": 100.0,
                "grade": "SS",
                "d_logic_scores": {
                    "1_distance_aptitude": 100.0,
                    "2_bloodline_evaluation": 100.0,
                    "3_jockey_compatibility": 100.0,
                    "4_trainer_evaluation": 100.0,
                    "5_track_aptitude": 100.0,
                    "6_weather_aptitude": 100.0,
                    "7_popularity_factor": 100.0,
                    "8_weight_impact": 100.0,
                    "9_horse_weight_impact": 100.0,
                    "10_corner_specialist_degree": 100.0,
                    "11_margin_analysis": 100.0,
                    "12_time_index": 100.0
                },
                "data_source": "baseline_horse",
                "calculation_time_seconds": calc_time,
                "horse_name": horse_name,
                "weather_condition": {1: "良", 2: "稍重", 3: "重", 4: "不良"}[baba_condition],
                "weather_adjustment": 0.0
            }
            return result
        
        # 天候適性計算を実行
        result = self.raw_manager.calculate_weather_adaptive_dlogic(horse_name, baba_condition)
        
        # ナレッジにない場合のフォールバック
        if "error" in result:
            result = {
                "error": f"{horse_name}のデータは現在のナレッジベースに含まれていません。",
                "total_score": 50.0,
                "grade": "未評価",
                "note": "この馬のデータは次回の更新時に追加される予定です。",
                "horse_name": horse_name,
                "weather_condition": {1: "良", 2: "稍重", 3: "重", 4: "不良"}[baba_condition],
                "data_source": "not_found"
            }
        else:
            result['data_source'] = 'knowledge_base'
        
        # 計算時間記録
        calc_time = (datetime.now() - start_time).total_seconds()
        result['calculation_time_seconds'] = calc_time
        
        return result
    
    def analyze_race_horses_weather(self, horse_names: List[str], baba_condition: int) -> Dict[str, Any]:
        """レース出走馬の天候適性一括分析
        
        Args:
            horse_names: 馬名リスト
            baba_condition: 馬場状態 (1=良, 2=稍重, 3=重, 4=不良)
        
        Returns:
            天候適性を考慮したレース分析結果
        """
        start_time = datetime.now()
        
        results = []
        knowledge_hits = 0
        mysql_fallbacks = 0
        
        for horse_name in horse_names:
            horse_result = self.analyze_single_horse_weather(horse_name, baba_condition)
            
            # 馬名を確実に含める
            if 'horse_name' in horse_result and 'name' not in horse_result:
                horse_result['name'] = horse_result['horse_name']
            elif 'name' not in horse_result:
                horse_result['name'] = horse_name
            
            if horse_result.get('data_source') == 'knowledge_base':
                knowledge_hits += 1
            else:
                mysql_fallbacks += 1
            
            results.append(horse_result)
        
        # 結果を分類
        valid_results = []
        not_found_results = []
        
        for r in results:
            if 'total_score' in r:
                valid_results.append(r)
            else:
                # データが見つからない馬も結果に含める
                not_found_results.append({
                    'name': r.get('name', r.get('horse_name', '不明')),
                    'horse_name': r.get('horse_name', r.get('name', '不明')),
                    'total_score': None,
                    'grade': 'データなし',
                    'error': r.get('error', 'ナレッジベースに含まれていません'),
                    'data_source': 'not_found',
                    'weather_condition': {1: "良", 2: "稍重", 3: "重", 4: "不良"}[baba_condition]
                })
        
        # D-Logic順でソート（スコアがある馬のみ）
        valid_results.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 順位付け（スコアがある馬のみ）
        for i, result in enumerate(valid_results):
            result['dlogic_rank'] = i + 1
        
        # すべての結果を結合（スコアがある馬 → データがない馬の順）
        all_results = valid_results + not_found_results
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'race_analysis': {
                'total_horses': len(horse_names),
                'analyzed_horses': len(valid_results),
                'not_found_horses': len(not_found_results),
                'knowledge_hits': knowledge_hits,
                'mysql_fallbacks': mysql_fallbacks,
                'total_calculation_time': total_time,
                'avg_time_per_horse': total_time / len(horse_names) if horse_names else 0,
                'baba_condition': baba_condition,
                'weather_condition': {1: "良", 2: "稍重", 3: "重", 4: "不良"}[baba_condition]
            },
            'horses': all_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_race_horses(self, horse_names: List[str]) -> Dict[str, Any]:
        """レース出走馬一括分析（目標: 16頭で2秒以内）"""
        start_time = datetime.now()
        
        results = []
        knowledge_hits = 0
        mysql_fallbacks = 0
        
        for horse_name in horse_names:
            horse_result = self.analyze_single_horse(horse_name)
            
            # 馬名を確実に含める（'name'フィールドとして）
            if 'horse_name' in horse_result and 'name' not in horse_result:
                horse_result['name'] = horse_result['horse_name']
            elif 'name' not in horse_result:
                horse_result['name'] = horse_name
            
            if horse_result.get('data_source') == 'knowledge_base':
                knowledge_hits += 1
            else:
                mysql_fallbacks += 1
            
            results.append(horse_result)
        
        # 結果を分類
        valid_results = []
        not_found_results = []
        
        for r in results:
            if 'total_score' in r:
                valid_results.append(r)
            else:
                # データが見つからない馬も結果に含める
                not_found_results.append({
                    'name': r.get('name', r.get('horse_name', '不明')),
                    'horse_name': r.get('horse_name', r.get('name', '不明')),
                    'total_score': None,
                    'grade': 'データなし',
                    'error': r.get('error', 'ナレッジベースに含まれていません'),
                    'data_source': 'not_found'
                })
        
        # D-Logic順でソート（スコアがある馬のみ）
        valid_results.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 順位付け（スコアがある馬のみ）
        for i, result in enumerate(valid_results):
            result['dlogic_rank'] = i + 1
        
        # すべての結果を結合（スコアがある馬 → データがない馬の順）
        all_results = valid_results + not_found_results
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'race_analysis': {
                'total_horses': len(horse_names),
                'analyzed_horses': len(valid_results),
                'not_found_horses': len(not_found_results),
                'knowledge_hits': knowledge_hits,
                'mysql_fallbacks': mysql_fallbacks,
                'total_calculation_time': total_time,
                'avg_time_per_horse': total_time / len(horse_names) if horse_names else 0
            },
            'horses': all_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_from_mysql(self, horse_name: str) -> Dict[str, Any]:
        """MySQLから直接計算（フォールバック用）"""
        # Renderではローカル MySQL にアクセスできないため、ナレッジにない馬は対応不可
        return {
            "error": f"{horse_name}のデータは現在のナレッジベースに含まれていません。データ更新をお待ちください。",
            "horse_name": horse_name,
            "data_source": "not_found"
            # total_scoreやgradeを含めないことで、分析不可を明確にする
        }
    
    def batch_analyze_with_progress(self, horse_names: List[str], 
                                   progress_callback=None) -> Dict[str, Any]:
        """プログレス付き一括分析"""
        start_time = datetime.now()
        results = []
        
        for i, horse_name in enumerate(horse_names):
            result = self.analyze_single_horse(horse_name)
            results.append(result)
            
            if progress_callback:
                progress = (i + 1) / len(horse_names) * 100
                progress_callback(progress, horse_name, result)
        
        return self.analyze_race_horses(horse_names)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """エンジン性能統計"""
        knowledge_horses = len(self.raw_manager.knowledge_data.get('horses', {}))
        
        return {
            "knowledge_base_horses": knowledge_horses,
            "cache_hit_rate": "N/A (要実装)",
            "avg_calculation_time": "N/A (要実装)",
            "last_updated": self.raw_manager.knowledge_data.get('meta', {}).get('last_updated'),
            "engine_version": "1.0"
        }

if __name__ == "__main__":
    # テスト実行
    engine = FastDLogicEngine()
    
    print("\n🧪 単体馬テスト:")
    test_horses = ["レガレイラ", "ダノンデサイル", "アーバンシック"]
    
    for horse in test_horses:
        result = engine.analyze_single_horse(horse)
        print(f"  {horse}: {result.get('total_score', 0):.1f}点 "
              f"({result.get('calculation_time_seconds', 0):.3f}秒) "
              f"- {result.get('data_source', 'unknown')}")
    
    print(f"\n🏇 レース分析テスト:")
    race_result = engine.analyze_race_horses(test_horses)
    print(f"  総計算時間: {race_result['race_analysis']['total_calculation_time']:.3f}秒")
    print(f"  馬1頭平均: {race_result['race_analysis']['avg_time_per_horse']:.3f}秒")
    print(f"  ナレッジヒット: {race_result['race_analysis']['knowledge_hits']}頭")
    
    print(f"\n📊 性能統計:")
    stats = engine.get_performance_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

# グローバルインスタンス（モジュールレベルで初期化）
fast_engine_instance = FastDLogicEngine()