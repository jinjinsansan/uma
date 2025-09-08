#!/usr/bin/env python3
"""
地方競馬版I-Logic（レース分析）エンジン V2
V2マネージャーを使用（JRAデータ混入なし）
"""
from typing import Dict, Any, List, Optional
from .race_analysis_engine import RaceAnalysisEngine
from .local_fast_dlogic_engine_v2 import LocalFastDLogicEngineV2
from .local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
from .local_jockey_data_manager import local_jockey_manager

class LocalRaceAnalysisEngineV2(RaceAnalysisEngine):
    """地方競馬版I-Logic（レース分析）エンジン V2"""
    
    def __init__(self):
        """初期化：地方競馬版V2エンジンを使用"""
        # 親クラスの初期化をスキップ
        # super().__init__() は呼ばない
        
        # 地方競馬版V2エンジンを使用
        self.dlogic_engine = LocalFastDLogicEngineV2()
        
        # 地方競馬版マネージャー
        self.raw_manager = local_dlogic_manager_v2
        self.jockey_manager = local_jockey_manager
        
        # modern_engineも必要（D-Logicエンジンと同じ）
        self.modern_engine = self.dlogic_engine
        
        # MySQL設定は本番環境では不要
        self.mysql_config = None
        
        # 基準馬（イクイノックス）
        self.baseline_horse = "イクイノックス"
        
        print(f"🏇 地方競馬版I-Logic分析エンジンV2初期化完了")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """エンジン情報を返す"""
        return {
            "engine_type": "LocalRaceAnalysisEngineV2",
            "venue": "南関東4場",
            "baseline_horse": self.baseline_horse,
            "knowledge_horses": len(self.raw_manager.knowledge_data.get('horses', {})),
            "manager_type": "V2"
        }

# グローバルインスタンス
local_race_analysis_engine_v2 = LocalRaceAnalysisEngineV2()