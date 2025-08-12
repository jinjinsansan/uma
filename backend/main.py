from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from openai import OpenAI
import os
from datetime import datetime
import json

# Dロジック関連のインポート
from api.d_logic import router as d_logic_router
from api.today_races import router as today_races_router
from api.chat import router as chat_router
from api.past_races import router as past_races_router
from api.fast_dlogic_api import router as fast_dlogic_router
from api.database_stats import router as database_stats_router
from api.user_management import router as user_management_router
from api.line_integration import router as line_integration_router
from api.today_races_ocr import router as today_races_ocr_router
from api.debug_knowledge import router as debug_knowledge_router
from api.admin_knowledge import router as admin_knowledge_router
from models.d_logic_models import ChatDLogicRequest, ChatDLogicResponse
from services.knowledge_base import KnowledgeBase

app = FastAPI(title="Dロジック競馬予想AI", version="2.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "https://uma-oracle-ai.netlify.app",
        "https://*.netlify.app",
        "https://*.onrender.com",
        "https://dlogicai.in",
        "https://www.dlogicai.in",
        "https://*.vercel.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI API設定
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

# ナレッジベース初期化
kb = KnowledgeBase()

# ルーターを含める
app.include_router(d_logic_router, prefix="/api/d-logic", tags=["D-Logic"])
app.include_router(today_races_router, prefix="/api", tags=["Today-Races"])
app.include_router(past_races_router, prefix="/api", tags=["Past-Races"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(fast_dlogic_router, prefix="/api/v2/dlogic", tags=["D-Logic V2 (Fast)"])
app.include_router(database_stats_router, tags=["Database Statistics"])
app.include_router(user_management_router, prefix="/api/users", tags=["User Management"])
app.include_router(line_integration_router, prefix="/api/line", tags=["LINE Integration"])
app.include_router(today_races_ocr_router, tags=["Today Races OCR"])
app.include_router(debug_knowledge_router, tags=["Debug"])
app.include_router(admin_knowledge_router, tags=["Admin Knowledge"])

# 本日レース情報（Phase C用固定データ）
TODAY_RACES = {
    "tokyo": [
        {"race_number": "1R", "race_name": "新馬戦", "distance": 1400, "track_type": "芝"},
        {"race_number": "2R", "race_name": "未勝利戦", "distance": 1600, "track_type": "芝"},
        {"race_number": "3R", "race_name": "3歳未勝利", "distance": 1800, "track_type": "芝"},
        {"race_number": "4R", "race_name": "3歳以上1勝クラス", "distance": 2000, "track_type": "芝"},
        {"race_number": "5R", "race_name": "3歳以上1勝クラス", "distance": 1600, "track_type": "ダート"},
        {"race_number": "6R", "race_name": "3歳以上2勝クラス", "distance": 1400, "track_type": "ダート"},
        {"race_number": "7R", "race_name": "3歳以上2勝クラス", "distance": 1800, "track_type": "芝"},
        {"race_number": "8R", "race_name": "3歳以上3勝クラス", "distance": 1600, "track_type": "芝"},
        {"race_number": "9R", "race_name": "東京競馬場特別", "distance": 2000, "track_type": "芝"},
        {"race_number": "10R", "race_name": "リステッド競走", "distance": 1600, "track_type": "芝"},
        {"race_number": "11R", "race_name": "G3競走", "distance": 2400, "track_type": "芝"},
        {"race_number": "12R", "race_name": "3歳以上1勝クラス", "distance": 1200, "track_type": "芝"}
    ],
    "nakayama": [
        {"race_number": "1R", "race_name": "新馬戦", "distance": 1200, "track_type": "芝"},
        {"race_number": "2R", "race_name": "未勝利戦", "distance": 1800, "track_type": "芝"},
        {"race_number": "3R", "race_name": "3歳未勝利", "distance": 1600, "track_type": "ダート"},
        {"race_number": "4R", "race_name": "3歳以上1勝クラス", "distance": 1800, "track_type": "芝"},
        {"race_number": "5R", "race_name": "3歳以上1勝クラス", "distance": 1200, "track_type": "ダート"},
        {"race_number": "6R", "race_name": "3歳以上2勝クラス", "distance": 1600, "track_type": "芝"},
        {"race_number": "7R", "race_name": "3歳以上2勝クラス", "distance": 1800, "track_type": "ダート"},
        {"race_number": "8R", "race_name": "3歳以上3勝クラス", "distance": 2000, "track_type": "芝"},
        {"race_number": "9R", "race_name": "中山競馬場特別", "distance": 1600, "track_type": "芝"},
        {"race_number": "10R", "race_name": "リステッド競走", "distance": 2200, "track_type": "芝"},
        {"race_number": "11R", "race_name": "G3競走", "distance": 1800, "track_type": "芝"},
        {"race_number": "12R", "race_name": "3歳以上1勝クラス", "distance": 1400, "track_type": "ダート"}
    ],
    "hanshin": [
        {"race_number": "1R", "race_name": "新馬戦", "distance": 1600, "track_type": "芝"},
        {"race_number": "2R", "race_name": "未勝利戦", "distance": 1400, "track_type": "芝"},
        {"race_number": "3R", "race_name": "3歳未勝利", "distance": 1800, "track_type": "ダート"},
        {"race_number": "4R", "race_name": "3歳以上1勝クラス", "distance": 1600, "track_type": "芝"},
        {"race_number": "5R", "race_name": "3歳以上1勝クラス", "distance": 1400, "track_type": "ダート"},
        {"race_number": "6R", "race_name": "3歳以上2勝クラス", "distance": 1800, "track_type": "芝"},
        {"race_number": "7R", "race_name": "3歳以上2勝クラス", "distance": 1600, "track_type": "ダート"},
        {"race_number": "8R", "race_name": "3歳以上3勝クラス", "distance": 2000, "track_type": "芝"},
        {"race_number": "9R", "race_name": "阪神競馬場特別", "distance": 1800, "track_type": "芝"},
        {"race_number": "10R", "race_name": "リステッド競走", "distance": 1400, "track_type": "芝"},
        {"race_number": "11R", "race_name": "G2競走", "distance": 2200, "track_type": "芝"},
        {"race_number": "12R", "race_name": "3歳以上1勝クラス", "distance": 1200, "track_type": "芝"}
    ]
}

# レガシー互換性用のデータモデル
class ChatRequest(BaseModel):
    message: str
    race_info: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    type: str
    data: Optional[dict] = None

@app.get("/")
async def root():
    return {"message": "Dロジック競馬予想AI - Phase B完了状態", "version": "2.0.0"}

@app.get("/api/races/today")
async def get_today_races():
    """本日開催レース情報を取得"""
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "races": TODAY_RACES,
        "message": "本日の開催レース情報（固定データ）"
    }

@app.get("/api/races/today/{course}")
async def get_today_races_by_course(course: str):
    """指定競馬場の本日開催レース情報を取得"""
    course_lower = course.lower()
    if course_lower not in TODAY_RACES:
        raise HTTPException(status_code=404, detail=f"競馬場'{course}'の情報が見つかりません")
    
    return {
        "course": course,
        "date": datetime.now().strftime("%Y-%m-%d"), 
        "races": TODAY_RACES[course_lower],
        "total_races": len(TODAY_RACES[course_lower])
    }

@app.get("/api/races/today/{course}/{race_number}")
async def get_specific_race(course: str, race_number: str):
    """特定レースの詳細情報を取得"""
    course_lower = course.lower()
    if course_lower not in TODAY_RACES:
        raise HTTPException(status_code=404, detail=f"競馬場'{course}'の情報が見つかりません")
    
    races = TODAY_RACES[course_lower]
    race = next((r for r in races if r["race_number"] == race_number), None)
    
    if not race:
        raise HTTPException(status_code=404, detail=f"{course}{race_number}の情報が見つかりません")
    
    return {
        "course": course,
        "race_info": race,
        "d_logic_available": True,
        "message": f"{course}{race_number}の情報です。Dロジックで指数を出しますか？"
    }

@app.post("/api/chat")
async def chat_with_d_logic(request: ChatDLogicRequest):
    """Dロジック対応チャットボット"""
    try:
        message = request.message.lower()
        
        # レース情報要求の判定
        if "本日" in request.message and ("レース" in request.message or "開催" in request.message):
            return ChatDLogicResponse(
                message="本日の開催レース情報をお調べします。どちらの競馬場の情報をお知りになりたいですか？\n\n・東京競馬場\n・中山競馬場\n・阪神競馬場",
                type="race_selection",
                data={"available_courses": ["tokyo", "nakayama", "hanshin"]}
            )
        
        # レース情報抽出・Dロジック実行要求の判定
        race_info = _extract_race_info(message)
        if race_info and ("指数" in message or "dロジック" in message):
            course_id, race_number = race_info
            
            # 本日レース詳細API経由でレース情報を取得
            try:
                from api.today_races import load_today_races_data
                today_data = load_today_races_data()
                
                # 指定されたレースを検索
                race_id = f"{course_id}_{race_number}r"
                target_race = None
                
                for racecourse in today_data.get("racecourses", []):
                    if racecourse.get("courseId") == course_id:
                        for race in racecourse.get("races", []):
                            if race.get("raceId") == race_id:
                                target_race = race
                                break
                        break
                
                if target_race:
                    # Dロジック計算を実行
                    from api.d_logic import calculate_d_logic
                    prediction = await calculate_d_logic(target_race)
                    
                    race_display_name = f"{racecourse.get('name', '競馬場')}{race_number}R {target_race.get('raceName', '')}"
                    
                    return ChatDLogicResponse(
                        message=f"{race_display_name}のDロジック指数を計算しました！12項目詳細分析結果をご確認ください。",
                        type="d_logic_result",
                        data={
                            "prediction": prediction.dict(),
                            "race_info": {
                                "raceName": race_display_name,
                                "distance": target_race.get("distance", ""),
                                "track": target_race.get("track", ""),
                                "time": target_race.get("time", ""),
                                "entryCount": target_race.get("entryCount", 0)
                            }
                        }
                    )
                else:
                    return ChatDLogicResponse(
                        message=f"申し訳ございません。{course_id.upper()}{race_number}Rのレース情報が見つかりませんでした。本日開催のレース情報をご確認ください。",
                        type="error"
                    )
                    
            except Exception as e:
                # エラー時はサンプル計算にフォールバック
                from api.d_logic import calculate_d_logic
                sample_data = kb.get_sample_race_data()
                prediction = await calculate_d_logic(sample_data)
                
                return ChatDLogicResponse(
                    message="指定レースのデータ取得でエラーが発生しました。サンプルDロジック計算を表示します。",
                    type="d_logic_result",
                    data={"prediction": prediction.dict()}
                )
        
        # 一般的なDロジック要求（レース指定なし）
        elif "dロジック" in message or ("指数" in message and "出" in message):
            # サンプルDロジック計算を実行
            from api.d_logic import calculate_d_logic
            
            sample_data = kb.get_sample_race_data()
            prediction = await calculate_d_logic(sample_data)
            
            return ChatDLogicResponse(
                message="Dロジック指数を計算しました！12項目詳細分析結果をご確認ください。",
                type="d_logic_result",
                data={"prediction": prediction.dict()}
            )
        
        # OpenAI応答（通常のチャット）
        if openai_client:
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "あなたはDロジック競馬予想AIのアシスタントです。独自基準100点のDロジック指数について説明できます。親切で分かりやすい説明を心がけてください。"},
                        {"role": "user", "content": request.message}
                    ],
                    max_tokens=300
                )
                ai_message = response.choices[0].message.content
            except Exception as e:
                ai_message = "申し訳ございません。現在OpenAI APIに接続できません。Dロジック機能は正常に動作しています。"
        else:
            ai_message = "こんにちは！Dロジック競馬予想AIです。\n\n「本日の東京3Rの指数を出して」のようにお話しください。12項目詳細分析でDロジック指数をお出しします。"
        
        return ChatDLogicResponse(
            message=ai_message,
            type="text"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"チャット処理エラー: {str(e)}")

def _extract_race_info(message: str) -> Optional[tuple]:
    """メッセージからレース情報を抽出"""
    import re
    
    # 「東京3R」「中山1R」などのパターンを検索
    course_mapping = {
        "東京": "tokyo",
        "中山": "nakayama", 
        "阪神": "hanshin"
    }
    
    for course_jp, course_en in course_mapping.items():
        pattern = rf"{course_jp}(\d+)R"
        match = re.search(pattern, message)
        if match:
            race_number = f"{match.group(1)}R"
            return (course_en, race_number)
    
    return None

# レガシー互換性エンドポイント（既存フロントエンドとの互換性維持）
@app.post("/chat")
async def legacy_chat(request: ChatRequest):
    """レガシーチャットエンドポイント（互換性維持）"""
    d_logic_request = ChatDLogicRequest(
        message=request.message,
        race_info=request.race_info
    )
    
    d_logic_response = await chat_with_d_logic(d_logic_request)
    
    return ChatResponse(
        message=d_logic_response.message,
        type=d_logic_response.type,
        data=d_logic_response.data
    )

@app.get("/api/d-logic/status")
async def d_logic_status():
    """Dロジックシステムの状態確認"""
    validation = kb.validate_knowledge_base()
    
    return {
        "status": "Phase B完了",
        "d_logic_engine": "動作中",
        "knowledge_base": "ダンスインザダーク基準データ読み込み済み",
        "validation": validation,
        "ready_for_phase_c": True,
        "features": [
            "12項目SQL分析エンジン",
            "ダンスインザダーク基準100点指数",
            "OpenAI統合チャット",
            "本日レース情報表示"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)

