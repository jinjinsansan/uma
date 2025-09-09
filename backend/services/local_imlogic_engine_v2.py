#!/usr/bin/env python3
"""
地方競馬版IMLogic統合エンジン V2
完全に独立した実装（親クラスの問題を回避）
"""
from typing import Dict, Any, List, Optional
from .local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
from .local_jockey_data_manager import local_jockey_manager
from .local_fast_dlogic_engine_v2 import LocalFastDLogicEngineV2
from .local_race_analysis_engine_v2 import LocalRaceAnalysisEngineV2

class LocalIMLogicEngineV2:
    """地方競馬版IMLogic統合エンジン V2（独立実装）"""
    
    def __init__(self):
        """初期化：地方競馬版V2マネージャーとエンジンを使用"""
        # 地方競馬版マネージャーを設定
        self.dlogic_manager = local_dlogic_manager_v2
        self.jockey_manager = local_jockey_manager
        
        # 地方競馬版エンジンを設定
        self.dlogic_engine = LocalFastDLogicEngineV2()
        self.ilogic_engine = LocalRaceAnalysisEngineV2()
        
        # MySQL設定は本番環境では不要
        self.mysql_config = None
        
        # 現在のAIモード
        self.current_ai_mode = "IMLogic"
        
        # 初期化完了メッセージ
        horse_count = len(self.dlogic_manager.knowledge_data.get('horses', {}))
        jockey_count = len(self.jockey_manager.knowledge_data.get('jockeys', {}))
        print(f"🏇 地方競馬版IMLogic統合エンジンV2初期化完了")
        print(f"   馬データ: {horse_count}頭, 騎手データ: {jockey_count}騎手")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """エンジン情報を返す"""
        return {
            "engine_type": "LocalIMLogicEngineV2",
            "venue": "南関東4場",
            "current_ai_mode": self.current_ai_mode,
            "knowledge_horses": len(self.dlogic_manager.knowledge_data.get('horses', {})),
            "knowledge_jockeys": len(self.jockey_manager.knowledge_data.get('jockeys', {})),
            "manager_type": "V2"
        }
    
    def switch_ai_mode(self, mode: str) -> bool:
        """AIモード切り替え"""
        valid_modes = ["D-Logic", "I-Logic", "IMLogic", "ViewLogic"]
        if mode in valid_modes:
            self.current_ai_mode = mode
            print(f"🔄 地方競馬版AIモード切替: {mode}")
            return True
        return False
    
    def analyze_for_chat(self, horses: List[str], race_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """チャット用分析（簡易実装）"""
        print(f"📊 {self.current_ai_mode}モードで{len(horses)}頭を分析")
        
        if self.current_ai_mode == "D-Logic":
            # D-Logic分析
            results = []
            for horse in horses:
                result = self.dlogic_engine.analyze_single_horse(horse)
                if result:
                    results.append({
                        'name': horse,
                        'total_score': result.get('total_score', 0),
                        'grade': result.get('grade', 'N/A')
                    })
            
            return {
                'mode': 'D-Logic',
                'rankings': sorted(results, key=lambda x: x['total_score'], reverse=True),
                'response': f"D-Logicで{len(horses)}頭を分析しました"
            }
        
        elif self.current_ai_mode == "I-Logic":
            # I-Logic分析
            race_data = {
                'horses': horses,
                'venue': race_info.get('venue', '川崎') if race_info else '川崎',
                'race_name': race_info.get('race_name', 'レース') if race_info else 'レース'
            }
            result = self.ilogic_engine.analyze_race(race_data)
            return {
                'mode': 'I-Logic',
                'rankings': result.get('rankings', []),
                'response': f"I-Logicで{len(horses)}頭を分析しました"
            }
        
        else:
            # IMLogic（統合分析）
            return {
                'mode': 'IMLogic',
                'rankings': [],
                'response': f"IMLogicで{len(horses)}頭を分析します（実装中）"
            }
    
    def analyze_race(self, race_data: Dict[str, Any], horse_weight: int = 70, jockey_weight: int = 30, item_weights: Dict[str, float] = None) -> Dict[str, Any]:
        """
        レース分析（V2チャット用）
        
        Args:
            race_data: レース情報
            horse_weight: 馬の重み（デフォルト70%）
            jockey_weight: 騎手の重み（デフォルト30%）
            item_weights: 各項目の重み
        
        Returns:
            分析結果
        """
        horses = race_data.get('horses', [])
        jockeys = race_data.get('jockeys', [])
        
        # スコア計算
        scores = []
        for i, horse_name in enumerate(horses):
            jockey_name = jockeys[i] if i < len(jockeys) else None
            
            # 馬スコア（地方競馬データから取得）
            horse_score = 0
            horse_data = self.dlogic_manager.get_horse_data(horse_name)
            if horse_data:
                races = horse_data.get('races', [])
                # 簡易スコア計算
                horse_score = min(100, len(races) * 2)
            
            # 騎手スコア（地方競馬騎手データから取得）
            jockey_score = 0
            if jockey_name:
                jockey_data = self.jockey_manager.get_jockey_data(jockey_name)
                if jockey_data:
                    win_rate = jockey_data.get('win_rate', 0)
                    jockey_score = min(100, win_rate * 5)
            
            # 総合スコア計算
            total_score = (horse_score * horse_weight / 100) + (jockey_score * jockey_weight / 100)
            
            scores.append({
                'horse_name': horse_name,
                'jockey_name': jockey_name,
                'horse_score': horse_score,
                'jockey_score': jockey_score,
                'total_score': total_score
            })
        
        # スコアでソート
        scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        return {
            'status': 'success',
            'scores': scores,
            'top_horses': [s['horse_name'] for s in scores[:5]],
            'venue': race_data.get('venue'),
            'race_number': race_data.get('race_number')
        }

# グローバルインスタンス
local_imlogic_engine_v2 = LocalIMLogicEngineV2()