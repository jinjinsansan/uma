from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
from datetime import datetime
import json
import logging
import random
import math

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="UmaOracle AI API", version="1.0.0")

# CORS設定 - より広範囲のドメインを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://uma-oracle-ai.netlify.app",
        "https://*.netlify.app",
        "https://*.onrender.com",
        "*"  # 開発中は全てのドメインを許可
    ],
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

# サンプル馬データ（より詳細なデータ）
SAMPLE_HORSES = [
    {
        "name": "シンボリクリスエス",
        "base_score": 75,
        "running_style": "先行",
        "course_direction": "右周り",
        "distance_category": "2000-2400m",
        "interval_category": "中3-4",
        "course_specific": "東京芝",
        "horse_count": "13-16頭",
        "track_condition": "良",
        "season_category": "4-6月"
    },
    {
        "name": "ディープインパクト",
        "base_score": 85,
        "running_style": "差し",
        "course_direction": "左周り",
        "distance_category": "1800-2000m",
        "interval_category": "中5-8",
        "course_specific": "阪神芝",
        "horse_count": "8-12頭",
        "track_condition": "良",
        "season_category": "10-12月"
    },
    {
        "name": "オルフェーヴル",
        "base_score": 70,
        "running_style": "追込",
        "course_direction": "右周り",
        "distance_category": "2400-3000m",
        "interval_category": "中9-12",
        "course_specific": "東京芝",
        "horse_count": "16-17頭",
        "track_condition": "重",
        "season_category": "1-3月"
    },
    {
        "name": "ジェンティルドンナ",
        "base_score": 65,
        "running_style": "先行",
        "course_direction": "左周り",
        "distance_category": "1600m",
        "interval_category": "中2",
        "course_specific": "阪神芝",
        "horse_count": "7頭以下",
        "track_condition": "やや重",
        "season_category": "7-9月"
    },
    {
        "name": "キタサンブラック",
        "base_score": 80,
        "running_style": "逃げ",
        "course_direction": "右周り",
        "distance_category": "2200m",
        "interval_category": "中1",
        "course_specific": "東京芝",
        "horse_count": "13-16頭",
        "track_condition": "良",
        "season_category": "4-6月"
    },
    {
        "name": "アーモンドアイ",
        "base_score": 90,
        "running_style": "先行",
        "course_direction": "左周り",
        "distance_category": "1600m",
        "interval_category": "連闘",
        "course_specific": "阪神芝",
        "horse_count": "8-12頭",
        "track_condition": "良",
        "season_category": "10-12月"
    },
    {
        "name": "クロノジェネシス",
        "base_score": 72,
        "running_style": "差し",
        "course_direction": "右周り",
        "distance_category": "1800-2000m",
        "interval_category": "中5-8",
        "course_specific": "東京芝",
        "horse_count": "13-16頭",
        "track_condition": "良",
        "season_category": "7-9月"
    },
    {
        "name": "グランアレグリア",
        "base_score": 68,
        "running_style": "先行",
        "course_direction": "左周り",
        "distance_category": "1400m",
        "interval_category": "中3-4",
        "course_specific": "阪神芝",
        "horse_count": "8-12頭",
        "track_condition": "良",
        "season_category": "4-6月"
    }
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
        'sample_data': {'1000-1200m': 0.30, '1400m': 0.35, '1600m': 0.40, '1800-2000m': 0.45, '2200m': 0.50, '2000-2400m': 0.55, '2500m': 0.60, '2400-3000m': 0.65, '3000-3600m': 0.70}
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

# 8条件計算エンジン
class PredictionEngine:
    def __init__(self):
        self.conditions_data = CONDITIONS_DATA
        self.weights = [0.40, 0.30, 0.20, 0.10]  # 1位40%、2位30%、3位20%、4位10%
    
    def calculate_condition_score(self, horse_data: dict, condition_id: str) -> float:
        """各条件のスコアを計算"""
        condition_data = self.conditions_data.get(condition_id)
        if not condition_data:
            return 0.0
        
        # 馬の該当条件の値を取得
        condition_field_map = {
            '1_running_style': 'running_style',
            '2_course_direction': 'course_direction',
            '3_distance_category': 'distance_category',
            '4_interval_category': 'interval_category',
            '5_course_specific': 'course_specific',
            '6_horse_count': 'horse_count',
            '7_track_condition': 'track_condition',
            '8_season_category': 'season_category'
        }
        
        field_name = condition_field_map.get(condition_id)
        if not field_name or field_name not in horse_data:
            return 0.0
        
        horse_value = horse_data[field_name]
        sample_data = condition_data['sample_data']
        
        # 複勝率からスコアを計算（0-100点）
        win_rate = sample_data.get(horse_value, 0.25)  # デフォルト値
        score = win_rate * 100
        return score
    
    def calculate_final_score(self, horse_data: dict, selected_conditions: List[str]) -> float:
        """最終指数を計算（0-100点）"""
        if len(selected_conditions) == 0:
            return horse_data['base_score']
        
        # 各条件のスコアを計算
        condition_scores = []
        for condition_id in selected_conditions:
            score = self.calculate_condition_score(horse_data, condition_id)
            condition_scores.append(score)
        
        # 重み付け計算
        weighted_score = 0.0
        for i, score in enumerate(condition_scores):
            if i < len(self.weights):
                weighted_score += score * self.weights[i]
        
        # ベーススコアとの加重平均
        base_score = horse_data['base_score']
        final_score = (weighted_score * 0.7) + (base_score * 0.3)
        
        # 0-100点に制限
        return max(0, min(100, final_score))
    
    def determine_confidence(self, horses: List[dict]) -> str:
        """信頼度を決定（高・中・低）"""
        if not horses:
            return "medium"
        
        # 平均スコアを計算
        avg_score = sum(horse.get('final_score', 0) for horse in horses) / len(horses)
        
        # スコアの分散を計算
        scores = [horse.get('final_score', 0) for horse in horses]
        variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)
        
        # 信頼度判定
        if avg_score >= 80 and variance < 100:  # 高スコアで分散が小さい
            return "high"
        elif avg_score >= 60:
            return "medium"
        else:
            return "low"

# 予想エンジンのインスタンス
prediction_engine = PredictionEngine()

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

def get_random_response(category: str) -> str:
    """カテゴリに応じたランダムなレスポンスを取得"""
    responses = FIXED_RESPONSES.get(category, FIXED_RESPONSES["general"])
    return random.choice(responses)

@app.get("/")
async def root():
    """ヘルスチェック用エンドポイント"""
    logger.info("Health check endpoint accessed")
    return {"message": "UmaOracle AI API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """詳細なヘルスチェック"""
    logger.info("Detailed health check endpoint accessed")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/conditions")
async def get_conditions():
    """8条件の一覧を取得"""
    try:
        logger.info("Conditions endpoint accessed")
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
        
        # 馬のデータをコピー
        horses = SAMPLE_HORSES.copy()
        
        # 各馬の最終指数を計算
        for horse in horses:
            final_score = prediction_engine.calculate_final_score(horse, request.selected_conditions)
            horse["final_score"] = round(final_score, 1)  # 小数点1位まで
        
        # スコアでソート（降順）
        horses.sort(key=lambda x: x["final_score"], reverse=True)
        
        # ランキングを追加
        for i, horse in enumerate(horses):
            horse["rank"] = i + 1
        
        # 信頼度を決定
        confidence = prediction_engine.determine_confidence(horses)
        
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