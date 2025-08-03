#!/usr/bin/env python3
"""
高速D-Logic分析API
ナレッジベース対応リアルタイム計算API
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.fast_dlogic_engine import FastDLogicEngine

router = APIRouter()
engine = FastDLogicEngine()

class HorseAnalysisRequest(BaseModel):
    horse_name: str
    analysis_type: Optional[str] = "standard"

class RaceAnalysisRequest(BaseModel):
    horse_names: List[str]
    race_name: Optional[str] = None
    race_date: Optional[str] = None

class HorseAnalysisResponse(BaseModel):
    horse_name: str
    total_score: float
    grade: str
    d_logic_scores: dict
    data_source: str
    calculation_time_seconds: float
    timestamp: str

class RaceAnalysisResponse(BaseModel):
    race_analysis: dict
    horses: List[dict]
    timestamp: str

@router.post("/horse-analysis", response_model=HorseAnalysisResponse)
async def analyze_single_horse(request: HorseAnalysisRequest):
    """
    単体馬D-Logic分析
    
    - **horse_name**: 分析する馬名
    - **analysis_type**: 分析タイプ（standard/detailed）
    """
    try:
        result = engine.analyze_single_horse(request.horse_name)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析エラー: {str(e)}")

@router.post("/race-analysis", response_model=RaceAnalysisResponse)
async def analyze_race_horses(request: RaceAnalysisRequest):
    """
    レース出走馬一括D-Logic分析
    
    - **horse_names**: 分析する馬名のリスト
    - **race_name**: レース名（オプション）
    - **race_date**: レース日（オプション）
    """
    try:
        if not request.horse_names:
            raise HTTPException(status_code=400, detail="馬名リストが空です")
        
        if len(request.horse_names) > 20:
            raise HTTPException(status_code=400, detail="一度に分析できるのは20頭までです")
        
        result = engine.analyze_race_horses(request.horse_names)
        
        # レース情報を追加
        if request.race_name:
            result['race_analysis']['race_name'] = request.race_name
        if request.race_date:
            result['race_analysis']['race_date'] = request.race_date
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"レース分析エラー: {str(e)}")

@router.get("/horse-search")
async def search_horse_by_name(
    query: str = Query(..., description="検索する馬名（部分一致）"),
    limit: int = Query(10, description="検索結果の最大件数")
):
    """
    馬名検索（ナレッジベース内）
    
    - **query**: 検索クエリ
    - **limit**: 結果件数制限
    """
    try:
        horses = engine.raw_manager.knowledge_data.get('horses', {})
        
        # 部分一致検索
        matches = []
        for horse_name in horses.keys():
            if query.lower() in horse_name.lower():
                horse_data = horses[horse_name]
                basic_info = horse_data.get('basic_info', {})
                stats = horse_data.get('aggregated_stats', {})
                
                matches.append({
                    'horse_name': horse_name,
                    'total_races': stats.get('total_races', 0),
                    'wins': stats.get('wins', 0),
                    'last_race_date': basic_info.get('last_race_date'),
                    'sex': basic_info.get('sex'),
                    'age': basic_info.get('age')
                })
        
        # レース数順でソート
        matches.sort(key=lambda x: x['total_races'], reverse=True)
        
        return {
            'query': query,
            'total_matches': len(matches),
            'horses': matches[:limit]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"検索エラー: {str(e)}")

@router.get("/performance-stats")
async def get_performance_stats():
    """
    エンジン性能統計
    """
    try:
        return engine.get_performance_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"統計取得エラー: {str(e)}")

@router.get("/arima-kinen-2024")
async def get_arima_kinen_2024_analysis():
    """
    2024年有馬記念特別分析（テスト用）
    """
    try:
        arima_horses = [
            "レガレイラ", "ダノンデサイル", "アーバンシック", "ドウデュース",
            "ベラジオオペラ", "ジャスティンパレス", "シャフリヤール", "ローシャムパーク",
            "スターズオンアース", "プログノーシス", "ブローザホーン", "ディープボンド",
            "シュトルーヴェ", "スタニングローズ", "ダノンベルーガ", "ハヤヤッコ"
        ]
        
        result = engine.analyze_race_horses(arima_horses)
        result['race_analysis']['race_name'] = "2024年有馬記念"
        result['race_analysis']['race_date'] = "2024-12-22"
        result['race_analysis']['racecourse'] = "中山競馬場"
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"有馬記念分析エラー: {str(e)}")

# 既存のmain.pyに統合するためのルーター登録例
"""
main.pyに以下を追加:

from api.fast_dlogic_api import router as fast_dlogic_router
app.include_router(fast_dlogic_router, prefix="/api/v2/dlogic", tags=["D-Logic V2"])
"""