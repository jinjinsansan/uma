#!/usr/bin/env python3
"""
地方競馬版IMLogic統合エンジン
南関東4場（大井・川崎・船橋・浦和）専用
JRA版を継承し、地方競馬版マネージャーを使用
"""
from typing import Dict, Any, List, Optional
from .imlogic_engine import IMLogicEngine
from .local_dlogic_raw_data_manager import local_dlogic_manager
from .local_jockey_data_manager import local_jockey_manager
from .local_fast_dlogic_engine import LocalFastDLogicEngine
from .local_race_analysis_engine import LocalRaceAnalysisEngine

class LocalIMLogicEngine(IMLogicEngine):
    """地方競馬版IMLogic統合エンジン"""
    
    def __init__(self):
        """初期化：地方競馬版マネージャーとエンジンを使用"""
        # 親クラスの初期化を呼ぶ（これで親クラスの基本的な属性が設定される）
        try:
            super().__init__()
        except Exception as e:
            # 親クラスの初期化でJRA版マネージャーが読み込まれるが、後で上書きするので無視
            print(f"⚠️ 親クラス初期化エラー（無視）: {e}")
        
        # 地方競馬版マネージャーで上書き
        self.dlogic_manager = local_dlogic_manager
        self.jockey_manager = local_jockey_manager
        
        # 地方競馬版エンジンで上書き
        self.dlogic_engine = LocalFastDLogicEngine()
        self.ilogic_engine = LocalRaceAnalysisEngine()
        
        # MySQL設定は本番環境では不要
        self.mysql_config = None
        
        # 現在のAIモード（親クラスから継承）
        if not hasattr(self, 'current_ai_mode'):
            self.current_ai_mode = "IMLogic"
        
        # 初期化完了メッセージ
        horse_count = len(self.dlogic_manager.knowledge_data.get('horses', {}))
        jockey_count = len(self.jockey_manager.knowledge_data.get('jockeys', {}))
        print(f"🏇 地方競馬版IMLogic統合エンジン初期化完了")
        print(f"   馬データ: {horse_count}頭, 騎手データ: {jockey_count}騎手")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """エンジン情報を返す（デバッグ用）"""
        return {
            "engine_type": "LocalIMLogicEngine",
            "venue": "南関東4場",
            "current_ai_mode": self.current_ai_mode,
            "knowledge_horses": len(self.dlogic_manager.knowledge_data.get('horses', {})),
            "knowledge_jockeys": len(self.jockey_manager.knowledge_data.get('jockeys', {})),
            "dlogic_cdn": "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_unified_knowledge_20250907.json",
            "jockey_cdn": "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_jockey_knowledge_20250907.json"
        }
    
    def switch_ai_mode(self, mode: str) -> bool:
        """AIモード切り替え（親クラスと同じ）"""
        valid_modes = ["D-Logic", "I-Logic", "IMLogic", "ViewLogic"]
        if mode in valid_modes:
            self.current_ai_mode = mode
            print(f"🔄 地方競馬版AIモード切替: {mode}")
            return True
        return False
    
    def analyze_for_chat(self, horses: List[str], race_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """チャット用分析（親クラスのメソッドをそのまま使用）"""
        # 親クラスのanalyze_for_chatメソッドを呼び出す
        # ただし、内部で使用するエンジンは全て地方競馬版になっている
        return super().analyze_for_chat(horses, race_info)

# グローバルインスタンス（シングルトン）
local_imlogic_engine = LocalIMLogicEngine()