"""
レースアナリシスV2 APIエンドポイント
イクイノックス基準の総合分析
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from services.race_analysis_engine import get_race_analysis_engine

logger = logging.getLogger(__name__)

router = APIRouter()

class RaceAnalysisRequest(BaseModel):
    """レース分析リクエスト"""
    race_date: str  # YYYY-MM-DD
    venue: str
    race_number: int
    race_name: Optional[str] = None
    grade: Optional[str] = None
    distance: Optional[str] = None
    track_condition: str = "良"
    
    # 出走情報（アーカイブから取得する場合は不要）
    horses: Optional[List[str]] = None
    jockeys: Optional[List[str]] = None
    posts: Optional[List[int]] = None
    horse_numbers: Optional[List[int]] = None

class QuickAnalysisRequest(BaseModel):
    """クイック分析リクエスト（会話から）"""
    message: str  # 例: "札幌記念を分析して"
    track_condition: Optional[str] = "良"

@router.post("/api/race-analysis-v2")
async def analyze_race(request: RaceAnalysisRequest):
    """
    レース総合分析（イクイノックス基準）
    """
    try:
        logger.info(f"レース分析リクエスト: {request.venue} {request.race_number}R")
        
        # アーカイブデータから情報を取得する場合
        if not request.horses:
            # TODO: アーカイブページとの連携実装
            # 現在はエラーを返す
            raise HTTPException(
                status_code=400,
                detail="出走情報が指定されていません。アーカイブ連携は開発中です。"
            )
        
        # レースデータの構築
        race_data = {
            'venue': request.venue,
            'race_number': request.race_number,
            'race_name': request.race_name or f"{request.venue}{request.race_number}R",
            'grade': request.grade or '',
            'distance': request.distance or '',
            'track_condition': request.track_condition,
            'horses': request.horses,
            'jockeys': request.jockeys or [],
            'posts': request.posts or [],
            'horse_numbers': request.horse_numbers or []
        }
        
        # 分析実行（chat.pyの共有インスタンスを使用）
        from api.chat import fast_engine_instance
        race_analysis_engine = get_race_analysis_engine(fast_engine_instance)
        result = race_analysis_engine.analyze_race(race_data)
        
        # エラーチェック
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        # 実行時刻を追加
        result['analyzed_at'] = datetime.now().isoformat()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"レース分析エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/race-analysis-v2/quick")
async def quick_analyze(request: QuickAnalysisRequest):
    """
    クイック分析（会話形式から）
    """
    try:
        # TODO: メッセージからレース情報を抽出
        # 現在はプレースホルダー
        return {
            "message": "クイック分析機能は開発中です",
            "request": request.message,
            "analysis_type": "race_analysis_v2"
        }
        
    except Exception as e:
        logger.error(f"クイック分析エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/race-analysis-v2/test")
async def test_analysis():
    """
    テスト用エンドポイント
    """
    # テストデータで分析実行
    test_data = {
        'venue': '東京',
        'race_number': 11,
        'race_name': 'テストレース',
        'grade': 'G1',
        'distance': '2000m',
        'track_condition': '良',
        'horses': ['イクイノックス', 'ドウデュース', 'ジャスティンパレス'],
        'jockeys': ['C.ルメール', '武豊', '横山和生'],
        'posts': [1, 2, 3],
        'horse_numbers': [1, 2, 3]
    }
    
    # テスト用でもchat.pyの共有インスタンスを使用
    from api.chat import fast_engine_instance
    race_analysis_engine = get_race_analysis_engine(fast_engine_instance)
    result = race_analysis_engine.analyze_race(test_data)
    
    return {
        "message": "テスト分析完了",
        "sample_result": result.get('results', [])[:3],  # 上位3頭のみ
        "analysis_type": "race_analysis_v2",
        "base_horse": "イクイノックス"
    }

@router.post("/chat")
async def race_analysis_chat(request: Dict[str, Any]):
    """レースアナリシスチャット用エンドポイント
    
    D-Logicチャットと同じインターフェースで、レース名から自動的に分析を実行
    """
    try:
        message = request.get('message', '').strip()
        user_id = request.get('user_id')
        
        logger.info(f"Race analysis chat request: {message[:100]}...")
        
        # レース名を検出（簡易的な実装）
        race_keywords = ['記念', 'ステークス', 'カップ', 'トロフィー', '賞', 'を分析', 'を予想']
        is_race_query = any(keyword in message for keyword in race_keywords)
        
        if not is_race_query:
            return {
                "status": "success",
                "response": "レース名を入力してください。例：「札幌記念を分析して」",
                "message": message
            }
        
        # レース名の抽出（簡易版）
        race_name = message.replace('を分析して', '').replace('を予想して', '').strip()
        
        # TODO: ここでレース情報を取得して実際の分析を実行
        # 現在はモックレスポンス
        
        response_text = f"""🏆 {race_name}のレースアナリシス

現在、レースアナリシスV2は開発中です。

レースアナリシスでは、以下の情報を総合的に分析します：
• 馬の能力（70%）- 独自基準による12項目評価
• 騎手の能力（30%）- 開催場適性、枠順適性

まもなく本格稼働予定です。"""
        
        return {
            "status": "success",
            "response": response_text,
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Race analysis chat error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "status": "error",
            "response": "エラーが発生しました。しばらく待ってから再度お試しください。",
            "message": request.get('message', ''),
            "error": str(e)
        }