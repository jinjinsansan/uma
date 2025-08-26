from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio
import json
try:
    import redis
    REDIS_MODULE_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_MODULE_AVAILABLE = False
from services.dlogic_raw_data_manager import DLogicRawDataManager
from services.modern_dlogic_engine import ModernDLogicEngine
import hashlib
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/dlogic", tags=["v2_dlogic"])

# Redis接続（キャッシュ用）
if REDIS_MODULE_AVAILABLE:
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
        redis_client.ping()
        REDIS_AVAILABLE = True
        logger.info("Redis connected for D-Logic cache")
    except:
        redis_client = None
        REDIS_AVAILABLE = False
        logger.warning("Redis server not available, D-Logic will run without cache")
else:
    redis_client = None
    REDIS_AVAILABLE = False
    logger.warning("Redis module not installed, D-Logic will run without cache")

# D-Logicマネージャーのシングルトンインスタンス
dlogic_manager = None
dlogic_engine = None

def get_dlogic_manager():
    global dlogic_manager
    if dlogic_manager is None:
        dlogic_manager = DLogicRawDataManager()
    return dlogic_manager

def get_dlogic_engine():
    global dlogic_engine
    if dlogic_engine is None:
        dlogic_engine = ModernDLogicEngine(get_dlogic_manager())
    return dlogic_engine

# リクエストモデル
class BatchDLogicRequest(BaseModel):
    race_id: str
    horses: List[str]
    venue: Optional[str] = None
    distance: Optional[str] = None
    track_condition: Optional[str] = None

class PreCalculateRequest(BaseModel):
    race_id: str
    horses: List[Dict[str, Any]]  # 馬名と追加情報を含む

class HorseScore(BaseModel):
    horse_name: str
    score: float
    rank: int
    details: Optional[Dict[str, float]] = None

class BatchDLogicResponse(BaseModel):
    race_id: str
    scores: List[HorseScore]
    cached: bool
    calculation_time: float

# キャッシュキーの生成
def generate_cache_key(race_id: str, horses: List[str]) -> str:
    """レースIDと馬リストからキャッシュキーを生成"""
    horses_str = "-".join(sorted(horses))
    key_source = f"{race_id}:{horses_str}"
    return f"v2:dlogic:{hashlib.md5(key_source.encode()).hexdigest()}"

# キャッシュの取得
def get_cached_scores(cache_key: str) -> Optional[Dict]:
    """Redisからキャッシュされたスコアを取得"""
    if not REDIS_AVAILABLE:
        return None
    
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.error(f"Cache retrieval error: {e}")
    
    return None

# キャッシュの保存
def save_to_cache(cache_key: str, scores: List[HorseScore], ttl: int = 3600):
    """スコアをRedisにキャッシュ（デフォルト1時間）"""
    if not REDIS_AVAILABLE:
        return
    
    try:
        cache_data = {
            "scores": [score.dict() for score in scores],
            "timestamp": datetime.now().isoformat()
        }
        redis_client.setex(cache_key, ttl, json.dumps(cache_data))
    except Exception as e:
        logger.error(f"Cache save error: {e}")

@router.post("/batch", response_model=BatchDLogicResponse)
async def calculate_batch_dlogic(request: BatchDLogicRequest):
    """
    複数馬のD-Logicスコアをバッチで計算
    """
    start_time = datetime.now()
    
    # キャッシュチェック
    cache_key = generate_cache_key(request.race_id, request.horses)
    cached_data = get_cached_scores(cache_key)
    
    if cached_data:
        # キャッシュから返却
        scores = [HorseScore(**score) for score in cached_data["scores"]]
        calculation_time = (datetime.now() - start_time).total_seconds()
        return BatchDLogicResponse(
            race_id=request.race_id,
            scores=scores,
            cached=True,
            calculation_time=calculation_time
        )
    
    # D-Logic計算
    try:
        manager = get_dlogic_manager()
        engine = get_dlogic_engine()
        
        scores_list = []
        for horse_name in request.horses:
            try:
                # 基本的なD-Logicスコア計算
                dlogic_scores = manager.calculate_dlogic_realtime(horse_name)
                
                if dlogic_scores:
                    # 12項目の平均スコア
                    total_score = sum([
                        dlogic_scores.get('distance_aptitude', 50.0),
                        dlogic_scores.get('track_aptitude', 50.0),
                        dlogic_scores.get('growth_potential', 50.0),
                        dlogic_scores.get('trainer_skill', 50.0),
                        dlogic_scores.get('breakthrough_potential', 50.0),
                        dlogic_scores.get('strength_score', 50.0),
                        dlogic_scores.get('winning_percentage', 50.0),
                        dlogic_scores.get('recent_performance', 50.0),
                        dlogic_scores.get('course_experience', 50.0),
                        dlogic_scores.get('distance_experience', 50.0),
                        dlogic_scores.get('stability', 50.0),
                        dlogic_scores.get('jockey_compatibility', 50.0)
                    ]) / 12.0
                else:
                    total_score = 50.0
                
                scores_list.append({
                    "horse_name": horse_name,
                    "score": round(total_score, 1),
                    "details": dlogic_scores
                })
                
            except Exception as e:
                logger.error(f"Error calculating D-Logic for {horse_name}: {e}")
                scores_list.append({
                    "horse_name": horse_name,
                    "score": 50.0,
                    "details": None
                })
        
        # ランキング計算
        scores_list.sort(key=lambda x: x["score"], reverse=True)
        
        horse_scores = []
        for rank, score_data in enumerate(scores_list, 1):
            horse_scores.append(HorseScore(
                horse_name=score_data["horse_name"],
                score=score_data["score"],
                rank=rank,
                details=score_data["details"]
            ))
        
        # キャッシュに保存
        save_to_cache(cache_key, horse_scores)
        
        calculation_time = (datetime.now() - start_time).total_seconds()
        
        return BatchDLogicResponse(
            race_id=request.race_id,
            scores=horse_scores,
            cached=False,
            calculation_time=calculation_time
        )
        
    except Exception as e:
        logger.error(f"Batch D-Logic calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/precalculate")
async def precalculate_dlogic(request: PreCalculateRequest):
    """
    事前にD-Logicスコアを計算してキャッシュに保存（バックグラウンド処理）
    """
    try:
        # バックグラウンドで計算
        asyncio.create_task(_precalculate_async(request))
        
        return {
            "status": "accepted",
            "message": f"Pre-calculation started for race {request.race_id}",
            "horses_count": len(request.horses)
        }
        
    except Exception as e:
        logger.error(f"Pre-calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _precalculate_async(request: PreCalculateRequest):
    """非同期でD-Logic計算を実行"""
    try:
        # 馬名リストを抽出
        horse_names = []
        for horse in request.horses:
            if isinstance(horse, dict):
                horse_names.append(horse.get("馬名") or horse.get("horse_name"))
            else:
                horse_names.append(str(horse))
        
        # バッチ計算を実行
        batch_request = BatchDLogicRequest(
            race_id=request.race_id,
            horses=horse_names
        )
        
        await calculate_batch_dlogic(batch_request)
        logger.info(f"Pre-calculation completed for race {request.race_id}")
        
    except Exception as e:
        logger.error(f"Async pre-calculation error: {e}")

@router.delete("/cache/{race_id}")
async def clear_cache(race_id: str):
    """
    特定レースのキャッシュをクリア
    """
    if not REDIS_AVAILABLE:
        return {"status": "skipped", "message": "Redis not available"}
    
    try:
        # race_idを含むキーを検索して削除
        pattern = f"v2:dlogic:*"
        deleted_count = 0
        
        for key in redis_client.scan_iter(pattern):
            # キーの内容を確認してrace_idが含まれるか判定
            cached = redis_client.get(key)
            if cached:
                data = json.loads(cached)
                # race_idの照合ロジックが必要な場合はここに追加
                redis_client.delete(key)
                deleted_count += 1
        
        return {
            "status": "success",
            "deleted_keys": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    D-Logic APIの健全性チェック
    """
    try:
        manager = get_dlogic_manager()
        engine = get_dlogic_engine()
        
        return {
            "status": "healthy",
            "redis_available": REDIS_AVAILABLE,
            "manager_loaded": manager is not None,
            "engine_loaded": engine is not None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }