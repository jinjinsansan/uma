#!/usr/bin/env python3
"""
CDNファイルとローカルキャッシュの差異を確認
"""

import json
import requests
import hashlib

def check_file_differences():
    """ローカルキャッシュとCDNファイルの差異を確認"""
    
    print("=== CDNファイル差異確認 ===\n")
    
    cdn_url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json"
    local_cache = "/tmp/jockey_knowledge_cache.json"
    
    # 1. ローカルキャッシュのハッシュ値確認
    try:
        with open(local_cache, 'r', encoding='utf-8') as f:
            local_data = f.read()
        
        local_hash = hashlib.md5(local_data.encode()).hexdigest()
        local_json = json.loads(local_data)
        
        print(f"ローカルキャッシュ:")
        print(f"  ファイルサイズ: {len(local_data):,} bytes")
        print(f"  MD5ハッシュ: {local_hash}")
        print(f"  騎手数: {len(local_json)}")
        
        # サンプルデータ確認
        sample_jockey = next(iter(local_json.keys()))
        sample_data = local_json[sample_jockey]
        post_stats = sample_data.get('post_position_stats', {})
        if post_stats:
            first_waku = next(iter(post_stats.keys()))
            first_stats = post_stats[first_waku]
            print(f"  サンプルデータ ({sample_jockey}, {first_waku}): {type(first_stats)} = {first_stats}")
        
    except Exception as e:
        print(f"ローカルキャッシュ読み込みエラー: {e}")
        return
    
    # 2. CDNファイルのハッシュ値確認
    try:
        print(f"\nCDNファイル取得中: {cdn_url}")
        response = requests.get(cdn_url, timeout=60)
        response.raise_for_status()
        
        cdn_data = response.text
        cdn_hash = hashlib.md5(cdn_data.encode()).hexdigest()
        cdn_json = response.json()
        
        print(f"CDNファイル:")
        print(f"  ファイルサイズ: {len(cdn_data):,} bytes")
        print(f"  MD5ハッシュ: {cdn_hash}")
        print(f"  騎手数: {len(cdn_json)}")
        
        # サンプルデータ確認
        if sample_jockey in cdn_json:
            sample_data = cdn_json[sample_jockey]
            post_stats = sample_data.get('post_position_stats', {})
            if post_stats and first_waku in post_stats:
                first_stats = post_stats[first_waku]
                print(f"  サンプルデータ ({sample_jockey}, {first_waku}): {type(first_stats)} = {first_stats}")
        
    except Exception as e:
        print(f"CDNファイル取得エラー: {e}")
        return
    
    # 3. ファイル比較
    print(f"\n=== 比較結果 ===")
    if local_hash == cdn_hash:
        print("✅ ローカルキャッシュとCDNファイルは同一です")
    else:
        print("🚨 ローカルキャッシュとCDNファイルが異なります！")
        print("   これがエラーの原因の可能性があります")
        
        # 差異の詳細分析
        if len(local_json) != len(cdn_json):
            print(f"   騎手数の差: ローカル{len(local_json)} vs CDN{len(cdn_json)}")
        
        # 共通騎手でデータ構造を比較
        common_jockeys = set(local_json.keys()) & set(cdn_json.keys())
        print(f"   共通騎手数: {len(common_jockeys)}")
        
        # 最初の5名で詳細比較
        for jockey in list(common_jockeys)[:5]:
            local_post = local_json[jockey].get('post_position_stats', {})
            cdn_post = cdn_json[jockey].get('post_position_stats', {})
            
            if local_post != cdn_post:
                print(f"   差異発見: {jockey}")
                
                # 具体的な差異を確認
                for waku in local_post.keys() | cdn_post.keys():
                    local_stats = local_post.get(waku)
                    cdn_stats = cdn_post.get(waku)
                    
                    if local_stats != cdn_stats:
                        print(f"     {waku}: ローカル={type(local_stats)}, CDN={type(cdn_stats)}")
                        if not isinstance(cdn_stats, dict):
                            print(f"       🚨 CDNのstatsが辞書でない: {cdn_stats}")

if __name__ == "__main__":
    check_file_differences()