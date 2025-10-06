import asyncio
import logging
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, Playwright

logger = logging.getLogger(__name__)

class ImageGeneratorService:
    """画像生成サービス（Chromium常時起動）"""
    
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        
    async def initialize(self):
        """Chromiumブラウザを起動"""
        try:
            logger.info("Initializing Playwright...")
            self.playwright = await async_playwright().start()
            
            logger.info("Launching Chromium browser...")
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-extensions',
                    '--font-render-hinting=none'
                ]
            )
            
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    
    async def cleanup(self):
        """Chromiumブラウザを終了"""
        try:
            if self.browser:
                await self.browser.close()
                logger.info("Browser closed")
            
            if self.playwright:
                await self.playwright.stop()
                logger.info("Playwright stopped")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    async def render_share_card(
        self,
        card_data: Dict[str, Any],
        options: Dict[str, Any]
    ) -> bytes:
        """
        共有カード画像を生成（タイムアウト付き・メモリリーク対策）
        
        Args:
            card_data: カードデータ
            options: レンダリングオプション
            
        Returns:
            PNG画像データ（bytes）
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized")
        
        context = None
        page = None
        
        try:
            # 新しいブラウザコンテキストを作成（メモリ隔離）
            context = await asyncio.wait_for(
                self.browser.new_context(
                    viewport={'width': 1200, 'height': 1200},
                    device_scale_factor=options.get('deviceScaleFactor', 2),
                    # リソース節約のための設定
                    java_script_enabled=True,
                    bypass_csp=True,
                    ignore_https_errors=True
                ),
                timeout=5.0
            )
            
            # 新しいページを作成
            page = await asyncio.wait_for(
                context.new_page(),
                timeout=5.0
            )
            
            # 不要なリソースをブロック（パフォーマンス向上）
            await page.route("**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf}", lambda route: route.abort())
            
            # HTMLコンテンツを生成
            html_content = self._generate_html(card_data)
            
            # HTMLを読み込み（タイムアウト付き）
            await asyncio.wait_for(
                page.set_content(html_content, wait_until='domcontentloaded'),
                timeout=10.0
            )
            
            # フォント読み込み待機（日本語フォント対応）
            await asyncio.sleep(0.5)
            
            # カード要素を取得
            card_element = await asyncio.wait_for(
                page.query_selector('[data-share-card]'),
                timeout=5.0
            )
            
            if not card_element:
                raise ValueError("Share card element not found")
            
            # スクリーンショット撮影（タイムアウト付き）
            screenshot = await asyncio.wait_for(
                card_element.screenshot(
                    type='png',
                    omit_background=False
                ),
                timeout=10.0
            )
            
            logger.info(f"Screenshot captured: {len(screenshot)} bytes")
            
            return screenshot
            
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout during rendering: {str(e)}")
            raise RuntimeError(f"Rendering timeout: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error rendering share card: {str(e)}", exc_info=True)
            raise
            
        finally:
            # 確実にリソースを解放（メモリリーク防止）
            try:
                if page:
                    await asyncio.wait_for(page.close(), timeout=2.0)
            except Exception as e:
                logger.warning(f"Error closing page: {e}")
            
            try:
                if context:
                    await asyncio.wait_for(context.close(), timeout=2.0)
            except Exception as e:
                logger.warning(f"Error closing context: {e}")
    
    def _generate_html(self, card_data: Dict[str, Any]) -> str:
        """
        カードデータからHTMLを生成
        
        Args:
            card_data: カードデータ
            
        Returns:
            HTML文字列
        """
        from templates.card_template import generate_card_html
        return generate_card_html(card_data)
