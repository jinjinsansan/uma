#!/usr/bin/env python3
"""
D-Logicナレッジファイル管理システム
過去5年分の馬データを事前計算・高速検索
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import mysql.connector
from .advanced_d_logic_analyzer import AdvancedDLogicAnalyzer

class DLogicKnowledgeManager:
    """D-Logicナレッジ管理システム"""
    
    def __init__(self):
        self.knowledge_file = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'dlogic_knowledge_recent.json'
        )
        self.knowledge_data = self._load_knowledge()
        self.analyzer = AdvancedDLogicAnalyzer()
        print("🚀 D-Logicナレッジマネージャー初期化完了")
        print(f"📊 登録済み馬数: {len(self.knowledge_data.get('horses', {}))}")
    
    def _load_knowledge(self) -> Dict[str, Any]:
        """ナレッジファイル読み込み"""
        if os.path.exists(self.knowledge_file):
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"✅ ナレッジファイル読み込み: {len(data.get('horses', {}))}頭")
                    return data
            except Exception as e:
                print(f"⚠️ ナレッジファイル読み込みエラー: {e}")
        
        # 新規作成
        return {
            "meta": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
                "target_years": "2020-2025"
            },
            "horses": {}
        }
    
    def _save_knowledge(self):
        """ナレッジファイル保存"""
        self.knowledge_data["meta"]["last_updated"] = datetime.now().isoformat()
        
        os.makedirs(os.path.dirname(self.knowledge_file), exist_ok=True)
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_data, f, ensure_ascii=False, indent=2)
    
    def get_dlogic_score(self, horse_name: str) -> Dict[str, Any]:
        """D-Logicスコア取得（高速検索 + 動的拡張）"""
        # 1. ナレッジから高速検索
        if horse_name in self.knowledge_data["horses"]:
            print(f"⚡ ナレッジヒット: {horse_name}")
            return self.knowledge_data["horses"][horse_name]
        
        # 2. ナレッジにない場合はSQL計算
        print(f"🔍 ナレッジ未登録: {horse_name} - SQL計算実行中...")
        analysis_result = self.analyzer.analyze_horse_complete_profile(horse_name)
        
        if "error" not in analysis_result:
            # 3. 計算結果をナレッジに追加
            horse_data = {
                "dLogicScore": int(analysis_result.get('dance_in_the_dark_total_score', 100)),
                "grade": analysis_result.get('performance_grade', 'C (平均)'),
                "detailed_scores": analysis_result.get('d_logic_scores', {}),
                "stats": analysis_result.get('detailed_stats', {}),
                "calculated_at": datetime.now().isoformat(),
                "source": "sql_realtime"
            }
            
            self.knowledge_data["horses"][horse_name] = horse_data
            self._save_knowledge()
            
            print(f"✅ {horse_name} D-Logic: {horse_data['dLogicScore']} - ナレッジに追加")
            return horse_data
        
        else:
            # エラー時はダンスインザダーク基準
            error_data = {
                "dLogicScore": 100,
                "grade": "C (平均)",
                "error": analysis_result.get('error'),
                "calculated_at": datetime.now().isoformat(),
                "source": "error_default"
            }
            return error_data
    
    def batch_create_recent_knowledge(self, years_back: int = 5):
        """過去N年分の馬データを一括ナレッジ化"""
        print(f"🏗️ 過去{years_back}年分D-Logicナレッジ一括作成開始")
        
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root', 
                password='',
                database='mykeibadb',
                charset='utf8mb4'
            )
            cursor = conn.cursor(dictionary=True)
            
            # 過去N年の馬名を取得
            start_year = datetime.now().year - years_back
            
            print(f"📅 対象期間: {start_year}年～{datetime.now().year}年")
            
            cursor.execute("""
                SELECT DISTINCT BAMEI, COUNT(*) as race_count
                FROM umagoto_race_joho 
                WHERE KAISAI_NEN >= %s
                AND BAMEI IS NOT NULL 
                AND BAMEI != ''
                GROUP BY BAMEI
                HAVING race_count >= 3
                ORDER BY race_count DESC
                LIMIT 5000
            """, (str(start_year),))
            
            horses = cursor.fetchall()
            print(f"🐎 対象馬数: {len(horses)}頭")
            
            processed = 0
            errors = 0
            
            for horse in horses:
                horse_name = horse['BAMEI']
                
                # 既にナレッジにある場合はスキップ
                if horse_name in self.knowledge_data["horses"]:
                    continue
                
                print(f"🔄 {processed+1:4d}/{len(horses)} {horse_name} 分析中...")
                
                try:
                    analysis_result = self.analyzer.analyze_horse_complete_profile(horse_name)
                    
                    if "error" not in analysis_result:
                        horse_data = {
                            "dLogicScore": int(analysis_result.get('dance_in_the_dark_total_score', 100)),
                            "grade": analysis_result.get('performance_grade', 'C (平均)'),
                            "detailed_scores": analysis_result.get('d_logic_scores', {}),
                            "stats": analysis_result.get('detailed_stats', {}),
                            "race_count": horse['race_count'],
                            "calculated_at": datetime.now().isoformat(),
                            "source": "batch_creation"
                        }
                        
                        self.knowledge_data["horses"][horse_name] = horse_data
                        processed += 1
                        
                        # 50頭ごとに保存
                        if processed % 50 == 0:
                            self._save_knowledge()
                            print(f"💾 中間保存: {processed}頭完了")
                    
                    else:
                        errors += 1
                        
                except Exception as e:
                    print(f"❌ {horse_name} エラー: {e}")
                    errors += 1
            
            # 最終保存
            self._save_knowledge()
            
            print(f"✅ D-Logicナレッジ一括作成完了!")
            print(f"📊 処理成功: {processed}頭")
            print(f"❌ エラー: {errors}頭")
            print(f"📁 ナレッジファイル: {self.knowledge_file}")
            
        except Exception as e:
            print(f"❌ バッチ処理エラー: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """ナレッジ統計情報"""
        horses = self.knowledge_data.get("horses", {})
        
        if not horses:
            return {"total_horses": 0}
        
        scores = [h.get("dLogicScore", 100) for h in horses.values()]
        grades = [h.get("grade", "C") for h in horses.values()]
        
        grade_counts = {}
        for grade in grades:
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        return {
            "total_horses": len(horses),
            "avg_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "grade_distribution": grade_counts,
            "last_updated": self.knowledge_data["meta"]["last_updated"]
        }

if __name__ == "__main__":
    # テスト実行
    manager = DLogicKnowledgeManager()
    
    # 統計表示
    stats = manager.get_knowledge_stats()
    print(f"\n📊 ナレッジ統計:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # テスト検索
    test_horses = ["レガレイラ", "ダノンデサイル", "アーバンシック"]
    for horse in test_horses:
        result = manager.get_dlogic_score(horse)
        print(f"\n🐎 {horse}: {result.get('dLogicScore')} - {result.get('grade', 'N/A')}")