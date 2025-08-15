import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime

def connect_to_database():
    """MySQLデータベースに接続"""
    try:
        connection = mysql.connector.connect(
            host='172.25.160.1',  # Renderから接続する場合のIP
            database='mykeibadb',
            user='root',
            password='root1234',
            port=3306,
            charset='utf8mb4'
        )
        return connection
    except Error as e:
        print(f"データベース接続エラー: {e}")
        return None

def investigate_tables(connection):
    """データベースのテーブル構造を調査"""
    cursor = connection.cursor()
    
    print("=== データベーステーブル一覧 ===")
    
    # 全テーブルを取得
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    jockey_related_tables = []
    race_related_tables = []
    
    for table in tables:
        table_name = table[0]
        print(f"\nテーブル: {table_name}")
        
        # テーブルの列情報を取得
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = cursor.fetchall()
        
        # 騎手関連のテーブルを探す
        if 'jockey' in table_name.lower() or 'kishu' in table_name.lower() or '騎手' in table_name:
            jockey_related_tables.append(table_name)
            print("  [騎手関連テーブル]")
        
        # レース関連のテーブルを探す
        if 'race' in table_name.lower() or 'result' in table_name.lower() or 'レース' in table_name or 'n_uma_race' in table_name:
            race_related_tables.append(table_name)
            print("  [レース関連テーブル]")
        
        # 列情報を表示
        for column in columns[:10]:  # 最初の10列のみ表示
            col_name = column[0]
            col_type = column[1]
            print(f"    - {col_name}: {col_type}")
        
        if len(columns) > 10:
            print(f"    ... 他 {len(columns) - 10} 列")
    
    print("\n=== 騎手関連の可能性があるテーブル ===")
    for table in jockey_related_tables:
        print(f"  - {table}")
        # サンプルデータを取得
        cursor.execute(f"SELECT * FROM {table} LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            print(f"    サンプルデータ: {len(rows)}件")
    
    print("\n=== レース関連の可能性があるテーブル ===")
    for table in race_related_tables:
        print(f"  - {table}")
        # レコード数を確認
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"    レコード数: {count:,}")
    
    # 騎手情報を含む可能性のある列を探す
    print("\n=== 騎手情報を含む可能性のある列を検索 ===")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = cursor.fetchall()
        
        for column in columns:
            col_name = column[0].lower()
            if any(keyword in col_name for keyword in ['jockey', 'kishu', '騎手', 'rider', 'kishumei']):
                print(f"  {table_name}.{column[0]} ({column[1]})")

def find_jockey_data_pattern(connection):
    """n_uma_raceテーブルから騎手データのパターンを探す"""
    cursor = connection.cursor()
    
    print("\n=== n_uma_race テーブルの騎手データパターン調査 ===")
    
    # n_uma_raceテーブルの構造を確認
    cursor.execute("DESCRIBE n_uma_race")
    columns = cursor.fetchall()
    print("\nn_uma_race テーブルの列（騎手関連）:")
    for col in columns:
        col_name = col[0].lower()
        if any(keyword in col_name for keyword in ['kishu', 'jockey', '騎手']):
            print(f"  {col[0]}: {col[1]}")
    
    # サンプルデータを取得（2020年以降）
    query = """
    SELECT 
        year, monthday, jyocd, kaiji, nichiji, racenum,
        kettonum, bamei, 
        kishumei, kishumei_ryakusho,
        kakuteijyuni, jyuni1c
    FROM n_uma_race
    WHERE year >= 2020
    AND kishumei IS NOT NULL
    AND kishumei != ''
    LIMIT 10
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print("\nサンプルデータ（騎手関連）:")
    for row in rows:
        print(f"  {row[0]}年 {row[7]}(馬名) - {row[8]}(騎手) - {row[10]}着")
    
    # 主要騎手のデータ数を確認
    print("\n=== 主要騎手のデータ数（2020年以降）===")
    query = """
    SELECT kishumei, COUNT(*) as ride_count
    FROM n_uma_race
    WHERE year >= 2020
    AND kishumei IS NOT NULL
    AND kishumei != ''
    GROUP BY kishumei
    ORDER BY ride_count DESC
    LIMIT 20
    """
    
    cursor.execute(query)
    jockeys = cursor.fetchall()
    
    for jockey, count in jockeys:
        print(f"  {jockey}: {count:,} 騎乗")

def main():
    """メイン処理"""
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        print("MySQLデータベース調査開始...")
        print(f"データベース: mykeibadb")
        print("-" * 50)
        
        # テーブル構造を調査
        investigate_tables(connection)
        
        # n_uma_raceテーブルから騎手データパターンを調査
        find_jockey_data_pattern(connection)
        
    except Error as e:
        print(f"エラー: {e}")
    finally:
        if connection.is_connected():
            connection.close()
            print("\nデータベース接続を閉じました")

if __name__ == "__main__":
    main()