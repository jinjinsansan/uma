#!/bin/bash

# 新しいAPI認証情報
ACCESS_KEY="62b127c384fe4a78f4110c5fd3ebbf4e"
SECRET_KEY="2876eb1b13d17ed1b002fb9164ce6db7d81f989cff3a848d72c17749a1f31a26"
ENDPOINT="https://954dcc10adf822b50ccceedef0aa97e6.r2.cloudflarestorage.com"
BUCKET="dlogic-knowledge-files"
FILE_PATH="unified_knowledge_20250903.json"
OBJECT_NAME="unified_knowledge_20250903.json"

# ファイル存在確認
if [ ! -f "$FILE_PATH" ]; then
    echo "❌ ファイルが存在しません: $FILE_PATH"
    exit 1
fi

# ファイルサイズ
FILE_SIZE=$(stat -c%s "$FILE_PATH" 2>/dev/null || stat -f%z "$FILE_PATH" 2>/dev/null)
echo "📁 アップロードファイル: $FILE_PATH"
echo "📊 サイズ: $((FILE_SIZE / 1048576))MB"

# 日付とコンテンツタイプ
DATE=$(date -R)
CONTENT_TYPE="application/json"

# S3 v4署名のための準備
SERVICE="s3"
REGION="auto"
REQUEST_TYPE="aws4_request"
ALGORITHM="AWS4-HMAC-SHA256"
DATE_SHORT=$(date +%Y%m%d)
DATE_LONG=$(date +%Y%m%dT%H%M%SZ)

# 正規リクエスト
CANONICAL_URI="/$BUCKET/$OBJECT_NAME"
CANONICAL_QUERYSTRING=""
CANONICAL_HEADERS="content-type:$CONTENT_TYPE\nhost:954dcc10adf822b50ccceedef0aa97e6.r2.cloudflarestorage.com\nx-amz-date:$DATE_LONG\n"
SIGNED_HEADERS="content-type;host;x-amz-date"

# ペイロードハッシュ
PAYLOAD_HASH=$(openssl dgst -sha256 -binary "$FILE_PATH" | xxd -p -c 256)

# 正規リクエスト作成
CANONICAL_REQUEST="PUT\n$CANONICAL_URI\n$CANONICAL_QUERYSTRING\n$CANONICAL_HEADERS\n$SIGNED_HEADERS\n$PAYLOAD_HASH"

# 署名文字列
STRING_TO_SIGN="$ALGORITHM\n$DATE_LONG\n$DATE_SHORT/$REGION/$SERVICE/$REQUEST_TYPE\n$(echo -n "$CANONICAL_REQUEST" | openssl dgst -sha256 | cut -d' ' -f2)"

# 署名キー作成
SIGNING_KEY=$(echo -n "AWS4$SECRET_KEY" | openssl dgst -sha256 -hmac "$DATE_SHORT" -binary | \
              openssl dgst -sha256 -hmac "$REGION" -binary | \
              openssl dgst -sha256 -hmac "$SERVICE" -binary | \
              openssl dgst -sha256 -hmac "$REQUEST_TYPE" -binary)

# 署名
SIGNATURE=$(echo -n "$STRING_TO_SIGN" | openssl dgst -sha256 -hmac "$SIGNING_KEY" | cut -d' ' -f2)

# Authorization header
AUTHORIZATION="$ALGORITHM Credential=$ACCESS_KEY/$DATE_SHORT/$REGION/$SERVICE/$REQUEST_TYPE, SignedHeaders=$SIGNED_HEADERS, Signature=$SIGNATURE"

echo ""
echo "⬆️ Cloudflare R2にアップロード中..."
echo "  エンドポイント: $ENDPOINT"
echo "  バケット: $BUCKET"
echo "  ファイル名: $OBJECT_NAME"

# curlでアップロード
curl -X PUT \
  "$ENDPOINT/$BUCKET/$OBJECT_NAME" \
  -H "Content-Type: $CONTENT_TYPE" \
  -H "x-amz-date: $DATE_LONG" \
  -H "Authorization: $AUTHORIZATION" \
  -H "x-amz-content-sha256: $PAYLOAD_HASH" \
  --data-binary "@$FILE_PATH" \
  -w "\nHTTP Status: %{http_code}\n" \
  -o /tmp/upload_response.txt

# レスポンス確認
if [ $? -eq 0 ]; then
    HTTP_CODE=$(tail -n1 /tmp/upload_response.txt | grep "HTTP Status" | cut -d: -f2 | tr -d ' ')
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
        echo "✅ アップロード成功！"
        echo ""
        echo "🔗 公開URL:"
        echo "  https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/$OBJECT_NAME"
    else
        echo "❌ アップロード失敗 (HTTP Status: $HTTP_CODE)"
        cat /tmp/upload_response.txt
    fi
else
    echo "❌ curlコマンドの実行に失敗しました"
fi

rm -f /tmp/upload_response.txt