#!/usr/bin/env python3
"""
分割されたD-LogicデータをRender環境で使用するFastAPIサンプル
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging
from render_data_manager import FastAPIDataManager

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション初期化
app = FastAPI(
    title="D-Logic Horse Data API",
    description="分割されたD-Logicデータを効率的に提供するAPI",
    version="3.1"
)

# データマネージャー（グローバル）
data_manager = FastAPIDataManager()

# Pydanticモデル
class HorseRequest(BaseModel):
    horse_name: str

class BatchHorseRequest(BaseModel):
    horse_names: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "horse_names": ["ヴァランセカズマ", "カップッチョ", "テイエムストーン"]
            }
        }

class HorseResponse(BaseModel):
    success: bool
    horse_name: str
    data: Optional[Dict[str, Any]]
    race_count: Optional[int]

class BatchHorseResponse(BaseModel):
    success: bool
    total_requested: int
    found_count: int
    data: Dict[str, Any]

class StatsResponse(BaseModel):
    total_chunks: int
    total_horses: int
    split_method: str
    cached_chunks: int
    cache_order: List[int]

# スタートアップイベント
@app.on_event("startup")
async def startup_event():
    """アプリケーション開始時の初期化"""
    try:
        await data_manager.initialize()
        stats = await data_manager.get_system_stats()
        logger.info(f"API started with {stats['total_horses']} horses in {stats['total_chunks']} chunks")
    except Exception as e:
        logger.error(f"Failed to initialize data manager: {e}")
        raise

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    """APIの稼働状況とデータ統計を返す"""
    try:
        stats = await data_manager.get_system_stats()
        return {
            "status": "healthy",
            "data_stats": {
                "total_horses": stats['total_horses'],
                "total_chunks": stats['total_chunks'],
                "cached_chunks": stats['cached_chunks']
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

# 単体馬検索エンドポイント
@app.get("/horse/{horse_name}", response_model=HorseResponse)
async def get_horse_data(horse_name: str):
    """指定した馬名のデータを取得"""
    try:
        horse_data = await data_manager.get_horse_data(horse_name)
        
        if horse_data is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Horse '{horse_name}' not found"
            )
        
        return HorseResponse(
            success=True,
            horse_name=horse_name,
            data=horse_data,
            race_count=horse_data.get('race_count', 0)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving horse {horse_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# バッチ馬検索エンドポイント
@app.post("/horses/batch", response_model=BatchHorseResponse)
async def get_multiple_horses(request: BatchHorseRequest):
    """複数の馬のデータを一括取得"""
    try:
        if len(request.horse_names) > 50:  # 制限を設ける
            raise HTTPException(
                status_code=400, 
                detail="Maximum 50 horses per request"
            )
        
        result = await data_manager.get_multiple_horses(request.horse_names)
        return BatchHorseResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 馬検索（部分一致）
@app.get("/search/{partial_name}")
async def search_horses(partial_name: str, limit: int = 20):
    """馬名の部分一致検索（注意：大量データの場合は重い処理）"""
    if len(partial_name) < 2:
        raise HTTPException(
            status_code=400, 
            detail="Search term must be at least 2 characters"
        )
    
    try:
        # 実際の実装では、検索用のインデックスを事前に作成することを推奨
        # ここでは簡単な実装として全データから検索
        stats = await data_manager.get_system_stats()
        matching_horses = []
        
        # 各チャンクを検索（実際のプロダクションでは最適化が必要）
        for chunk_info in stats['chunks'][:2]:  # 最大2チャンクまで検索
            if len(matching_horses) >= limit:
                break
                
            chunk_data = await data_manager.manager.get_chunk_horses(chunk_info['chunk_id'])
            for horse_name, horse_data in chunk_data.items():
                if partial_name in horse_name and len(matching_horses) < limit:
                    matching_horses.append({
                        'horse_name': horse_name,
                        'race_count': horse_data.get('race_count', 0)
                    })
        
        return {
            'success': True,
            'search_term': partial_name,
            'found_count': len(matching_horses),
            'horses': matching_horses[:limit]
        }
    
    except Exception as e:
        logger.error(f"Error in search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# システム統計エンドポイント
@app.get("/stats", response_model=StatsResponse)
async def get_system_stats():
    """システム統計情報を取得"""
    try:
        stats = await data_manager.get_system_stats()
        return StatsResponse(
            total_chunks=stats['total_chunks'],
            total_horses=stats['total_horses'],
            split_method=stats['split_method'],
            cached_chunks=stats['cached_chunks'],
            cache_order=stats['cache_order']
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# キャッシュ管理エンドポイント（管理者用）
@app.post("/admin/clear-cache")
async def clear_cache():
    """キャッシュをクリア（管理者用）"""
    try:
        data_manager.manager.clear_cache()
        return {"success": True, "message": "Cache cleared"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# D-Logic計算用のサンプルエンドポイント
@app.post("/dlogic/calculate")
async def calculate_dlogic(request: HorseRequest):
    """D-Logic計算のサンプル（実際の計算ロジックは別途実装）"""
    try:
        horse_data = await data_manager.get_horse_data(request.horse_name)
        
        if horse_data is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Horse '{request.horse_name}' not found"
            )
        
        # サンプル計算（実際のD-Logicアルゴリズムに置き換える）
        races = horse_data.get('races', [])
        if not races:
            return {
                "success": False,
                "message": "No race data available for calculation"
            }
        
        # 簡単な統計計算
        avg_finishing_position = sum(
            int(race.get('KAKUTEI_CHAKUJUN', 99)) 
            for race in races if race.get('KAKUTEI_CHAKUJUN', '').isdigit()
        ) / len(races)
        
        avg_odds = sum(
            int(race.get('TANSHO_ODDS', 0)) 
            for race in races if race.get('TANSHO_ODDS', '').isdigit()
        ) / len(races)
        
        return {
            "success": True,
            "horse_name": request.horse_name,
            "race_count": len(races),
            "avg_finishing_position": round(avg_finishing_position, 2),
            "avg_odds": round(avg_odds, 2),
            "note": "This is a sample calculation. Implement actual D-Logic algorithm here."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in D-Logic calculation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# エラーハンドラー
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# 開発用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_with_chunked_data:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )