"""
G1レースの詳細調査と純粋なJRA G1レースの識別
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

def debug_g1_detailed():
    """G1レースの詳細調査"""
    connection = get_mysql_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        
        print("=== 2022-2024年のG1レース詳細分析 ===")
        
        # 2022-2024年のG1レース（GRADE_CODE = 'A'）を全て取得
        cursor.execute("""
            SELECT 
                RACE_CODE,
                KAISAI_NEN,
                KAISAI_GAPPI,
                KEIBAJO_CODE,
                RACE_BANGO,
                KYOSOMEI_HONDAI,
                GRADE_CODE,
                SHUSSO_TOSU,
                KYOSOMEI_FUKUDAI,
                KYOSOMEI_KAKKONAI
            FROM race_shosai 
            WHERE GRADE_CODE = 'A' 
            AND KAISAI_NEN IN ('2022', '2023', '2024')
            ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC
        """)
        g1_races = cursor.fetchall()
        
        print(f"2022-2024年のG1レース総数: {len(g1_races)}件")
        print("\n=== レース名による分類 ===")
        
        # レース名による分類
        jra_g1_races = []
        jpn1_races = []
        downgraded_races = []
        other_races = []
        
        for race in g1_races:
            race_name = race['KYOSOMEI_HONDAI']
            sub_title = race['KYOSOMEI_FUKUDAI']
            additional = race['KYOSOMEI_KAKKONAI']
            
            # 地方競馬のJpn1を除外
            if '中央交流' in race_name or 'Ｊｐｎ１' in race_name or 'Jpn1' in race_name:
                jpn1_races.append(race)
            # 格下げされたレースを除外
            elif 'ホープフルステークス' in race_name:
                downgraded_races.append(race)
            # 純粋なJRA G1レース
            else:
                jra_g1_races.append(race)
        
        print(f"純粋なJRA G1レース: {len(jra_g1_races)}件")
        print(f"地方競馬Jpn1: {len(jpn1_races)}件")
        print(f"格下げされたレース: {len(downgraded_races)}件")
        
        print("\n=== 純粋なJRA G1レース一覧 ===")
        for race in jra_g1_races:
            print(f"  {race['KAISAI_NEN']}年{race['KAISAI_GAPPI']} - {race['KYOSOMEI_HONDAI']}")
        
        print("\n=== 地方競馬Jpn1一覧 ===")
        for race in jpn1_races:
            print(f"  {race['KAISAI_NEN']}年{race['KAISAI_GAPPI']} - {race['KYOSOMEI_HONDAI']}")
        
        print("\n=== 格下げされたレース一覧 ===")
        for race in downgraded_races:
            print(f"  {race['KAISAI_NEN']}年{race['KAISAI_GAPPI']} - {race['KYOSOMEI_HONDAI']}")
        
        print("\n=== 競馬場別分析 ===")
        
        # 競馬場別の分析
        keibajo_analysis = {}
        for race in jra_g1_races:
            keibajo_code = race['KEIBAJO_CODE']
            if keibajo_code not in keibajo_analysis:
                keibajo_analysis[keibajo_code] = []
            keibajo_analysis[keibajo_code].append(race)
        
        keibajo_names = {
            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟', '05': '東京',
            '06': '中山', '07': '中京', '08': '京都', '09': '阪神', '10': '小倉'
        }
        
        for keibajo_code, races in keibajo_analysis.items():
            keibajo_name = keibajo_names.get(keibajo_code, f"競馬場{keibajo_code}")
            print(f"  {keibajo_name}: {len(races)}件")
        
        print(f"\n=== 年別分析 ===")
        
        # 年別の分析
        year_analysis = {}
        for race in jra_g1_races:
            year = race['KAISAI_NEN']
            if year not in year_analysis:
                year_analysis[year] = []
            year_analysis[year].append(race)
        
        for year, races in year_analysis.items():
            print(f"  {year}年: {len(races)}件")
        
        return len(jra_g1_races)
        
    except Exception as e:
        print(f"エラー: {e}")
        return 0
    finally:
        if connection.is_connected():
            connection.close()

if __name__ == "__main__":
    debug_g1_detailed() 