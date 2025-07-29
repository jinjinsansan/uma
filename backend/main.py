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

# 環境変数が設定されていない場合の警告
if not openai.api_key:
    logger.warning("OPENAI_API_KEY environment variable is not set. Using fixed responses.")
    OPENAI_ENABLED = False
else:
    OPENAI_ENABLED = True
    logger.info("OpenAI API is enabled")

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

# 各馬の詳細な複勝率データ（過去5走分のデータを模擬）
HORSE_DETAILED_DATA = {
    "シンボリクリスエス": {
        "base_score": 75,
        "running_style": "先行",
        "course_direction": "右周り",
        "distance_category": "2000-2400m",
        "interval_category": "中3-4",
        "course_specific": "東京芝",
        "horse_count": "13-16頭",
        "track_condition": "良",
        "season_category": "4-6月",
        # 各条件の複勝率データ（過去5走分の平均）
        "condition_rates": {
            "1_running_style": 0.28,  # 先行の複勝率
            "2_course_direction": 0.40,  # 右周りの複勝率
            "3_distance_category": 0.55,  # 2000-2400mの複勝率
            "4_interval_category": 0.40,  # 中3-4の複勝率
            "5_course_specific": 0.35,  # 東京芝の複勝率
            "6_horse_count": 0.35,  # 13-16頭の複勝率
            "7_track_condition": 0.40,  # 良の複勝率
            "8_season_category": 0.40   # 4-6月の複勝率
        }
    },
    "ディープインパクト": {
        "base_score": 85,
        "running_style": "差し",
        "course_direction": "左周り",
        "distance_category": "1800-2000m",
        "interval_category": "中5-8",
        "course_specific": "阪神芝",
        "horse_count": "8-12頭",
        "track_condition": "良",
        "season_category": "10-12月",
        "condition_rates": {
            "1_running_style": 0.22,  # 差しの複勝率
            "2_course_direction": 0.35,  # 左周りの複勝率
            "3_distance_category": 0.45,  # 1800-2000mの複勝率
            "4_interval_category": 0.45,  # 中5-8の複勝率
            "5_course_specific": 0.40,  # 阪神芝の複勝率
            "6_horse_count": 0.30,  # 8-12頭の複勝率
            "7_track_condition": 0.40,  # 良の複勝率
            "8_season_category": 0.50   # 10-12月の複勝率
        }
    },
    "オルフェーヴル": {
        "base_score": 70,
        "running_style": "追込",
        "course_direction": "右周り",
        "distance_category": "2400-3000m",
        "interval_category": "中9-12",
        "course_specific": "東京芝",
        "horse_count": "16-17頭",
        "track_condition": "重",
        "season_category": "1-3月",
        "condition_rates": {
            "1_running_style": 0.15,  # 追込の複勝率
            "2_course_direction": 0.40,  # 右周りの複勝率
            "3_distance_category": 0.65,  # 2400-3000mの複勝率
            "4_interval_category": 0.50,  # 中9-12の複勝率
            "5_course_specific": 0.35,  # 東京芝の複勝率
            "6_horse_count": 0.40,  # 16-17頭の複勝率
            "7_track_condition": 0.35,  # 重の複勝率
            "8_season_category": 0.35   # 1-3月の複勝率
        }
    },
    "ジェンティルドンナ": {
        "base_score": 65,
        "running_style": "先行",
        "course_direction": "左周り",
        "distance_category": "1600m",
        "interval_category": "中2",
        "course_specific": "阪神芝",
        "horse_count": "7頭以下",
        "track_condition": "やや重",
        "season_category": "7-9月",
        "condition_rates": {
            "1_running_style": 0.28,  # 先行の複勝率
            "2_course_direction": 0.35,  # 左周りの複勝率
            "3_distance_category": 0.40,  # 1600mの複勝率
            "4_interval_category": 0.35,  # 中2の複勝率
            "5_course_specific": 0.40,  # 阪神芝の複勝率
            "6_horse_count": 0.25,  # 7頭以下の複勝率
            "7_track_condition": 0.30,  # やや重の複勝率
            "8_season_category": 0.45   # 7-9月の複勝率
        }
    },
    "キタサンブラック": {
        "base_score": 80,
        "running_style": "逃げ",
        "course_direction": "右周り",
        "distance_category": "2200m",
        "interval_category": "中1",
        "course_specific": "東京芝",
        "horse_count": "13-16頭",
        "track_condition": "良",
        "season_category": "4-6月",
        "condition_rates": {
            "1_running_style": 0.35,  # 逃げの複勝率
            "2_course_direction": 0.40,  # 右周りの複勝率
            "3_distance_category": 0.50,  # 2200mの複勝率
            "4_interval_category": 0.30,  # 中1の複勝率
            "5_course_specific": 0.35,  # 東京芝の複勝率
            "6_horse_count": 0.35,  # 13-16頭の複勝率
            "7_track_condition": 0.40,  # 良の複勝率
            "8_season_category": 0.40   # 4-6月の複勝率
        }
    },
    "アーモンドアイ": {
        "base_score": 90,
        "running_style": "先行",
        "course_direction": "左周り",
        "distance_category": "1600m",
        "interval_category": "連闘",
        "course_specific": "阪神芝",
        "horse_count": "8-12頭",
        "track_condition": "良",
        "season_category": "10-12月",
        "condition_rates": {
            "1_running_style": 0.28,  # 先行の複勝率
            "2_course_direction": 0.35,  # 左周りの複勝率
            "3_distance_category": 0.40,  # 1600mの複勝率
            "4_interval_category": 0.25,  # 連闘の複勝率
            "5_course_specific": 0.40,  # 阪神芝の複勝率
            "6_horse_count": 0.30,  # 8-12頭の複勝率
            "7_track_condition": 0.40,  # 良の複勝率
            "8_season_category": 0.50   # 10-12月の複勝率
        }
    },
    "クロノジェネシス": {
        "base_score": 72,
        "running_style": "差し",
        "course_direction": "右周り",
        "distance_category": "1800-2000m",
        "interval_category": "中5-8",
        "course_specific": "東京芝",
        "horse_count": "13-16頭",
        "track_condition": "良",
        "season_category": "7-9月",
        "condition_rates": {
            "1_running_style": 0.22,  # 差しの複勝率
            "2_course_direction": 0.40,  # 右周りの複勝率
            "3_distance_category": 0.45,  # 1800-2000mの複勝率
            "4_interval_category": 0.45,  # 中5-8の複勝率
            "5_course_specific": 0.35,  # 東京芝の複勝率
            "6_horse_count": 0.35,  # 13-16頭の複勝率
            "7_track_condition": 0.40,  # 良の複勝率
            "8_season_category": 0.45   # 7-9月の複勝率
        }
    },
    "グランアレグリア": {
        "base_score": 68,
        "running_style": "先行",
        "course_direction": "左周り",
        "distance_category": "1400m",
        "interval_category": "中3-4",
        "course_specific": "阪神芝",
        "horse_count": "8-12頭",
        "track_condition": "良",
        "season_category": "4-6月",
        "condition_rates": {
            "1_running_style": 0.28,  # 先行の複勝率
            "2_course_direction": 0.35,  # 左周りの複勝率
            "3_distance_category": 0.35,  # 1400mの複勝率
            "4_interval_category": 0.40,  # 中3-4の複勝率
            "5_course_specific": 0.40,  # 阪神芝の複勝率
            "6_horse_count": 0.30,  # 8-12頭の複勝率
            "7_track_condition": 0.40,  # 良の複勝率
            "8_season_category": 0.40   # 4-6月の複勝率
        }
    }
}

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

# 8条件計算エンジン（完璧実装）
class PredictionEngine:
    def __init__(self):
        self.conditions_data = CONDITIONS_DATA
        self.weights = [0.40, 0.30, 0.20, 0.10]  # 1位40%、2位30%、3位20%、4位10%
    
    def calculate_condition_score(self, horse_data: dict, condition_id: str) -> float:
        """各条件のスコアを計算（0-100点）"""
        # 馬の詳細データから該当条件の複勝率を取得
        condition_rates = horse_data.get('condition_rates', {})
        win_rate = condition_rates.get(condition_id, 0.25)  # デフォルト値
        
        # 複勝率を0-100点スケールに変換
        score = win_rate * 100
        
        logger.info(f"Condition {condition_id}: win_rate={win_rate}, score={score}")
        return score
    
    def calculate_final_score(self, horse_data: dict, selected_conditions: List[str]) -> float:
        """最終指数を計算（0-100点）"""
        logger.info(f"Calculating final score for {horse_data['name']} with conditions: {selected_conditions}")
        
        if len(selected_conditions) == 0:
            logger.info(f"No conditions selected, using base score: {horse_data['base_score']}")
            return horse_data['base_score']
        
        # 各条件のスコアを計算
        condition_scores = []
        for condition_id in selected_conditions:
            score = self.calculate_condition_score(horse_data, condition_id)
            condition_scores.append(score)
            logger.info(f"Condition {condition_id} score: {score}")
        
        # 重み付け計算（選択条件のみ使用）
        weighted_score = 0.0
        for i, score in enumerate(condition_scores):
            if i < len(self.weights):
                weight = self.weights[i]
                weighted_score += score * weight
                logger.info(f"Weight {i+1}: {score} × {weight} = {score * weight}")
        
        logger.info(f"Total weighted score before adjustment: {weighted_score}")
        
        # 最終指数を20-90点に制限
        final_score = max(20, min(90, weighted_score))  # 20-90点の範囲に制限
        
        logger.info(f"Final score for {horse_data['name']}: {final_score}")
        return round(final_score, 1)  # 小数点第1位まで
    
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
        if avg_score >= 70 and variance < 200:  # 高スコアで分散が小さい
            return "high"
        elif avg_score >= 50:
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

def get_openai_response(message: str, context: str = "") -> str:
    """OpenAI APIを使用してレスポンスを生成"""
    if not OPENAI_ENABLED:
        return get_random_response("general")
    
    try:
        # 競馬専門のプロンプト
        system_prompt = """あなたは競馬予想の専門AI「UmaOracle」です。

専門知識:
- JRA競馬の詳細な知識
- 8つの予想条件（脚質、コース回り、距離、出走間隔、コース、出走頭数、馬場、季節）
- 馬の血統、調教師、騎手の情報
- レース分析と予想技術

応答スタイル:
- 親切で分かりやすい説明
- 競馬初心者にも理解しやすい言葉遣い
- 具体的なアドバイスと根拠の提示
- 適度な専門用語の使用

禁止事項:
- 過度な確実性の表現
- 具体的な馬券の推奨
- 違法な情報の提供"""

        user_prompt = f"{context}\n\nユーザー: {message}\n\nUmaOracle:"
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return get_random_response("general")

def get_prediction_analysis(horses: List[dict], selected_conditions: List[str], confidence: str) -> str:
    """予想結果の詳細解説を生成"""
    if not OPENAI_ENABLED:
        return "予想結果の詳細分析をご提供いたします。"
    
    try:
        # 上位3頭の情報を整理
        top_horses = horses[:3]
        horse_info = []
        for horse in top_horses:
            horse_info.append(f"{horse['name']}: {horse['final_score']}点")
        
        analysis_prompt = f"""以下の予想結果について、競馬初心者にも分かりやすい詳細解説を提供してください：

予想結果:
{chr(10).join(horse_info)}

選択された条件: {', '.join(selected_conditions)}
信頼度: {confidence}

解説のポイント:
1. 上位馬の特徴と強み
2. 選択された条件が結果に与えた影響
3. 今後のレースでの参考ポイント
4. 競馬初心者へのアドバイス

専門的すぎず、親切で分かりやすい解説をお願いします。"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは競馬予想の専門AIです。親切で分かりやすい解説を提供してください。"},
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=400,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"OpenAI analysis error: {e}")
        return "予想結果の詳細分析をご提供いたします。"

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
    """レース予想を実行（8条件計算式完璧実装）"""
    try:
        logger.info(f"Prediction request received: {request}")
        logger.info(f"Selected conditions: {request.selected_conditions}")
        
        # 馬のデータをコピー
        horses = []
        for horse_name, horse_data in HORSE_DETAILED_DATA.items():
            horse = {
                "name": horse_name,
                "base_score": horse_data["base_score"],
                "running_style": horse_data["running_style"],
                "course_direction": horse_data["course_direction"],
                "distance_category": horse_data["distance_category"],
                "interval_category": horse_data["interval_category"],
                "course_specific": horse_data["course_specific"],
                "horse_count": horse_data["horse_count"],
                "track_condition": horse_data["track_condition"],
                "season_category": horse_data["season_category"],
                "condition_rates": horse_data["condition_rates"]
            }
            horses.append(horse)
        
        logger.info(f"Processing {len(horses)} horses")
        
        # 各馬の最終指数を計算
        for horse in horses:
            logger.info(f"Processing horse: {horse['name']}")
            final_score = prediction_engine.calculate_final_score(horse, request.selected_conditions)
            horse["final_score"] = final_score
            logger.info(f"Final score for {horse['name']}: {final_score}")
        
        # スコアでソート（降順）
        horses.sort(key=lambda x: x["final_score"], reverse=True)
        
        # ランキングを追加
        for i, horse in enumerate(horses):
            horse["rank"] = i + 1
        
        # 信頼度を決定
        confidence = prediction_engine.determine_confidence(horses)
        
        # OpenAIによる詳細解説を生成
        analysis = get_prediction_analysis(horses, request.selected_conditions, confidence)
        
        result = {
            "horses": horses,
            "confidence": confidence,
            "selectedConditions": request.selected_conditions,
            "calculationTime": datetime.now().isoformat(),
            "analysis": analysis
        }
        
        logger.info(f"Prediction completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in predict_race: {e}")
        raise HTTPException(status_code=500, detail=f"予想の実行に失敗しました: {str(e)}")

@app.post("/chat")
async def chat(request: ChatRequest):
    """チャットボット応答（OpenAI API統合）"""
    try:
        logger.info(f"Chat request received: {request.message}")
        
        # メッセージの内容に基づいてレスポンスを決定
        message_lower = request.message.lower()
        
        # 予想関連のキーワードをチェック
        prediction_keywords = ["予想", "レース", "競馬", "予測", "分析"]
        is_prediction_request = any(keyword in message_lower for keyword in prediction_keywords)
        
        if is_prediction_request:
            # 予想リクエストの場合
            ai_message = get_openai_response(request.message, "ユーザーが競馬予想を求めています。")
            response_type = "conditions"
            data = {"raceInfo": request.race_info} if request.race_info else None
        else:
            # 一般会話の場合
            ai_message = get_openai_response(request.message)
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