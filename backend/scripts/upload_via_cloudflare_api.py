#!/usr/bin/env python3
"""
Cloudflare APIを直接使用したアップロード
"""

import requests
import os
import json
from datetime import datetime

# Cloudflare R2の設定
R2_ACCOUNT_ID = "b56e33a7bc854e68c3c913e6f71f8795"
R2_ACCESS_KEY_ID = "2e067b146528feca436e587a6c59b0e4"
R2_SECRET_ACCESS_KEY = "27efdcee88ad43b5cf2b8e06e2e7cc0b8c728b056ccbff8cc0f896fc1aac5f68"
R2_BUCKET_NAME = "uma"

def upload_to_cloudflare():
    """Cloudflare APIを使用してアップロード"""
    
    local_file = "unified_knowledge_20250924.json"
    
    if not os.path.exists(local_file):
        print(f"❌ ファイルが存在しません: {local_file}")
        return False
    
    # ファイル情報
    file_size = os.path.getsize(local_file) / (1024 * 1024)
    print(f"📁 アップロードファイル: {local_file}")
    print(f"📊 サイズ: {file_size:.1f}MB")
    
    # curlコマンドを使用してアップロード
    import subprocess
    
    # 日付付きファイル名でアップロード
    remote_file = "unified_knowledge_20250924.json"
    
    # AWS CLIを使用（S3互換）
    cmd = [
        'aws', 's3', 'cp',
        local_file,
        f's3://{R2_BUCKET_NAME}/{remote_file}',
        '--endpoint-url', f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        '--region', 'auto',
        '--no-verify-ssl'
    ]
    
    # AWS認証情報を環境変数として設定
    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = R2_ACCESS_KEY_ID
    env['AWS_SECRET_ACCESS_KEY'] = R2_SECRET_ACCESS_KEY
    
    print(f"\n⬆️ Cloudflare R2にアップロード中...")
    print(f"  バケット: {R2_BUCKET_NAME}")
    print(f"  ファイル名: {remote_file}")
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ アップロード成功！")
            
            # 公開URL
            public_url = f"https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/{remote_file}"
            print(f"\n🔗 公開URL:")
            print(f"  {public_url}")
            
            # latest版もアップロード
            print(f"\n⬆️ latest版も更新中...")
            cmd_latest = [
                'aws', 's3', 'cp',
                local_file,
                f's3://{R2_BUCKET_NAME}/unified_knowledge_latest.json',
                '--endpoint-url', f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
                '--region', 'auto',
                '--no-verify-ssl'
            ]
            
            result_latest = subprocess.run(cmd_latest, env=env, capture_output=True, text=True)
            
            if result_latest.returncode == 0:
                latest_url = f"https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_latest.json"
                print(f"✅ latest版も更新完了！")
                print(f"  {latest_url}")
            
            print(f"\n" + "="*60)
            print(f"🎉 Cloudflare R2へのアップロード完了！")
            print(f"="*60)
            
            return True
        else:
            print(f"❌ アップロード失敗")
            print(f"エラー: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ AWS CLIがインストールされていません")
        print("別の方法を試します...")
        
        # rcloneを試す
        try:
            # rclone設定ファイルを作成
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
                f.write(f"""[r2]
type = s3
provider = Cloudflare
access_key_id = {R2_ACCESS_KEY_ID}
secret_access_key = {R2_SECRET_ACCESS_KEY}
endpoint = https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com
acl = private
""")
                config_file = f.name
            
            # rcloneでアップロード
            rclone_cmd = [
                'rclone', 'copy',
                local_file,
                f'r2:{R2_BUCKET_NAME}/',
                '--config', config_file,
                '--no-check-certificate'
            ]
            
            result = subprocess.run(rclone_cmd, capture_output=True, text=True)
            
            # 設定ファイルを削除
            os.unlink(config_file)
            
            if result.returncode == 0:
                print(f"✅ rcloneでアップロード成功！")
                return True
            else:
                print(f"❌ rcloneでもアップロード失敗: {result.stderr}")
                
        except FileNotFoundError:
            print("❌ rcloneもインストールされていません")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        
    return False

if __name__ == "__main__":
    upload_to_cloudflare()