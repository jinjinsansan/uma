"""
Phase C: 本日レース統合API - MySQL実装版
本日のレース情報取得・詳細表示機能（リアルタイムデータ）
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
import json
import os
import mysql.connector
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_mysql_connection():
    """MySQL接続を取得（最新設定を使用）"""
    try:
        config = {
            'host': '172.25.160.1',  # 修正版設定
            'port': 3306,
            'user': 'root',
            'password': '04050405Aoi-',
            'database': 'mykeibadb',
            'charset': 'utf8mb4'
        }
        conn = mysql.connector.connect(**config)
        logger.info("✅ MySQL接続成功 - 実データ取得可能")
        return conn
    except Exception as e:
        logger.error(f"MySQL接続エラー: {e}")
        # フォールバック設定も試行
        try:
            config['host'] = 'localhost'
            config['password'] = ''
            return mysql.connector.connect(**config)
        except Exception:
            return None

def load_today_races_data() -> Dict[str, Any]:
    """MySQLから本日レースデータを取得（未来データ対応版）"""
    try:
        conn = get_mysql_connection()
        if not conn:
            # MySQL接続失敗時はデモデータを使用
            return load_demo_data()
        
        cursor = conn.cursor(dictionary=True)
        today = date.today().strftime('%Y%m%d')  # YYYYMMDD形式に変更
        
        # 修正版: 正しいテーブル結合でレース情報を取得
        race_query = """
        SELECT DISTINCT
            u.KEIBAJO_CODE,
            k.JOMEI as KEIBAJO_NAME,
            u.RACE_BANGO,
            r.KYOSOMEI_HONDAI,
            r.KYORI,
            r.HASSO_JIKOKU,
            COUNT(*) as SHUSSO_TOSU
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
        LEFT JOIN keibajo_code k ON u.KEIBAJO_CODE = k.CODE
        WHERE CONCAT(u.KAISAI_NEN, u.KAISAI_GAPPI) = %s 
        GROUP BY u.KEIBAJO_CODE, k.JOMEI, u.RACE_BANGO, r.KYOSOMEI_HONDAI, r.KYORI, r.HASSO_JIKOKU
        ORDER BY u.KEIBAJO_CODE, CAST(u.RACE_BANGO AS UNSIGNED)
        """
        
        cursor.execute(race_query, (today,))
        races = cursor.fetchall()
        
        if not races:
            logger.info("本日のレースデータが見つかりません。デモデータを使用します。")
            return load_demo_data()
        
        # 競馬場ごとにグループ化
        racecourses = {}
        for race in races:
            keibajo = race['KEIBAJO_NAME'] or race['KEIBAJO_CODE']
            if keibajo not in racecourses:
                racecourses[keibajo] = {
                    'name': keibajo,
                    'courseId': keibajo.lower().replace('競馬場', ''),
                    'weather': '晴',  # 実データにない場合のデフォルト
                    'trackCondition': '良',  # 実データにない場合のデフォルト
                    'races': []
                }
            
            # 修正版: 正しいフィールド名を使用して出走馬情報を取得
            horses_query = """
            SELECT 
                UMABAN,
                BAMEI,
                KISHUMEI_RYAKUSHO as KISHU_MEI,
                FUTAN_JURYO,
                BATAIJU,
                ZOGEN_SA,
                TANSHO_ODDS,
                TANSHO_NINKIJUN as NINKI_JUN,
                SEIBETSU_CODE,
                BAREI
            FROM umagoto_race_joho 
            WHERE CONCAT(KAISAI_NEN, KAISAI_GAPPI) = %s 
            AND KEIBAJO_CODE = %s 
            AND RACE_BANGO = %s
            ORDER BY UMABAN
            """
            
            cursor.execute(horses_query, (today, race['KEIBAJO_CODE'], race['RACE_BANGO']))
            horse_data = cursor.fetchall()
            
            horses = []
            for horse in horse_data:  # 全ての出走馬を表示
                horses.append({
                    'number': horse['UMABAN'] or 0,
                    'name': horse['BAMEI'] or f"出走馬{horse['UMABAN'] or 0}",
                    'jockey': horse['KISHU_MEI'] or '未定',
                    'weight': f"{horse['FUTAN_JURYO'] or 56}kg",
                    'horseWeight': f"{horse['BATAIJU'] or 500}kg",
                    'weightChange': str(horse['ZOGEN_SA']) if horse['ZOGEN_SA'] else "±0",
                    'age': horse['BAREI'] or 3,
                    'sex': '牡',  # 実データから性別判定は後で実装
                    'trainer': '未定',
                    'odds': str(horse['TANSHO_ODDS'] or '未定'),
                    'popularity': horse['NINKI_JUN'] or (len(horses) + 1)
                })
            
            race_info = {
                'raceId': f"{racecourses[keibajo]['courseId']}_{race['RACE_BANGO']}r",
                'raceNumber': int(race['RACE_BANGO']),
                'raceName': race['KYOSOMEI_HONDAI'] or f"{race['RACE_BANGO']}R",
                'time': race['HASSO_JIKOKU'] or '未定',
                'distance': f"{race['KYORI']}m" if race['KYORI'] else '未定',
                'track': '芝',  # 実データから判定は後で実装
                'entryCount': race['SHUSSO_TOSU'] or len(horses),
                'prizePool': '未定',  # 実データから取得は後で実装
                'grade': None,  # 実データから判定は後で実装
                'horses': horses
            }
            
            racecourses[keibajo]['races'].append(race_info)
        
        # レスポンス形式に変換
        response_data = {
            'date': today,
            'lastUpdate': datetime.now().isoformat(),
            'racecourses': list(racecourses.values())
        }
        
        # 各競馬場のレース数を設定
        for racecourse in response_data['racecourses']:
            racecourse['raceCount'] = len(racecourse['races'])
        
        cursor.close()
        conn.close()
        
        logger.info(f"MySQL本日レースデータ取得成功: {len(races)}レース")
        return response_data
        
    except Exception as e:
        logger.error(f"MySQLデータ取得エラー: {e}")
        return load_demo_data()

def load_demo_data() -> Dict[str, Any]:
    """デモデータを読み込み（フォールバック）"""
    try:
        # 拡張版デモデータを優先使用
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "today_races_full_demo.json")
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        # フォールバック用に元のデモデータも試行
        try:
            data_path = os.path.join(os.path.dirname(__file__), "..", "data", "today_races_demo.json")
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"レースデータの読み込みに失敗しました: {str(e)}")

@router.get("/today-races")
async def get_today_races() -> Dict[str, Any]:
    """
    本日の全レース情報を取得
    GET /api/today-races
    """
    data = load_today_races_data()
    
    # レスポンス用にデータを整形
    response_data = {
        "date": data.get("date"),
        "lastUpdate": data.get("lastUpdate"),
        "racecourses": []
    }
    
    for racecourse in data.get("racecourses", []):
        racecourse_info = {
            "name": racecourse.get("name"),
            "courseId": racecourse.get("courseId"),
            "weather": racecourse.get("weather"),
            "trackCondition": racecourse.get("trackCondition"),
            "raceCount": len(racecourse.get("races", [])),
            "races": []
        }
        
        for race in racecourse.get("races", []):
            race_summary = {
                "raceId": race.get("raceId"),
                "raceNumber": race.get("raceNumber"),
                "raceName": race.get("raceName"),
                "time": race.get("time"),
                "distance": race.get("distance"),
                "track": race.get("track"),
                "entryCount": race.get("entryCount"),
                "prizePool": race.get("prizePool"),
                "horses": race.get("horses", [])  # 出走馬情報を含める
            }
            racecourse_info["races"].append(race_summary)
        
        response_data["racecourses"].append(racecourse_info)
    
    return response_data

@router.get("/race-detail/{race_id}")
async def get_race_detail(race_id: str) -> Dict[str, Any]:
    """
    指定レースの詳細情報を取得
    GET /api/race-detail/{race_id}
    """
    data = load_today_races_data()
    
    # 指定されたレースIDを検索
    target_race = None
    target_racecourse = None
    
    for racecourse in data.get("racecourses", []):
        for race in racecourse.get("races", []):
            if race.get("raceId") == race_id:
                target_race = race
                target_racecourse = racecourse
                break
        if target_race:
            break
    
    if not target_race:
        raise HTTPException(status_code=404, detail=f"レースID '{race_id}' が見つかりません")
    
    # 詳細情報を返す
    race_detail = {
        "raceInfo": {
            "raceId": target_race.get("raceId"),
            "raceNumber": target_race.get("raceNumber"),
            "raceName": target_race.get("raceName"),
            "time": target_race.get("time"),
            "distance": target_race.get("distance"),
            "track": target_race.get("track"),
            "condition": target_race.get("condition"),
            "grade": target_race.get("grade"),
            "prizePool": target_race.get("prizePool"),
            "entryCount": target_race.get("entryCount")
        },
        "racecourse": {
            "name": target_racecourse.get("name"),
            "courseId": target_racecourse.get("courseId"),
            "weather": target_racecourse.get("weather"),
            "trackCondition": target_racecourse.get("trackCondition")
        },
        "horses": target_race.get("horses", []),
        "date": data.get("date"),
        "lastUpdate": data.get("lastUpdate")
    }
    
    return race_detail

@router.get("/racecourse/{course_id}/races")
async def get_racecourse_races(course_id: str) -> Dict[str, Any]:
    """
    指定競馬場の本日レース一覧を取得
    GET /api/racecourse/{course_id}/races
    """
    data = load_today_races_data()
    
    # 指定された競馬場を検索
    target_racecourse = None
    for racecourse in data.get("racecourses", []):
        if racecourse.get("courseId") == course_id:
            target_racecourse = racecourse
            break
    
    if not target_racecourse:
        raise HTTPException(status_code=404, detail=f"競馬場ID '{course_id}' が見つかりません")
    
    response_data = {
        "racecourse": {
            "name": target_racecourse.get("name"),
            "courseId": target_racecourse.get("courseId"),
            "weather": target_racecourse.get("weather"),
            "trackCondition": target_racecourse.get("trackCondition")
        },
        "races": target_racecourse.get("races", []),
        "date": data.get("date"),
        "lastUpdate": data.get("lastUpdate")
    }
    
    return response_data

@router.get("/race-search")
async def search_races(
    course_id: Optional[str] = None,
    race_number: Optional[int] = None,
    distance: Optional[str] = None,
    track: Optional[str] = None
) -> Dict[str, Any]:
    """
    レース検索機能
    GET /api/race-search?course_id=tokyo&race_number=3
    """
    data = load_today_races_data()
    matching_races = []
    
    for racecourse in data.get("racecourses", []):
        # 競馬場IDフィルタ
        if course_id and racecourse.get("courseId") != course_id:
            continue
            
        for race in racecourse.get("races", []):
            # レース番号フィルタ
            if race_number and race.get("raceNumber") != race_number:
                continue
            
            # 距離フィルタ
            if distance and race.get("distance") != distance:
                continue
            
            # トラックフィルタ
            if track and race.get("track") != track:
                continue
            
            # 条件に合致したレースを追加
            race_info = {
                "raceId": race.get("raceId"),
                "raceNumber": race.get("raceNumber"),
                "raceName": race.get("raceName"),
                "time": race.get("time"),
                "distance": race.get("distance"),
                "track": race.get("track"),
                "racecourse": {
                    "name": racecourse.get("name"),
                    "courseId": racecourse.get("courseId")
                },
                "entryCount": race.get("entryCount"),
                "prizePool": race.get("prizePool")
            }
            matching_races.append(race_info)
    
    return {
        "searchResults": matching_races,
        "resultCount": len(matching_races),
        "searchCriteria": {
            "course_id": course_id,
            "race_number": race_number,
            "distance": distance,
            "track": track
        },
        "date": data.get("date"),
        "lastUpdate": data.get("lastUpdate")
    } 

def load_future_races_data(target_date: str) -> Dict[str, Any]:
    """未来レースデータを取得（指定日付用）"""
    try:
        conn = get_mysql_connection()
        if not conn:
            return load_demo_data()
        
        cursor = conn.cursor(dictionary=True)
        
        # 指定日付のレース情報を取得
        race_query = """
        SELECT DISTINCT
            u.KEIBAJO_CODE,
            k.JOMEI as KEIBAJO_NAME,
            u.RACE_BANGO,
            r.KYOSOMEI_HONDAI,
            r.KYORI,
            r.HASSO_JIKOKU,
            COUNT(*) as SHUSSO_TOSU
        FROM umagoto_race_joho u
        LEFT JOIN race_shosai r ON u.RACE_CODE = r.RACE_CODE
        LEFT JOIN keibajo_code k ON u.KEIBAJO_CODE = k.CODE
        WHERE CONCAT(u.KAISAI_NEN, u.KAISAI_GAPPI) = %s 
        GROUP BY u.KEIBAJO_CODE, k.JOMEI, u.RACE_BANGO, r.KYOSOMEI_HONDAI, r.KYORI, r.HASSO_JIKOKU
        ORDER BY u.KEIBAJO_CODE, CAST(u.RACE_BANGO AS UNSIGNED)
        """
        
        cursor.execute(race_query, (target_date,))
        races = cursor.fetchall()
        
        if not races:
            return {
                'date': f"{target_date[:4]}-{target_date[4:6]}-{target_date[6:8]}",
                'lastUpdate': datetime.now().isoformat(),
                'racecourses': [],
                'message': f'{target_date[:4]}年{target_date[4:6]}月{target_date[6:8]}日のレースデータはまだ登録されていません。'
            }
        
        # 以下は既存のロジックと同様
        racecourses = {}
        for race in races:
            keibajo = race['KEIBAJO_NAME'] or race['KEIBAJO_CODE']
            if keibajo not in racecourses:
                racecourses[keibajo] = {
                    'name': keibajo,
                    'courseId': keibajo.lower().replace('競馬場', ''),
                    'weather': '未定',
                    'trackCondition': '未定',
                    'races': []
                }
            
            # 出走馬情報取得
            horses_query = """
            SELECT 
                UMABAN,
                BAMEI,
                KISHUMEI_RYAKUSHO as KISHU_MEI,
                FUTAN_JURYO,
                BATAIJU,
                ZOGEN_SA,
                TANSHO_ODDS,
                TANSHO_NINKIJUN as NINKI_JUN,
                SEIBETSU_CODE,
                BAREI
            FROM umagoto_race_joho 
            WHERE CONCAT(KAISAI_NEN, KAISAI_GAPPI) = %s 
            AND KEIBAJO_CODE = %s 
            AND RACE_BANGO = %s
            ORDER BY UMABAN
            """
            
            cursor.execute(horses_query, (target_date, race['KEIBAJO_CODE'], race['RACE_BANGO']))
            horse_data = cursor.fetchall()
            
            horses = []
            for horse in horse_data:
                horses.append({
                    'number': horse['UMABAN'] or 0,
                    'name': horse['BAMEI'] or f"出走馬{horse['UMABAN'] or 0}",
                    'jockey': horse['KISHU_MEI'] or '未定',
                    'weight': f"{horse['FUTAN_JURYO'] or 56}kg",
                    'horseWeight': f"{horse['BATAIJU'] or 500}kg" if horse['BATAIJU'] else '未定',
                    'weightChange': str(horse['ZOGEN_SA']) if horse['ZOGEN_SA'] else "±0",
                    'age': horse['BAREI'] or 3,
                    'sex': '牡',
                    'trainer': '未定',
                    'odds': str(horse['TANSHO_ODDS'] or '未定'),
                    'popularity': horse['NINKI_JUN'] or (len(horses) + 1)
                })
            
            race_info = {
                'raceId': f"{racecourses[keibajo]['courseId']}_{race['RACE_BANGO']}r",
                'raceNumber': int(race['RACE_BANGO']),
                'raceName': race['KYOSOMEI_HONDAI'] or f"{race['RACE_BANGO']}R",
                'time': race['HASSO_JIKOKU'] or '未定',
                'distance': f"{race['KYORI']}m" if race['KYORI'] else '未定',
                'track': '芝',
                'entryCount': race['SHUSSO_TOSU'] or len(horses),
                'prizePool': '未定',
                'grade': None,
                'horses': horses
            }
            
            racecourses[keibajo]['races'].append(race_info)
        
        response_data = {
            'date': f"{target_date[:4]}-{target_date[4:6]}-{target_date[6:8]}",
            'lastUpdate': datetime.now().isoformat(),
            'racecourses': list(racecourses.values())
        }
        
        for racecourse in response_data['racecourses']:
            racecourse['raceCount'] = len(racecourse['races'])
        
        cursor.close()
        conn.close()
        
        return response_data
        
    except Exception as e:
        logger.error(f"未来レースデータ取得エラー: {e}")
        return {
            'date': f"{target_date[:4]}-{target_date[4:6]}-{target_date[6:8]}",
            'lastUpdate': datetime.now().isoformat(),
            'racecourses': [],
            'error': f'データ取得エラー: {str(e)}'
        }

@router.get("/future-races/{target_date}")
async def get_future_races(target_date: str) -> Dict[str, Any]:
    """
    指定日の未来レース情報を取得
    GET /api/future-races/20250804
    """
    # 日付形式チェック（YYYYMMDD）
    if len(target_date) != 8 or not target_date.isdigit():
        raise HTTPException(status_code=400, detail="日付は YYYYMMDD 形式で指定してください")
    
    data = load_future_races_data(target_date)
    return data