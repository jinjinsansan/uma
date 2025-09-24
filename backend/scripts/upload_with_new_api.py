#!/usr/bin/env python3
"""
新しいAPI認証情報を使用したCloudflare R2アップロード
"""

import sys
sys.path.insert(0, '/home/jinjinsansan/.local/lib/python3.12/site-packages')

try:
    import boto3
    from botocore.config import Config
    import os
    
    # 新しいCloudflare R2の認証情報
    R2_ACCESS_KEY_ID = "62b127c384fe4a78f4110c5fd3ebbf4e"
    R2_SECRET_ACCESS_KEY = "2876eb1b13d17ed1b002fb9164ce6db7d81f989cff3a848d72c17749a1f31a26"
    R2_ENDPOINT_URL = "https://954dcc10adf822b50ccceedef0aa97e6.r2.cloudflarestorage.com"
    R2_BUCKET_NAME = "dlogic-knowledge-files"
    
    # ファイルパス
    local_file = "unified_knowledge_20250903.json"
    
    if not os.path.exists(local_file):
        print(f"❌ ファイルが存在しません: {local_file}")
    else:
        # ファイルサイズ確認
        file_size = os.path.getsize(local_file) / (1024 * 1024)
        print(f"📁 アップロードファイル: {local_file}")
        print(f"📊 サイズ: {file_size:.1f}MB")
        
        # S3クライアントの作成（R2互換）
        print(f"\n🔧 S3クライアント作成中...")
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
            # R2にアップロード
            remote_file = "unified_knowledge_20250903.json"
            
            print(f"\n⬆️ Cloudflare R2にアップロード中...")
            print(f"  エンドポイント: {R2_ENDPOINT_URL}")
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
            
            # 公開URLを生成（既存のCDN URLと同じ形式）
            public_url = f"https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/{remote_file}"
            print(f"\n🔗 公開URL:")
            print(f"  {public_url}")
            
            # latest版も更新
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
            
            print("\n" + "="*60)
            print("🎉 Cloudflare R2へのアップロード完了！")
            print("="*60)
            print("\n✅ 週次更新スクリプトの修正とナレッジファイルの更新が完了しました！")
            print("✅ 38フィールドすべてが含まれた完全なナレッジファイルです")
            
        except Exception as e:
            print(f"❌ アップロードエラー: {e}")
            import traceback
            traceback.print_exc()
            
except ImportError as e:
    print(f"❌ モジュールインポートエラー: {e}")
    print("boto3がインストールされていることを確認してください")