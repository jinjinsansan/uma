#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloudflare R2 APIアップロードスクリプト
300MB超えの騎手ナレッジファイルをアップロード
"""

import boto3
import os
from datetime import datetime

# Cloudflare R2設定
R2_CONFIG = {
    'access_key_id': 'a99a85fd2a6a605da08dbaecee5f85bd',
    'secret_access_key': '43c5aa34efbeb423dc546f99a63cd70796a03279d39668ddb455754e62680fe3',
    'endpoint_url': 'https://954dcc10adf822b50ccceedef0aa97e6.r2.cloudflarestorage.com',
    'bucket_name': 'dlogic-knowledge-files'
}

def upload_to_r2(file_path, object_name=None):
    """
    Cloudflare R2にファイルをアップロード
    """
    if object_name is None:
        object_name = os.path.basename(file_path)

    try:
        # S3クライアント作成（R2はS3互換）
        s3_client = boto3.client(
            's3',
            aws_access_key_id=R2_CONFIG['access_key_id'],
            aws_secret_access_key=R2_CONFIG['secret_access_key'],
            endpoint_url=R2_CONFIG['endpoint_url'],
            region_name='auto'  # R2では'auto'を使用
        )

        # ファイルサイズ確認
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"📁 アップロードファイル: {file_path}")
        print(f"   サイズ: {file_size_mb:.2f} MB")
        print(f"   バケット: {R2_CONFIG['bucket_name']}")
        print(f"   オブジェクト名: {object_name}")

        print("\n⬆️ アップロード開始...")
        start_time = datetime.now()

        # マルチパートアップロード（大きなファイル用）
        if file_size > 100 * 1024 * 1024:  # 100MB以上
            print("   マルチパートアップロードを使用...")

            # マルチパートアップロードの設定
            config = boto3.s3.transfer.TransferConfig(
                multipart_threshold=1024 * 25,  # 25MB
                max_concurrency=10,
                multipart_chunksize=1024 * 25,
                use_threads=True
            )

            # アップロード実行
            s3_client.upload_file(
                file_path,
                R2_CONFIG['bucket_name'],
                object_name,
                Config=config,
                Callback=ProgressPercentage(file_path)
            )
        else:
            # 通常のアップロード
            s3_client.upload_file(
                file_path,
                R2_CONFIG['bucket_name'],
                object_name
            )

        end_time = datetime.now()
        upload_time = (end_time - start_time).total_seconds()

        print(f"\n✅ アップロード成功！")
        print(f"   所要時間: {upload_time:.1f}秒")

        # オブジェクトのURL生成
        object_url = f"{R2_CONFIG['endpoint_url']}/{R2_CONFIG['bucket_name']}/{object_name}"
        print(f"   URL: {object_url}")

        # パブリックURLの場合（R2の設定による）
        public_url = f"https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/{object_name}"
        print(f"   パブリックURL: {public_url}")

        return True

    except Exception as e:
        print(f"❌ アップロードエラー: {e}")
        return False

class ProgressPercentage:
    """アップロード進捗表示"""
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100
        print(f"\r   進捗: {percentage:.1f}% ({self._seen_so_far / (1024*1024):.1f}MB / {self._size / (1024*1024):.1f}MB)", end='')
        if percentage >= 100:
            print()  # 改行

def main():
    """メイン処理"""
    print("=" * 60)
    print("Cloudflare R2 騎手ナレッジファイルアップロード")
    print("=" * 60)
    print(f"実行時刻: {datetime.now()}")

    # アップロードするファイル
    file_path = "/mnt/e/dev/Cusor/chatbot/uma/backend/scripts/nankan_jockey_knowledge_20250907.json"

    if not os.path.exists(file_path):
        print(f"❌ ファイルが見つかりません: {file_path}")
        return False

    # アップロード実行
    success = upload_to_r2(file_path)

    if success:
        print("\n" + "=" * 60)
        print("✅ 全処理完了！")
        print("=" * 60)
        print("\n⚠️ 重要: セキュリティのため、APIトークンを無効化してください。")

    return success

if __name__ == "__main__":
    main()