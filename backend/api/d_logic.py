from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
from services.knowledge_base import d_logic_calculator

router = APIRouter(prefix="/api/d-logic", tags=["D Logic"])

logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """DロジックAPIの健全性チェック"""
    return {"status": "healthy", "service": "d_logic"}

@router.post("/calculate")
async def calculate_d_logic(race_data: Dict[str, Any]):
    """多次元Dロジック計算API"""
    try:
        # 計算エンジンの初期化
        await d_logic_calculator.initialize()
        
        # 各馬のDロジック指数計算
        horses_results = []
        
        for horse in race_data.get("horses", []):
            horse_result = d_logic_calculator.calculate_d_logic_score(horse)
            horses_results.append({
                "horse_id": horse.get("horse_id"),
                "horse_name": horse.get("horse_name"),
                "d_logic_score": horse_result.get("total_score", 0),
                "detailed_analysis": horse_result
            })
        
        # 結果をスコア順にソート
        horses_results.sort(key=lambda x: x["d_logic_score"], reverse=True)
        
        return {
            "status": "success",
            "race_code": race_data.get("race_code"),
            "calculation_method": "多次元Dロジック計算エンジン",
            "base_horse": "ダンスインザダーク",
            "base_score": 100,
            "sql_data_utilization": "12項目の多角的評価",
            "horses": horses_results,
            "calculation_summary": {
                "total_horses": len(horses_results),
                "average_score": sum(h["d_logic_score"] for h in horses_results) / len(horses_results) if horses_results else 0,
                "top_score": horses_results[0]["d_logic_score"] if horses_results else 0,
                "bottom_score": horses_results[-1]["d_logic_score"] if horses_results else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Dロジック計算エラー: {e}")
        raise HTTPException(status_code=500, detail="Dロジック計算中にエラーが発生しました")

@router.get("/knowledge-base")
async def get_knowledge_base():
    """ナレッジベース情報取得"""
    try:
        await d_logic_calculator.initialize()
        
        return {
            "status": "success",
            "knowledge_base": {
                "dance_in_the_dark_data": await d_logic_calculator.kb.get_dance_in_the_dark_data(),
                "sql_evaluation_criteria": await d_logic_calculator.kb.get_sql_evaluation_criteria(),
                "d_logic_weights": await d_logic_calculator.kb.get_d_logic_weights()
            }
        }
        
    except Exception as e:
        logger.error(f"ナレッジベース取得エラー: {e}")
        raise HTTPException(status_code=500, detail="ナレッジベース取得中にエラーが発生しました")

@router.post("/analyze-horse")
async def analyze_single_horse(horse_data: Dict[str, Any]):
    """単一馬の詳細分析"""
    try:
        await d_logic_calculator.initialize()
        
        result = d_logic_calculator.calculate_d_logic_score(horse_data)
        
        return {
            "status": "success",
            "horse_name": horse_data.get("horse_name"),
            "analysis": result
        }
        
    except Exception as e:
        logger.error(f"単一馬分析エラー: {e}")
        raise HTTPException(status_code=500, detail="単一馬分析中にエラーが発生しました") 