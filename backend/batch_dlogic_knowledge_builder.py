#!/usr/bin/env python3
"""
D-Logic生データナレッジファイル構築バッチ
12項目の分析に必要な過去5走（または3走）データのみを効率的に収集

出力ファイル:
1. dlogic_raw_knowledge.json - システム用JSONファイル
2. dlogic_raw_knowledge_summary.txt - 人間が読める進捗・馬名リスト
"""
import os
import json
import time
import mysql.connector
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import OrderedDict

class DLogicKnowledgeBuilder:
    """D-Logic生データナレッジファイル構築クラス"""
    
    def __init__(self):
        self.mysql_config = {
            'host': '172.25.160.1',
            'port': 3306,
            'user': 'root',
            'password': '04050405Aoi-',
            'database': 'mykeibadb',
            'charset': 'utf8mb4',
            'autocommit': True,
            'buffered': True
        }
        
        # 出力ファイル
        self.json_file = "data/dlogic_raw_knowledge.json"
        self.text_file = "data/dlogic_raw_knowledge_summary.txt"
        self.temp_json = "data/dlogic_raw_knowledge_temp.json"
        
        # D-Logic計算に必要な12項目に関連するフィールド
        self.required_fields = [
            # 基本情報
            "BAMEI",           # 馬名
            "RACE_CODE",       # レースコード
            "KAISAI_NEN",      # 開催年
            "KAISAI_GAPPI",    # 開催月日
            
            # 12項目の計算に必要なデータ
            "KAKUTEI_CHAKUJUN",     # 1. 距離適性計算用
            "KYORI",                # 1. 距離適性
            "KISHUMEI_RYAKUSHO",    # 3. 騎手相性
            "CHOKYOSHIMEI_RYAKUSHO",# 4. 調教師評価
            "TRACK_CODE",           # 5. トラック適性
            "TENKOU_CODE",          # 6. 天候適性
            "BABA_JOTAI_CODE",      # 6. 馬場状態適性
            "TANSHO_NINKIJUN",      # 7. 人気要素
            "FUTAN_JURYO",          # 8. 斤量影響
            "BATAIJU",              # 9. 馬体重影響
            "ZOGEN_SA",             # 9. 馬体重増減
            "CORNER1_JUNI",         # 10. コーナー巧者度
            "CORNER2_JUNI",         # 10. コーナー巧者度
            "CORNER3_JUNI",         # 10. コーナー巧者度
            "CORNER4_JUNI",         # 10. コーナー巧者度
            "TANSHO_ODDS",          # 11. 着差分析用
            "SOHA_TIME",            # 12. タイム指数
            
            # その他必要情報
            "SEIBETSU_CODE",        # 性別
            "BAREI"                 # 馬齢
        ]
        
    def create_connection(self):
        """MySQL接続を作成"""
        return mysql.connector.connect(**self.mysql_config)
    
    def extract_horse_data(self, conn, horse_name: str) -> Optional[Dict[str, Any]]:
        """
        単一馬の生データ抽出（最新5走または3走）
        D-Logic計算に必要な12項目のデータのみを取得
        """
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 最新のレースから順に取得
            query = f"""
                SELECT 
                    u.BAMEI,
                    u.RACE_CODE,
                    u.KAISAI_NEN,
                    u.KAISAI_GAPPI,
                    u.KAKUTEI_CHAKUJUN,
                    u.TANSHO_ODDS,
                    u.TANSHO_NINKIJUN,
                    u.FUTAN_JURYO,
                    u.BATAIJU,
                    u.ZOGEN_SA,
                    u.KISHUMEI_RYAKUSHO,
                    u.CHOKYOSHIMEI_RYAKUSHO,
                    u.CORNER1_JUNI,
                    u.CORNER2_JUNI,
                    u.CORNER3_JUNI,
                    u.CORNER4_JUNI,
                    u.SOHA_TIME,
                    u.BAREI,
                    u.SEIBETSU_CODE,
                    r.KYORI,
                    r.TRACK_CODE,
                    r.BABA_JOTAI_CODE,
                    r.TENKOU_CODE
                FROM umagoto_race_joho u
                LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
                WHERE u.BAMEI = %s
                AND u.KAISAI_NEN >= '2020'
                AND u.KAISAI_NEN <= '2025'
                AND u.KAKUTEI_CHAKUJUN IS NOT NULL
                ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
                LIMIT 5
            """
            
            cursor.execute(query, (horse_name,))
            races = cursor.fetchall()
            
            # 3走未満はスキップ
            if len(races) < 3:
                return None
            
            # 生データとして保存（計算はしない）
            race_data = []
            for race in races:
                # データクリーニング
                cleaned_race = {}
                for key, value in race.items():
                    if value is not None:
                        # 文字列の場合は前後の空白を削除
                        if isinstance(value, str):
                            cleaned_race[key] = value.strip()
                        else:
                            cleaned_race[key] = value
                    else:
                        cleaned_race[key] = None
                
                race_data.append(cleaned_race)
            
            return {
                "horse_name": horse_name,
                "race_count": len(race_data),
                "races": race_data,
                "last_update": datetime.now().isoformat()
            }
            
        finally:
            cursor.close()
    
    def build_knowledge(self):
        """ナレッジファイルを構築"""
        start_time = time.time()
        
        print("🏗️ D-Logic生データナレッジファイル構築開始")
        print(f"📅 対象期間: 2020年～2025年")
        print(f"🎯 対象条件: 3走以上の馬（最大5走分のデータ）")
        print(f"📝 12項目分析用データのみを収集")
        print(f"🕐 開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # ナレッジ構造初期化
        knowledge = {
            "meta": {
                "version": "3.0",
                "created": datetime.now().isoformat(),
                "description": "D-Logic生データナレッジ（12項目分析用）",
                "data_period": "2020-2025",
                "min_races": 3,
                "max_races": 5,
                "total_horses": 0,
                "last_updated": datetime.now().isoformat()
            },
            "horses": {}
        }
        
        # テキストファイル初期化
        with open(self.text_file, 'w', encoding='utf-8') as f:
            f.write("D-Logic生データナレッジファイル構築進捗\n")
            f.write("="*60 + "\n")
            f.write(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"対象期間: 2020-2025年\n")
            f.write(f"収集データ: 各馬の最新5走（最低3走）\n")
            f.write("="*60 + "\n\n")
        
        conn = None
        total_processed = 0
        total_skipped = 0
        total_errors = 0
        
        try:
            conn = self.create_connection()
            cursor = conn.cursor(dictionary=True)
            
            # 対象馬を取得（3走以上）
            print("📊 対象馬を抽出中...")
            cursor.execute("""
                SELECT BAMEI, COUNT(*) as race_count
                FROM umagoto_race_joho
                WHERE KAISAI_NEN >= '2020'
                AND KAISAI_NEN <= '2025'
                AND BAMEI IS NOT NULL
                AND BAMEI != ''
                AND KAKUTEI_CHAKUJUN IS NOT NULL
                GROUP BY BAMEI
                HAVING race_count >= 3
                ORDER BY race_count DESC, BAMEI
            """)
            
            horses = cursor.fetchall()
            cursor.close()
            
            total_horses = len(horses)
            print(f"✅ 対象馬数: {total_horses:,}頭（3走以上）\n")
            
            # 進捗パラメータ
            checkpoint_interval = 100
            save_interval = 500
            text_update_interval = 50
            
            # 処理開始
            for idx, horse_data in enumerate(horses):
                horse_name = horse_data['BAMEI']
                
                try:
                    # 生データ抽出
                    raw_data = self.extract_horse_data(conn, horse_name)
                    
                    if raw_data:
                        knowledge["horses"][horse_name] = raw_data
                        total_processed += 1
                    else:
                        total_skipped += 1
                    
                    # 進捗表示
                    if (idx + 1) % checkpoint_interval == 0:
                        progress = (idx + 1) / total_horses * 100
                        elapsed = time.time() - start_time
                        rate = total_processed / elapsed if elapsed > 0 else 0
                        eta = (total_horses - idx - 1) / rate if rate > 0 else 0
                        
                        print(f"⏳ {idx + 1:,}/{total_horses:,} 確認済 "
                              f"({progress:.1f}%) "
                              f"処理: {total_processed:,} "
                              f"スキップ: {total_skipped:,} "
                              f"速度: {rate:.1f}頭/秒 "
                              f"残り: {eta/60:.1f}分")
                    
                    # テキストファイル更新
                    if (idx + 1) % text_update_interval == 0:
                        self.update_text_file(knowledge, total_processed, total_skipped, 
                                            total_errors, elapsed, total_horses)
                    
                    # 定期保存
                    if total_processed % save_interval == 0 and total_processed > 0:
                        knowledge["meta"]["total_horses"] = total_processed
                        knowledge["meta"]["last_updated"] = datetime.now().isoformat()
                        with open(self.temp_json, 'w', encoding='utf-8') as f:
                            json.dump(knowledge, f, ensure_ascii=False, indent=2)
                        print(f"💾 中間保存: {total_processed:,}頭完了")
                
                except Exception as e:
                    total_errors += 1
                    if total_errors <= 10:
                        print(f"❌ エラー {horse_name}: {str(e)}")
            
            # 最終保存
            knowledge["meta"]["total_horses"] = total_processed
            knowledge["meta"]["last_updated"] = datetime.now().isoformat()
            knowledge["meta"]["status"] = "completed"
            
            print("\n💾 最終保存中...")
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge, f, ensure_ascii=False, indent=2)
            
            # 最終テキストファイル更新
            elapsed_total = time.time() - start_time
            self.create_final_summary(knowledge, total_processed, total_skipped, 
                                    total_errors, elapsed_total)
            
            # 一時ファイル削除
            if os.path.exists(self.temp_json):
                os.remove(self.temp_json)
            
            # 完了レポート
            self.print_completion_report(total_processed, total_skipped, 
                                       total_errors, elapsed_total)
            
        except Exception as e:
            print(f"\n❌ 致命的エラー: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            if conn:
                conn.close()
                print("🔌 MySQL接続終了")
    
    def update_text_file(self, knowledge, processed, skipped, errors, elapsed, total):
        """テキストファイルを更新"""
        with open(self.text_file, 'w', encoding='utf-8') as f:
            f.write("D-Logic生データナレッジファイル構築進捗\n")
            f.write("="*60 + "\n")
            f.write(f"更新時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"経過時間: {elapsed/60:.1f}分\n")
            f.write("\n[進捗状況]\n")
            f.write(f"総対象馬数: {total:,}頭\n")
            f.write(f"処理済み: {processed:,}頭\n")
            f.write(f"スキップ: {skipped:,}頭（3走未満）\n")
            f.write(f"エラー: {errors:,}件\n")
            f.write(f"進捗率: {(processed + skipped) / total * 100:.1f}%\n")
            f.write("\n[収録馬一覧]（アルファベット順）\n")
            f.write("-"*40 + "\n")
            
            # 馬名をソートして出力
            horse_names = sorted(knowledge["horses"].keys())
            for i, name in enumerate(horse_names):
                horse_data = knowledge["horses"][name]
                race_count = horse_data["race_count"]
                f.write(f"{i+1:5d}. {name} ({race_count}走)\n")
    
    def create_final_summary(self, knowledge, processed, skipped, errors, elapsed):
        """最終サマリーファイルを作成"""
        with open(self.text_file, 'w', encoding='utf-8') as f:
            f.write("D-Logic生データナレッジファイル構築完了レポート\n")
            f.write("="*60 + "\n")
            f.write(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"処理時間: {elapsed/3600:.1f}時間（{elapsed/60:.1f}分）\n")
            f.write("\n[最終結果]\n")
            f.write(f"収録馬数: {processed:,}頭\n")
            f.write(f"スキップ: {skipped:,}頭（3走未満）\n")
            f.write(f"エラー: {errors:,}件\n")
            f.write(f"JSONファイルサイズ: {os.path.getsize(self.json_file) / (1024*1024):.1f}MB\n")
            f.write("\n[収録データ仕様]\n")
            f.write("- 対象期間: 2020-2025年\n")
            f.write("- 収録条件: 3走以上\n")
            f.write("- データ内容: 各馬の最新5走（最大）の生データ\n")
            f.write("- 用途: D-Logic12項目分析の計算元データ\n")
            f.write("\n[収録馬一覧]（アルファベット順）\n")
            f.write("-"*60 + "\n")
            
            # 馬名をソートして詳細情報付きで出力
            horse_names = sorted(knowledge["horses"].keys())
            for i, name in enumerate(horse_names):
                horse_data = knowledge["horses"][name]
                race_count = horse_data["race_count"]
                if horse_data["races"]:
                    latest_race = horse_data["races"][0]
                    latest_date = f"{latest_race.get('KAISAI_NEN', '')}/{latest_race.get('KAISAI_GAPPI', '')[:2]}/{latest_race.get('KAISAI_GAPPI', '')[2:4]}" if latest_race.get('KAISAI_NEN') and latest_race.get('KAISAI_GAPPI') else "不明"
                else:
                    latest_date = "不明"
                f.write(f"{i+1:5d}. {name:<30} {race_count}走 最終出走: {latest_date}\n")
            
            f.write("\n[使用方法]\n")
            f.write("このファイルで収録されている馬名を確認し、\n")
            f.write("チャットテスト時にナレッジファイルに含まれているか確認できます。\n")
    
    def print_completion_report(self, processed, skipped, errors, elapsed):
        """完了レポートを表示"""
        print("\n" + "="*60)
        print("🎉 D-Logic生データナレッジファイル構築完了！")
        print(f"📊 処理結果:")
        print(f"   - 収録馬数: {processed:,}頭")
        print(f"   - スキップ: {skipped:,}頭（3走未満）")
        print(f"   - エラー: {errors:,}件")
        print(f"   - 処理時間: {elapsed/3600:.1f}時間")
        print(f"   - 平均速度: {processed/(elapsed/60):.0f}頭/分")
        print(f"\n📁 出力ファイル:")
        print(f"   - JSONファイル: {os.path.abspath(self.json_file)}")
        print(f"   - サマリーファイル: {os.path.abspath(self.text_file)}")
        
        if os.path.exists(self.json_file):
            file_size = os.path.getsize(self.json_file) / (1024 * 1024)
            print(f"   - ファイルサイズ: {file_size:.1f}MB")
        
        print("\n💡 次のステップ:")
        print("   1. サマリーファイルで収録馬を確認")
        print("   2. チャットでテスト（収録馬で動作確認）")
        print("   3. 未収録馬はMySQLから動的に取得されます")
        print("="*60)

if __name__ == "__main__":
    print("🚀 D-Logic生データナレッジファイル構築バッチ")
    print("")
    print("このバッチは以下の処理を行います：")
    print("  1. 2020-2025年の3走以上の馬データを収集")
    print("  2. 各馬の最新5走分の生データを保存")
    print("  3. JSONファイルとテキストサマリーを同時作成")
    print("  4. 12項目分析に必要なデータのみを効率的に収集")
    print("")
    print("⚠️ 推定処理時間: 1-2時間")
    print("⚠️ 既存のバッチ処理が動作していないことを確認してください")
    print("")
    print("続行しますか？ (yes/no): ", end="")
    
    response = input().strip().lower()
    if response in ['yes', 'y', 'はい']:
        print("\n🏁 処理を開始します！")
        builder = DLogicKnowledgeBuilder()
        builder.build_knowledge()
    else:
        print("❌ 処理をキャンセルしました")