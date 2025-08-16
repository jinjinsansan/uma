#!/usr/bin/env python3
"""ujsonのパフォーマンステスト"""
import time
import json

# ujsonをインポート（なければ標準jsonを使用）
try:
    import ujson
    has_ujson = True
except ImportError:
    ujson = json
    has_ujson = False

# テストデータ作成
test_data = {
    "horses": {
        f"horse_{i}": {
            "name": f"テスト馬{i}",
            "races": [
                {
                    "date": "2025-01-01",
                    "venue": "東京",
                    "distance": 2000,
                    "result": i % 18 + 1
                } for _ in range(5)
            ]
        } for i in range(1000)
    }
}

# 標準jsonでのテスト
start = time.time()
json_str = json.dumps(test_data)
json_time_dumps = time.time() - start

start = time.time()
json_data = json.loads(json_str)
json_time_loads = time.time() - start

print(f"標準json:")
print(f"  dumps: {json_time_dumps:.4f}秒")
print(f"  loads: {json_time_loads:.4f}秒")

if has_ujson:
    # ujsonでのテスト
    start = time.time()
    ujson_str = ujson.dumps(test_data)
    ujson_time_dumps = time.time() - start
    
    start = time.time()
    ujson_data = ujson.loads(ujson_str)
    ujson_time_loads = time.time() - start
    
    print(f"\nujson:")
    print(f"  dumps: {ujson_time_dumps:.4f}秒")
    print(f"  loads: {ujson_time_loads:.4f}秒")
    
    print(f"\n高速化率:")
    print(f"  dumps: {json_time_dumps/ujson_time_dumps:.1f}倍")
    print(f"  loads: {json_time_loads/ujson_time_loads:.1f}倍")
else:
    print("\nujsonがインストールされていません")
    print("pip install ujson でインストールしてください")