from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import logging
from middleware.rate_limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["v2_ilogic"])

# I-Logic用のリクエストモデル
class BatchILogicRequest(BaseModel):
    race_id: str
    horses: List[str]
    venue: Optional[str] = None
    race_number: Optional[int] = None
    jockeys: Optional[List[str]] = None
    posts: Optional[List[int]] = None
    horse_numbers: Optional[List[int]] = None

class HorseScore(BaseModel):
    horse_name: str
    score: float
    rank: int

class BatchILogicResponse(BaseModel):
    race_id: str
    scores: List[HorseScore]
    calculation_time: float
    error: Optional[str] = None

async def _compute_batch_ilogic(payload: BatchILogicRequest) -> BatchILogicResponse:
    """内部用: I-Logicバッチ計算"""
    start_time = datetime.now()
    
    try:
        # jockeys、posts、horse_numbersがある場合はI-Logicエンジンを使用
        if payload.jockeys and payload.posts and payload.venue:
            from services.race_analysis_engine import RaceAnalysisEngine
            
            # I-Logicエンジンのインスタンスを作成
            race_engine = RaceAnalysisEngine()
            
            # 実際のI-Logic計算を実行
            race_data = {
                'horses': payload.horses,
                'jockeys': payload.jockeys,
                'posts': payload.posts,
                'venue': payload.venue,
                'horse_numbers': payload.horse_numbers if payload.horse_numbers else list(range(1, len(payload.horses) + 1))
            }
            result = race_engine.analyze_race(race_data)
            
            if result and "scores" in result:
                scores_list = result["scores"]
            else:
                # エンジンからの結果がない場合は空のリストを返す
                scores_list = []
        else:
            # 騎手情報がない場合はエラーとする（簡易計算は行わない）
            logger.warning(f"I-Logic batch calculation requires jockeys, posts and venue. Request: {payload.dict()}")
            return BatchILogicResponse(
                race_id=payload.race_id,
                scores=[],
                calculation_time=(datetime.now() - start_time).total_seconds(),
                error="騎手情報、枠順、開催場が必要です"
            )
        
        # データが利用可能な馬のみでランキング計算
        valid_scores = [s for s in scores_list if s.get("data_available", False) and s.get("score") is not None]
        valid_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # ランキング付け
        horse_scores = []
        rank = 1
        
        # データありの馬（ランキング付き）
        for score_data in valid_scores:
            horse_scores.append(HorseScore(
                horse_name=score_data["horse_name"],
                score=score_data["score"],
                rank=rank
            ))
            rank += 1
        
        # データなしの馬（ランク0で「データなし」を示す）
        for score_data in scores_list:
            if not score_data.get("data_available", False):
                horse_scores.append(HorseScore(
                    horse_name=score_data["horse_name"],
                    score=0.0,  # フロントエンド用に0.0を設定
                    rank=0      # ランク0で「データなし」を示す
                ))
        
        calculation_time = (datetime.now() - start_time).total_seconds()
        
        return BatchILogicResponse(
            race_id=payload.race_id,
            scores=horse_scores,
            calculation_time=calculation_time
        )
        
    except Exception as e:
        logger.error(f"Batch I-Logic calculation error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # エラー時は空の結果を返す
        calculation_time = (datetime.now() - start_time).total_seconds()
        return BatchILogicResponse(
            race_id=payload.race_id,
            scores=[],
            calculation_time=calculation_time,
            error=str(e)
        )


@router.post("/batch", response_model=BatchILogicResponse)
@limiter.limit("12/minute")
async def calculate_batch_ilogic(request: Request, payload: BatchILogicRequest):
    """
    複数馬のI-Logicスコアをバッチで計算
    """
    return await _compute_batch_ilogic(payload)

async def calculate_ilogic_batch(
    horses: List[str],
    jockeys: List[str],
    posts: List[int],
    horse_numbers: List[int],
    venue: str
) -> Optional[Dict[str, Any]]:
    """
    I-Logicバッチ計算（内部使用）
    チャット作成時にv2_race_scoresに保存するため
    """
    try:
        from services.race_analysis_engine import RaceAnalysisEngine
        
        engine = RaceAnalysisEngine()
        
        # レースアナリシス（I-Logic）計算
        analysis_result = engine.analyze_race({
            'venue': venue,
            'horses': horses,
            'jockeys': jockeys,
            'posts': posts,
            'horse_numbers': horse_numbers
        })
        
        if not analysis_result or not analysis_result.get("rankings"):
            return None
        
        # 結果を辞書形式に変換
        result = {}
        for item in analysis_result["rankings"]:
            horse_name = item["horse_name"]
            result[horse_name] = {
                "score": round(item["final_score"], 1),
                "rank": item["rank"],
                "horse_score": round(item["horse_score"], 1),
                "jockey_score": round(item["jockey_score"], 1),
                "data_available": True
            }
        
        return result
        
    except Exception as e:
        logger.error(f"I-Logicバッチ計算エラー: {e}")
        return None