#!/usr/bin/env python3
"""
Phase D: 動的大量処理システム・最大活用ナレッジベース構築
mykeibadbの実データを最大限活用してナレッジベースを構築
"""
import sqlite3
import os
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime
import time
import math

from .database_analyzer import DatabaseAnalyzer

class MassSQLAnalyzer:
    """大量SQLデータ分析エンジン"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_connection(self):
        """データベース接続取得"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"❌ DB接続エラー: {e}")
            return None
    
    def analyze_horse_complete_data(self, horse_name: str) -> Dict[str, Any]:
        """指定馬の完全12項目分析"""
        conn = self.get_connection()
        if not conn:
            return {"error": "データベース接続失敗"}
        
        try:
            # 基本成績データ
            basic_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_races,
                    SUM(CASE WHEN CHAKUJUN = 1 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN CHAKUJUN <= 3 THEN 1 ELSE 0 END) as top3,
                    AVG(CAST(CHAKUJUN AS REAL)) as avg_finish,
                    COUNT(DISTINCT RACE_CODE) as unique_races
                FROM umagoto_race_joho 
                WHERE BAMEI = ?
                  AND CHAKUJUN IS NOT NULL AND CHAKUJUN != ''
            """, (horse_name,)).fetchone()
            
            if not basic_stats or basic_stats['total_races'] == 0:
                return {"error": f"馬 '{horse_name}' のデータが見つかりません"}
            
            # 距離別成績
            distance_stats = conn.execute("""
                SELECT 
                    KYORI,
                    COUNT(*) as races,
                    SUM(CASE WHEN CHAKUJUN = 1 THEN 1 ELSE 0 END) as wins,
                    AVG(CAST(CHAKUJUN AS REAL)) as avg_finish
                FROM umagoto_race_joho 
                WHERE BAMEI = ? AND KYORI IS NOT NULL
                GROUP BY KYORI
                ORDER BY races DESC
            """, (horse_name,)).fetchall()
            
            # 馬場別成績
            track_stats = conn.execute("""
                SELECT 
                    BABA,
                    COUNT(*) as races,
                    SUM(CASE WHEN CHAKUJUN = 1 THEN 1 ELSE 0 END) as wins,
                    AVG(CAST(CHAKUJUN AS REAL)) as avg_finish
                FROM umagoto_race_joho 
                WHERE BAMEI = ? AND BABA IS NOT NULL
                GROUP BY BABA
                ORDER BY races DESC
            """, (horse_name,)).fetchall()
            
            # 騎手別成績
            jockey_stats = conn.execute("""
                SELECT 
                    KISHI,
                    COUNT(*) as races,
                    SUM(CASE WHEN CHAKUJUN = 1 THEN 1 ELSE 0 END) as wins,
                    AVG(CAST(CHAKUJUN AS REAL)) as avg_finish
                FROM umagoto_race_joho 
                WHERE BAMEI = ? AND KISHI IS NOT NULL AND KISHI != ''
                GROUP BY KISHI
                ORDER BY races DESC
            """, (horse_name,)).fetchall()
            
            # 12項目分析結果を構築
            analysis_result = {
                "horse_name": horse_name,
                "basic_performance": {
                    "total_races": basic_stats['total_races'],
                    "wins": basic_stats['wins'],
                    "top3": basic_stats['top3'],
                    "win_rate": basic_stats['wins'] / basic_stats['total_races'] if basic_stats['total_races'] > 0 else 0,
                    "top3_rate": basic_stats['top3'] / basic_stats['total_races'] if basic_stats['total_races'] > 0 else 0,
                    "avg_finish": round(basic_stats['avg_finish'], 2) if basic_stats['avg_finish'] else 0
                },
                "distance_analysis": [
                    {
                        "distance": row['KYORI'],
                        "races": row['races'],
                        "wins": row['wins'],
                        "win_rate": row['wins'] / row['races'] if row['races'] > 0 else 0,
                        "avg_finish": round(row['avg_finish'], 2) if row['avg_finish'] else 0
                    } for row in distance_stats
                ],
                "track_analysis": [
                    {
                        "track": row['BABA'],
                        "races": row['races'],
                        "wins": row['wins'],
                        "win_rate": row['wins'] / row['races'] if row['races'] > 0 else 0,
                        "avg_finish": round(row['avg_finish'], 2) if row['avg_finish'] else 0
                    } for row in track_stats
                ],
                "jockey_analysis": [
                    {
                        "jockey": row['KISHI'],
                        "races": row['races'],
                        "wins": row['wins'],
                        "win_rate": row['wins'] / row['races'] if row['races'] > 0 else 0,
                        "avg_finish": round(row['avg_finish'], 2) if row['avg_finish'] else 0
                    } for row in jockey_stats[:5]  # 上位5騎手
                ]
            }
            
            return analysis_result
            
        except Exception as e:
            return {"error": f"分析エラー: {e}"}
        finally:
            conn.close()

class AdaptiveKnowledgeBuilder:
    """適応的ナレッジベース構築システム"""
    
    def __init__(self):
        self.db_analyzer = DatabaseAnalyzer()
        
        # データベースパス取得
        db_path = self.db_analyzer.db_path
        if not os.path.exists(db_path):
            print(f"❌ データベースが見つかりません: {db_path}")
            self.sql_analyzer = None
        else:
            self.sql_analyzer = MassSQLAnalyzer(db_path)
    
    def execute_maximum_expansion(self) -> Tuple[Dict[str, Any], int]:
        """利用可能データ最大活用拡張"""
        if not self.sql_analyzer:
            return {"error": "データベース接続不可"}, 0
        
        print("🚀 mykeibadb最大活用ナレッジベース構築開始")
        print("=" * 60)
        
        # データベース完全調査
        print("📊 Step 1: データベース完全調査実行中...")
        db_stats = self.db_analyzer.analyze_complete_database()
        
        if "error" in db_stats:
            print(f"❌ データベース調査エラー: {db_stats['error']}")
            return db_stats, 0
        
        # 調査結果表示
        self._display_database_stats(db_stats)
        
        # 処理対象馬リスト取得
        print("🏇 Step 2: 処理対象馬リスト生成中...")
        target_horses = self.db_analyzer.get_optimal_horse_list(min_races=2)  # 最低2戦以上
        total_target = len(target_horses)
        
        if total_target == 0:
            print("❌ 処理対象馬が見つかりません")
            return {"error": "処理対象馬なし"}, 0
        
        print(f"🎯 処理対象決定: {total_target:,}頭（2戦以上勝利実績馬）")
        
        # 段階的処理戦略決定
        batch_size = self._determine_batch_size(total_target)
        print(f"⚙️  処理戦略: {batch_size}頭ずつバッチ処理")
        
        # ナレッジベース初期化
        knowledge_base = {
            "metadata": {
                "creation_date": datetime.now().isoformat(),
                "database_stats": db_stats,
                "total_horses": total_target,
                "processing_strategy": f"{batch_size}頭バッチ処理",
                "version": "Phase_D_1.0"
            },
            "horses": {}
        }
        
        # バッチ処理実行
        print("🔄 Step 3: バッチ処理開始...")
        success_count = 0
        
        total_batches = math.ceil(total_target / batch_size)
        
        for i in range(0, total_target, batch_size):
            batch = target_horses[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"\n📦 バッチ {batch_num}/{total_batches} 処理中...")
            print(f"   対象: {len(batch)}頭 ({i+1}～{min(i+len(batch), total_target)})")
            
            batch_start_time = time.time()
            
            for j, horse_data in enumerate(batch):
                horse_name = horse_data[0]  # BAMEI
                total_races, wins, top3, avg_finish, unique_races = horse_data[1:6]
                
                try:
                    # 完全12項目分析
                    complete_analysis = self.sql_analyzer.analyze_horse_complete_data(horse_name)
                    
                    if "error" in complete_analysis:
                        print(f"   ⚠️  {horse_name}: {complete_analysis['error']}")
                        continue
                    
                    # Dロジック指数計算
                    d_logic_score = self._calculate_d_logic_score(complete_analysis)
                    
                    # 信頼度計算
                    confidence = self._calculate_confidence_level(complete_analysis)
                    
                    # ナレッジベース追加
                    knowledge_base["horses"][horse_name] = {
                        "baselineScore": round(d_logic_score, 1),
                        "careerRecord": f"{total_races}戦{wins}勝",
                        "winRate": round(wins / total_races if total_races > 0 else 0, 3),
                        "top3Rate": round(top3 / total_races if total_races > 0 else 0, 3),
                        "avgFinish": round(avg_finish, 2) if avg_finish else 0,
                        "confidence": confidence,
                        "sqlAnalysis": complete_analysis,
                        "lastUpdated": datetime.now().isoformat()
                    }
                    
                    success_count += 1
                    
                    # 進捗表示（100頭毎）
                    current_total = i + j + 1
                    if current_total % 100 == 0 or j == len(batch) - 1:
                        elapsed = time.time() - batch_start_time
                        print(f"   進捗: {current_total:,}/{total_target:,}頭 "
                              f"({current_total/total_target*100:.1f}%) "
                              f"成功: {success_count} "
                              f"時間: {elapsed:.1f}s")
                
                except Exception as e:
                    print(f"   ❌ {horse_name}: エラー - {e}")
                    continue
            
            # バッチ完了報告
            batch_elapsed = time.time() - batch_start_time
            print(f"   ✅ バッチ {batch_num} 完了 ({batch_elapsed:.1f}s)")
            
            # バッチごとに中間保存
            if batch_num % 5 == 0:  # 5バッチごと
                self._save_intermediate_knowledge_base(knowledge_base, batch_num)
        
        print(f"\n🎉 全処理完了！")
        print(f"   成功: {success_count:,}/{total_target:,}頭")
        print(f"   成功率: {success_count/total_target*100:.1f}%")
        
        return knowledge_base, success_count
    
    def _display_database_stats(self, db_stats: Dict[str, Any]):
        """データベース統計表示"""
        print("\n📊 データベース調査結果:")
        print("-" * 40)
        
        db_info = db_stats.get('database_info', {})
        horse_info = db_stats.get('horse_analysis', {})
        race_info = db_stats.get('race_analysis', {})
        date_info = db_stats.get('date_analysis', {})
        
        print(f"   📁 ファイルサイズ: {db_info.get('file_size_mb', 0)}MB")
        print(f"   📋 テーブル数: {db_info.get('table_count', 0)}")
        print(f"   🏇 総馬数: {horse_info.get('total_horses', 0):,}頭")
        print(f"   🏁 総レース記録: {race_info.get('total_race_records', 0):,}")
        print(f"   📅 期間: {date_info.get('period_description', '不明')}")
        
        print("-" * 40)
    
    def _determine_batch_size(self, total_horses: int) -> int:
        """処理対象数に応じたバッチサイズ決定"""
        if total_horses <= 1000:
            return 100
        elif total_horses <= 5000:
            return 250
        elif total_horses <= 10000:
            return 500
        else:
            return 1000
    
    def _calculate_d_logic_score(self, analysis: Dict[str, Any]) -> float:
        """12項目Dロジック指数計算"""
        basic = analysis.get('basic_performance', {})
        
        # ダンスインザダーク基準100点での計算
        base_score = 100.0
        
        # 基本成績による調整
        win_rate = basic.get('win_rate', 0)
        top3_rate = basic.get('top3_rate', 0)
        avg_finish = basic.get('avg_finish', 8.0)
        total_races = basic.get('total_races', 1)
        
        # 12項目評価（簡易版）
        distance_aptitude = min(win_rate * 150, 20)  # 距離適性
        bloodline_evaluation = min(top3_rate * 100, 15)  # 血統評価
        jockey_compatibility = min(win_rate * 120, 10)  # 騎手適性
        trainer_evaluation = min(top3_rate * 80, 8)  # 調教師評価
        track_aptitude = min(win_rate * 100, 12)  # 馬場適性
        weather_aptitude = 8  # 天候適性（固定）
        popularity_factor = max(15 - avg_finish * 2, 0)  # 人気要因
        weight_impact = 5  # 斤量影響（固定）
        horse_weight_impact = 5  # 馬体重影響（固定）
        corner_specialist = min(win_rate * 80, 8)  # コーナー専門度
        margin_analysis = min((8 - avg_finish) * 2, 10)  # 着差分析
        time_index = min(total_races / 10, 5)  # タイム指数
        
        total_adjustment = (
            distance_aptitude + bloodline_evaluation + jockey_compatibility +
            trainer_evaluation + track_aptitude + weather_aptitude +
            popularity_factor + weight_impact + horse_weight_impact +
            corner_specialist + margin_analysis + time_index
        )
        
        final_score = base_score + total_adjustment - 50  # 基準調整
        
        return max(final_score, 30.0)  # 最低30点保証
    
    def _calculate_confidence_level(self, analysis: Dict[str, Any]) -> str:
        """信頼度レベル計算"""
        basic = analysis.get('basic_performance', {})
        total_races = basic.get('total_races', 0)
        win_rate = basic.get('win_rate', 0)
        
        if total_races >= 20 and win_rate >= 0.2:
            return "high"
        elif total_races >= 10 and win_rate >= 0.1:
            return "medium"
        else:
            return "low"
    
    def _save_intermediate_knowledge_base(self, knowledge_base: Dict[str, Any], batch_num: int):
        """中間ナレッジベース保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"knowledge_base_intermediate_batch{batch_num}_{timestamp}.json"
        
        reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 中間保存: {filename}")
    
    def save_final_knowledge_base(self, knowledge_base: Dict[str, Any], success_count: int):
        """最終ナレッジベース保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # バックエンド用
        backend_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'knowledgeBase_complete.json')
        os.makedirs(os.path.dirname(backend_path), exist_ok=True)
        
        with open(backend_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
        
        # フロントエンド用
        frontend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'src', 'data', 'knowledgeBase_complete.json')
        os.makedirs(os.path.dirname(frontend_path), exist_ok=True)
        
        with open(frontend_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
        
        # レポート用
        reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        report_path = os.path.join(reports_dir, f"knowledge_base_final_{timestamp}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 最終ナレッジベース保存完了:")
        print(f"   Backend: {backend_path}")
        print(f"   Frontend: {frontend_path}")
        print(f"   Report: {report_path}")
        print(f"   構築馬数: {success_count:,}頭")

if __name__ == "__main__":
    # スタンドアロン実行用テスト
    builder = AdaptiveKnowledgeBuilder()
    
    print("🚀 AdaptiveKnowledgeBuilder テスト実行")
    knowledge_base, success_count = builder.execute_maximum_expansion()
    
    if success_count > 0:
        builder.save_final_knowledge_base(knowledge_base, success_count)
        print("✅ テスト完了")
    else:
        print("❌ テスト失敗")