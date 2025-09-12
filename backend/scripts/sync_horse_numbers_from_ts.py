#!/usr/bin/env python3
"""
TSファイルから馬番データを取得してSupabaseに同期
"""

import os
import re
import ast
from typing import Dict, List, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# Supabase設定
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Supabaseクライアント初期化
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# TSファイルパス
TS_FILES = [
    '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250831.ts',
    '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250906-中山.ts',
    '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250906-札幌.ts',
    '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250906-阪神.ts',
    '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250907-中山.ts',
    '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250907-札幌.ts',
    '/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/races-20250907-阪神.ts',
]

class HorseNumberSyncer:
    """馬番同期クラス"""
    
    def __init__(self):
        self.race_mapping = {}  # supabase_race_id -> ts_race_data
        self.success_count = 0
        self.error_count = 0
        
    def load_supabase_races(self):
        """Supabaseからレース情報を取得"""
        print("📊 Supabaseレース情報読み込み")
        
        result = supabase.table('jra_races').select('*').execute()
        races = result.data
        
        print(f"✅ Supabaseレース: {len(races)}件")
        return races
    
    def parse_ts_file(self, file_path: str) -> List[Dict]:
        """TSファイルを解析してレースデータを取得"""
        print(f"🔍 TSファイル解析: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # レースブロックを抽出
            races = []
            
            # 各レースブロックを正規表現で抽出
            race_pattern = r'\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
            matches = re.finditer(race_pattern, content, re.DOTALL)
            
            for match in matches:
                race_block = match.group(1)
                
                # race_date, venue, race_number, horses, horse_numbersを抽出
                race_data = self.extract_race_data(race_block)
                if race_data:
                    races.append(race_data)
            
            print(f"  抽出レース数: {len(races)}件")
            return races
            
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            return []
    
    def extract_race_data(self, race_block: str) -> Dict:
        """レースブロックからデータを抽出"""
        try:
            # race_date
            date_match = re.search(r'race_date:\s*["\']([^"\']+)["\']', race_block)
            if not date_match:
                return None
            race_date = date_match.group(1)
            
            # venue
            venue_match = re.search(r'venue:\s*["\']([^"\']+)["\']', race_block)
            if not venue_match:
                return None
            venue = venue_match.group(1)
            
            # race_number
            number_match = re.search(r'race_number:\s*(\d+)', race_block)
            if not number_match:
                return None
            race_number = int(number_match.group(1))
            
            # horses配列を抽出
            horses_match = re.search(r'horses:\s*\[(.*?)\]', race_block, re.DOTALL)
            if not horses_match:
                return None
            horses_str = horses_match.group(1)
            horses = re.findall(r'["\']([^"\']+)["\']', horses_str)
            
            # horse_numbers配列を抽出
            numbers_match = re.search(r'horse_numbers:\s*\[(.*?)\]', race_block, re.DOTALL)
            if not numbers_match:
                return None
            numbers_str = numbers_match.group(1)
            horse_numbers = [int(x.strip()) for x in numbers_str.split(',') if x.strip().isdigit()]
            
            return {
                'race_date': race_date,
                'venue': venue,
                'race_number': race_number,
                'horses': horses,
                'horse_numbers': horse_numbers
            }
            
        except Exception as e:
            return None
    
    def create_race_mapping(self, supabase_races: List[Dict], ts_races: List[Dict]):
        """SupabaseレースとTSレースのマッピングを作成"""
        print("\n🔄 レースマッピング作成")
        
        mapped_count = 0
        
        for sb_race in supabase_races:
            sb_date = sb_race['開催日']
            sb_venue = sb_race['競馬場']
            sb_number = sb_race['レース番号']
            sb_id = sb_race['id']
            
            # 対応するTSレースを検索
            for ts_race in ts_races:
                if (ts_race['race_date'] == sb_date and 
                    ts_race['venue'] == sb_venue and 
                    ts_race['race_number'] == sb_number):
                    
                    self.race_mapping[sb_id] = ts_race
                    mapped_count += 1
                    print(f"  ✅ {sb_date} {sb_venue} {sb_number}R → race_id:{sb_id}")
                    break
        
        print(f"🎯 マッピング完了: {mapped_count}件")
    
    def add_horse_number_column(self):
        """jra_horsesテーブルに馬番カラムを追加"""
        print("\n📋 jra_horsesテーブルに馬番カラム追加")
        
        try:
            # まず既存のjra_horsesテーブル構造を確認
            existing_horses = supabase.table('jra_horses').select('*').limit(1).execute()
            
            if existing_horses.data and '馬番' not in existing_horses.data[0]:
                print("⚠️ 馬番カラムが存在しません。SQLで手動追加が必要です:")
                print("ALTER TABLE jra_horses ADD COLUMN 馬番 INTEGER;")
                return False
            else:
                print("✅ 馬番カラムは既に存在します")
                return True
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            return False
    
    def update_horse_numbers(self):
        """馬番をSupabaseに更新"""
        print("\n🔄 馬番データ更新開始")
        
        for race_id, ts_race in self.race_mapping.items():
            try:
                horses = ts_race['horses']
                horse_numbers = ts_race['horse_numbers']
                
                if len(horses) != len(horse_numbers):
                    print(f"  ⚠️ race_id:{race_id} - 馬名と馬番の数が一致しません")
                    self.error_count += 1
                    continue
                
                # 各馬の馬番を更新
                updated_horses = 0
                for i, (horse_name, horse_number) in enumerate(zip(horses, horse_numbers)):
                    try:
                        # 該当する馬のレコードを更新
                        result = supabase.table('jra_horses').update({
                            '馬番': horse_number
                        }).eq('race_id', race_id).eq('馬名', horse_name).execute()
                        
                        if result.data:
                            updated_horses += 1
                    
                    except Exception as e:
                        print(f"    ❌ {horse_name} 更新エラー: {e}")
                
                if updated_horses > 0:
                    self.success_count += 1
                    print(f"  ✅ race_id:{race_id} - {updated_horses}頭更新完了")
                else:
                    self.error_count += 1
                    print(f"  ❌ race_id:{race_id} - 更新失敗")
                    
            except Exception as e:
                print(f"  ❌ race_id:{race_id} エラー: {e}")
                self.error_count += 1

def main():
    """メイン処理"""
    print("🚀 TSファイルから馬番同期システム")
    print("=" * 60)
    
    syncer = HorseNumberSyncer()
    
    # 1. Supabaseレース情報取得
    supabase_races = syncer.load_supabase_races()
    
    # 2. 馬番カラム確認・追加
    if not syncer.add_horse_number_column():
        print("⚠️ まず手動でカラム追加してください")
        return
    
    # 3. 全TSファイルを解析
    all_ts_races = []
    for ts_file in TS_FILES:
        ts_races = syncer.parse_ts_file(ts_file)
        all_ts_races.extend(ts_races)
    
    print(f"📊 TSファイル総レース数: {len(all_ts_races)}件")
    
    # 4. マッピング作成
    syncer.create_race_mapping(supabase_races, all_ts_races)
    
    # 5. 馬番更新
    syncer.update_horse_numbers()
    
    # 6. 結果サマリー
    print("\n" + "=" * 60)
    print("📈 同期結果サマリー")
    print(f"✅ 成功: {syncer.success_count}レース")
    print(f"❌ 失敗: {syncer.error_count}レース")
    print("=" * 60)

if __name__ == '__main__':
    main()