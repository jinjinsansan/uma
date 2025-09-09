#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地方競馬PostgreSQLデータベース構造調査スクリプト
"""

import psycopg2
import json
import sys
import io
from datetime import datetime

# Windows環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# データベース接続情報
# WSLからWindowsホストのPostgreSQLに接続
import subprocess
result = subprocess.run(['cat', '/etc/resolv.conf'], capture_output=True, text=True)
windows_host = None
for line in result.stdout.split('\n'):
    if 'nameserver' in line:
        windows_host = line.split()[1]
        break

# 複数の接続先を試す
possible_hosts = [
    "172.25.160.1",  # 典型的なWSL2 Windows host IP
    "172.25.176.1",  # 別のWSL2 Windows host IP
    "192.168.1.1",   # ローカルネットワーク
    "localhost",     # localhost
    windows_host,     # resolv.confから取得したIP
]

CONNECTION_PARAMS = {
    "host": "172.25.160.1",  # まず最も一般的なWSL2 host IPを試す
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

# 南関東競馬場コード
NANKAN_CODES = ['42', '43', '44', '45']  # 浦和、船橋、大井、川崎

def check_connection():
    """データベース接続確認"""
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        print("✅ PostgreSQL接続成功！")
        print(f"   Database: {CONNECTION_PARAMS['database']}")
        print(f"   Host: {CONNECTION_PARAMS['host']}:{CONNECTION_PARAMS['port']}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        return False

def analyze_table_structure(table_name, limit=5):
    """テーブル構造を分析"""
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # カラム情報取得
        cur.execute(f"""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        
        # レコード数取得
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        record_count = cur.fetchone()[0]
        
        # サンプルデータ取得
        cur.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        sample_data = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "columns": columns,
            "record_count": record_count,
            "sample_data": sample_data
        }
    except Exception as e:
        print(f"エラー ({table_name}): {e}")
        return None

def check_nankan_races():
    """南関東のレースデータを確認"""
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # 南関東の最新レースを取得
        cur.execute("""
            SELECT 
                kaisai_nen,
                kaisai_tsukihi,
                keibajo_code,
                race_bango,
                kyori,
                track_code
            FROM nvd_ra
            WHERE keibajo_code IN ('42', '43', '44', '45')
                AND kaisai_nen >= '2024'
            ORDER BY kaisai_nen DESC, kaisai_tsukihi DESC
            LIMIT 10
        """)
        
        races = cur.fetchall()
        
        # 競馬場別の集計
        cur.execute("""
            SELECT 
                keibajo_code,
                COUNT(*) as race_count
            FROM nvd_ra
            WHERE keibajo_code IN ('42', '43', '44', '45')
                AND kaisai_nen >= '2020'
            GROUP BY keibajo_code
            ORDER BY keibajo_code
        """)
        
        stats = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {"recent_races": races, "statistics": stats}
    except Exception as e:
        print(f"エラー: {e}")
        return None

def compare_with_jra_structure():
    """JRAとの構造比較用データ取得"""
    try:
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # nvd_seテーブルのカラムを確認（JRAの統合ナレッジに相当）
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'nvd_se'
            ORDER BY ordinal_position
        """)
        
        nar_columns = [col[0] for col in cur.fetchall()]
        
        # サンプルデータ取得（南関東の馬1頭）
        cur.execute("""
            SELECT DISTINCT ketto_toroku_bango, bamei
            FROM nvd_se
            WHERE keibajo_code IN ('42', '43', '44', '45')
                AND kaisai_nen >= '2024'
                AND bamei IS NOT NULL
                AND bamei != ''
            LIMIT 1
        """)
        
        sample_horse = cur.fetchone()
        
        if sample_horse:
            horse_id, horse_name = sample_horse
            
            # その馬の直近5走を取得
            cur.execute("""
                SELECT se.*, ra.kyori, ra.track_code, ra.tenko_code
                FROM nvd_se se
                JOIN nvd_ra ra ON (
                    se.kaisai_nen = ra.kaisai_nen
                    AND se.kaisai_tsukihi = ra.kaisai_tsukihi
                    AND se.keibajo_code = ra.keibajo_code
                    AND se.race_bango = ra.race_bango
                )
                WHERE se.ketto_toroku_bango = %s
                ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC
                LIMIT 5
            """, (horse_id,))
            
            horse_races = cur.fetchall()
            
            # カラム名を取得
            col_names = [desc[0] for desc in cur.description]
            
            cur.close()
            conn.close()
            
            return {
                "nar_columns": nar_columns,
                "sample_horse": {
                    "id": horse_id,
                    "name": horse_name,
                    "races": [dict(zip(col_names, race)) for race in horse_races]
                }
            }
        
        cur.close()
        conn.close()
        return {"nar_columns": nar_columns, "sample_horse": None}
        
    except Exception as e:
        print(f"エラー: {e}")
        return None

def main():
    """メイン処理"""
    print("=" * 60)
    print("地方競馬データベース構造調査")
    print("=" * 60)
    
    # 1. 接続確認
    if not check_connection():
        return
    
    print("\n" + "=" * 60)
    print("主要テーブル構造分析")
    print("=" * 60)
    
    # 2. 主要テーブルの調査
    tables = ['nvd_ra', 'nvd_se', 'nvd_um', 'nvd_ks']
    
    for table in tables:
        print(f"\n【{table}テーブル】")
        result = analyze_table_structure(table, limit=2)
        if result:
            print(f"  レコード数: {result['record_count']:,}")
            print(f"  カラム数: {len(result['columns'])}")
            print("  主要カラム:")
            for col in result['columns'][:10]:  # 最初の10カラムのみ表示
                print(f"    - {col[0]}: {col[1]}")
    
    print("\n" + "=" * 60)
    print("南関東データ確認")
    print("=" * 60)
    
    # 3. 南関東のデータ確認
    nankan_data = check_nankan_races()
    if nankan_data:
        print("\n【南関東の最新レース】")
        for race in nankan_data['recent_races'][:5]:
            print(f"  {race[0]}年{race[1]} 競馬場:{race[2]} R{race[3]} {race[4]}m")
        
        print("\n【南関東の競馬場別レース数（2020年以降）】")
        course_names = {'42': '浦和', '43': '船橋', '44': '大井', '45': '川崎'}
        for stat in nankan_data['statistics']:
            print(f"  {course_names.get(stat[0], stat[0])}: {stat[1]:,}レース")
    
    print("\n" + "=" * 60)
    print("JRAとの構造比較")
    print("=" * 60)
    
    # 4. JRAとの構造比較
    comparison = compare_with_jra_structure()
    if comparison:
        print(f"\n【nvd_seテーブル（出走情報）のカラム数】: {len(comparison['nar_columns'])}")
        
        if comparison['sample_horse']:
            horse = comparison['sample_horse']
            print(f"\n【サンプル馬データ】")
            print(f"  馬名: {horse['name']}")
            print(f"  ID: {horse['id']}")
            print(f"  収録レース数: {len(horse['races'])}")
            
            if horse['races']:
                print("\n  最新レースのデータ構造:")
                race = horse['races'][0]
                for key, value in list(race.items())[:20]:  # 最初の20項目
                    print(f"    {key}: {value}")
    
    # 5. 結果をファイルに保存
    report = {
        "調査日時": datetime.now().isoformat(),
        "データベース": CONNECTION_PARAMS['database'],
        "南関東データ": nankan_data,
        "構造比較": comparison
    }
    
    with open('nar_database_structure.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n✅ 調査完了！結果をnar_database_structure.jsonに保存しました。")

if __name__ == "__main__":
    main()