# LINE公式アカウント連携セットアップガイド

## Phase F-3: LINE公式アカウント連携完了

### 実装された機能

#### 1. 自動ポップアップ表示システム
- ✅ ログイン後30-45秒でLINE友達追加ポップアップ自動表示
- ✅ 無料トライアル中のユーザーのみ対象
- ✅ 24時間間隔での再表示制御
- ✅ チケット獲得済みユーザーは非表示

#### 2. LINE友達追加UI
- ✅ 3ステップのポップアップUI（紹介→QR→成功）
- ✅ リアルタイムQRコード生成（api.qrserver.com）
- ✅ 認証コード6桁自動生成
- ✅ LINEアプリ直接リンク対応

#### 3. バックエンドAPI
- ✅ LINE Messaging API Webhook対応
- ✅ 友達追加・メッセージ受信・解除イベント処理
- ✅ 認証コード生成・検証システム
- ✅ 3日間延長チケット自動付与

#### 4. データベース設計
- ✅ `line_verification_codes` - 認証コード管理
- ✅ `line_pending_friends` - 未連携友達管理
- ✅ `line_messages` - メッセージ履歴
- ✅ `line_users` - ユーザー連携情報（3日延長記録）

### LINE公式アカウント設定手順

#### 1. LINE Developers登録
1. https://developers.line.biz にアクセス
2. プロバイダー作成: 「D-Logic AI」
3. チャネル作成: Messaging API

#### 2. 必要な設定
```
チャネル名: D-Logic AI
チャネル説明: 競馬予想AI D-Logic の公式LINEアカウント
プライバシーポリシーURL: https://www.dlogicai.in/privacy
サービス利用規約URL: https://www.dlogicai.in/terms
```

#### 3. 環境変数設定
```bash
# 開発環境 (.env.local)
NEXT_PUBLIC_LINE_ACCOUNT_ID=@dlogic-ai
LINE_CHANNEL_SECRET=取得したチャネルシークレット
LINE_CHANNEL_ACCESS_TOKEN=取得したアクセストークン

# 本番環境 (Vercel環境変数)
NEXT_PUBLIC_LINE_ACCOUNT_ID=@dlogic-ai  
LINE_CHANNEL_SECRET=本番用チャネルシークレット
LINE_CHANNEL_ACCESS_TOKEN=本番用アクセストークン
```

#### 4. Webhook URL設定
```
本番: https://uma-i30n.onrender.com/api/line/webhook
開発: https://your-ngrok-url.ngrok.io/api/line/webhook
```

### 利用フロー

#### ユーザー側
1. D-Logic AI利用開始後30-45秒でポップアップ表示
2. 「LINE友達追加して延長チケットをもらう」クリック
3. QRコード読み取りまたはLINEアプリで直接友達追加
4. 表示された6桁認証コードをLINEで送信
5. 3日間延長チケット自動付与完了

#### システム側
1. Google OAuth認証でユーザー登録
2. 無料トライアル期間判定
3. ポップアップ表示タイミング制御
4. LINE友達追加検知
5. 認証コード生成・検証
6. データベース更新（無料期間+3日延長）

### 追加実装予定

#### LINE公式機能拡張
- 📅 定期的な競馬情報配信
- 🎯 レース開催日の通知
- 🏆 G1レース特別情報
- 💰 キャンペーン・割引情報

#### 管理機能
- 📊 LINE友達数・チケット配布統計
- 📝 一斉配信メッセージ機能
- 🔔 自動応答メッセージ設定
- 📈 エンゲージメント分析

### データベーステーブル実行
```sql
-- 以下のSQLを実行してLINE連携テーブルを作成
source /path/to/add_line_tables.sql
```

### API仕様

#### LINE Webhook
- `POST /api/line/webhook` - LINE events受信
- 対応イベント: follow, message, unfollow

#### 認証コード生成
- `POST /api/line/generate-verification-code`
- パラメータ: user_email
- レスポンス: verification_code (6桁)

#### QRコード情報
- `GET /api/line/qr-code/{user_email}`
- レスポンス: line_id, add_url, qr_code_url

### セキュリティ
- ✅ LINE署名検証実装
- ✅ 認証コード10分間有効期限
- ✅ 重複チケット付与防止
- ✅ ローカルストレージでポップアップ制御

**Phase F-3 完了 - LINE公式アカウント連携システム実装完成** 🎉