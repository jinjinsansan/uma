from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import json
import os
from datetime import datetime

router = APIRouter()

class DLogicResult(BaseModel):
    venue: str
    race_number: int
    race_name: str
    race_date: str
    horses: List[str]
    dlogic_top5: List[str]
    analysis_text: str

@router.post("/api/save-dlogic-result")
async def save_dlogic_result(result: DLogicResult):
    """D-Logic分析結果を保存するAPI"""
    try:
        # ファイル名
        filename = f"data/dlogic_results/{result.race_date.replace('-', '')}.json"
        os.makedirs("data/dlogic_results", exist_ok=True)
        
        # 既存データを読み込み
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}
        
        # 新しい結果を追加
        key = f"{result.venue}_{result.race_number}"
        data[key] = {
            "venue": result.venue,
            "race_number": result.race_number,
            "race_name": result.race_name,
            "race_date": result.race_date,
            "horses": result.horses,
            "dlogic_top5": result.dlogic_top5,
            "analysis_text": result.analysis_text,
            "saved_at": datetime.now().isoformat()
        }
        
        # 保存
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {"status": "success", "message": f"D-Logic結果を保存しました: {key}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))