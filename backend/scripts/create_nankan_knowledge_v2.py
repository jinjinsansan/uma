#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南関東競馬統合ナレッジファイル作成スクリプト（34項目版 v2.0）
大井・川崎・船橋・浦和の4競馬場データを統合
JRA版と完全互換性を持つ34フィールド構造（3Fタイムデータ含む）

重要変更点：
- 32項目から34項目へ拡張
- ZENHAN_3F_TIME（前半3F）追加
- KOHAN_3F_TIME（後半3F）追加
- ファイル名固定（nankan_unified_knowledge_20250907.json）
"""

import psycopg2
import json
import sys
import io
import time
from datetime import datetime
from collections import defaultdict

# Windows環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# PostgreSQL接続情報（PC-KEIBA）
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

# 南関東競馬場コード
NANKAN_KEIBAJO_MAP = {
    '42': '大井',
    '43': '川崎',
    '44': '船橋',
    '45': '浦和'
}

def create_nankan_knowledge_v2():
    """南関東競馬統合ナレッジファイル作成（34項目版）"""
    
    print("=" * 80)
    print("🏇 南関東競馬統合ナレッジファイル作成（34項目版 v2.0）")
    print("=" * 80)
    print("⚠️  重要: 3Fタイムデータ（ZENHAN_3F_TIME、KOHAN_3F_TIME）を含む34項目版")
    print("⚠️  ファイル名: nankan_unified_knowledge_20250907.json で固定")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # PostgreSQL接続
        print("\n📊 PostgreSQL接続中...")
        conn = psycopg2.connect(**CONNECTION_PARAMS)
        cur = conn.cursor()
        
        # nvdテーブル確認
        print("🔍 nvdテーブル確認中...")
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name LIKE 'nvd_%'
        """)
        nvd_count = cur.fetchone()[0]
        print(f"✅ {nvd_count}個のnvdテーブルを確認")
        
        # 3Fタイムフィールドの存在確認
        print("\n🔍 3Fタイムフィールドの存在確認中...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'nvd_ra' AND column_name IN ('zenhan_3f', 'kohan_3f')
        """)
        ra_3f_fields = [row[0] for row in cur.fetchall()]
        
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'nvd_se' AND column_name = 'kohan_3f'
        """)
        se_3f_fields = [row[0] for row in cur.fetchall()]
        
        print(f"✅ nvd_ra: {', '.join(ra_3f_fields) if ra_3f_fields else '3Fフィールドなし'}")
        print(f"✅ nvd_se: {', '.join(se_3f_fields) if se_3f_fields else '3Fフィールドなし'}")
        
        # 南関東レースデータ取得クエリ（34フィールド）
        query = """
        SELECT 
            se.bamei,
            se.kaisai_nen || se.kaisai_tsukihi || se.keibajo_code || 
                LPAD(se.race_bango::text, 2, '0') || LPAD(se.umaban::text, 2, '0') as race_code,
            se.kaisai_nen,
            se.kaisai_tsukihi as kaisai_gappi,
            CASE 
                WHEN se.kakutei_chakujun IS NULL OR se.kakutei_chakujun = '' THEN '00'
                ELSE LPAD(se.kakutei_chakujun::text, 2, '0')
            END as kakutei_chakujun,
            CASE 
                WHEN se.tansho_odds IS NULL OR se.tansho_odds = '' THEN '0000'
                ELSE LPAD(se.tansho_odds::text, 4, '0')
            END as tansho_odds,
            CASE 
                WHEN se.tansho_ninkijun IS NULL OR se.tansho_ninkijun = '' THEN '00'
                ELSE LPAD(se.tansho_ninkijun::text, 2, '0')
            END as tansho_ninkijun,
            CASE 
                WHEN se.futan_juryo IS NULL OR se.futan_juryo = '' THEN '000'
                ELSE LPAD(se.futan_juryo::text, 3, '0')
            END as futan_juryo,
            CASE 
                WHEN se.bataiju IS NULL OR se.bataiju = '' THEN '000'
                ELSE LPAD(se.bataiju::text, 3, '0')
            END as bataiju,
            CASE 
                WHEN se.zogen_fugo = '-' THEN '-' || LPAD(COALESCE(se.zogen_sa::text, '00'), 2, '0')
                WHEN se.zogen_sa IS NULL OR se.zogen_sa = '' THEN '+00'
                ELSE '+' || LPAD(se.zogen_sa::text, 2, '0')
            END as zogen_sa,
            COALESCE(se.kishumei_ryakusho, '') as kishumei_ryakusho,
            COALESCE(se.chokyoshimei_ryakusho, '') as chokyoshimei_ryakusho,
            CASE 
                WHEN se.corner_1 IS NULL OR se.corner_1 = '' THEN '00'
                ELSE LPAD(se.corner_1::text, 2, '0')
            END as corner1_juni,
            CASE 
                WHEN se.corner_2 IS NULL OR se.corner_2 = '' THEN '00'
                ELSE LPAD(se.corner_2::text, 2, '0')
            END as corner2_juni,
            CASE 
                WHEN se.corner_3 IS NULL OR se.corner_3 = '' THEN '00'
                ELSE LPAD(se.corner_3::text, 2, '0')
            END as corner3_juni,
            CASE 
                WHEN se.corner_4 IS NULL OR se.corner_4 = '' THEN '00'
                ELSE LPAD(se.corner_4::text, 2, '0')
            END as corner4_juni,
            CASE 
                WHEN se.soha_time IS NULL OR se.soha_time = '' THEN '0000'
                ELSE LPAD(se.soha_time::text, 4, '0')
            END as soha_time,
            CASE 
                WHEN um.seinengappi IS NOT NULL AND um.seinengappi != '' THEN 
                    LPAD(GREATEST(0, (se.kaisai_nen::int - SUBSTRING(um.seinengappi, 1, 4)::int))::text, 2, '0')
                ELSE '00'
            END as barei,
            COALESCE(um.seibetsu_code, '0') as seibetsu_code,
            se.keibajo_code,
            LPAD(se.race_bango::text, 2, '0') as race_bango,
            se.ketto_toroku_bango,
            CASE 
                WHEN se.time_sa LIKE '+%' THEN se.time_sa
                WHEN se.time_sa LIKE '-%' THEN se.time_sa
                WHEN se.time_sa IS NULL OR se.time_sa = '' THEN '+000'
                ELSE '+' || LPAD(se.time_sa::text, 3, '0')
            END as time_sa,
            CASE 
                WHEN ra.kyori IS NULL THEN '0000'
                ELSE LPAD(ra.kyori::text, 4, '0')
            END as kyori,
            COALESCE(ra.track_code, '00') as track_code,
            COALESCE(ra.babajotai_code_shiba, '0') as shiba_babajotai_code,
            COALESCE(ra.babajotai_code_dirt, '0') as dirt_babajotai_code,
            COALESCE(ra.tenko_code, '0') as tenko_code,
            COALESCE(um.ketto_joho_01b, '') as sire,
            '' as dam,
            COALESCE(um.ketto_joho_02b, '') as broodmare_sire,
            se.keibajo_code as keibajo_code_raw,
            
            -- ★重要：3Fタイムフィールド（33-34番目）
            CASE 
                WHEN ra.zenhan_3f IS NULL OR ra.zenhan_3f = '' THEN '000'
                ELSE LPAD(ra.zenhan_3f::text, 3, '0')
            END as zenhan_3f_time,
            CASE 
                WHEN se.kohan_3f IS NULL OR se.kohan_3f = '' THEN '000'
                ELSE LPAD(se.kohan_3f::text, 3, '0')
            END as kohan_3f_time
            
        FROM nvd_se se
        JOIN nvd_ra ra ON (
            se.kaisai_nen = ra.kaisai_nen
            AND se.kaisai_tsukihi = ra.kaisai_tsukihi
            AND se.keibajo_code = ra.keibajo_code
            AND se.race_bango = ra.race_bango
        )
        LEFT JOIN nvd_um um ON se.ketto_toroku_bango = um.ketto_toroku_bango
        WHERE se.kaisai_nen BETWEEN '2019' AND '2025'
            AND se.keibajo_code IN ('42','43','44','45')
            AND se.ketto_toroku_bango != '0000000000'
            AND se.kakutei_chakujun IS NOT NULL
            AND se.kakutei_chakujun != '00'
            AND se.bamei IS NOT NULL
            AND se.bamei != ''
        ORDER BY se.bamei, se.kaisai_nen DESC, se.kaisai_tsukihi DESC
        """
        
        print("\n🔍 南関東4場のレースデータ取得中...")
        print("  対象: 大井(42)・川崎(43)・船橋(44)・浦和(45)")
        print("  期間: 2019年～2025年")
        print("  フィールド数: 34項目（3Fタイム含む）")
        
        query_start = time.time()
        cur.execute(query)
        query_end = time.time()
        print(f"✅ クエリ実行時間: {query_end - query_start:.2f}秒")
        
        # カラム名定義（34項目）
        col_names = [
            "BAMEI", "RACE_CODE", "KAISAI_NEN", "KAISAI_GAPPI", "KAKUTEI_CHAKUJUN",
            "TANSHO_ODDS", "TANSHO_NINKIJUN", "FUTAN_JURYO", "BATAIJU", "ZOGEN_SA",
            "KISHUMEI_RYAKUSHO", "CHOKYOSHIMEI_RYAKUSHO", "CORNER1_JUNI", "CORNER2_JUNI",
            "CORNER3_JUNI", "CORNER4_JUNI", "SOHA_TIME", "BAREI", "SEIBETSU_CODE",
            "KEIBAJO_CODE", "RACE_BANGO", "KETTO_TOROKU_BANGO", "TIME_SA", "KYORI",
            "TRACK_CODE", "SHIBA_BABAJOTAI_CODE", "DIRT_BABAJOTAI_CODE", "TENKO_CODE",
            "sire", "dam", "broodmare_sire", "track_name",
            "ZENHAN_3F_TIME", "KOHAN_3F_TIME"  # ★3Fタイムフィールド
        ]
        
        # データ処理
        print("\n📊 データ処理中...")
        horses_data = defaultdict(list)
        total_races = 0
        keibajo_stats = defaultdict(int)
        time_3f_stats = {'zenhan_count': 0, 'kohan_count': 0}
        
        for row in cur:
            horse_name = row[0].strip()
            
            # 競馬場名を設定
            keibajo_code = row[31]  # keibajo_code_raw
            track_name = NANKAN_KEIBAJO_MAP.get(keibajo_code, keibajo_code)
            keibajo_stats[track_name] += 1
            
            # レースデータを構築（34項目）
            race_data = {}
            for i, col_name in enumerate(col_names[:-2]):  # track_nameまで
                if i < 31:
                    race_data[col_name] = row[i]
            
            # track_nameを設定
            race_data['track_name'] = track_name
            
            # 3Fタイムを設定（33-34番目）
            race_data['ZENHAN_3F_TIME'] = row[32]  # zenhan_3f_time
            race_data['KOHAN_3F_TIME'] = row[33]   # kohan_3f_time
            
            # 3Fタイムの統計
            if race_data['ZENHAN_3F_TIME'] != '000':
                time_3f_stats['zenhan_count'] += 1
            if race_data['KOHAN_3F_TIME'] != '000':
                time_3f_stats['kohan_count'] += 1
            
            # 血統情報をトリム
            if race_data['sire']:
                race_data['sire'] = race_data['sire'].strip()
            if race_data['broodmare_sire']:
                race_data['broodmare_sire'] = race_data['broodmare_sire'].strip()
            
            # 馬のレースリストに追加
            horses_data[horse_name].append(race_data)
            total_races += 1
            
            # 進捗表示
            if total_races % 10000 == 0:
                print(f"  {total_races}レース処理済み...")
        
        # 9走制限を適用
        print("\n🔧 9走制限を適用中...")
        for horse_name in horses_data:
            if len(horses_data[horse_name]) > 9:
                horses_data[horse_name] = horses_data[horse_name][:9]
        
        # 統計情報表示
        print("\n📊 処理結果:")
        print(f"  総馬数: {len(horses_data)}頭")
        print(f"  総レース数: {total_races}件")
        print(f"  フィールド数: 34項目")
        
        print("\n  競馬場別レース数:")
        for track, count in sorted(keibajo_stats.items()):
            print(f"    {track}: {count}件")
        
        # 3Fタイムデータの統計
        print("\n  3Fタイムデータ統計:")
        if total_races > 0:
            zenhan_rate = time_3f_stats['zenhan_count'] * 100 / total_races
            kohan_rate = time_3f_stats['kohan_count'] * 100 / total_races
            print(f"    前半3F（ZENHAN_3F_TIME）: {time_3f_stats['zenhan_count']}件 ({zenhan_rate:.1f}%)")
            print(f"    後半3F（KOHAN_3F_TIME）: {time_3f_stats['kohan_count']}件 ({kohan_rate:.1f}%)")
        
        # データ品質チェック
        print("\n🔍 データ品質チェック:")
        sample_horses = list(horses_data.keys())[:5]
        horses_with_sire = 0
        horses_with_broodmare_sire = 0
        horses_with_3f_time = 0
        
        for horse_name in horses_data:
            if horses_data[horse_name]:
                if horses_data[horse_name][0].get('sire'):
                    horses_with_sire += 1
                if horses_data[horse_name][0].get('broodmare_sire'):
                    horses_with_broodmare_sire += 1
                # 3Fタイムがある馬をカウント
                for race in horses_data[horse_name]:
                    if race.get('ZENHAN_3F_TIME', '000') != '000' or race.get('KOHAN_3F_TIME', '000') != '000':
                        horses_with_3f_time += 1
                        break
        
        print(f"  父名あり: {horses_with_sire}/{len(horses_data)} ({horses_with_sire*100/len(horses_data):.1f}%)")
        print(f"  母父名あり: {horses_with_broodmare_sire}/{len(horses_data)} ({horses_with_broodmare_sire*100/len(horses_data):.1f}%)")
        print(f"  3Fタイムあり: {horses_with_3f_time}/{len(horses_data)} ({horses_with_3f_time*100/len(horses_data):.1f}%)")
        
        # サンプル表示
        print("\n【サンプルデータ確認】")
        for i, horse_name in enumerate(sample_horses[:3]):
            print(f"\n{i+1}. {horse_name}")
            if horses_data[horse_name]:
                race = horses_data[horse_name][0]
                print(f"   最新走: {race['KAISAI_NEN']}/{race['KAISAI_GAPPI']} {race['track_name']}")
                print(f"   着順: {race['KAKUTEI_CHAKUJUN']}着")
                print(f"   父: {race['sire'] if race['sire'] else '不明'}")
                print(f"   母父: {race['broodmare_sire'] if race['broodmare_sire'] else '不明'}")
                print(f"   前半3F: {race.get('ZENHAN_3F_TIME', '000')}")
                print(f"   後半3F: {race.get('KOHAN_3F_TIME', '000')}")
                print(f"   フィールド数: {len(race)}")
        
        # ファイル保存（ファイル名固定）
        output_file = "nankan_unified_knowledge_20250907.json"  # 固定ファイル名
        
        print(f"\n💾 ファイル保存中: {output_file}")
        save_start = time.time()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dict(horses_data), f, ensure_ascii=False, indent=2)
        save_end = time.time()
        
        # ファイルサイズ確認
        import os
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        
        cur.close()
        conn.close()
        
        total_time = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("🎉 南関東競馬統合ナレッジファイル作成完了！（34項目版）")
        print("=" * 80)
        print(f"✅ ファイル名: {output_file} （固定）")
        print(f"✅ ファイルサイズ: {file_size:.1f}MB")
        print(f"✅ 処理時間: {total_time:.2f}秒")
        print(f"✅ 総馬数: {len(horses_data)}頭")
        print(f"✅ 総レース数: {total_races}件")
        print(f"✅ フィールド数: 34項目")
        print("\n【エンジン互換性】")
        print("• D-Logic AI ✓")
        print("• I-Logic AI ✓")
        print("• IM-Logic AI ✓")
        print("• ViewLogic AI ✓ （ペース予想対応）")
        print("\n【次のステップ】")
        print("1. このファイルをCDNにアップロード（同じURL維持）")
        print("2. ViewLogicでペース予想の動作確認")
        print("3. バックエンドの再デプロイは不要（URLが同じため）")
        
        return output_file
        
    except Exception as e:
        import traceback
        print(f"\n❌ エラー: {e}")
        print(f"詳細: {traceback.format_exc()}")
        return None

def main():
    """メイン処理"""
    print("🏇 南関東競馬ナレッジファイル作成開始（34項目版 v2.0）")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    result = create_nankan_knowledge_v2()
    
    if result:
        print("\n✅ 正常に完了しました")
        print("\n📝 重要な確認事項:")
        print("1. ファイル名が 'nankan_unified_knowledge_20250907.json' であること")
        print("2. 34項目すべてが含まれていること")
        print("3. ZENHAN_3F_TIME、KOHAN_3F_TIMEが存在すること")
        print("4. CDNに同じファイル名でアップロードすること")
    else:
        print("\n❌ 作成に失敗しました")

if __name__ == "__main__":
    main()