"""
G1レースデータの存在確認とデータベース構造調査
"""

import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# MySQL接続設定
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'mykeibadb'),
    'charset': 'utf8mb4'
}

def get_mysql_connection():
    """MySQL接続を取得"""
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        if connection.is_connected():
            return connection
        else:
            raise Exception("MySQL connection failed")
    except mysql.connector.Error as e:
        raise Exception(f"Database connection error: {str(e)}")

def debug_g1_data():
    """G1レースデータの存在確認とデータベース構造調査"""
    connection = get_mysql_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        
        print("=== GRADE_CODEの詳細分析 ===")
        
        # 各GRADE_CODEの件数とサンプルデータを確認
        grade_codes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'L']
        
        for grade in grade_codes:
            # 件数確認
            cursor.execute(f"SELECT COUNT(*) as count FROM race_shosai WHERE GRADE_CODE = '{grade}'")
            result = cursor.fetchone()
            count = result['count']
            
            print(f"\nGRADE_CODE = '{grade}' の件数: {count}")
            
            if count > 0:
                # サンプルデータ確認
                cursor.execute(f"""
                    SELECT 
                        RACE_CODE,
                        KAISAI_NEN,
                        KAISAI_GAPPI,
                        KEIBAJO_CODE,
                        RACE_BANGO,
                        KYOSOMEI_HONDAI,
                        GRADE_CODE,
                        SHUSSO_TOSU
                    FROM race_shosai 
                    WHERE GRADE_CODE = '{grade}' 
                    ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC
                    LIMIT 3
                """)
                sample_races = cursor.fetchall()
                
                print(f"  サンプルデータ:")
                for race in sample_races:
                    print(f"    {race['KAISAI_NEN']}年{race['KAISAI_GAPPI']} - {race['KYOSOMEI_HONDAI']} ({race['GRADE_CODE']})")
        
        print("\n=== 2022-2024年のデータ確認 ===")
        
        # 2022-2024年のデータで各GRADE_CODEの件数を確認
        for grade in grade_codes:
            cursor.execute(f"""
                SELECT COUNT(*) as count 
                FROM race_shosai 
                WHERE GRADE_CODE = '{grade}' 
                AND KAISAI_NEN IN ('2022', '2023', '2024')
            """)
            result = cursor.fetchone()
            count = result['count']
            
            if count > 0:
                print(f"GRADE_CODE = '{grade}' (2022-2024年): {count}件")
                
                # サンプルデータ確認
                cursor.execute(f"""
                    SELECT 
                        RACE_CODE,
                        KAISAI_NEN,
                        KAISAI_GAPPI,
                        KEIBAJO_CODE,
                        RACE_BANGO,
                        KYOSOMEI_HONDAI,
                        GRADE_CODE,
                        SHUSSO_TOSU
                    FROM race_shosai 
                    WHERE GRADE_CODE = '{grade}' 
                    AND KAISAI_NEN IN ('2022', '2023', '2024')
                    ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC
                    LIMIT 2
                """)
                sample_races = cursor.fetchall()
                
                for race in sample_races:
                    print(f"  {race['KAISAI_NEN']}年{race['KAISAI_GAPPI']} - {race['KYOSOMEI_HONDAI']}")
        
        print("\n=== 全期間の総件数確認 ===")
        
        # 全期間の総件数
        cursor.execute("SELECT COUNT(*) as count FROM race_shosai")
        total_count = cursor.fetchone()['count']
        print(f"全レース件数: {total_count}")
        
        # 2022-2024年の総件数
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM race_shosai 
            WHERE KAISAI_NEN IN ('2022', '2023', '2024')
        """)
        recent_count = cursor.fetchone()['count']
        print(f"2022-2024年のレース件数: {recent_count}")
        
        # GRADE_CODEが設定されている件数
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM race_shosai 
            WHERE GRADE_CODE IS NOT NULL AND GRADE_CODE != ''
        """)
        grade_count = cursor.fetchone()['count']
        print(f"GRADE_CODEが設定されている件数: {grade_count}")
        
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        if connection.is_connected():
            connection.close()

if __name__ == "__main__":
    debug_g1_data() 