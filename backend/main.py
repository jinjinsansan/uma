from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from openai import OpenAI
import os
from datetime import datetime
import json
import gc

# ガベージコレクションの最適化（保守的な設定）
# デフォルト値は (700, 10, 10)
# この設定により、GC頻度を適度に減らしつつ安定性を保つ
# 効果：大きなファイル読み込み時のパフォーマンス向上（5-10%）
# リスク：メモリ使用量が若干増加（5-10%）
gc.set_threshold(1000, 15, 15)
print(f"[GC設定] 閾値を変更しました: {gc.get_threshold()}")

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
from api.admin_cache import router as admin_cache_router
from api.mylogic import router as mylogic_router
# from api.future_races import router as future_races_router  # 一時的にコメントアウト（pymysqlエラー回避）
from api.batch_dlogic_complete import router as batch_dlogic_router
from api.race_analysis_v2 import router as race_analysis_v2_router
from api.jockey_data import router as jockey_data_router
from api.archive_races import router as archive_races_router
from models.d_logic_models import ChatDLogicRequest, ChatDLogicResponse
from services.knowledge_base import KnowledgeBase

app = FastAPI(title="Dロジック競馬予想AI", version="2.0.0")

# CORS設定（環境変数で動的に設定可能）
import os

# 環境変数からCORS設定を読み込む（デフォルト値を含む）
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []

# 基本的な許可オリジン
DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:3004",
    "https://uma-oracle-ai.netlify.app",
    "https://dlogicai.in",
    "https://www.dlogicai.in",
    "https://d-logic-ai-frontend.vercel.app",
    "https://d-logic-ai-frontend-git-main-jinjinsansans-projects.vercel.app"
]

# 開発環境では全オリジンを許可（本番環境では厳密に）
if os.getenv("ENVIRONMENT") == "development":
    allowed_origins = ["*"]
else:
    allowed_origins = DEFAULT_ORIGINS + CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Session-Token", "X-User-Email"],  # カスタムヘッダーを追加
    expose_headers=["*"]  # レスポンスヘッダーも公開
)

# OpenAI API設定
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

# ナレッジベース初期化
kb = KnowledgeBase()

# アプリケーション起動時に全ナレッジファイルを初期化
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の初期化処理"""
    print("=" * 80)
    print("🚀 アプリケーション起動時の初期化開始...")
    print("=" * 80)
    
    # 1. 通常のナレッジファイル（FastDLogicEngine経由で自動的に初期化される）
    try:
        from api.chat import fast_engine_instance
        print("✅ 通常ナレッジファイル: FastDLogicEngine経由で初期化済み")
    except Exception as e:
        print(f"⚠️  通常ナレッジファイル初期化エラー: {e}")
    
    # 2. 騎手ナレッジファイル
    try:
        from services.jockey_data_manager import jockey_manager
        jockey_count = len(jockey_manager.jockey_data)
        print(f"✅ 騎手ナレッジファイル: {jockey_count}騎手のデータを初期化")
    except Exception as e:
        print(f"⚠️  騎手ナレッジファイル初期化エラー: {e}")
    
    # 3. 拡張ナレッジファイル（レース分析V2用）
    try:
        from services.extended_knowledge_manager import get_extended_knowledge_manager
        extended_manager = get_extended_knowledge_manager()
        extended_horses = extended_manager.get_all_horses()
        print(f"✅ 拡張ナレッジファイル: {len(extended_horses)}頭のデータを初期化")
        
        # レース分析エンジンも事前に初期化
        from services.race_analysis_engine import get_race_analysis_engine
        from api.chat import fast_engine_instance
        race_engine = get_race_analysis_engine(fast_engine_instance)
        print("✅ レース分析エンジン: 初期化完了")
    except Exception as e:
        print(f"⚠️  拡張ナレッジファイル初期化エラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)
    print("✅ 起動時初期化完了")
    print("=" * 80)

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
app.include_router(admin_cache_router, tags=["Admin Cache"])
app.include_router(mylogic_router, tags=["MyLogicAI"])
# app.include_router(future_races_router, prefix="/api/future-races", tags=["Future Races"])
app.include_router(batch_dlogic_router, tags=["Batch D-Logic Analysis"])
app.include_router(race_analysis_v2_router, prefix="/api/race-analysis-v2", tags=["Race Analysis V2"])
app.include_router(jockey_data_router, prefix="/api", tags=["Jockey Data"])
app.include_router(archive_races_router, tags=["Archive Races"])

# Logic Chat V2の新しいルーターを追加（既存システムに影響なし）
from api.v2 import logic_chat, imlogic_settings, logic_chat_test
app.include_router(logic_chat.router)
app.include_router(imlogic_settings.router)
app.include_router(logic_chat_test.router)

# V2システムの新しいAPI（ポイント制）
try:
    from api.v2 import points as v2_points_router
    from api.v2 import chat as v2_chat_router
    from api.v2 import health as v2_health_router
    app.include_router(v2_points_router.router)
    app.include_router(v2_chat_router.router)
    app.include_router(v2_health_router.router)
    print("✅ V2ポイント制システムAPI登録完了")
except ImportError as e:
    print(f"⚠️ V2ポイント制システムAPIが見つかりません（開発中）: {e}")

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
    try:
        import uvicorn
        print("🚀 Uvicornでサーバーを起動します...")
        uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
    except ImportError:
        print("⚠️ Uvicornが見つかりません。")
        print("以下のコマンドでインストールしてください：")
        print("pip install uvicorn==0.35.0")
        print("\nまたは、以下のコマンドで直接起動してください：")
        print("python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload")

