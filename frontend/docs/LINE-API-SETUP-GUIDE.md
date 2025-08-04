# LINE API設定完全ガイド

## 1. LINE Developers アカウント作成

### Step 1: LINE Developers登録
1. https://developers.line.biz にアクセス
2. 「LINEアカウントでログイン」をクリック
3. 既存のLINEアカウントでログイン
4. 開発者規約に同意

### Step 2: プロバイダー作成
1. 「Create a new provider」をクリック
2. プロバイダー名: `D-Logic AI`
3. 「Create」をクリック

## 2. Messaging API チャネル作成

### Step 1: チャネル作成
1. 作成したプロバイダーを選択
2. 「Create a Messaging API channel」をクリック
3. 以下の情報を入力：

```
Channel name: D-Logic AI
Channel description: 競馬予想AI D-Logic の公式LINEアカウント
Category: Entertainment
Subcategory: Games
Region: Japan
Plan: Developer Trial (無料)
```

### Step 2: 会社・サービス情報
```
Company or owner's country or region: Japan
Company or owner's name: D-Logic AI
Company or owner's email address: あなたのメールアドレス
Company or owner's phone number: あなたの電話番号
```

### Step 3: 利用規約・プライバシーポリシー
```
Privacy policy URL: https://www.dlogicai.in/privacy
Terms of use URL: https://www.dlogicai.in/terms
```

## 3. チャネル設定

### Step 1: Basic Settings
1. チャネル作成後、「Basic settings」タブを開く
2. 以下の情報をメモ：
   - **Channel ID**: 長い数字（例：1234567890）
   - **Channel secret**: 32文字の文字列

### Step 2: Messaging API Settings
1. 「Messaging API」タブを開く
2. 「Channel access token」を生成
   - 「Issue」ボタンをクリック
   - 生成されたトークンをメモ（例：eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...）

### Step 3: Webhook設定
```
Webhook URL: https://uma-i30n.onrender.com/api/line/webhook
Use webhook: ON
Verify webhook: 後で設定（アプリデプロイ後）
```

### Step 4: 応答設定
```
Auto-reply messages: OFF（自動返信を無効）
Greeting messages: OFF（挨拶メッセージを無効）
Webhook: ON（Webhookを有効）
```

## 4. LINE公式アカウント設定

### Step 1: LINE公式アカウントマネージャー
1. https://manager.line.biz にアクセス
2. 作成したアカウントを選択
3. 「設定」→「応答設定」

### Step 2: 応答設定を調整
```
チャット: ON
応答メッセージ: OFF
AI応答メッセージ: OFF
挨拶メッセージ: OFF
```

### Step 3: アカウント情報設定
```
アカウント名: D-Logic AI
ステータスメッセージ: 🏇 競馬予想AIでレース分析！3日間延長チケットプレゼント🎁
プロフィール画像: D-Logicロゴ画像をアップロード
カバー画像: 競馬関連の画像
```

## 5. 環境変数設定

### 開発環境 (.env.local)
```bash
# LINE設定
NEXT_PUBLIC_LINE_ACCOUNT_ID=@あなたのLINE_ID
LINE_CHANNEL_SECRET=取得したChannel_Secret
LINE_CHANNEL_ACCESS_TOKEN=取得したAccess_Token
```

### 本番環境 (Vercel)
1. Vercelダッシュボード → Settings → Environment Variables
2. 以下の変数を追加：

```
NEXT_PUBLIC_LINE_ACCOUNT_ID = @あなたのLINE_ID
LINE_CHANNEL_SECRET = 取得したChannel_Secret  
LINE_CHANNEL_ACCESS_TOKEN = 取得したAccess_Token
```

## 6. Webhook検証

### Step 1: アプリデプロイ
1. 環境変数設定後、Vercelに再デプロイ
2. バックエンドもRenderに再デプロイ

### Step 2: Webhook URL検証
1. LINE Developers → Messaging API → Webhook settings
2. 「Verify」ボタンをクリック
3. 成功すれば ✓ が表示される

### テスト方法
```bash
# Webhook テスト用curl
curl -X POST https://uma-i30n.onrender.com/api/line/webhook \
  -H "Content-Type: application/json" \
  -H "X-Line-Signature: test" \
  -d '{"events":[],"destination":"test"}'
```

## 7. 実際の動作確認

### Step 1: QRコード生成確認
1. https://www.dlogicai.in にアクセス
2. ログイン後、30秒待機
3. LINE友達追加ポップアップが表示される
4. QRコードが正しく生成されている

### Step 2: 友達追加テスト
1. スマートフォンでQRコードを読み取り
2. LINE友達追加を実行
3. ウェルカムメッセージが届く

### Step 3: 認証コードテスト
1. ポップアップに表示される6桁コードをメモ
2. LINEでそのコードを送信
3. 「認証完了！3日間延長チケットを付与しました」メッセージ確認

## 8. トラブルシューティング

### Webhook エラー
```
Error: Invalid signature
→ Channel Secretが正しく設定されているか確認

Error: 401 Unauthorized  
→ Access Tokenが正しく設定されているか確認

Error: 403 Forbidden
→ Webhookが有効になっているか確認
```

### メッセージ送信エラー
```
Error: Invalid reply token
→ replyTokenの有効期限（30秒）を確認

Error: Invalid push message
→ LINE公式アカウントの種類を確認（無料プランの制限）
```

## 9. 料金について

### Developer Trial（無料）
- メッセージ送信: 月500通まで無料
- Webhook: 無制限
- 友達数: 無制限

### 有料プランへの移行
- Light: 月額5,000円（15,000通まで）
- Standard: 月額15,000円（45,000通まで）

## 10. セキュリティ設定

### IP制限（オプション）
```
許可IP: Renderサーバーの固定IP
```

### 署名検証
```python
# 実装済み - line_integration.py参照
def verify_line_signature(body: bytes, signature: str) -> bool:
    hash = hmac.new(
        LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(hash).decode('utf-8')
    return hmac.compare_digest(signature, expected_signature)
```

**設定完了後、実際にテストして動作確認してください！** 🚀