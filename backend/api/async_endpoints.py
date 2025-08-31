"""
非同期処理エンドポイント - V1/V2共通
バックグラウンドタスクの管理API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from services.async_processor import async_processor
from services.redis_cache import get_redis_cache

logger = logging.getLogger(__name__)
router = APIRouter()

class TaskSubmitRequest(BaseModel):
    """タスク送信リクエスト"""
    task_type: str
    data: Dict[str, Any]
    priority: Optional[str] = "normal"

class TaskStatusResponse(BaseModel):
    """タスク状態レスポンス"""
    task_id: str
    status: str
    type: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None

@router.post("/async/submit")
async def submit_async_task(request: TaskSubmitRequest) -> Dict[str, str]:
    """非同期タスクを送信"""
    try:
        task_id = None
        
        # タスクタイプに応じて処理を分岐
        if request.task_type == "dlogic_batch":
            # D-Logic一括計算
            from services.dlogic_engine import DLogicEngine
            
            def calculate_batch():
                engine = DLogicEngine()
                return engine.calculate_batch(
                    horse_names=request.data.get('horse_names', []),
                    race_date=request.data.get('race_date'),
                    venue=request.data.get('venue'),
                    race_number=request.data.get('race_number')
                )
            
            task_id = await async_processor.submit_task(
                func=calculate_batch,
                task_type="dlogic_batch"
            )
            
        elif request.task_type == "race_analysis":
            # レース分析
            from services.race_analyzer import RaceAnalyzer
            
            def analyze_race():
                analyzer = RaceAnalyzer()
                return analyzer.analyze(
                    race_data=request.data.get('race_data', {}),
                    analysis_type=request.data.get('analysis_type', 'full')
                )
            
            task_id = await async_processor.submit_task(
                func=analyze_race,
                task_type="race_analysis"
            )
            
        elif request.task_type == "mylogic_batch":
            # MyLogic一括計算
            from services.mylogic_engine import MyLogicEngine
            
            def calculate_mylogic():
                engine = MyLogicEngine()
                return engine.calculate_batch(
                    horse_data=request.data.get('horse_data', []),
                    preferences=request.data.get('preferences', {})
                )
            
            task_id = await async_processor.submit_task(
                func=calculate_mylogic,
                task_type="mylogic_batch"
            )
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown task type: {request.task_type}"
            )
        
        return {
            "task_id": task_id,
            "status": "submitted",
            "message": f"Task {task_id} submitted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to submit async task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/async/status/{task_id}")
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """タスクの状態を取得"""
    task_info = async_processor.get_task_status(task_id)
    
    if not task_info:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task_info['status'],
        type=task_info['type'],
        created_at=task_info['created_at'],
        started_at=task_info.get('started_at'),
        completed_at=task_info.get('completed_at'),
        failed_at=task_info.get('failed_at'),
        result=task_info.get('result'),
        error=task_info.get('error')
    )

@router.get("/async/tasks")
async def list_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = 100
) -> List[TaskStatusResponse]:
    """タスク一覧を取得"""
    tasks = []
    
    for task_id, task_info in async_processor.tasks.items():
        # フィルタリング
        if status and task_info['status'] != status:
            continue
        if task_type and task_info['type'] != task_type:
            continue
        
        tasks.append(TaskStatusResponse(
            task_id=task_id,
            status=task_info['status'],
            type=task_info['type'],
            created_at=task_info['created_at'],
            started_at=task_info.get('started_at'),
            completed_at=task_info.get('completed_at'),
            failed_at=task_info.get('failed_at'),
            result=task_info.get('result'),
            error=task_info.get('error')
        ))
        
        if len(tasks) >= limit:
            break
    
    return tasks

@router.delete("/async/cleanup")
async def cleanup_old_tasks(hours: int = 24) -> Dict[str, str]:
    """古いタスクをクリーンアップ"""
    try:
        async_processor.cleanup_old_tasks(hours=hours)
        return {
            "status": "success",
            "message": f"Cleaned up tasks older than {hours} hours"
        }
    except Exception as e:
        logger.error(f"Failed to cleanup tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# キャッシュ管理エンドポイント
@router.get("/cache/status")
async def get_cache_status() -> Dict[str, Any]:
    """キャッシュの状態を取得"""
    cache = get_redis_cache()
    
    return {
        "connected": cache.is_connected(),
        "host": cache.host,
        "port": cache.port
    }

@router.delete("/cache/clear")
async def clear_cache(pattern: Optional[str] = "*") -> Dict[str, Any]:
    """キャッシュをクリア"""
    cache = get_redis_cache()
    
    if not cache.is_connected():
        return {
            "status": "error",
            "message": "Redis not connected"
        }
    
    cleared = cache.clear_pattern(pattern)
    
    return {
        "status": "success",
        "cleared": cleared,
        "message": f"Cleared {cleared} keys matching pattern: {pattern}"
    }

@router.get("/cache/get/{key}")
async def get_cache_value(key: str) -> Dict[str, Any]:
    """キャッシュから値を取得"""
    cache = get_redis_cache()
    
    if not cache.is_connected():
        return {
            "status": "error",
            "message": "Redis not connected"
        }
    
    value = cache.get(key)
    exists = cache.exists(key)
    
    return {
        "key": key,
        "exists": exists,
        "value": value
    }

@router.post("/cache/set")
async def set_cache_value(
    key: str,
    value: Any,
    ttl: Optional[int] = None
) -> Dict[str, str]:
    """キャッシュに値を設定"""
    cache = get_redis_cache()
    
    if not cache.is_connected():
        return {
            "status": "error",
            "message": "Redis not connected"
        }
    
    success = cache.set(key, value, ttl=ttl)
    
    return {
        "status": "success" if success else "error",
        "message": f"Cache set for key: {key}" if success else "Failed to set cache"
    }