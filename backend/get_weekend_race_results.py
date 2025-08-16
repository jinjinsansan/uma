#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直近の土日レース結果取得スクリプト
毎週月曜日に手動実行して、土日のレース結果をMySQLから取得
"""

import json
import mysql.connector
from datetime import datetime, timedelta
import logging
import os

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class WeekendRaceResultsFetcher:
    def __init__(self):
        self.connection = None
        
    def connect_db(self):
        """データベース接続"""
        try:
            self.connection = mysql.connector.connect(
                host='172.25.160.1',
                user='root',
                password='04050405Aoi-',
                database='mykeibadb',
                charset='utf8mb4',
                collation='utf8mb4_general_ci'
            )
            logging.info("データベース接続成功")
            return True
        except Exception as e:
            logging.error(f"データベース接続エラー: {e}")
            return False
    
    def get_last_weekend_dates(self):
        """直近の土日の日付を取得"""
        today = datetime.now()
        # 今日が月曜日(0)の場合
        if today.weekday() == 0:
            sunday = today - timedelta(days=1)
            saturday = today - timedelta(days=2)
        else:
            # それ以外の曜日の場合（テスト用）
            days_since_sunday = (today.weekday() + 1) % 7
            sunday = today - timedelta(days=days_since_sunday)
            saturday = sunday - timedelta(days=1)
        
        return saturday.strftime('%Y%m%d'), sunday.strftime('%Y%m%d')
    
    def get_race_results(self, date):
        """指定日のレース結果を取得"""
        cursor = self.connection.cursor(dictionary=True)
        
        # レース結果を取得（着順1-3位）
        query = """
        SELECT 
            rr.racedate,
            rr.jyocd,
            rr.nichiji,
            rr.racenum,
            rl.kyosomei_hondai,
            rl.kyosomei_fukudai,
            rl.kyosomei_kakko,
            rr.bamei,
            rr.kakuteijyuni
        FROM jra_race_result rr
        JOIN jra_race_list rl ON 
            rr.racedate = rl.racedate AND 
            rr.jyocd = rl.jyocd AND 
            rr.nichiji = rl.nichiji AND 
            rr.racenum = rl.racenum
        WHERE rr.racedate = %s
        AND rr.kakuteijyuni IN (1, 2, 3)
        ORDER BY rr.jyocd, rr.racenum, rr.kakuteijyuni
        """
        
        cursor.execute(query, (date,))
        results = cursor.fetchall()
        
        # 開催場コード対応表
        jyo_names = {
            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
            '05': '東京', '06': '中山', '07': '中京', '08': '京都',
            '09': '阪神', '10': '小倉'
        }
        
        # レースごとにグループ化
        races = {}
        for row in results:
            key = f"{row['jyocd']}_{row['racenum']}"
            if key not in races:
                races[key] = {
                    'date': row['racedate'],
                    'venue': jyo_names.get(row['jyocd'], row['jyocd']),
                    'race_number': int(row['racenum']),
                    'race_name': self.format_race_name(row),
                    'result': {}
                }
            
            # 着順を記録
            if row['kakuteijyuni'] == 1:
                races[key]['result']['first'] = row['bamei']
            elif row['kakuteijyuni'] == 2:
                races[key]['result']['second'] = row['bamei']
            elif row['kakuteijyuni'] == 3:
                races[key]['result']['third'] = row['bamei']
        
        cursor.close()
        return list(races.values())
    
    def format_race_name(self, row):
        """レース名をフォーマット"""
        name = row['kyosomei_hondai'] or ""
        if row['kyosomei_fukudai']:
            name += f" {row['kyosomei_fukudai']}"
        if row['kyosomei_kakko']:
            name += f" {row['kyosomei_kakko']}"
        return name.strip()
    
    def save_results(self, saturday_results, sunday_results):
        """結果をJSONファイルに保存"""
        output = {
            'updated_at': datetime.now().isoformat(),
            'saturday': saturday_results,
            'sunday': sunday_results
        }
        
        # 出力ディレクトリ作成
        os.makedirs('data/race_results', exist_ok=True)
        
        # ファイル保存
        filename = f"data/race_results/weekend_results_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logging.info(f"結果を保存しました: {filename}")
        return filename
    
    def run(self):
        """メイン処理"""
        if not self.connect_db():
            return None
        
        try:
            saturday_date, sunday_date = self.get_last_weekend_dates()
            logging.info(f"取得対象: 土曜日 {saturday_date}, 日曜日 {sunday_date}")
            
            # 土日の結果を取得
            saturday_results = self.get_race_results(saturday_date)
            sunday_results = self.get_race_results(sunday_date)
            
            logging.info(f"土曜日: {len(saturday_results)}レース")
            logging.info(f"日曜日: {len(sunday_results)}レース")
            
            # 結果表示
            print("\n=== 土曜日のレース結果 ===")
            for race in saturday_results:
                print(f"\n{race['venue']} {race['race_number']}R: {race['race_name']}")
                print(f"  1着: {race['result'].get('first', '-')}")
                print(f"  2着: {race['result'].get('second', '-')}")
                print(f"  3着: {race['result'].get('third', '-')}")
            
            print("\n=== 日曜日のレース結果 ===")
            for race in sunday_results:
                print(f"\n{race['venue']} {race['race_number']}R: {race['race_name']}")
                print(f"  1着: {race['result'].get('first', '-')}")
                print(f"  2着: {race['result'].get('second', '-')}")
                print(f"  3着: {race['result'].get('third', '-')}")
            
            # ファイル保存
            filename = self.save_results(saturday_results, sunday_results)
            return filename
            
        except Exception as e:
            logging.error(f"エラーが発生しました: {e}")
            return None
        finally:
            if self.connection:
                self.connection.close()

if __name__ == "__main__":
    fetcher = WeekendRaceResultsFetcher()
    result_file = fetcher.run()
    
    if result_file:
        print(f"\n処理完了！結果ファイル: {result_file}")
        print("\n次のステップ:")
        print("1. 結果ファイルを確認")
        print("2. アーカイブページに反映")
        print("3. D-Logic予想と照合して的中判定")