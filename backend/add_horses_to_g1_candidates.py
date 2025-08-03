#!/usr/bin/env python3
"""
G1候補レースに出走馬データを追加
24レースの完全データ作成
"""
import mysql.connector
import json
import os
from typing import Dict, List, Any
from dotenv import load_dotenv
from pathlib import Path

def add_horses_to_g1_races():
    """G1候補レースに出走馬データを追加"""
    try:
        # G1候補レースデータを読み込み
        candidates_path = os.path.join(os.path.dirname(__file__), "data", "2024_g1_candidates.json")
        
        with open(candidates_path, 'r', encoding='utf-8') as f:
            candidates_data = json.load(f)
        
        candidate_races = candidates_data.get("races", [])
        print(f"📊 読み込み: {len(candidate_races)}レース")
        
        # MySQL接続
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        mysql_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'mykeibadb'),
            'charset': 'utf8mb4'
        }
        
        conn = mysql.connector.connect(**mysql_config)
        cursor = conn.cursor(dictionary=True)
        
        print("✅ MySQL接続成功")
        
        complete_g1_races = []
        
        for i, race in enumerate(candidate_races, 1):
            race_id = race['raceId']
            race_name = race['raceName']
            
            print(f"\n🏁 {i:2d}/24 {race_name} の出走馬データ取得中...")
            
            # 出走馬データを取得
            horses = extract_horses_for_race(cursor, race_id)
            
            if horses and len(horses) >= 12:  # 12頭以上のレース
                race['horses'] = horses
                race['description'] = f"2024年{race['date']}開催 {len(horses)}頭立ての激戦G1級レース"
                complete_g1_races.append(race)
                print(f"  ✅ {len(horses)}頭の出走馬データを取得")
                
                # 上位3頭を表示
                top3 = sorted(horses, key=lambda h: h.get('dLogicScore', 0), reverse=True)[:3]
                for rank, horse in enumerate(top3, 1):
                    result_str = f"({horse['result']}着)" if horse.get('result') else ""
                    print(f"    {rank}位予想: {horse['name']} (D-Logic:{horse['dLogicScore']}) {result_str}")
            else:
                print(f"  ⚠️  出走馬データ不足 ({len(horses) if horses else 0}頭)")
        
        cursor.close()
        conn.close()
        
        # 完全なG1レースデータとして保存
        final_data = {
            "races": complete_g1_races,
            "total": len(complete_g1_races),
            "extractedAt": candidates_data["extractedAt"],
            "source": "mykeibadb実データ - 2024年G1級レース完全版",
            "description": f"2024年開催G1級レース{len(complete_g1_races)}戦（全出走馬データ付き）"
        }
        
        output_path = os.path.join(os.path.dirname(__file__), "data", "2024_complete_g1_races.json")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎯 2024年G1級レース完全版作成完了!")
        print(f"📁 保存先: {output_path}")
        print(f"🏆 完成レース数: {len(complete_g1_races)}")
        print(f"🐎 総出走馬数: {sum(len(race['horses']) for race in complete_g1_races)}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

def extract_horses_for_race(cursor, race_code: str) -> List[Dict]:
    """レースの出走馬データを取得（最適化版）"""
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
            # 各データの安全な変換
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
            
            # 人気
            try:
                popularity = int(str(horse.get('TANSHO_NINKIJUN', 10)))
            except:
                popularity = 10
            
            # D-Logic指数計算（G1仕様）
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
                win_prob = round(85 + (dlogic_score - 140) * 0.2, 1)
            elif dlogic_score >= 120:
                win_prob = round(65 + (dlogic_score - 120) * 1.0, 1)
            elif dlogic_score >= 100:
                win_prob = round(35 + (dlogic_score - 100) * 1.5, 1)
            else:
                win_prob = round(10 + (dlogic_score - 80) * 1.25, 1)
            
            # 馬体重変化
            weight_change = horse.get('ZOGEN_SA')
            try:
                if weight_change is not None and str(weight_change) != '0':
                    weight_change_val = int(str(weight_change))
                    weight_change_str = f"{weight_change_val:+}" if weight_change_val != 0 else "±0"
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
            
            horse_info = {
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
            horses.append(horse_info)
        
        # D-Logic順位設定
        horses.sort(key=lambda x: x['dLogicScore'], reverse=True)
        for i, horse in enumerate(horses):
            horse['dLogicRank'] = i + 1
        
        return horses
        
    except Exception as e:
        print(f"⚠️  出走馬エラー: {e}")
        return []

if __name__ == "__main__":
    success = add_horses_to_g1_races()
    if success:
        print("\n✅ 2024年G1級レース完全版作成成功！")
        print("これで本物の24レースG1体験が可能になります。")
    else:
        print("\n❌ G1レース完全版作成失敗")