#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloudflare R2 シンプルアップロード（requestsライブラリ使用）
"""

import hashlib
import hmac
import datetime
import os
import requests
from urllib.parse import quote

# R2設定
ACCESS_KEY = "a99a85fd2a6a605da08dbaecee5f85bd"
SECRET_KEY = "43c5aa34efbeb423dc546f99a63cd70796a03279d39668ddb455754e62680fe3"
ENDPOINT = "https://954dcc10adf822b50ccceedef0aa97e6.r2.cloudflarestorage.com"
BUCKET = "dlogic-knowledge-files"
REGION = "auto"

def sign_aws4_auth(method, url, headers, payload, access_key, secret_key, region, service):
    """AWS Signature Version 4の署名を生成"""

    # 日付
    now = datetime.datetime.utcnow()
    datestamp = now.strftime('%Y%m%d')
    amzdate = now.strftime('%Y%m%dT%H%M%SZ')

    # ペイロードハッシュ
    if isinstance(payload, bytes):
        payload_hash = hashlib.sha256(payload).hexdigest()
    else:
        payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()

    # ヘッダー更新
    headers['x-amz-date'] = amzdate
    headers['x-amz-content-sha256'] = payload_hash

    # ホスト名取得
    host = url.split('/')[2]
    headers['host'] = host

    # Canonical Request作成
    canonical_uri = '/' + '/'.join(url.split('/')[3:])
    canonical_querystring = ''

    # ヘッダーをソート
    canonical_headers = ''
    signed_headers_list = []
    for key in sorted(headers.keys()):
        canonical_headers += f"{key.lower()}:{headers[key]}\n"
        signed_headers_list.append(key.lower())
    signed_headers = ';'.join(signed_headers_list)

    canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

    # String to Sign作成
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{datestamp}/{region}/{service}/aws4_request"
    string_to_sign = f"{algorithm}\n{amzdate}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

    # 署名キー作成
    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    kDate = sign(f"AWS4{secret_key}".encode('utf-8'), datestamp)
    kRegion = sign(kDate, region)
    kService = sign(kRegion, service)
    kSigning = sign(kService, 'aws4_request')

    # 署名作成
    signature = hmac.new(kSigning, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # Authorization header
    authorization = f"{algorithm} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    headers['Authorization'] = authorization

    return headers

def upload_file(file_path, object_name):
    """ファイルをR2にアップロード"""

    print("=" * 60)
    print("Cloudflare R2 アップロード")
    print("=" * 60)

    # ファイルサイズ確認
    file_size = os.path.getsize(file_path)
    print(f"ファイル: {file_path}")
    print(f"サイズ: {file_size / (1024*1024):.2f} MB")
    print(f"アップロード先: {BUCKET}/{object_name}")

    # ファイル読み込み
    print("\n📖 ファイル読み込み中...")
    with open(file_path, 'rb') as f:
        data = f.read()

    # URL作成
    url = f"{ENDPOINT}/{BUCKET}/{object_name}"

    # 基本ヘッダー
    headers = {
        'Content-Type': 'application/json',
        'Content-Length': str(len(data))
    }

    # 署名付きヘッダー作成
    headers = sign_aws4_auth('PUT', url, headers, data, ACCESS_KEY, SECRET_KEY, REGION, 's3')

    # アップロード実行
    print("\n⬆️ アップロード中...")
    try:
        response = requests.put(url, headers=headers, data=data, timeout=600)

        if response.status_code in [200, 201]:
            print("\n✅ アップロード成功！")
            print(f"ステータスコード: {response.status_code}")
            print(f"\nパブリックURL:")
            print(f"https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/{object_name}")
            return True
        else:
            print(f"\n❌ アップロード失敗")
            print(f"ステータスコード: {response.status_code}")
            print(f"レスポンス: {response.text}")
            return False

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False

def main():
    file_path = "/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/nankan_jockey_knowledge_20250907.json"
    object_name = "nankan_jockey_knowledge_20250907.json"

    if not os.path.exists(file_path):
        print(f"❌ ファイルが見つかりません: {file_path}")
        return

    success = upload_file(file_path, object_name)

    if success:
        print("\n⚠️ セキュリティのため、APIトークンを無効化してください。")

if __name__ == "__main__":
    main()