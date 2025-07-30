# race_identifier.py - 本日開催レース識別システム

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class RaceIdentifier:
    """本日開催レースを特定するクラス"""
    
    # 競馬場名の正規化マッピング
    COURSE_MAPPING = {
        "東京": "東京",
        "tokyo": "東京",
        "to": "東京",
        "阪神": "阪神",
        "hanshin": "阪神",
        "hs": "阪神",
        "京都": "京都",
        "kyoto": "京都",
        "kt": "京都",
        "中山": "中山",
        "nakayama": "中山",
        "nz": "中山",
        "福島": "福島",
        "fukushima": "福島",
        "fk": "福島",
        "新潟": "新潟",
        "niigata": "新潟",
        "ng": "新潟",
        "小倉": "小倉",
        "kokura": "小倉",
        "kk": "小倉",
        "札幌": "札幌",
        "sapporo": "札幌",
        "sp": "札幌",
        "函館": "函館",
        "hakodate": "函館",
        "hk": "函館",
        "中京": "中京",
        "chukyo": "中京",
        "ck": "中京"
    }
    
    # レース番号のパターン
    RACE_NUMBER_PATTERNS = [
        r"(\d+)R",  # 1R, 2R, 12R
        r"(\d+)レース",  # 1レース, 2レース
        r"(\d+)回",  # 1回, 2回
        r"(\d+)戦",  # 1戦, 2戦
    ]
    
    def __init__(self):
        self.today_races = self._get_today_races()
    
    def _get_today_races(self) -> List[Dict]:
        """本日の開催レース情報を取得（サンプルデータ）"""
        # 実際の実装ではJRA-VAN APIから取得
        return [
            {
                "course": "東京",
                "race_number": 1,
                "race_name": "3歳未勝利",
                "distance": 1600,
                "surface": "芝",
                "start_time": "10:30",
                "horses": 16
            },
            {
                "course": "東京",
                "race_number": 2,
                "race_name": "4歳以上1勝クラス",
                "distance": 2000,
                "surface": "芝",
                "start_time": "11:00",
                "horses": 14
            },
            {
                "course": "東京",
                "race_number": 3,
                "race_name": "3歳1勝クラス",
                "distance": 1400,
                "surface": "ダート",
                "start_time": "11:30",
                "horses": 12
            },
            {
                "course": "阪神",
                "race_number": 1,
                "race_name": "3歳未勝利",
                "distance": 1800,
                "surface": "芝",
                "start_time": "10:35",
                "horses": 15
            },
            {
                "course": "阪神",
                "race_number": 2,
                "race_name": "4歳以上2勝クラス",
                "distance": 1600,
                "surface": "芝",
                "start_time": "11:05",
                "horses": 13
            }
        ]
    
    def identify_race_from_message(self, message: str) -> Optional[Dict]:
        """メッセージからレースを特定"""
        try:
            # 競馬場名を抽出
            course = self._extract_course(message)
            if not course:
                return None
            
            # レース番号を抽出
            race_number = self._extract_race_number(message)
            if not race_number:
                return None
            
            # 該当するレースを検索
            target_race = self._find_race(course, race_number)
            
            if target_race:
                logger.info(f"レース特定成功: {course}{race_number}R")
                return target_race
            else:
                logger.warning(f"レースが見つかりません: {course}{race_number}R")
                return None
                
        except Exception as e:
            logger.error(f"レース特定エラー: {e}")
            return None
    
    def _extract_course(self, message: str) -> Optional[str]:
        """メッセージから競馬場名を抽出"""
        message_lower = message.lower()
        
        for pattern, normalized in self.COURSE_MAPPING.items():
            if pattern in message_lower:
                return normalized
        
        return None
    
    def _extract_race_number(self, message: str) -> Optional[int]:
        """メッセージからレース番号を抽出"""
        for pattern in self.RACE_NUMBER_PATTERNS:
            match = re.search(pattern, message)
            if match:
                try:
                    race_number = int(match.group(1))
                    if 1 <= race_number <= 12:  # 有効なレース番号
                        return race_number
                except ValueError:
                    continue
        
        return None
    
    def _find_race(self, course: str, race_number: int) -> Optional[Dict]:
        """指定された競馬場・レース番号のレースを検索"""
        for race in self.today_races:
            if race["course"] == course and race["race_number"] == race_number:
                return race
        return None
    
    def get_available_races(self) -> List[Dict]:
        """本日開催可能なレース一覧を取得"""
        return self.today_races
    
    def format_race_info(self, race: Dict) -> str:
        """レース情報を整形"""
        return f"""
🏇 {race['course']}{race['race_number']}R
📋 {race['race_name']}
📏 {race['distance']}m {race['surface']}
⏰ {race['start_time']}発走
🐎 {race['horses']}頭立て
        """.strip()
    
    def get_race_summary(self) -> str:
        """本日のレース概要を取得"""
        if not self.today_races:
            return "本日の開催レース情報はありません。"
        
        summary = "🏇 本日開催レース\n\n"
        
        # 競馬場別にグループ化
        courses = {}
        for race in self.today_races:
            course = race["course"]
            if course not in courses:
                courses[course] = []
            courses[course].append(race)
        
        for course, races in courses.items():
            summary += f"📍 {course}競馬場\n"
            for race in races:
                summary += f"  {race['race_number']}R: {race['race_name']} ({race['distance']}m{race['surface']})\n"
            summary += "\n"
        
        return summary.strip()


# 使用例
if __name__ == "__main__":
    identifier = RaceIdentifier()
    
    # レース特定テスト
    test_messages = [
        "東京1Rの予想を教えて",
        "阪神2レースの分析をお願い",
        "京都3回戦の結果は？",
        "中山1戦の出走馬は？"
    ]
    
    for message in test_messages:
        race = identifier.identify_race_from_message(message)
        if race:
            print(f"'{message}' → {race['course']}{race['race_number']}R")
        else:
            print(f"'{message}' → 特定できませんでした")
    
    # 本日のレース概要
    print("\n" + identifier.get_race_summary()) 