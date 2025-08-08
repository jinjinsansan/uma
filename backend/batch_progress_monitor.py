#!/usr/bin/env python3
"""
進捗監視付きバッチランナー
1000頭毎に進捗報告
"""
import os
import sys
import time
import json
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.dlogic_raw_data_manager import DLogicRawDataManager
from utils.mysql_connection_manager import get_mysql_manager

def main():
    print("🚀 D-Logic進捗監視付きバッチ処理開始")
    print("📊 目標: 43,231頭（既存8,400頭 → 51,631頭）")
    print("📈 報告間隔: 1,000頭毎")
    print("=" * 60)
    
    # MySQL接続マネージャー
    mysql_manager = get_mysql_manager()
    if not mysql_manager.test_connection():
        print("❌ MySQL接続失敗")
        return
    
    # データマネージャー
    manager = DLogicRawDataManager()
    start_time = time.time()
    
    try:
        # 対象馬取得
        print("🔍 対象馬抽出中...")
        horses = mysql_manager.execute_query("""
            SELECT DISTINCT BAMEI, COUNT(*) as race_count
            FROM umagoto_race_joho 
            WHERE KAISAI_NEN >= '2020'
            AND BAMEI IS NOT NULL 
            AND BAMEI != ''
            GROUP BY BAMEI
            HAVING race_count >= 3
            ORDER BY race_count DESC
        """)
        
        total_target = len(horses)
        print(f"🐎 MySQL対象馬数: {total_target:,}頭")
        
        # 既存データ確認
        existing_count = 0
        processed_in_session = 0
        errors = 0
        last_report = 0
        
        print(f"⏰ 処理開始: {datetime.now().strftime('%H:%M:%S')}")
        print("")
        
        for i, horse_data in enumerate(horses, 1):
            horse_name = horse_data['BAMEI']
            
            try:
                # 既存確認
                if manager.get_horse_raw_data(horse_name):
                    existing_count += 1
                    continue
                
                # 生データ抽出
                raw_data = extract_horse_raw_data(horse_name, mysql_manager)
                
                if raw_data and raw_data["race_history"]:
                    manager.add_horse_raw_data(horse_name, raw_data)
                    processed_in_session += 1
                    
                    # 1000頭毎の報告
                    if processed_in_session > 0 and processed_in_session % 1000 == 0:
                        elapsed = time.time() - start_time
                        rate = processed_in_session / elapsed * 3600  # 頭/時間
                        remaining = total_target - existing_count - processed_in_session
                        eta_hours = remaining / rate if rate > 0 else 0
                        
                        progress_report = f"""
🎯 進捗報告 #{processed_in_session // 1000}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 処理状況:
  ✅ セッション処理完了: {processed_in_session:,}頭
  📚 既存スキップ: {existing_count:,}頭  
  🐎 総処理済み: {existing_count + processed_in_session:,}頭
  📈 残り処理: {total_target - existing_count - processed_in_session:,}頭

⏱️ 処理統計:
  ⚡ 処理速度: {rate:.0f}頭/時間
  📅 経過時間: {elapsed/3600:.1f}時間
  🔮 残り時間: {eta_hours:.1f}時間
  ❌ エラー数: {errors}頭

💾 ファイル状況:
  📁 現在のナレッジ数: {existing_count + processed_in_session:,}頭
  🎯 目標達成率: {((existing_count + processed_in_session)/total_target)*100:.1f}%

⏰ 時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                        print(progress_report)
                        
                        # 中間保存
                        manager._save_knowledge()
                        print("💾 中間保存完了\n")
                
                # 処理間隔
                if i % 10 == 0:
                    time.sleep(1)  # 負荷軽減
                    
            except Exception as e:
                errors += 1
                if errors <= 20:
                    print(f"❌ {horse_name} エラー: {e}")
        
        # 最終保存
        manager._save_knowledge()
        
        # 完了報告
        total_time = time.time() - start_time
        final_report = f"""
🎉 D-Logicナレッジ蓄積バッチ完了！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 最終結果:
  🏁 セッション処理完了: {processed_in_session:,}頭
  📚 既存利用: {existing_count:,}頭
  🐎 総ナレッジ数: {existing_count + processed_in_session:,}頭
  🎯 目標達成率: {((existing_count + processed_in_session)/total_target)*100:.1f}%

⏱️ 処理統計:
  ⚡ 平均処理速度: {processed_in_session/(total_time/3600):.0f}頭/時間
  📅 総処理時間: {total_time/3600:.2f}時間
  ❌ 総エラー数: {errors}頭

🚀 システム準備完了:
  ✅ 現役馬データ蓄積完了
  ⚡ 高速LLM応答可能
  🏇 18頭立てレース瞬時計算対応

⏰ 完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        print(final_report)
        
    except Exception as e:
        print(f"❌ バッチ処理エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        mysql_manager.close_pool()

def extract_horse_raw_data(horse_name: str, mysql_manager) -> dict:
    """馬の生データ抽出（最大5走分）"""
    races = mysql_manager.execute_query("""
        SELECT 
            u.RACE_CODE,
            u.KAISAI_NEN,
            u.KAISAI_GAPPI,
            u.KAKUTEI_CHAKUJUN as finish,
            u.TANSHO_ODDS as odds,
            u.TANSHO_NINKIJUN as popularity,
            u.FUTAN_JURYO as weight,
            u.BATAIJU as horse_weight,
            u.ZOGEN_SA as weight_change,
            u.KISHUMEI_RYAKUSHO as jockey,
            u.CHOKYOSHIMEI_RYAKUSHO as trainer,
            u.CORNER1_JUNI,
            u.CORNER2_JUNI,
            u.CORNER3_JUNI,
            u.CORNER4_JUNI,
            u.SOHA_TIME as time,
            u.BAREI as age,
            u.SEIBETSU_CODE as sex,
            r.KYORI as distance,
            r.TRACK_CODE as track
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
        WHERE u.BAMEI = %s
        AND u.KAISAI_NEN IS NOT NULL
        ORDER BY u.KAISAI_NEN DESC, u.KAISAI_GAPPI DESC
        LIMIT 5
    """, (horse_name,))
    
    race_history = []
    for race in races:
        if race.get("finish") and str(race["finish"]).isdigit():
            race_data = {
                "race_code": race.get("RACE_CODE"),
                "date": f"{race.get('KAISAI_NEN', '')}{race.get('KAISAI_GAPPI', '')}" if race.get('KAISAI_NEN') and race.get('KAISAI_GAPPI') else None,
                "finish": int(race["finish"]),
                "odds": float(race["odds"]) / 10 if race.get("odds") and str(race["odds"]).isdigit() else None,
                "popularity": int(race["popularity"]) if race.get("popularity") and str(race["popularity"]).isdigit() else None,
                "weight": int(race["weight"]) if race.get("weight") and str(race["weight"]).isdigit() else None,
                "horse_weight": int(race["horse_weight"]) if race.get("horse_weight") and str(race["horse_weight"]).isdigit() else None,
                "weight_change": race.get("weight_change"),
                "jockey": race.get("jockey"),
                "trainer": race.get("trainer"),
                "corner_positions": [],
                "time": float(race["time"]) / 10 if race.get("time") and str(race["time"]).isdigit() else None,
                "age": int(race["age"]) if race.get("age") and str(race["age"]).isdigit() else None,
                "sex": race.get("sex"),
                "distance": int(race["distance"]) if race.get("distance") and str(race["distance"]).isdigit() else None,
                "track": race.get("track")
            }
            
            # コーナー順位
            for i in range(1, 5):
                corner = race.get(f"CORNER{i}_JUNI")
                if corner and str(corner).isdigit():
                    race_data["corner_positions"].append(int(corner))
            
            race_history.append(race_data)
    
    if not race_history:
        return None
    
    # 基本情報
    latest = race_history[0]
    basic_info = {
        "sex": latest.get("sex"),
        "age": latest.get("age"),
        "last_race_date": latest.get("date")
    }
    
    return {
        "basic_info": basic_info,
        "race_history": race_history[:5]  # 最大5走分
    }

if __name__ == "__main__":
    main()