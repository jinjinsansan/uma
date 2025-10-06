# D-Logic Image Generator Service

画像生成専用サーバー（Render用）

## 特徴
- Chromium常時起動（起動時間0秒）
- Playwrightによる高速レンダリング
- FastAPI（軽量・高速）

## ローカル開発
```bash
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload
```

## Renderデプロイ
1. Renderダッシュボードで新しいWeb Serviceを作成
2. このディレクトリをリポジトリとして指定
3. render.yamlが自動的に適用される

## API
- `POST /api/render/share-card` - 共有カード画像生成
- `GET /health` - ヘルスチェック
