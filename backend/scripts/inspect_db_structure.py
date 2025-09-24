#!/usr/bin/env python3
"""
PostgreSQLのテーブル構造を調査
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def main():
    try:
        # 接続パラメータ
        conn = psycopg2.connect(
            host='172.25.160.1',
            port=5432,
            database='keiba_dw',
            user='postgres',
            password='admin'
        )
        
        # エンコーディング設定
        conn.set_client_encoding('UTF8')
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print("="*80)
            print("PostgreSQL テーブル構造調査")
            print("="*80)
            
            # 1. jvd_seテーブルのカラム調査
            print("\n【1. jvd_seテーブル】")
            cur.execute("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'jvd_se'
                AND (
                    column_name LIKE '%3f%' 
                    OR column_name LIKE '%3F%'
                    OR column_name LIKE '%kohan%'
                    OR column_name LIKE '%zenhan%'
                    OR column_name LIKE '%dochaku%'
                    OR column_name LIKE '%tosu%'
                )
                ORDER BY ordinal_position
            """)
            
            se_columns = cur.fetchall()
            if se_columns:
                for col in se_columns:
                    print(f"  - {col['column_name']}: {col['data_type']}")
            else:
                print("  該当カラムなし")
            
            # 2. jvd_raテーブルのカラム調査
            print("\n【2. jvd_raテーブル】")
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'jvd_ra'
                AND (
                    column_name LIKE '%3f%' 
                    OR column_name LIKE '%3F%'
                    OR column_name LIKE '%kohan%'
                    OR column_name LIKE '%zenhan%'
                    OR column_name LIKE '%race%'
                    OR column_name LIKE '%kyosomei%'
                    OR column_name LIKE '%grade%'
                )
                ORDER BY ordinal_position
            """)
            
            ra_columns = cur.fetchall()
            if ra_columns:
                for col in ra_columns:
                    print(f"  - {col['column_name']}: {col['data_type']}")
            else:
                print("  該当カラムなし")
            
            # 3. jvd_umテーブルの血統カラム調査
            print("\n【3. jvd_umテーブル（血統）】")
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'jvd_um'
                AND column_name LIKE 'ketto%'
                ORDER BY column_name
            """)
            
            um_columns = cur.fetchall()
            if um_columns:
                for col in um_columns:
                    print(f"  - {col['column_name']}: {col['data_type']}")
            else:
                print("  該当カラムなし")
            
            # 4. 実際のデータでカラム内容を確認（jvd_ra）
            print("\n【4. jvd_raテーブルの実データサンプル（2025年）】")
            cur.execute("""
                SELECT *
                FROM jvd_ra
                WHERE kaisai_nen = '2025'
                AND kaisai_tsukihi IN ('0920', '0921')
                LIMIT 1
            """)
            
            ra_sample = cur.fetchone()
            if ra_sample:
                # 3F関連のカラムだけ表示
                for key, value in ra_sample.items():
                    if '3f' in key.lower() or 'kohan' in key.lower() or 'zenhan' in key.lower():
                        print(f"  - {key}: {value}")
            
            # 5. 実際のデータでカラム内容を確認（jvd_se）
            print("\n【5. jvd_seテーブルの実データサンプル（2025年）】")
            cur.execute("""
                SELECT *
                FROM jvd_se
                WHERE kaisai_nen = '2025'
                AND kaisai_tsukihi IN ('0920', '0921')
                AND bamei IS NOT NULL
                LIMIT 1
            """)
            
            se_sample = cur.fetchone()
            if se_sample:
                # 3F関連のカラムだけ表示
                for key, value in se_sample.items():
                    if '3f' in key.lower() or 'kohan' in key.lower() or 'zenhan' in key.lower():
                        print(f"  - {key}: {value}")
            
            # 6. テーブル一覧確認（race_shosai、kyosoba_master2の存在確認）
            print("\n【6. その他のテーブル存在確認】")
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND (
                    table_name LIKE '%race_shosai%'
                    OR table_name LIKE '%kyosoba%'
                    OR table_name LIKE '%master%'
                )
                ORDER BY table_name
            """)
            
            other_tables = cur.fetchall()
            if other_tables:
                for table in other_tables:
                    print(f"  - {table['table_name']}")
            else:
                print("  該当テーブルなし")
                
        print("\n" + "="*80)
        print("調査完了")
        print("="*80)
        
    except psycopg2.OperationalError as e:
        print(f"接続エラー: {e}")
        print("\n代替案: SQLクエリだけ生成します")
        print("以下のSQLを手動で実行してください：")
        print("""
-- jvd_seテーブルのカラム確認
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'jvd_se' 
AND (column_name LIKE '%3f%' OR column_name LIKE '%kohan%');

-- jvd_raテーブルのカラム確認
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'jvd_ra' 
AND (column_name LIKE '%3f%' OR column_name LIKE '%zenhan%');
        """)
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()