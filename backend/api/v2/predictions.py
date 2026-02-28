"""
V2競馬予想新聞用 全エンジン予想一括取得API
認証不要・ポイント消費なし
レースアーカイブ作成時に呼び出して静的データとして保存する用途
"""
from fastapi import APIRouter
from typing import List, Optional, Dict
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["v2_predictions"])


class NewspaperPredictionRequest(BaseModel):
    race_id: str
    horses: List[str]
    horse_numbers: List[int]
    venue: Optional[str] = None
    race_number: Optional[int] = None
    jockeys: Optional[List[str]] = None
    posts: Optional[List[int]] = None
    distance: Optional[str] = None
    track_condition: Optional[str] = None
    odds: Optional[List[float]] = None


class NewspaperPredictionResponse(BaseModel):
    race_id: str
    dlogic: List[int]
    ilogic: List[int]
    viewlogic: List[int]
    metalogic: List[int]


def _names_to_numbers(ranked_names: List[str], horses: List[str], horse_numbers: List[int]) -> List[int]:
    """馬名の順位リストを馬番リストに変換"""
    name_to_num = {name: num for name, num in zip(horses, horse_numbers)}
    result = []
    for name in ranked_names:
        num = name_to_num.get(name)
        if num is not None:
            result.append(num)
    return result[:5]


def _scores_to_ranked_names(scores: Dict[str, float]) -> List[str]:
    """スコア辞書をスコア順の馬名リストに変換"""
    if not scores:
        return []
    return [name for name, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]


@router.post("/newspaper", response_model=NewspaperPredictionResponse)
async def get_newspaper_predictions(request: NewspaperPredictionRequest):
    """
    競馬予想新聞用: 全4エンジンの予想top-5 horse_numbersを一括返却
    - 認証不要
    - ポイント消費なし
    - レースアーカイブ作成時にfetch_jra_entries.pyから呼び出す
    """
    horses = request.horses
    horse_numbers = request.horse_numbers
    jockeys = request.jockeys or []
    posts = request.posts or []
    odds = request.odds or [0.0] * len(horses)
    venue = request.venue or ""
    distance = request.distance or ""
    track_condition = request.track_condition or "良"

    context = {
        "venue": venue,
        "distance": distance,
        "track_type": "芝" if "芝" in (distance or "") else "ダート",
        "track_condition": track_condition,
    }
    race_data = {
        "horses": horses,
        "jockeys": jockeys,
        "posts": posts,
        "odds": odds,
        "venue": venue,
        "distance": distance,
        "track_type": context["track_type"],
        "track_condition": track_condition,
    }

    dlogic_top5: List[int] = []
    ilogic_top5: List[int] = []
    viewlogic_top5: List[int] = []
    metalogic_top5: List[int] = []

    d_scores: Dict[str, float] = {}
    i_scores: Dict[str, float] = {}
    v_scores: Dict[str, float] = {}

    try:
        from services.metalogic_engine import MetaLogicEngine
        engine = MetaLogicEngine()

        # D-Logic
        try:
            d_scores = await engine.calculate_dlogic_scores(horses, context)
            dlogic_top5 = _names_to_numbers(_scores_to_ranked_names(d_scores), horses, horse_numbers)
        except Exception as e:
            logger.warning(f"D-Logic計算失敗 ({request.race_id}): {e}")

        # I-Logic
        try:
            i_scores = engine.calculate_ilogic_scores(horses, jockeys, posts, context)
            ilogic_top5 = _names_to_numbers(_scores_to_ranked_names(i_scores), horses, horse_numbers)
        except Exception as e:
            logger.warning(f"I-Logic計算失敗 ({request.race_id}): {e}")

        # ViewLogic
        try:
            v_scores = engine.calculate_viewlogic_scores(horses, jockeys, posts, context)
            viewlogic_top5 = _names_to_numbers(_scores_to_ranked_names(v_scores), horses, horse_numbers)
        except Exception as e:
            logger.warning(f"ViewLogic計算失敗 ({request.race_id}): {e}")

        # MetaLogic
        try:
            meta_results = engine.calculate_meta_scores(
                d_scores,
                i_scores,
                v_scores,
                odds,
                horses,
            )
            meta_names = [horse for horse, _, _ in meta_results]
            metalogic_top5 = _names_to_numbers(meta_names, horses, horse_numbers)
        except Exception as e:
            logger.warning(f"MetaLogic計算失敗 ({request.race_id}): {e}")

    except Exception as e:
        logger.error(f"エンジン初期化失敗 ({request.race_id}): {e}")

    return NewspaperPredictionResponse(
        race_id=request.race_id,
        dlogic=dlogic_top5,
        ilogic=ilogic_top5,
        viewlogic=viewlogic_top5,
        metalogic=metalogic_top5,
    )
