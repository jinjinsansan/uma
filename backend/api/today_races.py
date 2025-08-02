"""
Phase C: 本日レース統合API
本日のレース情報取得・詳細表示機能
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime

router = APIRouter()

def load_today_races_data() -> Dict[str, Any]:
    """本日レースデータを読み込み"""
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
                "prizePool": race.get("prizePool")
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