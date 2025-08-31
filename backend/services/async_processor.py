"""
非同期処理ワーカー - V1/V2共通
重い処理をバックグラウンドで実行
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional, Callable
import logging
from datetime import datetime
import json
import hashlib

logger = logging.getLogger(__name__)

class AsyncProcessor:
    """非同期処理マネージャー"""
    
    def __init__(self, max_workers: int = 4):
        """
        Args:
            max_workers: 同時実行する最大ワーカー数
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = {}  # タスクID -> タスク情報のマッピング
        logger.info(f"AsyncProcessor initialized with {max_workers} workers")
    
    def generate_task_id(self, prefix: str = "task") -> str:
        """ユニークなタスクIDを生成"""
        timestamp = datetime.now().isoformat()
        hash_input = f"{prefix}_{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]
    
    async def submit_task(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        task_id: Optional[str] = None,
        task_type: str = "generic"
    ) -> str:
        """
        タスクを非同期で実行
        
        Args:
            func: 実行する関数
            args: 関数の位置引数
            kwargs: 関数のキーワード引数
            task_id: タスクID（指定しない場合は自動生成）
            task_type: タスクの種類（ログ用）
        
        Returns:
            タスクID
        """
        if kwargs is None:
            kwargs = {}
        
        if task_id is None:
            task_id = self.generate_task_id(task_type)
        
        # タスク情報を保存
        self.tasks[task_id] = {
            'status': 'pending',
            'type': task_type,
            'created_at': datetime.now().isoformat(),
            'result': None,
            'error': None
        }
        
        # 非同期でタスクを実行
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            self.executor,
            self._run_task,
            task_id,
            func,
            args,
            kwargs
        )
        
        # タスク完了後の処理を設定
        asyncio.create_task(self._handle_task_completion(task_id, future))
        
        logger.info(f"Task {task_id} ({task_type}) submitted")
        return task_id
    
    def _run_task(self, task_id: str, func: Callable, args: tuple, kwargs: dict) -> Any:
        """タスクを実行（ThreadPoolExecutor内で実行）"""
        try:
            self.tasks[task_id]['status'] = 'running'
            self.tasks[task_id]['started_at'] = datetime.now().isoformat()
            
            result = func(*args, **kwargs)
            
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
            self.tasks[task_id]['result'] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            self.tasks[task_id]['failed_at'] = datetime.now().isoformat()
            raise
    
    async def _handle_task_completion(self, task_id: str, future):
        """タスク完了後の処理"""
        try:
            result = await future
            logger.info(f"Task {task_id} completed successfully")
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """タスクの状態を取得"""
        return self.tasks.get(task_id)
    
    def cleanup_old_tasks(self, hours: int = 24):
        """古いタスクを削除"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours)
        
        tasks_to_remove = []
        for task_id, task_info in self.tasks.items():
            created_at = datetime.fromisoformat(task_info['created_at'])
            if created_at < cutoff:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
    
    def shutdown(self):
        """ExecutorPoolをシャットダウン"""
        self.executor.shutdown(wait=True)
        logger.info("AsyncProcessor shutdown complete")


# グローバルインスタンス
async_processor = AsyncProcessor(max_workers=4)


# 使用例：D-Logic計算を非同期化
async def calculate_dlogic_async(
    horse_names: list,
    race_date: str,
    venue: str,
    race_number: int
) -> str:
    """D-Logic計算を非同期で実行"""
    from services.dlogic_engine import DLogicEngine
    
    def _calculate():
        engine = DLogicEngine()
        return engine.calculate_batch(
            horse_names=horse_names,
            race_date=race_date,
            venue=venue,
            race_number=race_number
        )
    
    task_id = await async_processor.submit_task(
        func=_calculate,
        task_type="dlogic_calculation"
    )
    
    return task_id


# 使用例：レース分析を非同期化
async def analyze_race_async(
    race_data: dict,
    analysis_type: str = "full"
) -> str:
    """レース分析を非同期で実行"""
    from services.race_analyzer import RaceAnalyzer
    
    def _analyze():
        analyzer = RaceAnalyzer()
        return analyzer.analyze(race_data, analysis_type)
    
    task_id = await async_processor.submit_task(
        func=_analyze,
        args=(race_data,),
        kwargs={'analysis_type': analysis_type},
        task_type="race_analysis"
    )
    
    return task_id