#!/usr/bin/env python3
"""
地方競馬版I-Logic（レース分析）エンジン
南関東4場（大井・川崎・船橋・浦和）専用
JRA版を継承し、地方競馬版D-Logicエンジンを使用
"""
from typing import Dict, Any, List, Optional
from .race_analysis_engine import RaceAnalysisEngine
from .local_fast_dlogic_engine import LocalFastDLogicEngine
from .local_dlogic_raw_data_manager import local_dlogic_manager

class LocalRaceAnalysisEngine(RaceAnalysisEngine):
    """地方競馬版I-Logic（レース分析）エンジン"""
    
    def __init__(self):
        """初期化：地方競馬版エンジンを使用"""
        # 親クラスの初期化をスキップ
        # super().__init__() は呼ばない
        
        # 地方競馬版D-Logicエンジンを使用
        self.dlogic_engine = LocalFastDLogicEngine()
        
        # 地方競馬版マネージャー
        self.raw_manager = local_dlogic_manager
        
        # 地方競馬版騎手マネージャー（I-Logicでも必要）
        from .local_jockey_data_manager import local_jockey_manager
        self.jockey_manager = local_jockey_manager
        
        # modern_engineも必要（D-Logicエンジンと同じ）
        self.modern_engine = self.dlogic_engine
        
        # MySQL設定は本番環境では不要
        self.mysql_config = None
        
        # 基準馬（イクイノックス）は同じ
        self.baseline_horse = "イクイノックス"
        
        print(f"🏇 地方競馬版I-Logic分析エンジン初期化完了")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """エンジン情報を返す（デバッグ用）"""
        return {
            "engine_type": "LocalRaceAnalysisEngine",
            "venue": "南関東4場",
            "baseline_horse": self.baseline_horse,
            "dlogic_engine": self.dlogic_engine.get_engine_info()
        }
    
    # analyze_raceメソッドは親クラスのものをそのまま使用
    # 親クラスのシグネチャ: analyze_race(self, race_data: Dict[str, Any])
    # race_dataには'horses'キーで馬名リストが入る

# グローバルインスタンス（シングルトン）
local_race_analysis_engine = LocalRaceAnalysisEngine()