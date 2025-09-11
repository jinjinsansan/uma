#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南関東レース情報TSファイル自動生成スクリプト
PostgreSQL nvd_テーブルから取得してJRAと同じフォーマットで生成
"""

import psycopg2
import json
import sys
import io
from datetime import datetime, timedelta

# Windows環境での文字化け対策
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# PostgreSQL接続情報
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
    '45': '川崎',  # 2025年9月10日・11日は川崎がコード45を使用
    '46': '川崎',  # 2025年9月8日は川崎がコード46を使用
    '47': '浦和'
}

def get_nankan_races_for_date(date_str, venue_code):
    """指定日・指定競馬場の南関東レース情報を取得"""
    
    conn = psycopg2.connect(**CONNECTION_PARAMS)
    cur = conn.cursor()
    
    # YYYYMMDD形式からMMDD形式に変換
    mmdd = date_str[4:8]
    year = date_str[0:4]
    
    print(f"    デバッグ: year={year}, mmdd={mmdd}, venue_code={venue_code}")
    
    # レース情報を取得
    query = """
    SELECT DISTINCT
        ra.race_bango,
        ra.kyosomei_hondai,
        ra.kyori,
        ra.track_code,
        ra.babajotai_code_dirt,
        ra.hasso_jikoku
    FROM nvd_ra ra
    WHERE ra.kaisai_nen = %s
        AND ra.kaisai_tsukihi = %s
        AND ra.keibajo_code = %s
    ORDER BY ra.race_bango
    """
    
    cur.execute(query, (year, mmdd, venue_code))
    
    # デバッグ: 取得件数確認
    results = cur.fetchall()
    print(f"    取得レース数: {len(results)}")
    
    races = []
    
    for row in results:
        race_number = int(row[0])
        race_name = row[1].strip() if row[1] else f"{race_number}R"
        distance = int(row[2]) if row[2] else 0
        track_code = row[3]
        baba_code = row[4]
        hassotime = row[5]
        
        # 馬場状態を判定
        if baba_code == '1':
            track_condition = '良'
        elif baba_code == '2':
            track_condition = '稍重'
        elif baba_code == '3':
            track_condition = '重'
        elif baba_code == '4':
            track_condition = '不良'
        else:
            track_condition = '良'
        
        # 出馬表を取得
        query2 = """
        SELECT 
            se.umaban,
            se.wakuban,
            se.bamei,
            se.seibetsu_code,
            se.barei,
            se.futan_juryo,
            se.kishumei_ryakusho,
            se.chokyoshimei_ryakusho,
            se.tansho_odds,
            se.tansho_ninkijun
        FROM nvd_se se
        WHERE se.kaisai_nen = %s
            AND se.kaisai_tsukihi = %s
            AND se.keibajo_code = %s
            AND se.race_bango = %s
        ORDER BY se.umaban
        """
        
        cur2 = conn.cursor()
        cur2.execute(query2, (year, mmdd, venue_code, str(race_number).zfill(2)))
        
        horses = []
        jockeys = []
        posts = []
        horse_numbers = []
        sex_ages = []
        weights = []
        trainers = []
        odds = []
        popularities = []
        
        for horse_row in cur2:
            horse_numbers.append(int(horse_row[0]))
            posts.append(int(horse_row[1]) if horse_row[1] else 0)
            horses.append(horse_row[2].strip() if horse_row[2] else '')
            
            # 性齢を生成
            sex = horse_row[3]
            age = horse_row[4]
            if sex == '1':
                sex_str = '牡'
            elif sex == '2':
                sex_str = '牝'
            elif sex == '3':
                sex_str = 'セ'
            else:
                sex_str = ''
            # 馬齢を2桁表示（例：02, 03）
            age_str = str(age).zfill(2) if age else '00'
            sex_ages.append(f"{sex_str}{age_str}")
            
            weights.append(float(horse_row[5]) / 10 if horse_row[5] else 0)
            jockeys.append(horse_row[6].strip() if horse_row[6] else '')
            trainers.append(horse_row[7].strip() if horse_row[7] else '')
            
            # オッズと人気
            odds_val = float(horse_row[8]) / 10 if horse_row[8] and horse_row[8] != '0000' else 0
            odds.append(odds_val)
            pop = int(horse_row[9]) if horse_row[9] else 0
            popularities.append(pop)
        
        if horses:  # 出馬表がある場合のみ追加
            venue_name = NANKAN_KEIBAJO_MAP.get(venue_code, venue_code)
            date_obj = datetime.strptime(f"{year}{mmdd}", "%Y%m%d")
            formatted_date = date_obj.strftime("%Y-%m-%d")
            
            race_data = {
                "race_id": f"{year}{mmdd}-{venue_name}-{race_number}",
                "race_date": formatted_date,
                "venue": venue_name,
                "race_number": race_number,
                "race_name": race_name,
                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                "distance": f"ダ{distance}m",
                "track_condition": track_condition,
                "horses": horses,
                "jockeys": jockeys,
                "posts": posts,
                "horse_numbers": horse_numbers,
                "sex_ages": sex_ages,
                "weights": weights,
                "trainers": trainers,
                "odds": odds,
                "popularities": popularities
            }
            races.append(race_data)
        
        cur2.close()
    
    cur.close()
    conn.close()
    
    return races

def generate_ts_file(date_str, venue_code):
    """TSファイルを生成"""
    
    venue_name = NANKAN_KEIBAJO_MAP.get(venue_code, venue_code)
    races = get_nankan_races_for_date(date_str, venue_code)
    
    if not races:
        print(f"  ⚠️ {date_str} {venue_name}: レースデータなし")
        return None
    
    # TSファイル内容を生成
    ts_content = """import { ArchiveRace } from '@/types/archive';

export const races: ArchiveRace[] = ["""
    
    for i, race in enumerate(races):
        if i > 0:
            ts_content += ","
        
        ts_content += f"""
  {{
    race_id: '{race['race_id']}',
    race_date: '{race['race_date']}',
    venue: '{race['venue']}',
    race_number: {race['race_number']},
    race_name: '{race['race_name']}',
    created_at: '{race['created_at']}',
    distance: '{race['distance']}',
    track_condition: '{race['track_condition']}',
    horses: {json.dumps(race['horses'], ensure_ascii=False)},
    jockeys: {json.dumps(race['jockeys'], ensure_ascii=False)},
    posts: {race['posts']},
    horse_numbers: {race['horse_numbers']},
    sex_ages: {json.dumps(race['sex_ages'], ensure_ascii=False)},
    weights: {race['weights']},
    trainers: {json.dumps(race['trainers'], ensure_ascii=False)},
    odds: {race['odds']},
    popularities: {race['popularities']}
  }}"""
    
    ts_content += """
];"""
    
    # ファイル名
    filename = f"races-{date_str}-{venue_name}.ts"
    filepath = f"/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/local/{filename}"
    
    # ファイル保存
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(ts_content)
    
    print(f"  ✅ {filename} 生成完了 ({len(races)}レース)")
    return filename

def update_v2_metadata(generated_files):
    """v2-metadata.jsonを更新"""
    metadata_path = "/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/v2-metadata.json"
    
    # 既存のメタデータを読み込む
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # localセクションがなければ作成
    if 'local' not in metadata:
        metadata['local'] = []
    
    # 生成したファイルの情報をメタデータに追加
    for file_info in generated_files:
        date_str = file_info['date']
        venue = file_info['venue']
        
        # 既存の日付データを探す
        date_entry = None
        for entry in metadata['local']:
            if entry.get('date') == date_str:
                date_entry = entry
                break
        
        # なければ新規作成
        if not date_entry:
            date_entry = {
                "date": date_str,
                "venues": []
            }
            metadata['local'].append(date_entry)
        
        # 競馬場が含まれていなければ追加
        if venue not in date_entry['venues']:
            date_entry['venues'].append(venue)
    
    # ソート
    metadata['local'] = sorted(metadata['local'], key=lambda x: x['date'], reverse=True)
    
    # ファイルに書き込み
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 v2-metadata.json更新完了")

def main():
    """メイン処理"""
    
    print("=" * 60)
    print("🏇 南関東レース情報TSファイル生成")
    print("=" * 60)
    
    # 9月10日・11日のデータを生成
    today = datetime(2025, 9, 10)  # 9月10日から開始
    
    print("\n📊 レースデータ生成中...")
    
    generated_files = []
    for days_ahead in range(0, 2):  # 9月10日・11日の2日間
        target_date = today + timedelta(days=days_ahead)
        date_str = target_date.strftime("%Y%m%d")
        
        print(f"\n📅 {date_str}:")
        
        # 各競馬場をチェック
        for venue_code, venue_name in NANKAN_KEIBAJO_MAP.items():
            filename = generate_ts_file(date_str, venue_code)
            if filename:
                generated_files.append({
                    "date": target_date.strftime("%Y-%m-%d"),
                    "venue": venue_name,
                    "filename": filename
                })
    
    print("\n" + "=" * 60)
    print("✅ 生成完了!")
    print(f"生成ファイル数: {len(generated_files)}")
    
    if generated_files:
        print("\n📁 生成されたファイル:")
        for file_info in generated_files:
            print(f"  - {file_info['date']} {file_info['venue']}: {file_info['filename']}")
        
        # v2-metadata.json更新
        update_v2_metadata(generated_files)
    
    return generated_files

if __name__ == "__main__":
    main()