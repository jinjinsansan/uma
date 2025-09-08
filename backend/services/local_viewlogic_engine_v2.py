#!/usr/bin/env python3
"""
地方競馬版ViewLogic展開予想エンジン V2
ViewLogicの4つのサブエンジン機能を地方競馬版で実装:
1. 展開予想 (predict_race_flow_advanced)
2. 傾向分析 (analyze_course_trend)  
3. 推奨馬券 (recommend_betting_tickets)
4. 過去データ (get_horse_history/get_jockey_history)
"""

from typing import Dict, Any, List, Optional
from .viewlogic_engine import ViewLogicEngine
from .local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
from .local_jockey_data_manager import local_jockey_manager

class LocalViewLogicEngineV2(ViewLogicEngine):
    """地方競馬版ViewLogic展開予想エンジン V2"""
    
    def __init__(self):
        """初期化：地方競馬版マネージャーを使用"""
        # 親クラスの初期化を呼ぶ
        super().__init__()
        
        # 地方競馬版マネージャーで上書き
        self.data_manager = local_dlogic_manager_v2
        self.jockey_manager = local_jockey_manager
        
        print(f"🏇 地方競馬版ViewLogicエンジンV2初期化完了")
        horse_count = len(self.data_manager.knowledge_data.get('horses', {}))
        jockey_count = len(self.jockey_manager.knowledge_data.get('jockeys', {}))
        print(f"   馬データ: {horse_count}頭, 騎手データ: {jockey_count}騎手")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """エンジン情報を返す"""
        return {
            "engine_type": "LocalViewLogicEngineV2",
            "venue": "南関東4場",
            "knowledge_horses": len(self.data_manager.knowledge_data.get('horses', {})),
            "knowledge_jockeys": len(self.jockey_manager.knowledge_data.get('jockeys', {})),
            "manager_type": "V2",
            "subengines": [
                "展開予想 (predict_race_flow_advanced)",
                "傾向分析 (analyze_course_trend)",
                "推奨馬券 (recommend_betting_tickets)",
                "過去データ (horse/jockey history)"
            ]
        }
    
    def get_horse_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """馬データを取得（ViewLogicDataManagerとの互換性のため）"""
        return self.data_manager.get_horse_raw_data(horse_name)

# グローバルインスタンス
local_viewlogic_engine_v2 = LocalViewLogicEngineV2()