from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import asyncio
from contextlib import asynccontextmanager

from services.image_service import ImageGeneratorService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# グローバル変数としてサービスを保持
image_service: Optional[ImageGeneratorService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーション起動・終了時の処理"""
    global image_service
    
    # 起動時：Chromiumブラウザを起動
    logger.info("Starting image generation service...")
    image_service = ImageGeneratorService()
    await image_service.initialize()
    logger.info("Image generation service ready")
    
    yield
    
    # 終了時：Chromiumブラウザを終了
    logger.info("Shutting down image generation service...")
    if image_service:
        await image_service.cleanup()
    logger.info("Image generation service stopped")

app = FastAPI(
    title="D-Logic Image Generator",
    description="Dedicated image generation service for share cards",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定（本番環境では特定のドメインのみ許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.dlogicai.in",
        "https://dlogicai.in",
        "http://localhost:3000",
        "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

class ShareCardData(BaseModel):
    """共有カードのデータ構造"""
    raceMeta: Optional[Dict[str, Any]] = None
    analyses: List[Dict[str, Any]]
    userNote: Optional[str] = None
    hashtags: Optional[List[str]] = None
    generatedAt: Optional[str] = None

class RenderRequest(BaseModel):
    """画像生成リクエスト"""
    card: ShareCardData
    options: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    """ヘルスチェック"""
    return {
        "service": "D-Logic Image Generator",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """詳細なヘルスチェック"""
    if not image_service or not image_service.browser:
        raise HTTPException(status_code=503, detail="Browser not initialized")
    
    return {
        "status": "healthy",
        "browser": "ready",
        "timestamp": asyncio.get_event_loop().time()
    }

@app.post("/api/render/share-card")
async def render_share_card(request: RenderRequest):
    """
    共有カード画像を生成
    
    - card: カードデータ
    - options: レンダリングオプション（オプション）
    
    戻り値: PNG画像（バイナリ）
    """
    if not image_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Rendering share card request received")
        
        # 画像生成
        image_data = await image_service.render_share_card(
            card_data=request.card.dict(),
            options=request.options or {}
        )
        
        logger.info(f"Share card rendered successfully, size: {len(image_data)} bytes")
        
        # PNG画像として返す
        return Response(
            content=image_data,
            media_type="image/png",
            headers={
                "Cache-Control": "no-cache",
                "Content-Disposition": "inline; filename=share-card.png"
            }
        )
        
    except Exception as e:
        logger.error(f"Error rendering share card: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to render image: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
