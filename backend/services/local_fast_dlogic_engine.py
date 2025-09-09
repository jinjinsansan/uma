#!/usr/bin/env python3
"""
地方競馬版高速D-Logic計算エンジン
南関東4場（大井・川崎・船橋・浦和）専用
JRA版を継承し、地方競馬版マネージャーを使用
"""
from typing import Dict, Any
from .fast_dlogic_engine import FastDLogicEngine
from .local_dlogic_raw_data_manager import local_dlogic_manager

class LocalFastDLogicEngine(FastDLogicEngine):
    """地方競馬版高速D-Logic計算エンジン"""
    
    def __init__(self):
        """初期化：地方競馬版マネージャーを使用"""
        # 親クラスの初期化をスキップして、独自に設定
        # super().__init__() は呼ばない（JRA版マネージャーを使わないため）
        
        # 地方競馬版マネージャーを設定
        self.raw_manager = local_dlogic_manager
        
        # MySQL設定は本番環境では不要なのでNone
        self.mysql_config = None
        
        # 初期化完了メッセージ
        horse_count = len(self.raw_manager.knowledge_data.get('horses', {}))
        print(f"🏇 地方競馬版D-Logic計算エンジン初期化完了 (ナレッジ: {horse_count}頭)")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """エンジン情報を返す（デバッグ用）"""
        return {
            "engine_type": "LocalFastDLogicEngine",
            "venue": "南関東4場",
            "knowledge_horses": len(self.raw_manager.knowledge_data.get('horses', {})),
            "cdn_url": "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_unified_knowledge_20250907.json"
        }

# グローバルインスタンス（シングルトン）
local_fast_dlogic_engine = LocalFastDLogicEngine()