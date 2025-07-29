from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
from datetime import datetime
import json

app = FastAPI(title="UmaOracle AI API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI API設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# データモデル
class Condition(BaseModel):
    id: str
    name: str
    description: str

class PredictRequest(BaseModel):
    race_id: str
    selected_conditions: List[str]

class ChatRequest(BaseModel):
    message: str
    race_info: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    type: str
    data: Optional[dict] = None

# サンプルデータ
SAMPLE_HORSES = [
    {"name": "シンボリクリスエス", "base_score": 75},
    {"name": "ディープインパクト", "base_score": 85},
    {"name": "オルフェーヴル", "base_score": 70},
    {"name": "ジェンティルドンナ", "base_score": 65},
    {"name": "キタサンブラック", "base_score": 80},
    {"name": "アーモンドアイ", "base_score": 90},
    {"name": "クロノジェネシス", "base_score": 72},
    {"name": "グランアレグリア", "base_score": 68}
]

CONDITIONS_DATA = {
    '1_running_style': {
        'name': '脚質',
        'description': '逃げ、先行、差し、追込の適性',
        'sample_data': {'逃げ': 0.35, '先行': 0.28, '差し': 0.22, '追込': 0.15}
    },
    '2_course_direction': {
        'name': '右周り・左周り複勝率',
        'description': 'コース回り方向別成績',
        'sample_data': {'右周り': 0.42, '左周り': 0.38}
    },
    '3_distance_category': {
        'name': '距離毎複勝率',
        'description': '1000-3600mの距離別成績',
        'sample_data': {'1000-1200m': 0.25, '1400m': 0.30, '1600m': 0.35, '1800-2000m': 0.40, '2200m': 0.45, '2000-2400m': 0.50, '2500m': 0.55, '2400-3000m': 0.60, '3000-3600m': 0.65}
    },
    '4_interval_category': {
        'name': '出走間隔毎複勝率',
        'description': '連闘、中1、中2、中3-4、中5-8、中9-12、中13以上',
        'sample_data': {'連闘': 0.20, '中1': 0.25, '中2': 0.30, '中3-4': 0.35, '中5-8': 0.40, '中9-12': 0.45, '中13以上': 0.50}
    },
    '5_course_specific': {
        'name': 'コース毎複勝率',
        'description': '競馬場・芝ダート・距離の組み合わせ',
        'sample_data': {'東京芝': 0.35, '東京ダ': 0.30, '阪神芝': 0.40, '阪神ダ': 0.35}
    },
    '6_horse_count': {
        'name': '出走頭数毎複勝率',
        'description': '7頭以下、8-12頭、13-16頭、16-17頭、16-18頭',
        'sample_data': {'7頭以下': 0.25, '8-12頭': 0.30, '13-16頭': 0.35, '16-17頭': 0.40, '16-18頭': 0.45}
    },
    '7_track_condition': {
        'name': '馬場毎複勝率',
        'description': '良、重、やや重、不良',
        'sample_data': {'良': 0.40, '重': 0.35, 'やや重': 0.30, '不良': 0.25}
    },
    '8_season_category': {
        'name': '季節毎複勝率',
        'description': '1-3月、4-6月、7-9月、10-12月',
        'sample_data': {'1-3月': 0.35, '4-6月': 0.40, '7-9月': 0.45, '10-12月': 0.50}
    }
}

@app.get("/")
async def root():
    return {"message": "UmaOracle AI API"}

@app.get("/conditions")
async def get_conditions():
    """8条件の一覧を取得"""
    conditions = []
    for condition_id, data in CONDITIONS_DATA.items():
        conditions.append({
            "id": condition_id,
            "name": data["name"],
            "description": data["description"]
        })
    return conditions

@app.post("/predict")
async def predict_race(request: PredictRequest):
    """レース予想を実行"""
    try:
        # サンプル予想ロジック
        horses = SAMPLE_HORSES.copy()
        
        # 選択された条件に基づいてスコアを調整
        for horse in horses:
            base_score = horse["base_score"]
            adjusted_score = base_score
            
            # 条件に基づくスコア調整（サンプル）
            for condition in request.selected_conditions:
                if condition in CONDITIONS_DATA:
                    # 簡単なスコア調整ロジック
                    adjustment = len(request.selected_conditions) * 2
                    adjusted_score += adjustment
            
            horse["final_score"] = min(100, max(0, adjusted_score))
        
        # スコアでソート
        horses.sort(key=lambda x: x["final_score"], reverse=True)
        
        # ランキングを追加
        for i, horse in enumerate(horses):
            horse["rank"] = i + 1
        
        # 信頼度を決定
        confidence = "medium"  # サンプルでは常にmedium
        
        return {
            "horses": horses,
            "confidence": confidence,
            "selectedConditions": request.selected_conditions,
            "calculationTime": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    """チャットボット応答"""
    try:
        # OpenAI APIを使用した応答生成
        if openai.api_key:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたは競馬予想の専門家です。親切で分かりやすい説明を心がけてください。"},
                    {"role": "user", "content": request.message}
                ],
                max_tokens=200
            )
            ai_message = response.choices[0].message.content
        else:
            # API Keyがない場合のサンプル応答
            if "予想" in request.message or "レース" in request.message:
                ai_message = "レース予想をご希望ですね。8つの条件から4つを選択していただき、AIが予想を実行いたします。"
                return ChatResponse(
                    message=ai_message,
                    type="conditions",
                    data={"raceInfo": request.race_info}
                )
            else:
                ai_message = "こんにちは！競馬予想AIのUmaOracleです。今日のレースの予想をお手伝いします。"
        
        return ChatResponse(
            message=ai_message,
            type="text"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)