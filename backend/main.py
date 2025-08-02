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
from models.d_logic_models import ChatDLogicRequest, ChatDLogicResponse
from services.knowledge_base import KnowledgeBase

app = FastAPI(title="Dロジック競馬予想AI", version="2.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://uma-oracle-ai.netlify.app",
        "https://*.netlify.app",
        "https://*.onrender.com",
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

# Dロジックルーターを含める
app.include_router(d_logic_router, prefix="/api/d-logic", tags=["D-Logic"])

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
        
        # 特定レースの指数要求の判定
        race_pattern_matches = _extract_race_info(request.message)
        if race_pattern_matches:
            course, race_number = race_pattern_matches
            
            # レース情報を取得
            try:
                race_info = await get_specific_race(course, race_number)
                return ChatDLogicResponse(
                    message=f"{course}{race_number}の情報を表示しました。\n\n**{race_info['race_info']['race_name']}**\n距離: {race_info['race_info']['distance']}m\n馬場: {race_info['race_info']['track_type']}\n\nDロジックで指数を出しますか？",
                    type="d_logic_prompt",
                    data={
                        "race_info": race_info,
                        "course": course,
                        "race_number": race_number
                    },
                    show_d_logic_button=True
                )
            except HTTPException:
                return ChatDLogicResponse(
                    message=f"申し訳ございません。{course}{race_number}の情報が見つかりませんでした。",
                    type="text"
                )
        
        # Dロジック実行要求の判定
        if "dロジック" in message or ("指数" in message and "出" in message):
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
                        {"role": "system", "content": "あなたはDロジック競馬予想AIのアシスタントです。ダンスインザダーク基準100点のDロジック指数について説明できます。親切で分かりやすい説明を心がけてください。"},
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

