# race_data_service.py - 本日開催レース情報管理サービス

import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime, date
import json

logger = logging.getLogger(__name__)

class RaceDataService:
    """本日開催レース情報を管理するサービス"""
    
    def __init__(self):
        self.today_races = {}
        self.last_update = None
        self.update_race_data()
    
    def update_race_data(self) -> bool:
        """本日のレース情報を更新"""
        try:
            # 実際の実装ではJRA-VAN APIから取得
            # 現在はサンプルデータを使用
            today_races = self._get_sample_race_data()
            
            self.today_races = today_races
            self.last_update = datetime.now()
            
            logger.info(f"レース情報更新完了: {len(today_races)}レース")
            return True
            
        except Exception as e:
            logger.error(f"レース情報更新エラー: {e}")
            return False
    
    def _get_sample_race_data(self) -> Dict[str, List[Dict]]:
        """サンプルレースデータ（実際はJRA-VAN APIから取得）"""
        return {
            "東京": [
                {
                    "race_number": 1,
                    "race_name": "3歳未勝利",
                    "distance": 1600,
                    "surface": "芝",
                    "start_time": "10:30",
                    "horses": 16,
                    "prize_money": "1000万円",
                    "weather": "晴",
                    "track_condition": "良",
                    "course_direction": "右",
                    "horse_details": [
                        {"number": 1, "name": "サクラエイシン", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 2, "name": "ディープインパクト", "jockey": "福永祐一", "trainer": "池江泰寿"},
                        {"number": 3, "name": "オルフェーヴル", "jockey": "岩田康誠", "trainer": "池江泰寿"},
                        {"number": 4, "name": "トウカイテイオー", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 5, "name": "メジロマックイーン", "jockey": "福永祐一", "trainer": "池江泰寿"},
                        {"number": 6, "name": "ナリタタイシン", "jockey": "岩田康誠", "trainer": "池江泰寿"},
                        {"number": 7, "name": "エアグルーヴ", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 8, "name": "サイレンススズカ", "jockey": "福永祐一", "trainer": "池江泰寿"}
                    ]
                },
                {
                    "race_number": 2,
                    "race_name": "4歳以上1勝クラス",
                    "distance": 2000,
                    "surface": "芝",
                    "start_time": "11:00",
                    "horses": 14,
                    "prize_money": "1200万円",
                    "weather": "晴",
                    "track_condition": "良",
                    "course_direction": "右",
                    "horse_details": [
                        {"number": 1, "name": "シンボリクリスエス", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 2, "name": "オグリキャップ", "jockey": "福永祐一", "trainer": "池江泰寿"},
                        {"number": 3, "name": "タイキシャトル", "jockey": "岩田康誠", "trainer": "池江泰寿"},
                        {"number": 4, "name": "エルコンドルパサー", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 5, "name": "サイレンススズカ", "jockey": "福永祐一", "trainer": "池江泰寿"},
                        {"number": 6, "name": "メジロマックイーン", "jockey": "岩田康誠", "trainer": "池江泰寿"},
                        {"number": 7, "name": "ナリタブライアン", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 8, "name": "ディープインパクト", "jockey": "福永祐一", "trainer": "池江泰寿"}
                    ]
                },
                {
                    "race_number": 3,
                    "race_name": "3歳1勝クラス",
                    "distance": 1400,
                    "surface": "ダート",
                    "start_time": "11:30",
                    "horses": 12,
                    "prize_money": "800万円",
                    "weather": "晴",
                    "track_condition": "良",
                    "course_direction": "右",
                    "horse_details": [
                        {"number": 1, "name": "エアグルーヴ", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 2, "name": "サイレンススズカ", "jockey": "福永祐一", "trainer": "池江泰寿"},
                        {"number": 3, "name": "メジロマックイーン", "jockey": "岩田康誠", "trainer": "池江泰寿"},
                        {"number": 4, "name": "ナリタタイシン", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 5, "name": "ディープインパクト", "jockey": "福永祐一", "trainer": "池江泰寿"},
                        {"number": 6, "name": "オルフェーヴル", "jockey": "岩田康誠", "trainer": "池江泰寿"}
                    ]
                }
            ],
            "阪神": [
                {
                    "race_number": 1,
                    "race_name": "3歳未勝利",
                    "distance": 1800,
                    "surface": "芝",
                    "start_time": "10:35",
                    "horses": 15,
                    "prize_money": "1000万円",
                    "weather": "晴",
                    "track_condition": "良",
                    "course_direction": "右",
                    "horse_details": [
                        {"number": 1, "name": "トウカイテイオー", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 2, "name": "メジロマックイーン", "jockey": "福永祐一", "trainer": "池江泰寿"},
                        {"number": 3, "name": "ナリタタイシン", "jockey": "岩田康誠", "trainer": "池江泰寿"},
                        {"number": 4, "name": "エアグルーヴ", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 5, "name": "サイレンススズカ", "jockey": "福永祐一", "trainer": "池江泰寿"},
                        {"number": 6, "name": "ディープインパクト", "jockey": "岩田康誠", "trainer": "池江泰寿"},
                        {"number": 7, "name": "オルフェーヴル", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 8, "name": "シンボリクリスエス", "jockey": "福永祐一", "trainer": "池江泰寿"}
                    ]
                },
                {
                    "race_number": 2,
                    "race_name": "4歳以上2勝クラス",
                    "distance": 1600,
                    "surface": "芝",
                    "start_time": "11:05",
                    "horses": 13,
                    "prize_money": "1200万円",
                    "weather": "晴",
                    "track_condition": "良",
                    "course_direction": "右",
                    "horse_details": [
                        {"number": 1, "name": "エルコンドルパサー", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 2, "name": "タイキシャトル", "jockey": "福永祐一", "trainer": "池江泰寿"},
                        {"number": 3, "name": "オグリキャップ", "jockey": "岩田康誠", "trainer": "池江泰寿"},
                        {"number": 4, "name": "シンボリクリスエス", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 5, "name": "ディープインパクト", "jockey": "福永祐一", "trainer": "池江泰寿"},
                        {"number": 6, "name": "オルフェーヴル", "jockey": "岩田康誠", "trainer": "池江泰寿"},
                        {"number": 7, "name": "トウカイテイオー", "jockey": "武豊", "trainer": "藤沢和雄"},
                        {"number": 8, "name": "メジロマックイーン", "jockey": "福永祐一", "trainer": "池江泰寿"}
                    ]
                }
            ]
        }
    
    def get_race_info(self, course: str, race_number: int) -> Optional[Dict]:
        """特定のレース情報を取得"""
        try:
            if course in self.today_races:
                for race in self.today_races[course]:
                    if race["race_number"] == race_number:
                        return race
            return None
        except Exception as e:
            logger.error(f"レース情報取得エラー: {e}")
            return None
    
    def get_all_races(self) -> Dict[str, List[Dict]]:
        """全てのレース情報を取得"""
        return self.today_races
    
    def get_course_races(self, course: str) -> List[Dict]:
        """特定競馬場のレース情報を取得"""
        return self.today_races.get(course, [])
    
    def format_race_details(self, race: Dict) -> str:
        """レース詳細情報を整形"""
        details = f"""
🏇 {race['race_name']}
📏 {race['distance']}m {race['surface']} {race['course_direction']}周り
⏰ {race['start_time']}発走
🐎 {race['horses']}頭立て
💰 賞金: {race['prize_money']}
🌤️ 天候: {race['weather']}
🏃 馬場: {race['track_condition']}

【出走馬】
"""
        
        for horse in race["horse_details"]:
            details += f"{horse['number']}番 {horse['name']} (騎手: {horse['jockey']}, 調教師: {horse['trainer']})\n"
        
        return details.strip()
    
    def get_race_summary(self) -> str:
        """本日のレース概要を取得"""
        if not self.today_races:
            return "本日の開催レース情報はありません。"
        
        summary = f"🏇 本日開催レース ({date.today().strftime('%Y年%m月%d日')})\n\n"
        
        for course, races in self.today_races.items():
            summary += f"📍 {course}競馬場\n"
            for race in races:
                summary += f"  {race['race_number']}R: {race['race_name']} ({race['distance']}m{race['surface']}) - {race['start_time']}発走\n"
            summary += "\n"
        
        return summary.strip()
    
    def is_race_exists(self, course: str, race_number: int) -> bool:
        """レースが存在するかチェック"""
        return self.get_race_info(course, race_number) is not None


# 使用例
if __name__ == "__main__":
    service = RaceDataService()
    
    # レース情報取得テスト
    race = service.get_race_info("東京", 1)
    if race:
        print(service.format_race_details(race))
    
    # 全レース概要
    print("\n" + service.get_race_summary()) 