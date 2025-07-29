from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
from datetime import datetime
import json
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="UmaOracle AI API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://uma-oracle-ai.netlify.app"],
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
        'sample_data': {'右周り': 0.40, '左周り': 0.35}
    },
    '3_distance_category': {
        'name': '距離毎複勝率',
        'description': '1000-1200m、1400m、1600m、1800-2000m、2200m、2000-2400m、2500m、2400-3000m、3000-3600m',
        'sample_data': {'1000-1200m': 0.30, '1400m': 0.35, '1600m': 0.40, '1800-2000m': 0.45, '2200m': 0.50}
    },
    '4_interval_category': {
        'name': '出走間隔毎複勝率',
        'description': '連闘、中1、中2、中3-4、中5-8、中9-12、中13以上',
        'sample_data': {'連闘': 0.25, '中1': 0.30, '中2': 0.35, '中3-4': 0.40, '中5-8': 0.45, '中9-12': 0.50, '中13以上': 0.55}
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

# 固定レスポンスのテンプレート
FIXED_RESPONSES = {
    "greeting": [
        "こんにちは！競馬予想AIのUmaOracleです。今日のレースの予想をお手伝いします。",
        "UmaOracle AIです！レース予想でお困りのことがあれば、お気軽にお声かけください。",
        "競馬予想の専門AI、UmaOracleです。どのようなご相談でしょうか？"
    ],
    "prediction_request": [
        "レース予想をご希望ですね。8つの条件から4つを選択していただき、AIが予想を実行いたします。",
        "予想を開始しますね。まずは8つの条件から4つを選んでください。",
        "レース予想の準備をします。条件を選択していただければ、すぐに予想を実行いたします。"
    ],
    "general": [
        "競馬予想について何かお手伝いできることはありますか？",
        "レースの予想や分析について、ご質問がございましたらお聞かせください。",
        "UmaOracle AIが競馬予想をお手伝いします。何かご質問はありますか？"
    ]
}

import random

def get_random_response(category: str) -> str:
    """カテゴリに応じたランダムなレスポンスを取得"""
    responses = FIXED_RESPONSES.get(category, FIXED_RESPONSES["general"])
    return random.choice(responses)

@app.get("/")
async def root():
    """ヘルスチェック用エンドポイント"""
    return {"message": "UmaOracle AI API is running", "status": "healthy"}

@app.get("/conditions")
async def get_conditions():
    """8条件の一覧を取得"""
    try:
        conditions = []
        for condition_id, data in CONDITIONS_DATA.items():
            conditions.append({
                "id": condition_id,
                "name": data["name"],
                "description": data["description"]
            })
        return conditions
    except Exception as e:
        logger.error(f"Error in get_conditions: {e}")
        raise HTTPException(status_code=500, detail=f"条件の取得に失敗しました: {str(e)}")

@app.post("/predict")
async def predict_race(request: PredictRequest):
    """レース予想を実行"""
    try:
        logger.info(f"Prediction request received: {request}")
        
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
        
        result = {
            "horses": horses,
            "confidence": confidence,
            "selectedConditions": request.selected_conditions,
            "calculationTime": datetime.now().isoformat()
        }
        
        logger.info(f"Prediction completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in predict_race: {e}")
        raise HTTPException(status_code=500, detail=f"予想の実行に失敗しました: {str(e)}")

@app.post("/chat")
async def chat(request: ChatRequest):
    """チャットボット応答"""
    try:
        logger.info(f"Chat request received: {request.message}")
        
        # メッセージの内容に基づいてレスポンスを決定
        message_lower = request.message.lower()
        
        # 予想関連のキーワードをチェック
        prediction_keywords = ["予想", "レース", "競馬", "予測", "分析"]
        is_prediction_request = any(keyword in message_lower for keyword in prediction_keywords)
        
        if is_prediction_request:
            ai_message = get_random_response("prediction_request")
            response_type = "conditions"
            data = {"raceInfo": request.race_info} if request.race_info else None
        else:
            ai_message = get_random_response("greeting")
            response_type = "text"
            data = None
        
        response = ChatResponse(
            message=ai_message,
            type=response_type,
            data=data
        )
        
        logger.info(f"Chat response: {response}")
        return response
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=f"チャット応答の生成に失敗しました: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting UmaOracle AI API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)