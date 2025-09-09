#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
レース情報ページ自動生成スクリプト
PostgreSQL速報系データから自動的にレース情報を生成
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

# JRA競馬場コード
JRA_KEIBAJO_MAP = {
    '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
    '05': '東京', '06': '中山', '07': '中京', '08': '京都',
    '09': '阪神', '10': '小倉'
}

# 南関東競馬場コード
NANKAN_KEIBAJO_MAP = {
    '42': '大井', '43': '川崎', '44': '船橋', '45': '浦和'
}

def get_jra_races_for_date(date_str):
    """指定日のJRAレース情報を取得"""
    
    conn = psycopg2.connect(**CONNECTION_PARAMS)
    cur = conn.cursor()
    
    # YYYYMMDD形式からMMDD形式に変換
    mmdd = date_str[4:8]
    year = date_str[0:4]
    
    query = """
    SELECT DISTINCT
        ra.keibajo_code,
        ra.race_bango,
        ra.race_name,
        ra.kyori,
        ra.track_code,
        ra.hassotime,
        ra.shusso_tosu,
        ra.grade_code
    FROM jvd_ra ra
    WHERE ra.kaisai_nen = %s
        AND ra.kaisai_tsukihi = %s
        AND ra.keibajo_code IN ('01','02','03','04','05','06','07','08','09','10')
    ORDER BY ra.keibajo_code, ra.race_bango
    """
    
    cur.execute(query, (year, mmdd))
    
    races_by_venue = {}
    for row in cur:
        keibajo_code = row[0]
        venue = JRA_KEIBAJO_MAP.get(keibajo_code, keibajo_code)
        
        if venue not in races_by_venue:
            races_by_venue[venue] = []
        
        races_by_venue[venue].append({
            "race_number": int(row[1]),
            "race_name": row[2].strip() if row[2] else "",
            "distance": int(row[3]) if row[3] else 0,
            "track": "芝" if row[4] == "17" else "ダート",
            "time": row[5],
            "horses": int(row[6]) if row[6] else 0,
            "grade": row[7]
        })
    
    cur.close()
    conn.close()
    
    return races_by_venue

def get_nankan_races_for_date(date_str):
    """指定日の南関東レース情報を取得"""
    
    conn = psycopg2.connect(**CONNECTION_PARAMS)
    cur = conn.cursor()
    
    # YYYYMMDD形式からMMDD形式に変換
    mmdd = date_str[4:8]
    year = date_str[0:4]
    
    query = """
    SELECT DISTINCT
        ra.keibajo_code,
        ra.race_bango,
        ra.race_name,
        ra.kyori,
        ra.track_code,
        ra.hassotime,
        ra.shusso_tosu,
        ra.grade_code
    FROM nvd_ra ra
    WHERE ra.kaisai_nen = %s
        AND ra.kaisai_tsukihi = %s
        AND ra.keibajo_code IN ('42','43','44','45')
    ORDER BY ra.keibajo_code, ra.race_bango
    """
    
    cur.execute(query, (year, mmdd))
    
    races_by_venue = {}
    for row in cur:
        keibajo_code = row[0]
        venue = NANKAN_KEIBAJO_MAP.get(keibajo_code, keibajo_code)
        
        if venue not in races_by_venue:
            races_by_venue[venue] = []
        
        races_by_venue[venue].append({
            "race_number": int(row[1]),
            "race_name": row[2].strip() if row[2] else "",
            "distance": int(row[3]) if row[3] else 0,
            "track": "芝" if row[4] == "17" else "ダート",
            "time": row[5],
            "horses": int(row[6]) if row[6] else 0,
            "grade": row[7]
        })
    
    cur.close()
    conn.close()
    
    return races_by_venue

def generate_metadata_entry(date_str, race_type="jra"):
    """メタデータエントリーを生成"""
    
    # 日付フォーマット
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    display_date = date_obj.strftime("%m月%d日(%a)")
    display_date = display_date.replace("Mon", "月").replace("Tue", "火").replace("Wed", "水")
    display_date = display_date.replace("Thu", "木").replace("Fri", "金").replace("Sat", "土").replace("Sun", "日")
    
    formatted_date = date_obj.strftime("%Y-%m-%d")
    
    if race_type == "jra":
        races_data = get_jra_races_for_date(date_str)
    else:
        races_data = get_nankan_races_for_date(date_str)
    
    if not races_data:
        return None
    
    # レース一覧を作成
    all_races = []
    for venue, races in races_data.items():
        for race in races:
            all_races.append(f"{venue}{race['race_number']}R")
    
    metadata = {
        "date": formatted_date,
        "displayDate": display_date,
        "venues": list(races_data.keys()),
        "totalRaces": len(all_races),
        "hasResults": False,
        "hasDLogic": False,
        "races": all_races,
        "raceDetails": races_data  # 詳細データも含める
    }
    
    return metadata

def generate_race_component(venue, date, races):
    """レースコンポーネントを生成"""
    
    component = f"""'use client'

import {{ useState }} from 'react'
import {{ Card, CardContent, CardHeader, CardTitle }} from '@/components/ui/card'

export default function {venue}RacesPage() {{
  const races = {json.dumps(races, ensure_ascii=False, indent=2)}

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">{venue}競馬場 - {date}</h1>
      <div className="grid gap-4">
        {{races.map((race, index) => (
          <Card key={{index}}>
            <CardHeader>
              <CardTitle>{{race.race_number}}R: {{race.race_name}}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2">
                <div>距離: {{race.distance}}m</div>
                <div>馬場: {{race.track}}</div>
                <div>発走: {{race.time}}</div>
                <div>頭数: {{race.horses}}頭</div>
              </div>
            </CardContent>
          </Card>
        ))}}
      </div>
    </div>
  )
}}"""
    
    return component

def update_v2_metadata(new_entries):
    """v2-metadata.jsonを更新"""
    
    metadata_path = "/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/v2-metadata.json"
    
    # 既存のメタデータを読み込み
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # 新しいエントリーを追加（重複チェック）
    existing_dates = {entry['date'] for entry in metadata['archives']}
    
    for entry in new_entries:
        if entry['date'] not in existing_dates:
            # raceDetailsは保存しない（メタデータには不要）
            entry_copy = entry.copy()
            entry_copy.pop('raceDetails', None)
            metadata['archives'].insert(0, entry_copy)
    
    # 日付でソート（新しい順）
    metadata['archives'].sort(key=lambda x: x['date'], reverse=True)
    
    # 最終更新日時を更新
    metadata['lastUpdated'] = datetime.now().isoformat()
    
    # ファイルを保存
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return metadata

def main():
    """メイン処理"""
    
    print("🏇 レース情報自動生成システム")
    print("=" * 50)
    
    # 今週末の日付を取得
    today = datetime.now()
    days_to_saturday = (5 - today.weekday()) % 7
    if days_to_saturday == 0:
        days_to_saturday = 7
    
    saturday = today + timedelta(days=days_to_saturday)
    sunday = saturday + timedelta(days=1)
    
    saturday_str = saturday.strftime("%Y%m%d")
    sunday_str = sunday.strftime("%Y%m%d")
    
    print(f"対象日: {saturday_str} (土), {sunday_str} (日)")
    
    # JRAレース情報を取得
    print("\n📊 JRAレース情報取得中...")
    jra_entries = []
    
    sat_meta = generate_metadata_entry(saturday_str, "jra")
    if sat_meta:
        jra_entries.append(sat_meta)
        print(f"✅ {saturday_str}: {len(sat_meta['venues'])}場 {sat_meta['totalRaces']}レース")
    
    sun_meta = generate_metadata_entry(sunday_str, "jra")
    if sun_meta:
        jra_entries.append(sun_meta)
        print(f"✅ {sunday_str}: {len(sun_meta['venues'])}場 {sun_meta['totalRaces']}レース")
    
    # 南関東レース情報を取得
    print("\n📊 南関東レース情報取得中...")
    nankan_entries = []
    
    for i in range(7):  # 1週間分
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y%m%d")
        
        nankan_meta = generate_metadata_entry(date_str, "nankan")
        if nankan_meta:
            nankan_entries.append(nankan_meta)
            print(f"✅ {date_str}: {len(nankan_meta['venues'])}場 {nankan_meta['totalRaces']}レース")
    
    # メタデータを更新
    if jra_entries or nankan_entries:
        print("\n📝 メタデータ更新中...")
        all_entries = jra_entries + nankan_entries
        update_v2_metadata(all_entries)
        print(f"✅ {len(all_entries)}日分のデータを追加")
    
    # コンポーネント生成例
    if jra_entries and jra_entries[0].get('raceDetails'):
        print("\n🎨 コンポーネント生成例:")
        for venue, races in jra_entries[0]['raceDetails'].items():
            filename = f"{venue.lower()}-{saturday_str}.tsx"
            print(f"  - {filename}")
            # 実際のファイル生成はコメントアウト
            # component = generate_race_component(venue, saturday_str, races)
            # with open(f"generated/{filename}", 'w', encoding='utf-8') as f:
            #     f.write(component)
    
    print("\n✅ 完了!")

if __name__ == "__main__":
    main()