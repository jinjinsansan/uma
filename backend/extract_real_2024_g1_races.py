#!/usr/bin/env python3
"""
2024年本物のG1レース抽出（効率的版）
race_shosaiテーブルのKYOSOMEI_HONDAIカラムから直接検索
"""
import mysql.connector
import json
import os
from datetime import datetime
from typing import Dict, List, Any

def extract_real_2024_g1_races():
    """2024年の本物のG1レース全24戦を効率的に抽出"""
    try:
        # 直接接続情報を使用
        config = {
            'host': '172.25.160.1',
            'port': 3306,
            'user': 'root',
            'password': '04050405Aoi-',
            'database': 'mykeibadb',
            'charset': 'utf8mb4'
        }
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        print("🏆 2024年本物のG1レース抽出開始")
        print("=" * 50)
        
        # 2024年のG1レース名リスト（正式名称）
        g1_race_names = [
            '有馬記念', 'ジャパンカップ', '天皇賞（秋）', '天皇賞（春）',
            '東京優駿', 'オークス', '桜花賞', '皐月賞', '菊花賞',
            'NHKマイルカップ', 'ヴィクトリアマイル', '安田記念',
            '宝塚記念', 'スプリンターズステークス', '秋華賞',
            'エリザベス女王杯', 'マイルチャンピオンシップ',
            'チャンピオンズカップ', '阪神ジュベナイルフィリーズ',
            '朝日杯フューチュリティステークス', 'ホープフルステークス',
            'フェブラリーステークス', '高松宮記念', '大阪杯'
        ]
        
        all_g1_races = []
        
        # 各G1レース名で検索
        for race_name in g1_race_names:
            query = """
            SELECT DISTINCT
                r.RACE_CODE,
                r.KAISAI_NEN,
                r.KAISAI_GAPPI,
                r.KEIBAJO_CODE,
                r.RACE_BANGO,
                r.KYOSOMEI_HONDAI,
                r.KYORI,
                r.GRADE_CODE,
                COUNT(u.UMABAN) as SHUSSO_TOSU
            FROM race_shosai r
            INNER JOIN umagoto_race_joho u ON r.RACE_CODE = u.RACE_CODE
            WHERE r.KAISAI_NEN = '2024'
            AND r.KYOSOMEI_HONDAI LIKE %s
            GROUP BY r.RACE_CODE, r.KAISAI_NEN, r.KAISAI_GAPPI, 
                     r.KEIBAJO_CODE, r.RACE_BANGO, r.KYOSOMEI_HONDAI, 
                     r.KYORI, r.GRADE_CODE
            """
            
            cursor.execute(query, (f'%{race_name}%',))
            races = cursor.fetchall()
            
            for race in races:
                print(f"✅ 発見: {race['KYOSOMEI_HONDAI']} ({race['KAISAI_GAPPI']})")
                
                # 日付フォーマット
                year = race['KAISAI_NEN']
                month_day = race['KAISAI_GAPPI']
                if len(month_day) == 4:
                    race_date = f"{year}-{month_day[:2]}-{month_day[2:]}"
                else:
                    race_date = f"{year}-01-01"
                
                # 競馬場名
                course_names = {
                    "01": "札幌", "02": "函館", "03": "福島", "04": "新潟",
                    "05": "東京", "06": "中山", "07": "中京", "08": "京都",
                    "09": "阪神", "10": "小倉"
                }
                
                race_info = {
                    "raceId": race['RACE_CODE'],
                    "raceName": race['KYOSOMEI_HONDAI'],
                    "date": race_date,
                    "racecourse": course_names.get(race['KEIBAJO_CODE'], '') + "競馬場",
                    "raceNumber": int(race['RACE_BANGO']),
                    "distance": f"{race['KYORI']}m",
                    "track": "芝",  # 後で実データから判定
                    "grade": "G1",
                    "weather": "晴",  # 後で実データから取得
                    "trackCondition": "良",  # 後で実データから取得
                    "entryCount": race['SHUSSO_TOSU']
                }
                all_g1_races.append(race_info)
        
        print(f"\n📊 発見された2024年G1レース: {len(all_g1_races)}レース")
        
        # 各レースの出走馬データを取得
        complete_g1_races = []
        for i, race in enumerate(all_g1_races, 1):
            print(f"\n🏁 {i}/{len(all_g1_races)} {race['raceName']} の出走馬データ取得中...")
            
            horses = extract_horses_for_race(cursor, race['raceId'])
            if horses and len(horses) >= 8:
                race['horses'] = horses
                race['description'] = f"2024年{race['raceName']}（{len(horses)}頭立て）"
                complete_g1_races.append(race)
                print(f"  ✅ {len(horses)}頭の出走馬データを取得")
                
                # 上位3頭を表示
                top3 = sorted(horses, key=lambda h: h.get('dLogicScore', 0), reverse=True)[:3]
                for rank, horse in enumerate(top3, 1):
                    result_str = f"({horse['result']}着)" if horse.get('result') else ""
                    print(f"    {rank}位: {horse['name']} D-Logic:{horse['dLogicScore']} {result_str}")
        
        cursor.close()
        conn.close()
        
        # JSONファイルに保存
        output_data = {
            "races": complete_g1_races,
            "total": len(complete_g1_races),
            "extractedAt": datetime.now().isoformat(),
            "source": "mykeibadb実データ - 2024年正式G1レース",
            "description": f"JRA公式2024年G1レース全{len(complete_g1_races)}戦"
        }
        
        output_path = os.path.join(os.path.dirname(__file__), "data", "2024_real_g1_races.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎯 2024年本物のG1レース抽出完了!")
        print(f"📁 保存先: {output_path}")
        print(f"🏆 G1レース数: {len(complete_g1_races)}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def extract_horses_for_race(cursor, race_code: str) -> List[Dict]:
    """指定レースの出走馬データを取得"""
    try:
        horses_query = """
        SELECT 
            UMABAN,
            BAMEI,
            KISHUMEI_RYAKUSHO,
            CHOKYOSHIMEI_RYAKUSHO,
            FUTAN_JURYO,
            BATAIJU,
            ZOGEN_SA,
            TANSHO_ODDS,
            TANSHO_NINKIJUN,
            KAKUTEI_CHAKUJUN,
            SEIBETSU_CODE,
            BAREI
        FROM umagoto_race_joho 
        WHERE RACE_CODE = %s
        AND BAMEI IS NOT NULL 
        AND BAMEI != ''
        ORDER BY UMABAN
        """
        
        cursor.execute(horses_query, (race_code,))
        horses_data = cursor.fetchall()
        
        horses = []
        for horse in horses_data:
            # 各データの安全な変換とD-Logic計算
            horse_info = format_horse_data(horse)
            horses.append(horse_info)
        
        # D-Logic順位設定
        horses.sort(key=lambda x: x['dLogicScore'], reverse=True)
        for i, horse in enumerate(horses):
            horse['dLogicRank'] = i + 1
        
        return horses
        
    except Exception as e:
        print(f"⚠️  出走馬エラー: {e}")
        return []

def format_horse_data(horse: Dict) -> Dict:
    """馬データのフォーマットとD-Logic計算"""
    # 基本情報の安全な変換
    try:
        number = int(str(horse.get('UMABAN', 0)))
    except:
        number = 0
    
    # 着順
    result = horse.get('KAKUTEI_CHAKUJUN')
    if result and str(result).isdigit() and int(str(result)) > 0:
        result = int(result)
    else:
        result = None
    
    # 人気
    try:
        popularity = int(str(horse.get('TANSHO_NINKIJUN', 10)))
    except:
        popularity = 10
    
    # オッズ
    odds = horse.get('TANSHO_ODDS', 0)
    try:
        odds_val = float(str(odds)) if odds else 0
        if odds_val > 0:
            if odds_val >= 1000:
                odds_str = f"{odds_val/100:.1f}"
            elif odds_val >= 100:
                odds_str = f"{odds_val/10:.1f}"
            else:
                odds_str = f"{odds_val:.1f}"
        else:
            odds_str = "999.9"
    except:
        odds_str = "999.9"
    
    # G1用D-Logic指数計算
    base_score = 100
    
    # 人気補正
    if popularity == 1:
        popularity_bonus = 35
    elif popularity <= 3:
        popularity_bonus = 25
    elif popularity <= 5:
        popularity_bonus = 15
    elif popularity <= 8:
        popularity_bonus = 5
    else:
        popularity_bonus = -10
    
    # オッズ補正
    try:
        odds_val = float(odds_str)
        if odds_val <= 2.0:
            odds_bonus = 30
        elif odds_val <= 5.0:
            odds_bonus = 20
        elif odds_val <= 10.0:
            odds_bonus = 10
        else:
            odds_bonus = 0
    except:
        odds_bonus = 0
    
    # 実績補正
    if result:
        if result == 1:
            result_bonus = 30
        elif result == 2:
            result_bonus = 20
        elif result == 3:
            result_bonus = 15
        elif result <= 5:
            result_bonus = 5
        else:
            result_bonus = 0
    else:
        result_bonus = 0
    
    total_score = base_score + popularity_bonus + odds_bonus + result_bonus
    dlogic_score = max(75, min(150, total_score))
    
    # 勝率計算
    if dlogic_score >= 140:
        win_prob = round(85 + (dlogic_score - 140) * 0.3, 1)
    elif dlogic_score >= 120:
        win_prob = round(60 + (dlogic_score - 120) * 1.25, 1)
    elif dlogic_score >= 100:
        win_prob = round(30 + (dlogic_score - 100) * 1.5, 1)
    else:
        win_prob = round(5 + (dlogic_score - 80) * 1.25, 1)
    
    # 馬体重変化
    weight_change = horse.get('ZOGEN_SA')
    try:
        if weight_change is not None and str(weight_change) != '0':
            weight_val = int(str(weight_change))
            weight_change_str = f"{weight_val:+}" if weight_val != 0 else "±0"
        else:
            weight_change_str = "±0"
    except:
        weight_change_str = "±0"
    
    # その他の数値
    try:
        weight = int(str(horse.get('FUTAN_JURYO', 57)))
    except:
        weight = 57
        
    try:
        horse_weight = int(str(horse.get('BATAIJU', 500)))
    except:
        horse_weight = 500
        
    try:
        age = int(str(horse.get('BAREI', 4)))
    except:
        age = 4
    
    # 性別
    sex_code = horse.get('SEIBETSU_CODE')
    sex_names = {"1": "牡", "2": "牝", "3": "せん"}
    sex = sex_names.get(str(sex_code) if sex_code else "1", "牡")
    
    return {
        "number": number,
        "name": horse.get('BAMEI', ''),
        "jockey": horse.get('KISHUMEI_RYAKUSHO', ''),
        "trainer": horse.get('CHOKYOSHIMEI_RYAKUSHO', ''),
        "weight": f"{weight}kg",
        "horseWeight": f"{horse_weight}kg",
        "weightChange": weight_change_str,
        "age": age,
        "sex": sex,
        "odds": odds_str,
        "popularity": popularity,
        "result": result,
        "dLogicScore": dlogic_score,
        "winProbability": win_prob
    }

if __name__ == "__main__":
    success = extract_real_2024_g1_races()
    if success:
        print("\n✅ 2024年本物のG1レース抽出成功！")
    else:
        print("\n❌ G1レース抽出失敗")