#!/usr/bin/env python3
"""
高速テスト専用サーバー（ポート8002）
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI
from api.chat import extract_horse_name
import uvicorn

app = FastAPI()

@app.post("/test")
async def test_extract(request: dict):
    """馬名抽出テスト専用エンドポイント"""
    message = request.get("message", "")
    horse_name = extract_horse_name(message)
    
    return {
        "input": message,
        "extracted_horse_name": horse_name,
        "will_trigger_dlogic": bool(horse_name),
        "status": "skip_dlogic" if not horse_name else "trigger_dlogic"
    }

if __name__ == "__main__":
    print("🧪 高速テスト専用サーバー起動（ポート8002）")
    uvicorn.run(app, host="127.0.0.1", port=8002)