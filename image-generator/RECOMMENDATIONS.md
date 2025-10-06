# Image Generator Service - 負荷対策の推奨事項

## 🔴 CRITICAL（即座に対応すべき）

### 1. 並行処理制限の実装

**現状の問題:**
- 同時リクエストで512MB RAMをすぐ使い切る
- メモリ不足でサーバークラッシュのリスク

**推奨される修正:**

```python
# main.py に追加
from asyncio import Semaphore

# 最大2並行処理に制限（512MB RAMの制約）
MAX_CONCURRENT_RENDERS = 2
render_semaphore = Semaphore(MAX_CONCURRENT_RENDERS)

@app.post("/api/render/share-card")
async def render_share_card(request: RenderRequest):
    if not image_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    # セマフォで並行処理を制限
    async with render_semaphore:
        try:
            logger.info(f"Rendering share card (active: {MAX_CONCURRENT_RENDERS - render_semaphore._value})")
            
            image_data = await image_service.render_share_card(
                card_data=request.card.dict(),
                options=request.options or {}
            )
            
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
            raise HTTPException(status_code=500, detail=f"Failed to render image: {str(e)}")
```

**効果:**
- メモリオーバーフロー防止
- サーバー安定性向上
- 待機中のリクエストはキューで処理

---

## 🟠 HIGH（早急に対応すべき）

### 2. タイムアウト設定

**フロントエンド側:**

```typescript
// useShareCardRenderer.ts
const RENDER_TIMEOUT_MS = 30000; // 30秒

const response = await Promise.race([
  fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ card })
  }),
  new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error('画像生成がタイムアウトしました')), RENDER_TIMEOUT_MS)
  )
]);
```

**バックエンド側:**

```python
# image_service.py
async def render_share_card(self, card_data: Dict[str, Any], options: Dict[str, Any]) -> bytes:
    if not self.browser:
        raise RuntimeError("Browser not initialized")
    
    page: Optional[Page] = None
    
    try:
        # タイムアウト付きでページ作成
        page = await asyncio.wait_for(
            self.browser.new_page(
                viewport={'width': 1200, 'height': 1200},
                device_scale_factor=options.get('deviceScaleFactor', 2)
            ),
            timeout=10.0  # 10秒
        )
        
        html_content = self._generate_html(card_data)
        
        # コンテンツ読み込みもタイムアウト設定
        await asyncio.wait_for(
            page.set_content(html_content, wait_until='networkidle'),
            timeout=10.0
        )
        
        # ... rest of the code
```

---

### 3. レート制限の実装

```python
# main.py に追加
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/render/share-card")
@limiter.limit("5/minute")  # 1分間に5リクエストまで
async def render_share_card(request: Request, render_request: RenderRequest):
    # ... existing code
```

**requirements.txt に追加:**
```
slowapi==0.1.9
```

---

## 🟡 MEDIUM（計画的に対応）

### 4. リトライロジック

```typescript
// useShareCardRenderer.ts
const MAX_RETRIES = 2;

const renderWithRetry = async (retries = 0): Promise<RenderResult | null> => {
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ card })
    });
    
    if (!response.ok) {
      if (response.status === 503 && retries < MAX_RETRIES) {
        // サーバー過負荷時はリトライ
        await new Promise(resolve => setTimeout(resolve, 2000 * (retries + 1)));
        return renderWithRetry(retries + 1);
      }
      throw new Error('サーバーでの画像生成に失敗しました');
    }
    
    // ... process response
    
  } catch (err) {
    if (retries < MAX_RETRIES) {
      await new Promise(resolve => setTimeout(resolve, 2000 * (retries + 1)));
      return renderWithRetry(retries + 1);
    }
    throw err;
  }
};
```

---

### 5. ブラウザコンテキスト管理

```python
# image_service.py
async def render_share_card(self, card_data: Dict[str, Any], options: Dict[str, Any]) -> bytes:
    if not self.browser:
        raise RuntimeError("Browser not initialized")
    
    context = None
    page = None
    
    try:
        # 新しいコンテキストを作成（メモリ隔離）
        context = await self.browser.new_context(
            viewport={'width': 1200, 'height': 1200},
            device_scale_factor=options.get('deviceScaleFactor', 2)
        )
        
        page = await context.new_page()
        
        # ... existing rendering logic
        
    finally:
        if page:
            await page.close()
        if context:
            await context.close()  # コンテキストも確実にクローズ
```

---

### 6. メモリモニタリング

```python
# main.py に追加
import psutil

@app.get("/metrics")
async def metrics():
    """メモリ使用状況を返す"""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "memory_mb": memory_info.rss / 1024 / 1024,
        "memory_percent": process.memory_percent(),
        "cpu_percent": process.cpu_percent(interval=0.1)
    }
```

**requirements.txt に追加:**
```
psutil==5.9.8
```

---

## 🟢 LOW（推奨される改善）

### 7. キャッシング（オプション）

画像生成は重い処理なので、同じカード内容なら結果をキャッシュ:

```python
from functools import lru_cache
import hashlib
import json

def generate_cache_key(card_data: Dict[str, Any]) -> str:
    """カードデータからキャッシュキーを生成"""
    data_str = json.dumps(card_data, sort_keys=True)
    return hashlib.md5(data_str.encode()).hexdigest()

# 簡易的なメモリキャッシュ（最大10件）
image_cache: Dict[str, bytes] = {}
MAX_CACHE_SIZE = 10

@app.post("/api/render/share-card")
async def render_share_card(request: RenderRequest):
    cache_key = generate_cache_key(request.card.dict())
    
    # キャッシュチェック
    if cache_key in image_cache:
        logger.info(f"Cache hit for {cache_key}")
        return Response(
            content=image_cache[cache_key],
            media_type="image/png"
        )
    
    # 画像生成
    image_data = await image_service.render_share_card(...)
    
    # キャッシュ保存
    if len(image_cache) >= MAX_CACHE_SIZE:
        # 最古のエントリを削除
        image_cache.pop(next(iter(image_cache)))
    image_cache[cache_key] = image_data
    
    return Response(content=image_data, media_type="image/png")
```

---

## 📊 Renderプランのアップグレード検討

**現状: Starter ($7/month)**
- RAM: 512MB
- CPU: 0.5 vCPU
- 並行処理: 2-3リクエストが限界

**推奨: Standard ($25/month)**
- RAM: 2GB → **4倍**
- CPU: 1 vCPU → **2倍**
- 並行処理: 10-15リクエスト可能

**判断基準:**
- 同時ユーザー数が5人以上になる場合
- 秋華賞などの大型イベント時

---

## 🔍 監視とアラート

### Renderダッシュボードで確認すべき項目:

1. **メモリ使用率**
   - 常時80%超え → プランアップグレード検討
   
2. **CPU使用率**
   - 常時90%超え → プランアップグレード検討
   
3. **レスポンスタイム**
   - 10秒以上が頻発 → 並行処理制限の調整
   
4. **エラー率**
   - 5%以上 → コード修正が必要

---

## まとめ

### 即座に実装すべき（今日中）:
1. ✅ 並行処理制限（Semaphore）
2. ✅ タイムアウト設定

### 今週中に実装すべき:
3. ✅ レート制限
4. ✅ リトライロジック

### 計画的に実装:
5. ブラウザコンテキスト管理
6. メモリモニタリング
7. キャッシング（オプション）

### 予算があれば:
- Renderプランアップグレード（$25/month）
