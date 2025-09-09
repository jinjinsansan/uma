#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JRAデータの品質チェック - 欠損データの詳細調査
"""

import psycopg2
import json
import sys
import io

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

def check_data_quality():
    """JRAデータの品質を詳細にチェック"""
    
    print("=" * 80)
    print("🔍 JRAデータ品質チェック - 重要フィールドの欠損状況")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 1. 重要フィールドの欠損率チェック
        print("\n【1. 重要フィールドの欠損状況】")
        print("-" * 60)
        
        important_fields = [
            ('tansho_odds', '単勝オッズ'),
            ('tansho_ninkijun', '単勝人気順'),
            ('bataiju', '馬体重'),
            ('zogen_sa', '増減差'),
            ('corner_1', 'コーナー1'),
            ('corner_2', 'コーナー2'),
            ('corner_3', 'コーナー3'),
            ('corner_4', 'コーナー4'),
            ('soha_time', '走破タイム'),
            ('time_sa', 'タイム差'),
            ('ketto_toroku_bango', '血統登録番号')
        ]
        
        for field, label in important_fields:
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN {field} IS NULL THEN 1 ELSE 0 END) as null_count,
                    SUM(CASE WHEN {field} = '' THEN 1 ELSE 0 END) as empty_count,
                    SUM(CASE WHEN {field} = '0' OR {field} = '00' OR {field} = '000' OR {field} = '0000' THEN 1 ELSE 0 END) as zero_count
                FROM jvd_se
                WHERE kaisai_nen IN ('2023', '2024')
            """)
            
            result = cur.fetchone()
            if result:
                total = result[0]
                null_pct = (result[1] / total * 100) if total > 0 else 0
                empty_pct = (result[2] / total * 100) if total > 0 else 0
                zero_pct = (result[3] / total * 100) if total > 0 else 0
                valid_pct = 100 - null_pct - empty_pct - zero_pct
                
                print(f"\n{label} ({field}):")
                print(f"  NULL: {null_pct:.1f}%")
                print(f"  空文字: {empty_pct:.1f}%")
                print(f"  ゼロ値: {zero_pct:.1f}%")
                print(f"  ✅ 有効値: {valid_pct:.1f}%")
        
        # 2. 血統情報（jvd_umテーブル）のチェック
        print("\n" + "=" * 60)
        print("【2. 血統情報（jvd_umテーブル）の状況】")
        print("-" * 60)
        
        cur.execute("""
            SELECT 
                COUNT(DISTINCT se.ketto_toroku_bango) as total_horses,
                COUNT(DISTINCT um.ketto_toroku_bango) as horses_with_pedigree
            FROM jvd_se se
            LEFT JOIN jvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
            WHERE se.kaisai_nen IN ('2023', '2024')
        """)
        
        result = cur.fetchone()
        if result:
            total = result[0]
            with_pedigree = result[1] if result[1] else 0
            print(f"総馬数: {total:,}")
            print(f"血統情報あり: {with_pedigree:,} ({with_pedigree/total*100:.1f}%)")
            print(f"血統情報なし: {total - with_pedigree:,} ({(total-with_pedigree)/total*100:.1f}%)")
        
        # 3. 実際の血統データサンプル
        print("\n【3. 血統データがある馬のサンプル】")
        print("-" * 60)
        
        cur.execute("""
            SELECT 
                se.bamei,
                um.ketto_joho_01a as sire,
                um.ketto_joho_01b as dam,
                um.ketto_joho_02a as broodmare_sire
            FROM jvd_se se
            JOIN jvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
            WHERE se.kaisai_nen = '2024'
            AND um.ketto_joho_01a IS NOT NULL
            AND um.ketto_joho_01a != ''
            LIMIT 5
        """)
        
        results = cur.fetchall()
        if results:
            for row in results:
                print(f"\n馬名: {row[0].strip()}")
                print(f"  父: {row[1]}")
                print(f"  母: {row[2]}")
                print(f"  母父: {row[3]}")
        else:
            print("❌ 血統データが見つかりません")
        
        # 4. ketto_toroku_bangoの問題を調査
        print("\n【4. 血統登録番号の問題調査】")
        print("-" * 60)
        
        cur.execute("""
            SELECT 
                ketto_toroku_bango,
                COUNT(*) as count
            FROM jvd_se
            WHERE kaisai_nen = '2024'
            GROUP BY ketto_toroku_bango
            ORDER BY count DESC
            LIMIT 5
        """)
        
        results = cur.fetchall()
        print("最も頻出する血統登録番号:")
        for row in results:
            print(f"  {row[0]}: {row[1]}件")
        
        # 5. 正常なデータの例を探す
        print("\n【5. すべてのデータが揃っている馬の例】")
        print("-" * 60)
        
        cur.execute("""
            SELECT 
                se.bamei,
                se.tansho_odds,
                se.tansho_ninkijun,
                se.corner_1,
                se.corner_4,
                se.soha_time,
                um.ketto_joho_01a
            FROM jvd_se se
            LEFT JOIN jvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
            WHERE se.kaisai_nen = '2024'
            AND se.tansho_odds IS NOT NULL AND se.tansho_odds != '0000'
            AND se.corner_1 IS NOT NULL AND se.corner_1 != '00'
            AND um.ketto_joho_01a IS NOT NULL
            LIMIT 3
        """)
        
        results = cur.fetchall()
        if results:
            for row in results:
                print(f"\n馬名: {row[0].strip()}")
                print(f"  単勝オッズ: {row[1]}")
                print(f"  人気順: {row[2]}")
                print(f"  1角: {row[3]}, 4角: {row[4]}")
                print(f"  走破タイム: {row[5]}")
                print(f"  父: {row[6]}")
        else:
            print("⚠️ 完全なデータを持つ馬が見つかりません")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        import traceback
        print(f"エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")

def check_existing_json():
    """作成済みJSONファイルの品質確認"""
    print("\n" + "=" * 80)
    print("📄 作成済みJSONファイルの品質確認")
    print("=" * 80)
    
    json_file = "/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/jra_knowledge_test_20250907.json"
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # サンプル馬のデータ品質確認
    sample_horses = list(data.keys())[:3]
    
    for horse in sample_horses:
        races = data[horse]
        if races:
            race = races[0]
            print(f"\n馬名: {horse}")
            print(f"  データ数: {len(races)}走")
            
            # 欠損フィールドをチェック
            missing = []
            zeros = []
            
            for key, value in race.items():
                if value == "" or value is None:
                    missing.append(key)
                elif value in ["0", "00", "000", "0000", "0000000000"]:
                    zeros.append(key)
            
            if missing:
                print(f"  ❌ 空欄フィールド: {', '.join(missing)}")
            if zeros:
                print(f"  ⚠️ ゼロ値フィールド: {', '.join(zeros)}")
            
            if not missing and not zeros:
                print(f"  ✅ 全フィールド有効")

if __name__ == "__main__":
    check_data_quality()
    check_existing_json()