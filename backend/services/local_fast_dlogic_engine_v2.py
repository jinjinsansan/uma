#!/usr/bin/env python3
"""
地方競馬版高速D-Logic計算エンジン V2
V2マネージャーを使用（JRAデータ混入なし）
"""
import logging
from typing import Dict, Any
# from .fast_dlogic_engine import FastDLogicEngine  # MySQL依存のため、独立実装
from .local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2

class LocalFastDLogicEngineV2:  # FastDLogicEngineを継承しない独立実装
    """地方競馬版高速D-Logic計算エンジン V2"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初期化：地方競馬版V2マネージャーを使用"""
        # 既に初期化済みの場合はスキップ
        if LocalFastDLogicEngineV2._initialized:
            return
            
        # 親クラスの初期化をスキップ
        # super().__init__() は呼ばない
        
        # 地方競馬版V2マネージャーを設定
        self.raw_manager = local_dlogic_manager_v2
        
        # MySQL設定は本番環境では不要
        self.mysql_config = None
        
        # 初期化完了メッセージ
        horse_count = len(self.raw_manager.knowledge_data.get('horses', {}))
        logger = logging.getLogger(__name__)
        logger.info("🏇 地方競馬版D-Logic計算エンジンV2初期化完了 (ナレッジ: %s頭)", horse_count)
        LocalFastDLogicEngineV2._initialized = True
    
    def get_engine_info(self) -> Dict[str, Any]:
        """エンジン情報を返す"""
        return {
            "engine_type": "LocalFastDLogicEngineV2",
            "venue": "南関東4場",
            "knowledge_horses": len(self.raw_manager.knowledge_data.get('horses', {})),
            "manager_type": "V2"
        }
    
    def analyze_batch(self, horses: list, jockeys: list = None) -> Dict[str, Any]:
        """バッチ分析（I-Logicで必要）"""
        results = {}
        for horse in horses:
            score_data = self.raw_manager.calculate_dlogic_realtime(horse)
            if not score_data.get('error'):
                results[horse] = score_data.get('total_score', 0)
            else:
                # データがない場合は-1を返す
                results[horse] = -1
        return results

# グローバルインスタンス
local_fast_dlogic_engine_v2 = LocalFastDLogicEngineV2()