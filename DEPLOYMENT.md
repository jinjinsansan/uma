# D-Logic 競馬AI デプロイメントガイド

## 概要
D-Logic競馬予想AIシステムの本番環境デプロイ手順書

## システム構成
- **フロントエンド**: Next.js 14 + TypeScript
- **バックエンド**: FastAPI + Python
- **データベース**: MySQL (mykeibadb)
- **AI/ML**: OpenAI API + 独自D-Logic計算エンジン
- **ナレッジベース**: 1,760頭分のD-Logic事前計算データ

## デプロイ準備チェックリスト

### フロントエンド
- [x] TypeScript ビルドエラー: 0件
- [x] 構文エラー修正完了
- [x] レスポンシブデザイン実装
- [x] 環境変数設定準備

### バックエンド  
- [x] FastAPI エンドポイント完成
- [x] OpenAI API統合
- [x] D-Logic計算エンジン実装
- [x] データベース接続設定

## 推奨デプロイ構成

### Option 1: Vercel + Railway
**フロントエンド (Vercel)**
```bash
# ビルド
cd frontend
npm run build

# デプロイ
vercel --prod
```

**バックエンド (Railway)**
1. Railwayアカウント作成
2. GitHubリポジトリ連携
3. 環境変数設定
4. MySQLアドオン追加

### Option 2: AWS構成
- **Frontend**: CloudFront + S3
- **Backend**: EC2 + RDS (MySQL)
- **API Gateway**: REST API管理

### Option 3: フルマネージド
- **Frontend**: Vercel
- **Backend**: Google Cloud Run
- **Database**: PlanetScale (MySQL互換)

## 環境変数設定

### フロントエンド (.env.production)
```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_APP_URL=https://your-app-domain.com
```

### バックエンド (.env)
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
DATABASE_URL=mysql://user:password@host:3306/mykeibadb
CORS_ORIGINS=https://your-app-domain.com
```

## デプロイ前の最終確認

1. **セキュリティ**
   - [x] APIキーの環境変数化
   - [x] CORS設定
   - [x] SQLインジェクション対策
   - [x] 機密情報（基準馬）の非表示

2. **パフォーマンス**
   - [x] D-Logic計算: 0.001秒/頭
   - [x] ナレッジベース: 1,760頭対応
   - [ ] CDN設定
   - [ ] データベースインデックス最適化

3. **運用**
   - [ ] エラーログ設定
   - [ ] 監視ツール設定
   - [ ] バックアップ設定

## デプロイコマンド

### ローカルビルドテスト
```bash
# フロントエンド
cd frontend
npm run build
npm run start

# バックエンド
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 本番デプロイ
```bash
# Vercel CLIインストール
npm i -g vercel

# デプロイ
vercel --prod
```

## トラブルシューティング

### MySQL接続エラー
- 接続タイムアウト設定を延長
- コネクションプール設定を調整

### CORS エラー
- バックエンドのCORS設定確認
- フロントエンドのAPI URLを確認

## 運用開始後のタスク

1. **Phase F**: 簡易会員制システム構築
2. **Phase G**: メンテナンスモード実装
3. **Phase H**: 決済システム統合
4. **MySQL接続改善**: 残り8,220頭の処理

## サポート

問題が発生した場合は、以下を確認：
- GitHub Issues
- デプロイログ
- エラーログ

---
作成日: 2025-08-04
バージョン: 1.0