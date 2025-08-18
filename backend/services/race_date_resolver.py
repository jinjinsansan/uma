"""
レース日付解決サービス
曖昧なレース指定から適切な日付を特定する
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class RaceDateResolver:
    """レース日付を解決するサービス"""
    
    def __init__(self):
        pass  # シンプルな日付推定のみ行う
        
    def resolve_race_query(self, message: str) -> Dict[str, any]:
        """
        メッセージからレース情報を解析し、適切な日付を推定
        デフォルトは次の土日を想定（未来志向）
        
        Args:
            message: ユーザーのメッセージ（例: "新潟3Rを分析して"）
            
        Returns:
            {
                'venue': '新潟',
                'race_number': 3,
                'estimated_date': '2025-08-23',
                'date_type': 'future_weekend',
                'suggestion': '今週末（8月23-24日）の新潟3Rを想定しています。...'
            }
        """
        # レース番号と開催場を抽出
        venue_pattern = r'(東京|中山|京都|阪神|中京|新潟|札幌|函館|福島|小倉)'
        race_number_pattern = r'(\d+)[Rr]'
        
        venue_match = re.search(venue_pattern, message)
        race_number_match = re.search(race_number_pattern, message)
        
        if not venue_match or not race_number_match:
            return {
                'error': 'レース指定が不明確です',
                'suggestion': '「新潟3R」のように開催場とレース番号を指定してください'
            }
        
        venue = venue_match.group(1)
        race_number = int(race_number_match.group(1))
        
        # 過去・未来の判定
        past_keywords = ['先週', '昨日', '前回', '過去', 'だった', 'でした', '先月']
        is_past_query = any(keyword in message for keyword in past_keywords)
        
        # 日付推定
        today = datetime.now()
        
        if is_past_query:
            # 過去のレースを想定（前の土日）
            estimated_date = self._get_previous_weekend(today)
            date_type = 'past_weekend'
            date_description = '先週末'
        else:
            # 未来のレースを想定（次の土日）
            estimated_date = self._get_next_weekend(today)
            date_type = 'future_weekend'
            date_description = '今週末'
        
        # 日付を読みやすい形式に
        formatted_date = estimated_date.strftime('%m月%d日')
        day_of_week = ['月', '火', '水', '木', '金', '土', '日'][estimated_date.weekday()]
        
        return {
            'venue': venue,
            'race_number': race_number,
            'estimated_date': estimated_date.strftime('%Y-%m-%d'),
            'date_type': date_type,
            'suggestion': f"{date_description}（{formatted_date} {day_of_week}曜日）の{venue}{race_number}Rを想定しています。\n\n具体的な日付の分析をご希望の場合は、アーカイブページから該当レースをお選びください。",
            'resolved': True
        }
    
    def _get_next_weekend(self, base_date: datetime) -> datetime:
        """次の土曜日または日曜日を取得"""
        weekday = base_date.weekday()
        
        # 土曜日=5, 日曜日=6
        if weekday == 5:  # 土曜日の場合
            # 午前中なら今日、午後なら明日（日曜）
            if base_date.hour < 12:
                return base_date
            else:
                return base_date + timedelta(days=1)
        elif weekday == 6:  # 日曜日の場合
            # 午前中なら今日、午後なら次の土曜
            if base_date.hour < 12:
                return base_date
            else:
                return base_date + timedelta(days=6)
        else:  # 平日の場合
            # 次の土曜日まで
            days_until_saturday = (5 - weekday) % 7
            if days_until_saturday == 0:
                days_until_saturday = 7
            return base_date + timedelta(days=days_until_saturday)
    
    def _get_previous_weekend(self, base_date: datetime) -> datetime:
        """前の土曜日または日曜日を取得"""
        weekday = base_date.weekday()
        
        # 土曜日=5, 日曜日=6
        if weekday == 6:  # 日曜日の場合
            # 午後なら今日、午前なら昨日（土曜）
            if base_date.hour >= 12:
                return base_date
            else:
                return base_date - timedelta(days=1)
        elif weekday == 5:  # 土曜日の場合
            # 午後なら今日、午前なら先週の日曜
            if base_date.hour >= 12:
                return base_date
            else:
                return base_date - timedelta(days=6)
        else:  # 平日の場合
            # 前の日曜日
            if weekday == 0:  # 月曜日
                return base_date - timedelta(days=1)
            else:
                return base_date - timedelta(days=weekday)

# グローバルインスタンス
race_date_resolver = RaceDateResolver()