#!/usr/bin/env python3
"""
JRA未来レース自動生成スクリプト
PostgreSQLのjvd_ra/jvd_seテーブルから未来レースデータを取得し、
フロントエンド用のTypeScriptファイルを自動生成します。

2歳戦・新馬戦は除外します。
"""

import json
import os
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# =====================================
# 設定
# =====================================

# PostgreSQL接続情報
CONNECTION_PARAMS = {
    "host": "172.25.160.1",  # WSL2からWindowsのPostgreSQL
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

# 競馬場コードマッピング
JYO_CODE_MAP = {
    '01': '札幌', '02': '函館', '03': '福島', '04': '新潟', '05': '東京',
    '06': '中山', '07': '中京', '08': '京都', '09': '阪神', '10': '小倉'
}

# 2歳戦・新馬戦の除外レース（9月13日）
EXCLUDE_RACES_0913 = {
    '06': [1, 2, 5, 6],  # 中山: 1R, 2R, 5R, 6R
    '09': [1, 2, 3, 5, 6]  # 阪神: 1R, 2R, 3R, 5R, 6R
}

# 出力先ディレクトリ（フロントエンド）
OUTPUT_DIR = "/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive"
METADATA_FILE = "/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/v2-metadata.json"

# =====================================
# データベース接続
# =====================================

def get_connection():
    """PostgreSQL接続を取得"""
    return psycopg2.connect(**CONNECTION_PARAMS)

# =====================================
# レースデータ取得
# =====================================

def get_races_for_date(date_str: str) -> List[Dict[str, Any]]:
    """
    指定日のレース情報を取得
    
    Args:
        date_str: MMDD形式の日付文字列（例: '0913'）
    
    Returns:
        レース情報のリスト
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # レース情報を取得
    query = """
    SELECT 
        r.keibajo_code,
        r.race_bango,
        r.kyosomei_hondai,
        r.kyosomei_fukudai,
        r.kyosomei_kakkonai,
        r.kyori,
        r.track_code,
        r.tenko_code,
        r.babajotai_code_shiba,
        r.babajotai_code_dirt,
        r.kaisai_kai,
        r.kaisai_nichime
    FROM jvd_ra r
    WHERE r.kaisai_nen = '2025'
      AND r.kaisai_tsukihi = %s
      AND r.keibajo_code IN ('01','02','03','04','05','06','07','08','09','10')
    ORDER BY r.keibajo_code, r.race_bango
    """
    
    cur.execute(query, (date_str,))
    races = cur.fetchall()
    
    # 出馬表データを取得
    horse_query = """
    SELECT 
        s.keibajo_code,
        s.race_bango,
        s.bamei,
        s.kishumei_ryakusho,
        s.umaban,
        s.wakuban,
        s.seibetsu_code,
        s.barei,
        s.futan_juryo,
        s.chokyoshimei_ryakusho,
        s.tansho_odds,
        s.tansho_ninkijun
    FROM jvd_se s
    WHERE s.kaisai_nen = '2025'
      AND s.kaisai_tsukihi = %s
      AND s.keibajo_code = %s
      AND s.race_bango = %s
    ORDER BY s.umaban
    """
    
    results = []
    for race in races:
        keibajo_code = race[0]
        race_no = int(race[1])
        
        # 除外レースをスキップ
        if date_str == '0913' and keibajo_code in EXCLUDE_RACES_0913:
            if race_no in EXCLUDE_RACES_0913[keibajo_code]:
                print(f"  除外: {JYO_CODE_MAP.get(keibajo_code, keibajo_code)} {race_no}R (2歳戦・新馬戦)")
                continue
        
        # 出馬表を取得
        cur.execute(horse_query, (date_str, keibajo_code, str(race_no).zfill(2)))
        horses = cur.fetchall()
        
        if not horses:
            continue
        
        # レース名
        race_name = race[2].strip() if race[2] else f"第{race_no}レース"
        
        # 距離
        kyori = race[5]
        track = 'ダ' if race[6] == '2' else '芝'
        distance = f"{track}{kyori}m"
        
        # 馬場状態
        if track == '芝':
            baba_code = race[8]
        else:
            baba_code = race[9]
        baba_map = {'1': '良', '2': '稍重', '3': '重', '4': '不良'}
        track_condition = baba_map.get(baba_code, '良')
        
        # 馬データを整理
        horse_names = []
        jockeys = []
        posts = []
        horse_numbers = []
        sex_ages = []
        weights = []
        trainers = []
        odds = []
        popularities = []
        
        for h in horses:
            horse_names.append(h[2].strip() if h[2] else f"馬{h[4]}")
            jockeys.append(h[3].strip() if h[3] else "未定")
            horse_numbers.append(int(h[4]))
            posts.append(int(h[5]) if h[5] else 0)
            
            # 性齢
            sex_map = {'1': '牡', '2': '牝', '3': 'セ'}
            sex = sex_map.get(h[6], '牡')
            age = h[7] if h[7] else '03'
            sex_ages.append(f"{sex}{age}")
            
            weights.append(float(h[8]) / 10 if h[8] else 55.0)
            trainers.append(h[9].strip() if h[9] else "未定")
            odds.append(float(h[10]) / 10 if h[10] and h[10] != '0' else 0.0)
            popularities.append(int(h[11]) if h[11] else 0)
        
        # 年を2025年に設定
        year = '2025'
        month = date_str[:2]
        day = date_str[2:]
        
        race_data = {
            'race_id': f"{year}{month}{day}-{JYO_CODE_MAP[keibajo_code]}-{race_no}",
            'race_date': f"{year}-{month}-{day}",
            'venue': JYO_CODE_MAP[keibajo_code],
            'race_number': race_no,
            'race_name': race_name,
            'distance': distance,
            'track_condition': track_condition,
            'horses': horse_names,
            'jockeys': jockeys,
            'posts': posts,
            'horse_numbers': horse_numbers,
            'sex_ages': sex_ages,
            'weights': weights,
            'trainers': trainers,
            'odds': odds,
            'popularities': popularities
        }
        
        results.append(race_data)
        print(f"  追加: {JYO_CODE_MAP[keibajo_code]} {race_no}R - {race_name}")
    
    cur.close()
    conn.close()
    
    return results

# =====================================
# ファイル生成
# =====================================

def generate_ts_file(date_str: str, venue: str, races: List[Dict[str, Any]]):
    """
    TypeScriptファイルを生成
    
    Args:
        date_str: YYYYMMDD形式の日付文字列
        venue: 競馬場名
        races: レースデータのリスト
    """
    # ファイル名
    filename = f"races-{date_str}-{venue}.ts"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # TypeScriptコード生成
    ts_content = f"""// {date_str[:4]}年{date_str[4:6]}月{date_str[6:8]}日 {venue}競馬場
// 自動生成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

export const races{date_str.replace('-', '')}{venue} = [
"""
    
    for i, race in enumerate(races):
        ts_content += "  {\n"
        ts_content += f"    race_id: '{race['race_id']}',\n"
        ts_content += f"    race_date: '{race['race_date']}',\n"
        ts_content += f"    venue: '{race['venue']}',\n"
        ts_content += f"    race_number: {race['race_number']},\n"
        ts_content += f"    race_name: '{race['race_name']}',\n"
        ts_content += f"    distance: '{race['distance']}',\n"
        ts_content += f"    track_condition: '{race['track_condition']}',\n"
        ts_content += f"    horses: {json.dumps(race['horses'], ensure_ascii=False)},\n"
        ts_content += f"    jockeys: {json.dumps(race['jockeys'], ensure_ascii=False)},\n"
        ts_content += f"    posts: {race['posts']},\n"
        ts_content += f"    horse_numbers: {race['horse_numbers']},\n"
        ts_content += f"    sex_ages: {json.dumps(race['sex_ages'], ensure_ascii=False)},\n"
        ts_content += f"    weights: {race['weights']},\n"
        ts_content += f"    trainers: {json.dumps(race['trainers'], ensure_ascii=False)},\n"
        ts_content += f"    odds: {race['odds']},\n"
        ts_content += f"    popularities: {race['popularities']}\n"
        ts_content += "  }"
        
        if i < len(races) - 1:
            ts_content += ","
        ts_content += "\n"
    
    ts_content += "];\n"
    
    # ファイル書き込み
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(ts_content)
    
    print(f"✅ ファイル生成: {filepath}")

def update_metadata(date_str: str, venues: List[str]):
    """
    メタデータファイルを更新
    
    Args:
        date_str: YYYY-MM-DD形式の日付文字列
        venues: 競馬場名のリスト
    """
    # 既存のメタデータを読み込み
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # archivesセクションに追加（重複チェック）
    if 'archives' not in metadata:
        metadata['archives'] = []
    
    # 既存エントリを探す
    existing = None
    for entry in metadata['archives']:
        if entry['date'] == date_str:
            existing = entry
            break
    
    if existing:
        # 既存エントリを更新
        for venue in venues:
            if venue not in existing['venues']:
                existing['venues'].append(venue)
        print(f"📝 メタデータ更新: {date_str} - {', '.join(venues)}")
    else:
        # 新規エントリを追加
        metadata['archives'].append({
            'date': date_str,
            'venues': venues
        })
        print(f"📝 メタデータ追加: {date_str} - {', '.join(venues)}")
    
    # 日付順にソート（新しい順）
    metadata['archives'].sort(key=lambda x: x['date'], reverse=True)
    
    # ファイル書き込み
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

# =====================================
# メイン処理
# =====================================

def main():
    """メイン処理"""
    print("=" * 50)
    print("JRA未来レース自動生成スクリプト")
    print("=" * 50)
    
    # 9月13日のレースを処理
    target_date = '0913'
    year = '2025'
    
    print(f"\n📅 {year}年9月13日のレース処理")
    
    # レースデータ取得
    all_races = get_races_for_date(target_date)
    
    if not all_races:
        print("⚠️ レースデータが見つかりません")
        return
    
    # 競馬場ごとにグループ化
    races_by_venue = {}
    for race in all_races:
        venue = race['venue']
        if venue not in races_by_venue:
            races_by_venue[venue] = []
        races_by_venue[venue].append(race)
    
    # TSファイル生成
    date_str = f"{year}{target_date[:2]}{target_date[2:]}"
    generated_venues = []
    
    for venue, races in races_by_venue.items():
        print(f"\n【{venue}競馬場】{len(races)}レース")
        generate_ts_file(date_str, venue, races)
        generated_venues.append(venue)
    
    # メタデータ更新
    if generated_venues:
        update_metadata(f"{year}-{target_date[:2]}-{target_date[2:]}", generated_venues)
    
    print("\n✅ 処理完了！")
    print(f"生成ファイル数: {len(generated_venues)}個")
    print(f"対象レース数: {len(all_races)}レース（2歳戦・新馬戦除外済み）")

if __name__ == "__main__":
    main()