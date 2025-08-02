from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging
import os

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="UmaOracle AI API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターを追加
try:
    from api.race_data import router as race_data_router
    app.include_router(race_data_router, tags=["race-data"])
    logger.info("Race data router loaded successfully")
except Exception as e:
    logger.error(f"Failed to load race data router: {e}")

try:
    from api.d_logic import router as d_logic_router
    app.include_router(d_logic_router, tags=["d-logic"])
    logger.info("D-logic router loaded successfully")
except Exception as e:
    logger.error(f"Failed to load d-logic router: {e}")

try:
    from api.chat import router as chat_router
    app.include_router(chat_router, tags=["chat"])
    logger.info("Chat router loaded successfully")
except Exception as e:
    logger.error(f"Failed to load chat router: {e}")

@app.get("/")
async def root():
    """ヘルスチェック用エンドポイント"""
    return {"message": "UmaOracle AI API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """詳細なヘルスチェック"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting UmaOracle AI API server...")
    uvicorn.run(app, host="0.0.0.0", port=8002) 