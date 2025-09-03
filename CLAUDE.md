# CLAUDE.md - D-Logic AI バックエンド

## 🚨 最重要：ディレクトリ構成

### プロジェクト構成
```
/mnt/e/dev/Cusor/
├── chatbot/uma/           # ⭐ バックエンド（FastAPI）
│   ├── backend/           # メインコード
│   ├── api/               # APIエンドポイント
│   └── services/          # ビジネスロジック
└── front/d-logic-ai-frontend/  # ⭐ フロントエンド（Next.js）
```

### 作業ディレクトリ
- **バックエンド作業時**: `cd /mnt/e/dev/Cusor/chatbot/uma/backend`
- **フロントエンド作業時**: `cd /mnt/e/dev/Cusor/front/d-logic-ai-frontend`

## 🔐 極秘情報（絶対厳守）

### D-Logic基準馬
- **基準馬名は絶対に秘密**（ユーザーに見せない）
- 「独自基準100点」という表現で統一
- システムプロンプトにも記載しない

## 📊 MySQL接続情報（JRAデータ取得）

### 接続設定
```python
# ローカルMySQL（WSL2からWindows側のMySQLに接続）
host = "172.25.160.1"  # WSL2からWindowsのMySQL
port = 3306
database = "keiba_dw"
user = "root"
password = "admin"
```

### 主要テーブル
- `umagoto_race_joho` - 馬ごとのレース情報（過去走データ）
- `race_shosai` - レース詳細情報
- `uma_prof` - 馬プロフィール
- `kishu_prof` - 騎手プロフィール
- `chokyo_prof` - 調教師プロフィール

### データ取得例
```python
import mysql.connector

conn = mysql.connector.connect(
    host="172.25.160.1",
    port=3306,
    database="keiba_dw",
    user="root",
    password="admin"
)
cursor = conn.cursor()

# 馬の過去5走データ取得
query = """
SELECT * FROM umagoto_race_joho 
WHERE BAMEI = %s 
ORDER BY KAISAI_NEN DESC, KAISAI_GAPPI DESC 
LIMIT 5
"""
cursor.execute(query, (horse_name,))
```

## 🎯 V1とV2の違い

### V1システム（既存2500ユーザー）
- **エンドポイント**: `/api/`
- **機能**: D-Logic AI、MyLogic AI、I-Logic AI
- **使用制限**: 日次制限（無料2回、LINE連携5回）
- **データベース**: Supabase（ユーザー管理）
- **特徴**: 馬単体の分析に特化

### V2システム（ポイント制）
- **エンドポイント**: `/api/v2/`
- **機能**: IMLogic（統合版）、レース単位のチャット
- **使用制限**: ポイント制（1チャット = 1ポイント）
- **データベース**: Supabase（v2_テーブル）
- **特徴**: レース全体を分析、4つのAI切り替え可能

### 重要な違い
- V1は**変更禁止**（既存ユーザーのため）
- V2は新機能追加OK
- APIエンドポイントは完全分離
- データベーステーブルも別（v2_プレフィックス）

## 🗄️ ナレッジファイル管理

### 統合ナレッジファイル（2025-09-03統合）
- **CDN URL**: `https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json`
- **馬数**: 53,618頭
- **用途**: D-Logic、MyLogic、I-Logic、ViewLogic全てで使用
- **注意**: GitHubにプッシュしない（100MB制限超過）

### ナレッジファイル更新手順
1. MySQLから新データ取得
2. 既存ナレッジとマージ
3. CDN（Cloudflare R2）にアップロード
4. `services/dlogic_raw_data_manager.py`のURLを更新

## 🚀 環境とデプロイ

### 開発環境
```bash
# バックエンド起動
cd /mnt/e/dev/Cusor/chatbot/uma/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 本番環境
- **ホスト**: Render (https://uma-i30n.onrender.com)
- **自動デプロイ**: GitHubプッシュで自動
- **環境変数**: Renderダッシュボードで管理

### 必須環境変数
```
# Supabase
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY

# CDN
KNOWLEDGE_CDN_URL

# MySQL（ローカルのみ）
MYSQL_HOST=172.25.160.1
MYSQL_PORT=3306
MYSQL_DATABASE=keiba_dw
MYSQL_USER=root
MYSQL_PASSWORD=admin
```

## 📁 重要ファイルパス

### サービス層
- `/services/dlogic_engine.py` - D-Logic計算エンジン
- `/services/imlogic_engine.py` - IMLogic（V2）エンジン
- `/services/viewlogic_engine.py` - ViewLogic展開予想
- `/services/v2/chat_service.py` - V2チャット管理
- `/services/dlogic_raw_data_manager.py` - ナレッジファイル管理

### API層
- `/api/chat.py` - V1チャットAPI
- `/api/v2/chat.py` - V2チャットAPI
- `/api/v2/points.py` - V2ポイント管理

## 🔧 よく使うコマンド

### Git操作
```bash
# バックエンド
cd /mnt/e/dev/Cusor/chatbot/uma/backend
git add -A && git commit -m "コミットメッセージ"
git push origin main

# フロントエンド
cd /mnt/e/dev/Cusor/front/d-logic-ai-frontend
git add -A && git commit -m "コミットメッセージ"
git push origin main
```

### デバッグ
```bash
# ログ確認
tail -f logs/app.log

# Renderログ確認
render logs --tail
```

## ⚠️ 注意事項

1. **V1は変更禁止** - 既存ユーザーに影響するため
2. **大きなファイルはGitにプッシュしない** - 100MB制限
3. **基準馬名は絶対に表示しない**
4. **MySQLはローカルのみ** - Renderからは接続不可
5. **ナレッジファイルはCDN経由** - GitHub Releasesは使用しない

## 📝 最終更新: 2025-09-03