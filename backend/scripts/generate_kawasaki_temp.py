import psycopg2
import json
from datetime import datetime

# PostgreSQL接続パラメータ
CONNECTION_PARAMS = {
    "host": "172.25.160.1",
    "port": "5432",
    "database": "pckeiba",
    "user": "postgres",
    "password": "postgres"
}

# 正しい競馬場コードマッピング
NANKAN_KEIBAJO_MAP = {
    '35': '盛岡',
    '44': '船橋',
    '45': '浦和',
    '46': '川崎',  # 正しいコード
    '48': '大井'
}

def generate_race_ts_file(date, keibajo_code='46'):
    """川崎競馬のTSファイル生成"""
    
    conn = psycopg2.connect(**CONNECTION_PARAMS)
    cur = conn.cursor()
    
    # 日付処理
    kaisai_nen = str(date.year)
    kaisai_tsukihi = date.strftime('%m%d')
    date_str = date.strftime('%Y-%m-%d')
    
    keibajo_name = NANKAN_KEIBAJO_MAP.get(keibajo_code, '不明')
    
    # レース情報取得
    query_races = """
    SELECT 
        race_bango,
        kyosomei_hondai,
        kyori,
        hasso_jikoku
    FROM nvd_ra
    WHERE kaisai_nen = %s 
      AND kaisai_tsukihi = %s
      AND keibajo_code = %s
    ORDER BY race_bango
    """
    
    cur.execute(query_races, (kaisai_nen, kaisai_tsukihi, keibajo_code))
    races = cur.fetchall()
    
    if not races:
        print(f"レースデータが見つかりません: {date_str} {keibajo_name}")
        return None
    
    # TSファイル生成
    ts_content = "export const races = [\n"
    
    for race in races:
        race_number = int(race[0])
        race_name = race[1].strip() if race[1] else f"第{race_number}レース"
        distance = f"ダ{race[2]}m"
        
        # 出馬表取得
        query_horses = """
        SELECT 
            bamei,
            umaban,
            wakuban,
            kishumei,
            futan_juryo,
            seibetsu_code,
            barei,
            chokyoshimei_ryakusho
        FROM nvd_se
        WHERE kaisai_nen = %s 
          AND kaisai_tsukihi = %s
          AND keibajo_code = %s
          AND race_bango = %s
        ORDER BY umaban
        """
        
        cur.execute(query_horses, (kaisai_nen, kaisai_tsukihi, keibajo_code, race[0]))
        horses_data = cur.fetchall()
        
        # データ整形
        horses = []
        jockeys = []
        posts = []
        horse_numbers = []
        sex_ages = []
        weights = []
        trainers = []
        
        for horse in horses_data:
            horses.append(horse[0].strip() if horse[0] else "")
            horse_numbers.append(int(horse[1]))
            posts.append(int(horse[2]))
            jockeys.append(horse[3].strip() if horse[3] else "")
            weights.append(float(horse[4]) if horse[4] else 0)
            
            # 性齢
            sex_map = {1: '牡', 2: '牝', 3: 'セ'}
            sex = sex_map.get(horse[5], '')
            age = str(horse[6]).zfill(2) if horse[6] else '00'
            sex_ages.append(f"{sex}{age}")
            
            trainers.append(horse[7].strip() if horse[7] else "")
        
        # レースオブジェクト作成
        race_obj = f"""  {{
    race_id: '{date.strftime("%Y%m%d")}-{keibajo_name}-{race_number}',
    race_date: '{date_str}',
    venue: '{keibajo_name}',
    race_number: {race_number},
    race_name: '{race_name}',
    created_at: '{datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00")}',
    distance: '{distance}',
    track_condition: '良',
    horses: {json.dumps(horses, ensure_ascii=False)},
    jockeys: {json.dumps(jockeys, ensure_ascii=False)},
    posts: {posts},
    horse_numbers: {horse_numbers},
    sex_ages: {json.dumps(sex_ages, ensure_ascii=False)},
    weights: {weights},
    trainers: {json.dumps(trainers, ensure_ascii=False)},
    odds: {[0] * len(horses)},
    popularities: {[0] * len(horses)}
  }},
"""
        ts_content += race_obj
    
    ts_content = ts_content.rstrip(',\n') + "\n];"
    
    # ファイル保存
    output_dir = "/mnt/e/dev/Cusor/front/d-logic-ai-frontend/src/data/archive/local"
    filename = f"{output_dir}/races-{date.strftime('%Y%m%d')}-{keibajo_name}.ts"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(ts_content)
    
    print(f"✅ TSファイル生成完了: {filename}")
    print(f"   {keibajo_name}競馬場 {len(races)}レース")
    
    cur.close()
    conn.close()
    
    return keibajo_name, len(races)

# 実行
if __name__ == "__main__":
    today = datetime(2025, 9, 8)
    generate_race_ts_file(today, '46')  # 川崎
