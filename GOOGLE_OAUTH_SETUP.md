# Google OAuth設定手順 - D-Logic AI

## 概要
D-Logic AIアプリケーションでGoogle認証を有効にするための設定手順です。

## 1. Google Cloud Console設定

### Step 1: プロジェクト作成・選択
1. https://console.cloud.google.com/ にアクセス
2. 新しいプロジェクト作成または既存プロジェクト選択
3. プロジェクト名: "D-Logic AI" (推奨)

### Step 2: Google+ API有効化
1. 左メニュー「APIとサービス」→「ライブラリ」
2. "Google+ API" を検索して有効化
3. "People API" も有効化（ユーザー情報取得のため）

### Step 3: OAuth同意画面設定
1. 左メニュー「APIとサービス」→「OAuth同意画面」
2. **ユーザータイプ**: 外部 を選択
3. **アプリ情報**:
   - アプリ名: `D-Logic AI`
   - ユーザーサポートメール: `あなたのGmailアドレス`
   - アプリのロゴ: （任意）
4. **承認済みドメイン**:
   - `dlogicai.com`
   - `localhost` (開発用)
5. **スコープ**: デフォルトのまま
6. **テストユーザー**: あなたのGmailアドレスを追加

### Step 4: OAuth 2.0認証情報作成
1. 左メニュー「APIとサービス」→「認証情報」
2. 「認証情報を作成」→「OAuth 2.0 クライアントID」
3. **アプリケーションの種類**: ウェブアプリケーション
4. **名前**: `D-Logic AI Web Client`
5. **承認済みのJavaScript生成元**:
   - `http://localhost:3004`
   - `https://dlogicai.com`
6. **承認済みのリダイレクトURI**:
   - `http://localhost:3004/api/auth/callback/google`
   - `https://dlogicai.com/api/auth/callback/google`

## 2. 環境変数設定

### 開発環境 (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3004
NEXTAUTH_SECRET=your-complex-secret-key-minimum-32-chars
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
```

### 本番環境 (.env.production)
```env
NEXT_PUBLIC_API_URL=https://uma-i30n.onrender.com
NEXTAUTH_URL=https://dlogicai.com
NEXTAUTH_SECRET=your-production-secret-key-different-from-dev
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
```

## 3. NEXTAUTH_SECRET生成方法

### Option 1: OpenSSLを使用
```bash
openssl rand -base64 32
```

### Option 2: Node.jsを使用
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

### Option 3: オンラインツール
https://generate-secret.vercel.app/32

## 4. Netlify環境変数設定

1. Netlifyダッシュボードにアクセス
2. D-Logic AIプロジェクトを選択
3. 「Site settings」→「Environment variables」
4. 以下の変数を追加:

```
NEXTAUTH_URL = https://dlogicai.com
NEXTAUTH_SECRET = [生成したシークレット]
GOOGLE_CLIENT_ID = [Google Consoleで作成したクライアントID]
GOOGLE_CLIENT_SECRET = [Google Consoleで作成したクライアントシークレット]
```

## 5. テスト手順

### 開発環境テスト
1. `npm run dev` でローカルサーバー起動
2. http://localhost:3004 にアクセス
3. 右上「ログイン」ボタンをクリック
4. Google認証画面が表示されることを確認
5. 認証後、ユーザー情報が表示されることを確認

### 本番環境テスト
1. https://dlogicai.com にアクセス
2. 同様にログイン機能をテスト

## 6. トラブルシューティング

### よくあるエラー

#### "redirect_uri_mismatch"
- Google Cloud ConsoleのリダイレクトURIが正確に設定されているか確認
- httpとhttpsの違いに注意

#### "invalid_client"
- GOOGLE_CLIENT_IDとGOOGLE_CLIENT_SECRETが正しく設定されているか確認
- 環境変数が正しく読み込まれているか確認

#### "Configuration error"
- NEXTAUTH_URLが正しく設定されているか確認
- 本番環境では必ずhttpsを使用

## 7. セキュリティ重要事項

1. **GOOGLE_CLIENT_SECRET**: 絶対に公開しない
2. **NEXTAUTH_SECRET**: 推測困難な32文字以上の文字列を使用
3. **リダイレクトURI**: 正確なURLのみ設定
4. **スコープ**: 必要最小限の権限のみ許可

## 8. 次のステップ

Google OAuth設定完了後:
1. ユーザーデータベース設計 (Phase F-2)
2. LINE公式アカウント連携 (Phase F-3)  
3. マイページ機能実装 (Phase F-4)

---
作成日: 2025年8月4日
更新者: Claude Code