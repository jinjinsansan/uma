#!/usr/bin/env python3
"""
地方競馬版I-Logic（レース分析）エンジン V2
V2マネージャーを使用（JRAデータ混入なし）
"""
from typing import Dict, Any, List, Optional
# from .race_analysis_engine import RaceAnalysisEngine  # MySQL依存のため独立実装
from .local_fast_dlogic_engine_v2 import LocalFastDLogicEngineV2
from .local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
from .local_jockey_data_manager import local_jockey_manager

class LocalRaceAnalysisEngineV2:  # RaceAnalysisEngineを継承しない独立実装
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
    
    def analyze_race(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """レース分析（独立実装）"""
        horses = race_data.get('horses', [])
        jockeys = race_data.get('jockeys', [])
        
        if not horses:
            return {
                'status': 'error',
                'message': '出走馬情報がありません'
            }
        
        # D-Logicスコアを取得
        dlogic_scores = self.dlogic_engine.analyze_batch(horses, jockeys)
        
        # 騎手分析
        jockey_scores = {}
        for jockey in jockeys:
            jockey_data = self.jockey_manager.get_jockey_data(jockey)
            if jockey_data:
                jockey_scores[jockey] = jockey_data.get('win_rate', 0)
            else:
                jockey_scores[jockey] = 0
        
        # 総合スコア計算
        scores = []
        for i, horse in enumerate(horses):
            jockey = jockeys[i] if i < len(jockeys) else None
            horse_score = dlogic_scores.get(horse, 0)
            jockey_score = jockey_scores.get(jockey, 0) if jockey else 0
            
            # 総合スコア（70:30の比率）
            total_score = horse_score * 0.7 + jockey_score * 0.3
            
            scores.append({
                'horse': horse,
                'jockey': jockey,
                'horse_score': horse_score,
                'jockey_score': jockey_score,
                'total_score': total_score
            })
        
        # スコア順にソート
        scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        return {
            'status': 'success',
            'scores': scores,
            'top_horses': [s['horse'] for s in scores[:5]]
        }

# グローバルインスタンス
local_race_analysis_engine_v2 = LocalRaceAnalysisEngineV2()