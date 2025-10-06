from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import asyncio
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time

from services.image_service import ImageGeneratorService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# グローバル変数としてサービスを保持
image_service: Optional[ImageGeneratorService] = None

# 並行処理制限（2GBプランで安全な並行数）
# 1リクエスト = 約150-200MB → 2GB / 200MB = 10並行が理論値
# 安全のため8並行に制限（バッファ確保）
MAX_CONCURRENT_RENDERS = 8
render_semaphore: Optional[asyncio.Semaphore] = None

# レート制限の設定
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーション起動・終了時の処理"""
    global image_service, render_semaphore
    
    # 起動時：Chromiumブラウザを起動
    logger.info("Starting image generation service...")
    logger.info(f"Max concurrent renders: {MAX_CONCURRENT_RENDERS}")
    
    render_semaphore = asyncio.Semaphore(MAX_CONCURRENT_RENDERS)
    image_service = ImageGeneratorService()
    await image_service.initialize()
    
    logger.info("Image generation service ready")
    
    yield
    
    # 終了時：グレースフルシャットダウン
    logger.info("Shutting down image generation service...")
    
    # 進行中のリクエストが完了するまで最大30秒待機
    shutdown_start = time.time()
    while render_semaphore and render_semaphore._value < MAX_CONCURRENT_RENDERS:
        if time.time() - shutdown_start > 30:
            logger.warning("Forced shutdown after 30s timeout")
            break
        await asyncio.sleep(0.5)
        logger.info(f"Waiting for {MAX_CONCURRENT_RENDERS - render_semaphore._value} active renders...")
    
    if image_service:
        await image_service.cleanup()
    logger.info("Image generation service stopped")

app = FastAPI(
    title="D-Logic Image Generator",
    description="Dedicated image generation service for share cards",
    version="1.0.0",
    lifespan=lifespan
)

# レート制限の設定
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    
    active_renders = MAX_CONCURRENT_RENDERS - (render_semaphore._value if render_semaphore else MAX_CONCURRENT_RENDERS)
    
    return {
        "status": "healthy",
        "browser": "ready",
        "active_renders": active_renders,
        "max_concurrent": MAX_CONCURRENT_RENDERS,
        "queue_available": render_semaphore._value if render_semaphore else 0,
        "timestamp": time.time()
    }

@app.get("/metrics")
async def metrics():
    """メモリ・CPU使用状況"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        active_renders = MAX_CONCURRENT_RENDERS - (render_semaphore._value if render_semaphore else MAX_CONCURRENT_RENDERS)
        
        return {
            "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
            "memory_percent": round(process.memory_percent(), 2),
            "cpu_percent": round(process.cpu_percent(interval=0.1), 2),
            "active_renders": active_renders,
            "max_concurrent": MAX_CONCURRENT_RENDERS,
            "queue_available": render_semaphore._value if render_semaphore else 0
        }
    except ImportError:
        return {"error": "psutil not installed"}
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {"error": str(e)}

@app.post("/api/render/share-card")
@limiter.limit("10/minute")  # 1分間に10リクエストまで（同一IPから）
async def render_share_card(request: Request, render_request: RenderRequest):
    """
    共有カード画像を生成（並行処理制限・タイムアウト・レート制限付き）
    
    - card: カードデータ
    - options: レンダリングオプション（オプション）
    
    戻り値: PNG画像（バイナリ）
    """
    if not image_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if not render_semaphore:
        raise HTTPException(status_code=503, detail="Semaphore not initialized")
    
    start_time = time.time()
    
    # キュー待機状態をログ
    active_renders = MAX_CONCURRENT_RENDERS - render_semaphore._value
    logger.info(f"Render request received (active: {active_renders}/{MAX_CONCURRENT_RENDERS})")
    
    # セマフォで並行処理を制限（キューイング）
    async with render_semaphore:
        try:
            wait_time = time.time() - start_time
            if wait_time > 1.0:
                logger.info(f"Request waited {wait_time:.2f}s in queue")
            
            # タイムアウト付きで画像生成（最大25秒）
            image_data = await asyncio.wait_for(
                image_service.render_share_card(
                    card_data=render_request.card.dict(),
                    options=render_request.options or {}
                ),
                timeout=25.0
            )
            
            total_time = time.time() - start_time
            logger.info(f"Share card rendered successfully in {total_time:.2f}s, size: {len(image_data)} bytes")
            
            # PNG画像として返す
            return Response(
                content=image_data,
                media_type="image/png",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "Content-Disposition": "inline; filename=share-card.png",
                    "X-Render-Time": f"{total_time:.2f}",
                    "X-Queue-Wait": f"{wait_time:.2f}"
                }
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Render timeout after 25s")
            raise HTTPException(
                status_code=504,
                detail="Image generation timed out. Please try again."
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
