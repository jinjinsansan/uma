from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v2/logic-chat-test", tags=["Logic Chat V2 Test"])

# テスト用のメモリ内ストレージ
test_chats = {}
test_settings = {}

class CreateChatRequest(BaseModel):
    race_id: str
    venue: str
    race_number: int
    race_name: str
    horses: List[str]
    jockeys: List[str]
    posts: List[int]
    horse_numbers: List[int]

class AnalyzeRequest(BaseModel):
    chat_id: str
    engine_type: str  # 'imlogic', 'ilogic'
    imlogic_settings_id: Optional[str] = None
    message: str

@router.post("/create")
async def create_chat(request: CreateChatRequest):
    """新規チャット作成（テスト用）"""
    chat_id = str(uuid.uuid4())
    
    locked_race_data = {
        "venue": request.venue,
        "race_number": request.race_number,
        "race_name": request.race_name,
        "horses": request.horses,
        "jockeys": request.jockeys,
        "posts": request.posts,
        "horse_numbers": request.horse_numbers,
        "locked_at": datetime.now().isoformat()
    }
    
    test_chats[chat_id] = {
        "id": chat_id,
        "race_id": request.race_id,
        "locked_race_data": locked_race_data,
        "created_at": datetime.now().isoformat()
    }
    
    return {
        "id": chat_id,
        "race_data": locked_race_data,
        "created_at": datetime.now().isoformat()
    }

@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """分析実行（テスト用）"""
    # チャットの存在確認
    if request.chat_id not in test_chats:
        raise HTTPException(status_code=404, detail="チャットが見つかりません")
    
    chat = test_chats[request.chat_id]
    locked_race_data = chat["locked_race_data"]
    
    # エンジンの取得と実行
    if request.engine_type == "imlogic":
        # IMLogicエンジンの使用
        from services.imlogic_engine import IMLogicEngine
        
        # 設定の取得（テスト用デフォルト値）
        settings = {
            "horse_weight": 80,
            "jockey_weight": 20,
            "item_weights": {
                "1_distance_aptitude": 5.0,
                "2_bloodline_evaluation": 40.0,
                "3_jockey_compatibility": 5.0,
                "4_trainer_evaluation": 5.0,
                "5_track_aptitude": 5.0,
                "6_weather_aptitude": 5.0,
                "7_popularity_factor": 5.0,
                "8_weight_impact": 5.0,
                "9_horse_weight_impact": 5.0,
                "10_corner_specialist": 5.0,
                "11_margin_analysis": 5.0,
                "12_time_index": 10.0
            }
        }
        
        if request.imlogic_settings_id and request.imlogic_settings_id in test_settings:
            settings = test_settings[request.imlogic_settings_id]
        
        try:
            engine = IMLogicEngine()
            # 同期メソッドとして直接呼び出し
            result = engine.analyze_race(
                race_data=locked_race_data,
                horse_weight=settings["horse_weight"],
                jockey_weight=settings["jockey_weight"],
                item_weights=settings["item_weights"]
            )
            
            return result
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ IMLogic分析エラー詳細: {e}")
            print(f"❌ スタックトレース:\n{error_details}")
            
            # エラー情報を含む結果を返す
            return {
                "type": "imlogic",
                "error": f"IMLogic分析エラー: {str(e)}",
                "error_details": error_details,
                "settings": settings,
                "race_data": locked_race_data
            }
        
    elif request.engine_type == "ilogic":
        # ILogicエンジンの使用
        from services.race_analysis_engine import get_race_analysis_engine
        from api.chat import fast_engine_instance
        
        engine = get_race_analysis_engine(fast_engine_instance)
        result = engine.analyze_race(locked_race_data)
        
        return result
        
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"不明なエンジンタイプ: {request.engine_type}"
        )

# テスト用設定作成エンドポイント
@router.post("/settings/create")
async def create_test_settings(settings: Dict[str, Any]):
    """テスト用IMLogic設定作成"""
    settings_id = str(uuid.uuid4())
    test_settings[settings_id] = settings
    return {"id": settings_id}