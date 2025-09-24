#!/bin/bash
# Cloudflare R2 アップロードスクリプト (S3互換API使用)

# 設定
ACCESS_KEY="a99a85fd2a6a605da08dbaecee5f85bd"
SECRET_KEY="43c5aa34efbeb423dc546f99a63cd70796a03279d39668ddb455754e62680fe3"
ENDPOINT="https://954dcc10adf822b50ccceedef0aa97e6.r2.cloudflarestorage.com"
BUCKET="dlogic-knowledge-files"
OBJECT_NAME="nankan_jockey_knowledge_20250907.json"
FILE_PATH="/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/nankan_jockey_knowledge_20250907.json"

# 日時設定
DATE=$(date -u +"%Y%m%dT%H%M%SZ")
DATE_SHORT=$(date -u +"%Y%m%d")
AWS_SERVICE="s3"
AWS_REGION="auto"
AWS_REQUEST="aws4_request"

# ファイルサイズ確認
FILE_SIZE=$(stat -c%s "$FILE_PATH")
FILE_SIZE_MB=$((FILE_SIZE / 1024 / 1024))

echo "=========================================="
echo "Cloudflare R2 アップロード"
echo "=========================================="
echo "ファイル: $FILE_PATH"
echo "サイズ: ${FILE_SIZE_MB} MB"
echo "バケット: $BUCKET"
echo "オブジェクト: $OBJECT_NAME"
echo ""

# Content-Type設定
CONTENT_TYPE="application/json"

# HTTPメソッド
HTTP_METHOD="PUT"

# Canonical URI
CANONICAL_URI="/${BUCKET}/${OBJECT_NAME}"

# Canonical Query String (空)
CANONICAL_QUERY=""

# ペイロードハッシュ計算
PAYLOAD_HASH=$(sha256sum "$FILE_PATH" | awk '{print $1}')

# Canonical Headers
CANONICAL_HEADERS="content-type:${CONTENT_TYPE}\nhost:954dcc10adf822b50ccceedef0aa97e6.r2.cloudflarestorage.com\nx-amz-content-sha256:${PAYLOAD_HASH}\nx-amz-date:${DATE}"

# Signed Headers
SIGNED_HEADERS="content-type;host;x-amz-content-sha256;x-amz-date"

# Canonical Request作成
CANONICAL_REQUEST="${HTTP_METHOD}\n${CANONICAL_URI}\n${CANONICAL_QUERY}\n${CANONICAL_HEADERS}\n\n${SIGNED_HEADERS}\n${PAYLOAD_HASH}"

# String to Sign作成
ALGORITHM="AWS4-HMAC-SHA256"
CREDENTIAL_SCOPE="${DATE_SHORT}/${AWS_REGION}/${AWS_SERVICE}/${AWS_REQUEST}"
CANONICAL_REQUEST_HASH=$(echo -ne "$CANONICAL_REQUEST" | sha256sum | awk '{print $1}')
STRING_TO_SIGN="${ALGORITHM}\n${DATE}\n${CREDENTIAL_SCOPE}\n${CANONICAL_REQUEST_HASH}"

# 署名計算
DATE_KEY=$(echo -n "$DATE_SHORT" | openssl dgst -sha256 -mac HMAC -macopt key:"AWS4${SECRET_KEY}" | awk '{print $2}')
REGION_KEY=$(echo -n "$AWS_REGION" | openssl dgst -sha256 -mac HMAC -macopt hexkey:$DATE_KEY | awk '{print $2}')
SERVICE_KEY=$(echo -n "$AWS_SERVICE" | openssl dgst -sha256 -mac HMAC -macopt hexkey:$REGION_KEY | awk '{print $2}')
SIGNING_KEY=$(echo -n "$AWS_REQUEST" | openssl dgst -sha256 -mac HMAC -macopt hexkey:$SERVICE_KEY | awk '{print $2}')
SIGNATURE=$(echo -ne "$STRING_TO_SIGN" | openssl dgst -sha256 -mac HMAC -macopt hexkey:$SIGNING_KEY | awk '{print $2}')

# Authorization Header
AUTHORIZATION="${ALGORITHM} Credential=${ACCESS_KEY}/${CREDENTIAL_SCOPE}, SignedHeaders=${SIGNED_HEADERS}, Signature=${SIGNATURE}"

echo "⬆️ アップロード開始..."

# curlでアップロード実行
curl -X PUT \
  "${ENDPOINT}${CANONICAL_URI}" \
  -H "Authorization: ${AUTHORIZATION}" \
  -H "Content-Type: ${CONTENT_TYPE}" \
  -H "x-amz-date: ${DATE}" \
  -H "x-amz-content-sha256: ${PAYLOAD_HASH}" \
  --data-binary "@${FILE_PATH}" \
  --progress-bar \
  -o upload_response.txt \
  -w "\n\nHTTP Status: %{http_code}\n"

# 結果確認
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ アップロード完了！"
    echo ""
    echo "パブリックURL:"
    echo "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/${OBJECT_NAME}"
    echo ""
    echo "⚠️ 重要: セキュリティのため、APIトークンを無効化してください。"
else
    echo ""
    echo "❌ アップロードに失敗しました"
    cat upload_response.txt
fi