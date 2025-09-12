#!/usr/bin/env python3
"""
データ形式調査スクリプト
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# .envファイルの読み込み
load_dotenv()

# Supabase設定
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Supabaseクライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def debug_data():
    print("=" * 80)
    print("🔍 データ形式調査")
    print("=" * 80)
    
    # 予測データ1件を表示
    predictions = supabase.table('jra_predictions').select('*').limit(3).execute()
    print("\n【予測データサンプル】")
    for i, pred in enumerate(predictions.data):
        print(f"\n{i+1}件目:")
        for key, value in pred.items():
            print(f"  {key}: {value}")
    
    # 払い戻しデータ1件を表示
    payouts = supabase.table('jra_payouts').select('*').limit(3).execute()
    print("\n【払い戻しデータサンプル】")
    for i, payout in enumerate(payouts.data):
        print(f"\n{i+1}件目:")
        for key, value in payout.items():
            print(f"  {key}: {value}")
    
    # レース情報1件を表示
    races = supabase.table('jra_races').select('*').limit(3).execute()
    print("\n【レース情報サンプル】")
    for i, race in enumerate(races.data):
        print(f"\n{i+1}件目:")
        for key, value in race.items():
            print(f"  {key}: {value}")

if __name__ == '__main__':
    debug_data()