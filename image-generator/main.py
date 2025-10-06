from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import asyncio
import os
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

# 環境設定
MAX_CONCURRENT_RENDERS = int(os.getenv("MAX_CONCURRENT_RENDERS", "6"))
MAX_QUEUE_LENGTH = int(os.getenv("MAX_QUEUE_LENGTH", "12"))
QUEUE_WAIT_TIMEOUT_SECONDS = float(os.getenv("QUEUE_WAIT_TIMEOUT_SECONDS", "8"))
RENDER_TIMEOUT_SECONDS = float(os.getenv("RENDER_TIMEOUT_SECONDS", "25"))
RETRY_AFTER_SECONDS = int(os.getenv("RETRY_AFTER_SECONDS", "5"))

render_semaphore: Optional[asyncio.Semaphore] = None

# リクエスト監視用カウンタ
pending_requests: int = 0
active_requests: int = 0
total_queue_rejections: int = 0
total_queue_timeouts: int = 0
pending_lock: Optional[asyncio.Lock] = None


def _parse_bool(value: Optional[str], default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off", "disabled"}


def is_share_rendering_enabled() -> bool:
    return _parse_bool(os.getenv("SHARE_RENDERING_ENABLED"), True)

# レート制限の設定
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーション起動・終了時の処理"""
    global image_service, render_semaphore, pending_lock
    
    # 起動時：Chromiumブラウザを起動
    logger.info("Starting image generation service...")
    logger.info(f"Max concurrent renders: {MAX_CONCURRENT_RENDERS}")
    logger.info(f"Max queued requests: {MAX_QUEUE_LENGTH}")
    logger.info(f"Share rendering enabled: {is_share_rendering_enabled()}")
    
    render_semaphore = asyncio.Semaphore(MAX_CONCURRENT_RENDERS)
    pending_lock = asyncio.Lock()
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
    queue_depth = max(0, pending_requests - active_requests)
    
    return {
        "status": "healthy",
        "browser": "ready",
        "active_renders": active_renders,
        "max_concurrent": MAX_CONCURRENT_RENDERS,
        "queue_available": max(MAX_QUEUE_LENGTH - queue_depth, 0),
        "pending_requests": pending_requests,
        "queue_depth": queue_depth,
        "queue_rejections": total_queue_rejections,
        "queue_timeouts": total_queue_timeouts,
        "share_rendering_enabled": is_share_rendering_enabled(),
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
        queue_depth = max(0, pending_requests - active_requests)
        
        return {
            "memory_mb": round(memory_info.rss / 1024 / 1024, 2),
            "memory_percent": round(process.memory_percent(), 2),
            "cpu_percent": round(process.cpu_percent(interval=0.1), 2),
            "active_renders": active_renders,
            "max_concurrent": MAX_CONCURRENT_RENDERS,
            "queue_available": max(MAX_QUEUE_LENGTH - queue_depth, 0),
            "pending_requests": pending_requests,
            "queue_depth": queue_depth,
            "queue_rejections": total_queue_rejections,
            "queue_timeouts": total_queue_timeouts,
            "share_rendering_enabled": is_share_rendering_enabled()
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
    global pending_requests, active_requests, total_queue_rejections, total_queue_timeouts

    if not is_share_rendering_enabled():
        logger.warning("Share rendering request rejected: feature flag disabled")
        raise HTTPException(
            status_code=503,
            detail="Share rendering is temporarily disabled.",
            headers={"Retry-After": str(RETRY_AFTER_SECONDS)}
        )

    if not image_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if not render_semaphore:
        raise HTTPException(status_code=503, detail="Semaphore not initialized")
    
    start_time = time.time()
    queue_start_time = None
    acquired = False

    # リクエストエントリ管理
    if not pending_lock:
        raise HTTPException(status_code=503, detail="Queue manager not initialized")

    async with pending_lock:
        pending_requests += 1
        current_active = active_requests
        current_queue = max(0, pending_requests - current_active - 1)
        if current_queue >= MAX_QUEUE_LENGTH:
            pending_requests -= 1
            total_queue_rejections += 1
            logger.warning(
                "Queue rejection: queue_depth=%d max_queue=%d", current_queue, MAX_QUEUE_LENGTH
            )
            raise HTTPException(
                status_code=503,
                detail="Image generator is busy. Please retry shortly.",
                headers={"Retry-After": str(RETRY_AFTER_SECONDS)}
            )

    try:
        queue_start_time = time.time()
        active_before = MAX_CONCURRENT_RENDERS - render_semaphore._value
        logger.info(
            "Render request received (active: %d/%d, queue: %d)",
            active_before,
            MAX_CONCURRENT_RENDERS,
            max(0, pending_requests - active_requests)
        )

        try:
            await asyncio.wait_for(render_semaphore.acquire(), timeout=QUEUE_WAIT_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            async with pending_lock:
                total_queue_timeouts += 1
            logger.warning(
                "Queue timeout after %.2fs (queue depth %d)",
                QUEUE_WAIT_TIMEOUT_SECONDS,
                max(0, pending_requests - active_requests)
            )
            raise HTTPException(
                status_code=503,
                detail="Image generator queue is full. Please retry shortly.",
                headers={"Retry-After": str(RETRY_AFTER_SECONDS)}
            )

        acquired = True
        async with pending_lock:
            active_requests += 1

        wait_time = time.time() - queue_start_time
        if wait_time > 1.0:
            logger.info("Request waited %.2fs in queue", wait_time)

        image_data = await asyncio.wait_for(
            image_service.render_share_card(
                card_data=render_request.card.dict(),
                options=render_request.options or {}
            ),
            timeout=RENDER_TIMEOUT_SECONDS
        )

        total_time = time.time() - start_time
        logger.info(
            "Share card rendered successfully in %.2fs (queue %.2fs), size: %d bytes",
            total_time,
            wait_time,
            len(image_data)
        )

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
        logger.error("Render timeout after %.2fs", RENDER_TIMEOUT_SECONDS)
        raise HTTPException(
            status_code=504,
            detail="Image generation timed out. Please try again.",
            headers={"Retry-After": str(RETRY_AFTER_SECONDS)}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rendering share card: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to render image: {str(e)}"
        )
    finally:
        if acquired:
            render_semaphore.release()
            if pending_lock:
                async with pending_lock:
                    active_requests -= 1
        if pending_lock:
            async with pending_lock:
                pending_requests = max(pending_requests - 1, 0)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
