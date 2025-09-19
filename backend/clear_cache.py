#!/usr/bin/env python3
"""
キャッシュクリアスクリプト
本番環境でキャッシュをクリアするために使用
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.v2.config_cache import points_config_cache
from api.v2.config import v2_config

print("=== キャッシュクリア開始 ===")

# キャッシュをクリア
points_config_cache.clear()
print("✅ ポイント設定キャッシュをクリアしました")

# 現在の設定を再読み込み
v2_config._config_cache = None
v2_config._last_cache_update = None

# 新しい値を確認
print("\n=== 現在の設定値（キャッシュクリア後） ===")
print(f"POINTS_PER_CHAT: {v2_config.POINTS_PER_CHAT}")

# 詳細確認
print("\n=== 詳細情報 ===")
print(f"環境変数 V2_POINTS_PER_CHAT: {os.getenv('V2_POINTS_PER_CHAT')}")

# Supabaseから直接取得
db_config = v2_config._get_db_config()
if db_config:
    print(f"DB chat_cost_points: {db_config.get('chat_cost_points')}")
else:
    print("DB設定: なし")

print("\n✅ キャッシュクリア完了！")