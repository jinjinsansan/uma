#!/usr/bin/env python3
"""
騎手ナレッジファイル用アップロードスクリプト
"""

import os
import hashlib
import hmac
import datetime
import requests
from urllib.parse import quote

# 新しいAPI認証情報（2025-10-06更新）
ACCESS_KEY = "80bb7aca390fc82976b09b1005f7f531"
SECRET_KEY = "dd64d5ea1bedd6acfff0a42ebc771c81c459976fff03fd6677f5ba65b0e7fbbd"
ENDPOINT = "https://954dcc10adf822b50ccceedef0aa97e6.r2.cloudflarestorage.com"
BUCKET = "dlogic-knowledge-files"
REGION = "auto"

def sign_request(method, url, headers, payload, access_key, secret_key, region, service='s3'):
    """AWS Signature Version 4の署名を生成"""
    
    # 現在時刻（UTC）
    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')
    
    # ヘッダーに日時を追加
    headers['x-amz-date'] = amz_date
    
    # ペイロードのハッシュ
    if payload is None:
        payload = b''
    elif isinstance(payload, str):
        payload = payload.encode('utf-8')
    
    payload_hash = hashlib.sha256(payload).hexdigest()
    headers['x-amz-content-sha256'] = payload_hash
    
    # 正規リクエストの作成
    canonical_uri = '/' + BUCKET + '/' + 'jockey_knowledge.json'
    canonical_querystring = ''
    
    # ヘッダーをソート
    canonical_headers = ''
    signed_headers = []
    for key in sorted(headers.keys()):
        canonical_headers += key.lower() + ':' + headers[key] + '\n'
        signed_headers.append(key.lower())
    signed_headers_str = ';'.join(signed_headers)
    
    canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers_str}\n{payload_hash}"
    
    # 署名文字列の作成
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    
    # 署名キーの生成
    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
    
    k_date = sign(('AWS4' + secret_key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    k_signing = sign(k_service, 'aws4_request')
    
    # 署名の計算
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # Authorizationヘッダーの作成
    authorization_header = f"{algorithm} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers_str}, Signature={signature}"
    headers['Authorization'] = authorization_header
    
    return headers

def upload_file():
    """ファイルをアップロード"""
    
    local_file = "jockey_knowledge.json"
    
    if not os.path.exists(local_file):
        print(f"❌ ファイルが存在しません: {local_file}")
        return False
    
    # ファイルサイズ確認
    file_size = os.path.getsize(local_file) / (1024 * 1024)
    print(f"📁 アップロードファイル: {local_file}")
    print(f"📊 サイズ: {file_size:.1f}MB")
    
    # ファイルを読み込む
    with open(local_file, 'rb') as f:
        file_data = f.read()
    
    # URLとヘッダーの準備
    url = f"{ENDPOINT}/{BUCKET}/jockey_knowledge.json"
    headers = {
        'Host': '954dcc10adf822b50ccceedef0aa97e6.r2.cloudflarestorage.com',
        'Content-Type': 'application/json'
    }
    
    # 署名付きヘッダーを生成
    signed_headers = sign_request('PUT', url, headers, file_data, ACCESS_KEY, SECRET_KEY, REGION)
    
    print(f"\n⬆️ Cloudflare R2にアップロード中...")
    print(f"  URL: {url}")
    
    try:
        # アップロード実行（タイムアウト600秒、SSL検証有効）
        response = requests.put(
            url, 
            data=file_data, 
            headers=signed_headers,
            timeout=600,  # 10分のタイムアウト
            verify=True   # SSL証明書検証
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ アップロード成功！")
            print(f"\n🔗 公開URL:")
            print(f"  https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json")
            print("\n" + "="*60)
            print("🎉 完了！")
            print("="*60)
            return True
        else:
            print(f"❌ アップロード失敗")
            print(f"  ステータスコード: {response.status_code}")
            print(f"  レスポンス: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    upload_file()
