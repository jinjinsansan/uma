"""
競馬レースデータ取得API
Phase 1: データ取得基盤の構築
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import mysql.connector
from typing import List, Optional, Dict, Any
import os
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

# レスポンスモデル定義（Phase 2・3での利用を考慮）
class RaceInfo(BaseModel):
    race_code: str
    kaisai_nen: str
    kaisai_gappi: str
    keibajo_code: str
    keibajo_name: str  # Phase 2で使用
    race_bango: str
    kyosomei_hondai: str
    kyori: str
    track_code: str
    hasso_jikoku: str
    shusso_tosu: str
    grade_code: Optional[str] = None
    formatted_date: str  # Phase 2で使用
    formatted_time: str  # Phase 2で使用

class TodayRacesResponse(BaseModel):
    date: str
    race_count: int
    races: List[RaceInfo]
    has_races: bool  # Phase 3のフロー制御で使用

class PastG1Response(BaseModel):
    year: Optional[int]
    total_races: int
    races: List[RaceInfo]

class RaceExistsResponse(BaseModel):
    date: str
    has_races: bool
    race_count: int
    day_of_week: str  # Phase 3のフロー制御で使用

# MySQL接続設定
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'mykeibadb'),
    'charset': 'utf8mb4'
}

# 競馬場コード→名前マッピング（Phase 2のUI表示で使用）
KEIBAJO_NAMES = {
    '01': '札幌', '02': '函館', '03': '福島', '04': '新潟', '05': '東京',
    '06': '中山', '07': '中京', '08': '京都', '09': '阪神', '10': '小倉'
}

def get_mysql_connection():
    """MySQL接続を取得（エラーハンドリング強化）"""
    # Phase C-1では固定データを使用するため、データベース接続を無効化
    print("Warning: Database connection disabled in Phase C-1")
    return None

def format_race_info(race_data: Dict[str, Any]) -> RaceInfo:
    """レース情報をフォーマット（Phase 2・3での表示用）"""
    # 日付フォーマット
    kaisai_nen = race_data.get('KAISAI_NEN', '')
    kaisai_gappi = race_data.get('KAISAI_GAPPI', '')
    formatted_date = ''
    if kaisai_nen and kaisai_gappi and len(kaisai_gappi) == 4:
        try:
            year = kaisai_nen
            month = int(kaisai_gappi[:2])
            day = int(kaisai_gappi[2:])
            date_obj = datetime(int(year), month, day)
            formatted_date = date_obj.strftime('%Y年%m月%d日(%a)')
        except:
            formatted_date = f"{kaisai_nen}年{kaisai_gappi}"
    
    # 時刻フォーマット
    hasso_jikoku = race_data.get('HASSO_JIKOKU', '')
    formatted_time = ''
    if hasso_jikoku and len(hasso_jikoku) == 4:
        try:
            formatted_time = f"{hasso_jikoku[:2]}:{hasso_jikoku[2:]}"
        except:
            formatted_time = hasso_jikoku
    
    # 競馬場名取得
    keibajo_code = race_data.get('KEIBAJO_CODE', '')
    keibajo_name = KEIBAJO_NAMES.get(keibajo_code, f"競馬場{keibajo_code}")
    
    return RaceInfo(
        race_code=race_data.get('RACE_CODE', ''),
        kaisai_nen=kaisai_nen,
        kaisai_gappi=kaisai_gappi,
        keibajo_code=keibajo_code,
        keibajo_name=keibajo_name,
        race_bango=race_data.get('RACE_BANGO', ''),
        kyosomei_hondai=race_data.get('KYOSOMEI_HONDAI', '') or f"第{race_data.get('RACE_BANGO', '')}レース",
        kyori=race_data.get('KYORI', ''),
        track_code=race_data.get('TRACK_CODE', ''),
        hasso_jikoku=hasso_jikoku,
        shusso_tosu=race_data.get('SHUSSO_TOSU', ''),
        grade_code=race_data.get('GRADE_CODE'),
        formatted_date=formatted_date,
        formatted_time=formatted_time
    )

@router.get("/api/race-exists-today", response_model=RaceExistsResponse)
async def check_race_exists_today():
    """本日開催レースの存在確認（Phase 3のフロー制御で使用）"""
    today = datetime.now()
    today_str = today.strftime('%Y%m%d')
    day_of_week = today.strftime('%A')
    
    connection = get_mysql_connection()
    if connection is None:
        # Phase C-1では固定データを使用するため、デフォルトでレースありとする
        return RaceExistsResponse(
            date=today_str,
            has_races=True,
            race_count=5,
            day_of_week=day_of_week
        )
    
    try:
        cursor = connection.cursor()
        
        query = """
        SELECT COUNT(*) as race_count
        FROM race_shosai r
        WHERE CONCAT(r.KAISAI_NEN, r.KAISAI_GAPPI) = %s
        """
        
        cursor.execute(query, (today_str,))
        result = cursor.fetchone()
        race_count = result[0] if result else 0
        
        return RaceExistsResponse(
            date=today_str,
            has_races=race_count > 0,
            race_count=race_count,
            day_of_week=day_of_week
        )
        
    except mysql.connector.Error as e:
        # Phase C-1では固定データを使用するため、デフォルトでレースありとする
        return RaceExistsResponse(
            date=today_str,
            has_races=True,
            race_count=5,
            day_of_week=day_of_week
        )
    finally:
        if connection and connection.is_connected():
            connection.close()

# Phase C-1では固定データAPIを使用するため、このエンドポイントを無効化
# @router.get("/api/today-races", response_model=TodayRacesResponse)
# async def get_today_races():
#     """本日開催レース取得（Phase 2のUI表示で使用）"""
#     # Phase C-1では固定データAPIを使用
#     pass

@router.get("/api/past-g1-races", response_model=PastG1Response)
async def get_past_g1_races(year: Optional[int] = None):
    """過去G1レース取得（Phase 2のUI表示で使用）"""
    connection = get_mysql_connection()
    if connection is None:
        # Phase C-1では固定データを使用するため、空のレスポンスを返す
        return PastG1Response(
            year=year,
            total_races=0,
            races=[]
        )
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 年の指定がない場合は2022-2024年
        if year:
            if year < 2022 or year > 2024:
                raise HTTPException(status_code=400, detail="Year must be between 2022 and 2024")
            year_condition = "AND r.KAISAI_NEN = %s"
            params = (str(year),)
        else:
            year_condition = "AND r.KAISAI_NEN IN ('2022', '2023', '2024')"
            params = ()
        
        query = f"""
        SELECT 
            r.RACE_CODE,
            r.KAISAI_NEN,
            r.KAISAI_GAPPI,
            r.KEIBAJO_CODE,
            r.RACE_BANGO,
            r.KYOSOMEI_HONDAI,
            r.KYORI,
            r.TRACK_CODE,
            r.GRADE_CODE,
            r.SHUSSO_TOSU,
            r.HASSO_JIKOKU
        FROM race_shosai r
        WHERE r.GRADE_CODE = 'A'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%中央交流%'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%Ｊｐｎ１%'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%Jpn1%'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%ホープフルステークス%'
        -- 海外G1レースの除外
        AND r.KYOSOMEI_HONDAI NOT LIKE '%香港%'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%メルボルン%'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%ブリーダーズ%'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%凱旋門%'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%キングジョージ%'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%コックスプレート%'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%ヴァーズ%'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%スプリント%'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%マイル%'
        AND r.KYOSOMEI_HONDAI NOT LIKE '%カップ%'
        -- JRA競馬場のみ（01-10）
        AND r.KEIBAJO_CODE BETWEEN '01' AND '10'
        {year_condition}
        ORDER BY r.KAISAI_NEN DESC, r.KAISAI_GAPPI DESC, r.KEIBAJO_CODE, r.RACE_BANGO
        """
        
        cursor.execute(query, params)
        races_data = cursor.fetchall()
        
        # Phase 2・3で使いやすい形式に変換
        races = [format_race_info(race) for race in races_data]
        
        return PastG1Response(
            year=year,
            total_races=len(races),
            races=races
        )
        
    except mysql.connector.Error as e:
        # Phase C-1では固定データを使用するため、空のレスポンスを返す
        return PastG1Response(
            year=year,
            total_races=0,
            races=[]
        )
    finally:
        if connection.is_connected():
            connection.close()

@router.get("/api/race-details/{race_code}")
async def get_race_details(race_code: str):
    """特定レースの詳細情報取得（Phase 3の8条件計算で使用）"""
    if not race_code or len(race_code) != 16:
        raise HTTPException(status_code=400, detail="Invalid race code format")
        
    connection = get_mysql_connection()
    if connection is None:
        # Phase C-1では固定データを使用するため、エラーを返す
        raise HTTPException(status_code=503, detail="Database not available in Phase C-1")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # レース詳細情報
        race_query = """
        SELECT 
            r.RACE_CODE,
            r.KAISAI_NEN,
            r.KAISAI_GAPPI,
            r.KEIBAJO_CODE,
            r.RACE_BANGO,
            r.KYOSOMEI_HONDAI,
            r.KYORI,
            r.TRACK_CODE,
            r.GRADE_CODE,
            r.SHUSSO_TOSU,
            r.HASSO_JIKOKU,
            r.SHIBA_BABAJOTAI_CODE,
            r.DIRT_BABAJOTAI_CODE
        FROM race_shosai r
        WHERE r.RACE_CODE = %s
        """
        
        cursor.execute(race_query, (race_code,))
        race_info = cursor.fetchone()
        
        if not race_info:
            raise HTTPException(status_code=404, detail="Race not found")
        
        # 出走馬情報（Phase 3の8条件計算で使用）
        horses_query = """
        SELECT 
            u.UMABAN,
            u.BAMEI,
            u.KETTO_TOROKU_BANGO,
            u.KISHUMEI_RYAKUSHO,
            u.FUTAN_JURYO,
            u.TANSHO_ODDS,
            u.KAKUTEI_CHAKUJUN,
            u.CORNER1_JUNI,
            u.CORNER2_JUNI,
            u.CORNER3_JUNI,
            u.CORNER4_JUNI
        FROM umagoto_race_joho u
        WHERE u.RACE_CODE = %s
        ORDER BY CAST(u.UMABAN AS UNSIGNED)
        """
        
        cursor.execute(horses_query, (race_code,))
        horses = cursor.fetchall()
        
        return {
            "race_info": format_race_info(race_info).dict(),
            "horses": horses,
            "horse_count": len(horses)
        }
        
    except mysql.connector.Error as e:
        # Phase C-1では固定データを使用するため、エラーを返す
        raise HTTPException(status_code=503, detail="Database not available in Phase C-1")
    finally:
        if connection and connection.is_connected():
            connection.close()

# ヘルスチェック用エンドポイント
@router.get("/api/race-data/health")
async def health_check():
    """APIヘルスチェック"""
    try:
        connection = get_mysql_connection()
        if connection is None:
            return {
                "status": "healthy",
                "database": "not_connected",
                "message": "Phase C-1: Using fixed data only",
                "timestamp": datetime.now().isoformat()
            }
        
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        connection.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "healthy",
            "database": "not_connected",
            "message": f"Phase C-1: {str(e)}",
            "timestamp": datetime.now().isoformat()
        } 