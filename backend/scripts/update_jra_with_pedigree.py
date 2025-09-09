#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JRAナレッジファイルに父名と母父名を追加（最終版）
"""

import json
import psycopg2
import sys
import io
import time

# Windows環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# データベース接続情報
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

def update_with_pedigree():
    """既存のJRAナレッジファイルに父名と母父名を追加"""
    
    print("=" * 80)
    print("🐴 父名・母父名データの追加（最終版）")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 既存ファイルを読み込み
        input_file = "jra_knowledge_quality_20250907.json"
        print(f"\n📁 ファイル読み込み: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            horses_data = json.load(f)
        
        print(f"✅ {len(horses_data)}頭のデータ読み込み完了")
        
        # PostgreSQL接続
        print("\n📊 PostgreSQL接続中...")
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 血統データを取得
        print("\n🔍 血統データ取得中...")
        
        updated_count = 0
        missing_count = 0
        
        for horse_name, races in horses_data.items():
            if races and len(races) > 0:
                # 最初のレースから血統登録番号を取得
                ketto_bango = races[0].get('KETTO_TOROKU_BANGO')
                
                if ketto_bango and ketto_bango != '0000000000':
                    # 父名と母父名を取得
                    cur.execute("""
                        SELECT 
                            ketto_joho_01b as sire_name,
                            ketto_joho_02b as broodmare_sire_name
                        FROM jvd_um
                        WHERE ketto_toroku_bango = %s
                    """, (ketto_bango,))
                    
                    result = cur.fetchone()
                    if result:
                        sire_name = result[0].strip() if result[0] else ""
                        broodmare_sire_name = result[1].strip() if result[1] else ""
                        
                        # すべてのレースに血統情報を追加
                        for race in races:
                            race['sire'] = sire_name
                            race['broodmare_sire'] = broodmare_sire_name
                            # damは空欄のまま（統合ナレッジでは不要）
                        
                        if sire_name or broodmare_sire_name:
                            updated_count += 1
                    else:
                        missing_count += 1
                        
                if updated_count % 1000 == 0:
                    print(f"  {updated_count}頭処理済み...")
        
        print(f"\n✅ {updated_count}頭の血統情報を追加")
        print(f"⚠️ {missing_count}頭はデータなし")
        
        # 更新版を保存
        output_file = "jra_knowledge_complete_20250907.json"
        print(f"\n💾 完全版ファイル保存中: {output_file}")
        
        save_start = time.time()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(horses_data, f, ensure_ascii=False, indent=2)
        save_end = time.time()
        
        print(f"✅ 保存完了！（{save_end - save_start:.2f}秒）")
        
        # サンプル表示
        print("\n【サンプル確認】")
        sample_horses = list(horses_data.keys())[:5]
        for horse_name in sample_horses:
            if horses_data[horse_name]:
                race = horses_data[horse_name][0]
                sire = race.get('sire', '')
                broodmare_sire = race.get('broodmare_sire', '')
                print(f"  {horse_name}:")
                print(f"    父: {sire if sire else '不明'}")
                print(f"    母父: {broodmare_sire if broodmare_sire else '不明'}")
        
        cur.close()
        conn.close()
        
        total_time = time.time() - start_time
        
        # ファイルサイズ確認
        import os
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        
        print("\n" + "=" * 80)
        print("🎉 完全版JRAナレッジファイル作成完了！")
        print("=" * 80)
        print(f"✅ ファイル名: {output_file}")
        print(f"✅ ファイルサイズ: {file_size:.1f}MB")
        print(f"✅ 処理時間: {total_time:.2f}秒")
        print(f"✅ 血統情報追加: {updated_count}頭")
        print("\n【データ品質】")
        print("• 国内JRAレースのみ")
        print("• 海外馬除外済み")
        print("• 父名・母父名追加済み")
        print("• ViewLogicエンジン対応完了")
        
    except Exception as e:
        import traceback
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")

if __name__ == "__main__":
    update_with_pedigree()