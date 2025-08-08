# D-Logic分割データのRenderデプロイガイド

## 概要

150MBのdlogic_raw_knowledge.jsonファイルを2つの75MBファイルに分割し、GitHub（100MB制限）とRender環境で効率的に使用できるようにしました。

## ファイル構成

```
backend/
├── data/
│   ├── chunks/                           # 分割されたデータディレクトリ
│   │   ├── dlogic_index.json            # インデックスファイル（620B）
│   │   ├── dlogic_loader.py             # データローダー（3.4KB）
│   │   ├── dlogic_raw_knowledge_chunk_01.json  # チャンク1（75MB）
│   │   └── dlogic_raw_knowledge_chunk_02.json  # チャンク2（75MB）
│   └── dlogic_raw_knowledge.json        # 元ファイル（150MB）
├── split_dlogic_data.py                 # 分割スクリプト
├── render_data_manager.py               # Render用データマネージャー
├── api_with_chunked_data.py             # FastAPI実装サンプル
└── requirements_render.txt              # Render用依存関係
```

## 分割詳細

### データ分割方法
- **方式**: アルファベット順分割（検索最適化）
- **チャンク1**: 18,939頭（AUGUSTE RODIN ～ テイエムストーン）
- **チャンク2**: 18,939頭（テイエムスパーダ ～ ヴーレヴー）
- **各ファイルサイズ**: 約75MB（GitHub 100MB制限内）

### インデックス構造
```json
{
  "meta": {
    "version": "3.1",
    "split_method": "alphabetical",
    "total_chunks": 2,
    "created": "2025-08-08T16:09:50.022539",
    "split_date": "2025-08-08T16:33:18.772676"
  },
  "chunks": [
    {
      "chunk_id": 1,
      "filename": "dlogic_raw_knowledge_chunk_01.json",
      "horses_count": 18939,
      "first_horse": "AUGUSTE RODIN",
      "last_horse": "テイエムストーン"
    }
  ]
}
```

## Renderデプロイ手順

### 1. GitHubリポジトリの準備
```bash
# 分割データをコミット
git add data/chunks/
git commit -m "Add chunked D-Logic data for GitHub size limit compliance"
git push origin main
```

### 2. Renderサービス作成
1. Renderダッシュボードで新しいWebサービスを作成
2. GitHubリポジトリを接続
3. 以下の設定を使用：
   - **Build Command**: `pip install -r requirements_render.txt`
   - **Start Command**: `uvicorn api_with_chunked_data:app --host 0.0.0.0 --port $PORT`
   - **Python Version**: 3.11以降

### 3. 環境変数設定
Renderのサービス設定で以下を設定：
```
PYTHONPATH=/opt/render/project/src
```

## API使用方法

### エンドポイント一覧

#### 基本情報
- `GET /health` - ヘルスチェックとデータ統計
- `GET /stats` - システム統計情報

#### 馬データ検索
- `GET /horse/{horse_name}` - 単体馬検索
- `POST /horses/batch` - 複数馬一括検索
- `GET /search/{partial_name}` - 馬名部分一致検索

#### D-Logic計算
- `POST /dlogic/calculate` - D-Logic計算（サンプル実装）

#### 管理
- `POST /admin/clear-cache` - キャッシュクリア

### 使用例

```python
import requests

# 基本URL（Renderデプロイ後に更新）
BASE_URL = "https://your-service.onrender.com"

# 単体馬検索
response = requests.get(f"{BASE_URL}/horse/ヴァランセカズマ")
print(response.json())

# 複数馬検索
response = requests.post(f"{BASE_URL}/horses/batch", json={
    "horse_names": ["ヴァランセカズマ", "カップッチョ", "テイエムストーン"]
})
print(response.json())

# システム統計
response = requests.get(f"{BASE_URL}/stats")
print(response.json())
```

## パフォーマンス特性

### データアクセス性能
- **LRUキャッシュ**: 最大3チャンクまでメモリキャッシュ
- **非同期処理**: FastAPIとaiofilesによる非同期I/O
- **アルファベット検索**: O(1)でのチャンク特定
- **バッチ処理**: 並列処理による高速化

### メモリ使用量
- **アイドル時**: 約50MB（基本プロセス）
- **1チャンク読み込み時**: 約125MB（75MB + オーバーヘッド）
- **3チャンクキャッシュ時**: 約275MB（225MB + オーバーヘッド）

### レスポンス時間（目安）
- **キャッシュヒット**: 1-5ms
- **キャッシュミス**: 100-500ms（初回読み込み）
- **バッチ検索**: 数十ms（並列処理）

## ローカル開発

### セットアップ
```bash
# 依存関係インストール
pip install -r requirements_render.txt

# 開発サーバー起動
python api_with_chunked_data.py
# または
uvicorn api_with_chunked_data:app --reload
```

### テスト実行
```bash
# パフォーマンステスト
python render_data_manager.py

# APIテスト
curl http://localhost:8000/health
curl http://localhost:8000/horse/ヴァランセカズマ
```

## トラブルシューティング

### よくある問題

1. **ファイルが見つからない**
   - `data/chunks/`ディレクトリがリポジトリに含まれているか確認
   - Renderのビルドログで相対パスエラーを確認

2. **メモリ不足**
   - Renderの無料プランは512MBまで
   - `max_cache_chunks`を1に減らす

3. **レスポンスが遅い**
   - よく使用するチャンクの事前読み込みを検討
   - キャッシュヒット率をモニタリング

### デバッグ設定
```python
# より詳細なログを出力
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 今後の拡張案

1. **検索インデックス**: 部分一致検索の高速化
2. **データ圧縮**: gzip圧縮による転送量削減
3. **CDN連携**: 静的ファイルのキャッシュ配信
4. **メトリクス**: Prometheus/Grafanaによる監視
5. **自動更新**: 新データの自動分割・デプロイ

## 注意事項

- Renderの無料プランではCPU制限があるため、大量の同時リクエストは避ける
- ファイルサイズが100MBを超える場合は再分割が必要
- 実際のD-Logic計算アルゴリズムは別途実装が必要