#!/usr/bin/env python3
"""
Cloudflare R2へのアップロードスクリプト
"""

import boto3
from botocore.config import Config
import os
from datetime import datetime

# Cloudflare R2の設定
R2_ACCOUNT_ID = "b56e33a7bc854e68c3c913e6f71f8795"
R2_ACCESS_KEY_ID = "2e067b146528feca436e587a6c59b0e4"
R2_SECRET_ACCESS_KEY = "27efdcee88ad43b5cf2b8e06e2e7cc0b8c728b056ccbff8cc0f896fc1aac5f68"
R2_BUCKET_NAME = "uma"
R2_ENDPOINT_URL = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

def upload_to_r2():
    """ナレッジファイルをR2にアップロード"""
    
    # ファイルパス
    local_file = "unified_knowledge_20250924.json"
    
    if not os.path.exists(local_file):
        print(f"❌ ファイルが存在しません: {local_file}")
        return False
    
    # ファイルサイズ確認
    file_size = os.path.getsize(local_file) / (1024 * 1024)
    print(f"📁 アップロードファイル: {local_file}")
    print(f"📊 サイズ: {file_size:.1f}MB")
    
    # S3クライアントの作成（R2互換）
    s3_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(
            signature_version='s3v4',
            retries={'max_attempts': 3}
        ),
        region_name='auto'
    )
    
    try:
        # R2にアップロード（新しいファイル名で）
        remote_file = "unified_knowledge_20250924.json"
        
        print(f"\n⬆️ Cloudflare R2にアップロード中...")
        print(f"  バケット: {R2_BUCKET_NAME}")
        print(f"  ファイル名: {remote_file}")
        
        # アップロード実行
        s3_client.upload_file(
            local_file,
            R2_BUCKET_NAME,
            remote_file,
            ExtraArgs={
                'ContentType': 'application/json',
                'CacheControl': 'public, max-age=3600'
            }
        )
        
        print(f"✅ アップロード成功！")
        
        # 公開URLを生成
        public_url = f"https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/{remote_file}"
        print(f"\n🔗 公開URL:")
        print(f"  {public_url}")
        
        # 既存のファイルも更新（unified_knowledge_latest.jsonとして）
        print(f"\n⬆️ latest版も更新中...")
        s3_client.upload_file(
            local_file,
            R2_BUCKET_NAME,
            "unified_knowledge_latest.json",
            ExtraArgs={
                'ContentType': 'application/json',
                'CacheControl': 'public, max-age=3600'
            }
        )
        
        latest_url = f"https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_latest.json"
        print(f"✅ latest版も更新完了！")
        print(f"  {latest_url}")
        
        print(f"\n" + "="*60)
        print(f"🎉 Cloudflare R2へのアップロード完了！")
        print(f"="*60)
        print(f"\n次のステップ:")
        print(f"1. サービスのURLを新しいものに更新")
        print(f"   services/dlogic_raw_data_manager.py の")
        print(f"   KNOWLEDGE_CDN_URL を以下に変更:")
        print(f"   {public_url}")
        print(f"\n2. または latest版を使用する場合:")
        print(f"   {latest_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ アップロードエラー: {e}")
        return False

if __name__ == "__main__":
    upload_to_r2()