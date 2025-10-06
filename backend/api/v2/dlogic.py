from fastapi import APIRouter, HTTPException, Request
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
from middleware.rate_limiter import limiter
import hashlib
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["v2_dlogic"])

# Redis接続（統合キャッシュサービス使用）
try:
    from services.redis_cache import get_redis_cache
    redis_cache = get_redis_cache()
    REDIS_AVAILABLE = redis_cache.is_connected()
    if REDIS_AVAILABLE:
        logger.info("Redis connected for V2 D-Logic cache via unified service")
    else:
        logger.warning("Redis not available, V2 D-Logic will use memory cache")
except ImportError as e:
    redis_cache = None
    REDIS_AVAILABLE = False
    logger.warning(f"Redis cache service not available: {e}")

# D-Logicマネージャーのシングルトンインスタンス
# main.pyで初期化されたインスタンスを再利用して初回ロード時間を削減
dlogic_manager = None
dlogic_engine = None


def _get_total_horses(manager: Any) -> int:
    if hasattr(manager, "get_total_horses"):
        try:
            return manager.get_total_horses()
        except Exception as exc:
            logger.debug(f"get_total_horses unavailable: {exc}")

    knowledge = getattr(manager, "knowledge_data", None)
    if isinstance(knowledge, dict):
        horses = knowledge.get("horses", {})
        if isinstance(horses, dict):
            return len(horses)
    return 0

def get_dlogic_manager():
    global dlogic_manager
    if dlogic_manager is None:
        # 既存のfast_engine_instanceから共有インスタンスを取得
        try:
            from api.chat import fast_engine_instance
            # FastDLogicEngineが既にDLogicRawDataManagerを保持
            dlogic_manager = fast_engine_instance.raw_manager
            horses_count = _get_total_horses(dlogic_manager)
            logger.info(f"V2 D-Logic: Using pre-initialized knowledge from FastDLogicEngine (horses: {horses_count})")
            print(f"✅ V2 D-Logic: Using shared instance from FastDLogicEngine (horses: {horses_count})")
        except ImportError as e:
            # フォールバック：新規作成（互換性のため）
            logger.warning(f"V2 D-Logic: ImportError - {e}")
            print(f"⚠️ V2 D-Logic: ImportError when getting fast_engine_instance - {e}")
            logger.warning("V2 D-Logic: Creating new DLogicRawDataManager instance")
            dlogic_manager = DLogicRawDataManager()
            horses_count = _get_total_horses(dlogic_manager)
            print(f"⚠️ V2 D-Logic: Created new instance (horses: {horses_count})")
        except Exception as e:
            logger.error(f"V2 D-Logic: Unexpected error - {e}")
            print(f"❌ V2 D-Logic: Unexpected error - {e}")
            dlogic_manager = DLogicRawDataManager()
    else:
        horses_count = _get_total_horses(dlogic_manager)
        print(f"♻️ V2 D-Logic: Using existing instance (horses: {horses_count})")
    return dlogic_manager

def get_dlogic_engine():
    global dlogic_engine
    if dlogic_engine is None:
        # FastDLogicEngineはsingletonなので遅延インポートして共通インスタンスを取得
        from services.fast_dlogic_engine import FastDLogicEngine

        base_engine = FastDLogicEngine()

        # FastDLogicEngineのraw_managerが最新のマネージャーを参照するように同期
        manager = get_dlogic_manager()
        if hasattr(base_engine, "raw_manager") and base_engine.raw_manager is not manager:
            base_engine.raw_manager = manager

        dlogic_engine = ModernDLogicEngine(base_engine)
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
    error: Optional[str] = None

# キャッシュキーの生成
def generate_cache_key(race_id: str, horses: List[str]) -> str:
    """レースIDと馬リストからキャッシュキーを生成"""
    horses_str = "-".join(sorted(horses))
    key_source = f"{race_id}:{horses_str}"
    return f"v2:dlogic:{hashlib.md5(key_source.encode()).hexdigest()}"

# キャッシュの取得
def get_cached_scores(cache_key: str) -> Optional[Dict]:
    """統合Redisキャッシュからスコアを取得"""
    if not REDIS_AVAILABLE or not redis_cache:
        return None
    
    try:
        cached_data = redis_cache.get(cache_key)
        if cached_data:
            return cached_data
    except Exception as e:
        logger.error(f"V2 Cache retrieval error: {e}")
    
    return None

# キャッシュの保存
def save_to_cache(cache_key: str, scores: List[HorseScore], ttl: int = 3600):
    """統合Redisキャッシュにスコアを保存（デフォルト1時間）"""
    if not REDIS_AVAILABLE or not redis_cache:
        return
    
    try:
        cache_data = {
            "scores": [score.dict() for score in scores],
            "timestamp": datetime.now().isoformat()
        }
        success = redis_cache.set(cache_key, cache_data, ttl=ttl)
        if success:
            logger.info(f"V2 D-Logic scores cached: {cache_key} (TTL: {ttl}s)")
    except Exception as e:
        logger.error(f"V2 Cache save error: {e}")

async def _compute_batch_dlogic(payload: BatchDLogicRequest) -> BatchDLogicResponse:
    """内部用: D-Logicバッチ計算"""
    start_time = datetime.now()
    
    # キャッシュチェック
    cache_key = generate_cache_key(payload.race_id, payload.horses)
    cached_data = get_cached_scores(cache_key)
    
    if cached_data:
        # キャッシュから返却
        scores = [HorseScore(**score) for score in cached_data["scores"]]
        calculation_time = (datetime.now() - start_time).total_seconds()
        return BatchDLogicResponse(
            race_id=payload.race_id,
            scores=scores,
            cached=True,
            calculation_time=calculation_time
        )
    
    # D-Logic計算
    try:
        manager = get_dlogic_manager()
        engine = get_dlogic_engine()
        
        scores_list = []
        for horse_name in payload.horses:
            try:
                # 基本的なD-Logicスコア計算
                dlogic_scores = manager.calculate_dlogic_realtime(horse_name)
                
                # エラーチェック：馬データが存在しない場合
                if "error" in dlogic_scores:
                    # データが存在しない馬の場合
                    scores_list.append({
                        "horse_name": horse_name,
                        "score": None,  # スコアをNullにして「データなし」を示す
                        "details": None,
                        "data_available": False
                    })
                    continue
                
                if dlogic_scores and "total_score" in dlogic_scores:
                    # ナレッジベースから正常に計算された場合
                    total_score = dlogic_scores.get('total_score', 50.0)
                    
                    # 12項目詳細スコア
                    details = dlogic_scores.get('d_logic_scores', {})
                else:
                    # データが不完全な場合のフォールバック
                    total_score = 50.0
                    details = None
                
                scores_list.append({
                    "horse_name": horse_name,
                    "score": round(total_score, 1),
                    "details": details,
                    "data_available": True
                })
                
            except Exception as e:
                logger.error(f"Error calculating D-Logic for {horse_name}: {e}")
                scores_list.append({
                    "horse_name": horse_name,
                    "score": None,
                    "details": None,
                    "data_available": False
                })
        
        # データが利用可能な馬のみでランキング計算
        valid_scores = [s for s in scores_list if s.get("data_available", False) and s.get("score") is not None]
        valid_scores.sort(key=lambda x: x["score"], reverse=True)
        
        horse_scores = []
        rank = 1
        
        # データありの馬（ランキング付き）
        for score_data in valid_scores:
            horse_scores.append(HorseScore(
                horse_name=score_data["horse_name"],
                score=score_data["score"],
                rank=rank,
                details=score_data["details"]
            ))
            rank += 1
        
        # データなしの馬（ランク0で「データなし」を示す）
        for score_data in scores_list:
            if not score_data.get("data_available", False):
                horse_scores.append(HorseScore(
                    horse_name=score_data["horse_name"],
                    score=0.0,  # フロントエンド用に0.0を設定
                    rank=0,      # ランク0で「データなし」を示す
                    details=None
                ))
        
        # キャッシュに保存
        save_to_cache(cache_key, horse_scores)
        
        calculation_time = (datetime.now() - start_time).total_seconds()
        
        return BatchDLogicResponse(
            race_id=payload.race_id,
            scores=horse_scores,
            cached=False,
            calculation_time=calculation_time
        )
        
    except Exception as e:
        logger.error(f"Batch D-Logic calculation error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # エラーでも部分的な結果を返す
        if 'horse_scores' in locals() and horse_scores:
            return BatchDLogicResponse(
                race_id=payload.race_id,
                scores=horse_scores,
                cached=False,
                calculation_time=(datetime.now() - start_time).total_seconds(),
                error=str(e)
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchDLogicResponse)
@limiter.limit("15/minute")
async def calculate_batch_dlogic(request: Request, payload: BatchDLogicRequest):
    """
    複数馬のD-Logicスコアをバッチで計算
    """
    return await _compute_batch_dlogic(payload)

async def calculate_dlogic_batch(horses: List[str]) -> Optional[Dict[str, Any]]:
    """
    D-Logicバッチ計算（内部使用）
    チャット作成時にv2_race_scoresに保存するため
    """
    try:
        manager = get_dlogic_manager()
        engine = get_dlogic_engine()
        
        result = {}
        for horse_name in horses:
            try:
                dlogic_scores = manager.calculate_dlogic_realtime(horse_name)
                
                if "error" in dlogic_scores:
                    result[horse_name] = {
                        "score": None,
                        "rank": 0,
                        "data_available": False
                    }
                    continue
                
                if dlogic_scores and "total_score" in dlogic_scores:
                    total_score = dlogic_scores.get('total_score', 50.0)
                    details = dlogic_scores.get('d_logic_scores', {})
                else:
                    total_score = 50.0
                    details = None
                
                result[horse_name] = {
                    "score": round(total_score, 1),
                    "details": details,
                    "data_available": True
                }
                
            except Exception as e:
                logger.error(f"Error calculating D-Logic for {horse_name}: {e}")
                result[horse_name] = {
                    "score": None,
                    "rank": 0,
                    "data_available": False
                }
        
        # ランク付け
        valid_horses = [h for h in result.keys() if result[h].get("data_available", False)]
        sorted_horses = sorted(valid_horses, key=lambda h: result[h]["score"], reverse=True)
        
        for rank, horse_name in enumerate(sorted_horses, 1):
            result[horse_name]["rank"] = rank
        
        return result
        
    except Exception as e:
        logger.error(f"D-Logicバッチ計算エラー: {e}")
        return None

@router.post("/precalculate")
@limiter.limit("6/minute")
async def precalculate_dlogic(request: Request, payload: PreCalculateRequest):
    """
    事前にD-Logicスコアを計算してキャッシュに保存（バックグラウンド処理）
    """
    try:
        # バックグラウンドで計算
        asyncio.create_task(_precalculate_async(payload))
        
        return {
            "status": "accepted",
            "message": f"Pre-calculation started for race {payload.race_id}",
            "horses_count": len(payload.horses)
        }
        
    except Exception as e:
        logger.error(f"Pre-calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _precalculate_async(request_data: PreCalculateRequest):
    """非同期でD-Logic計算を実行"""
    try:
        # 馬名リストを抽出
        horse_names = []
        for horse in request_data.horses:
            if isinstance(horse, dict):
                horse_names.append(horse.get("馬名") or horse.get("horse_name"))
            else:
                horse_names.append(str(horse))
        
        # バッチ計算を実行
        batch_request = BatchDLogicRequest(
            race_id=request_data.race_id,
            horses=horse_names
        )
        
        await _compute_batch_dlogic(batch_request)
        logger.info(f"Pre-calculation completed for race {request_data.race_id}")
        
    except Exception as e:
        logger.error(f"Async pre-calculation error: {e}")

@router.delete("/cache/{race_id}")
@limiter.limit("5/minute")
async def clear_cache(request: Request, race_id: str):
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