"""
動的アーカイブレース検索ハンドラー
フロントエンドのアーカイブデータを動的に検索し、日付優先順位を管理
"""
import re
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from services.archive_race_handler import archive_race_handler

logger = logging.getLogger(__name__)

class DynamicArchiveHandler:
    """動的アーカイブレース検索と日付管理"""
    
    def __init__(self):
        # フロントエンドと同期したアーカイブ日付リスト
        self.available_archives = []  # 動的に取得
        self.frontend_base_url = "https://www.dlogicai.in"  # 本番環境
        # 開発環境では "http://localhost:3000" を使用
        
        # 既存のarchive_race_handlerを継承
        self.base_handler = archive_race_handler
    
    def extract_race_info(self, message: str) -> Optional[Dict[str, Any]]:
        """メッセージからレース情報を抽出（既存機能を利用）"""
        return self.base_handler.extract_race_info(message)
    
    def extract_specific_date(self, message: str) -> Optional[str]:
        """
        メッセージから具体的な日付を抽出
        例: "8月16日の新潟3R" -> "2025-08-16"
        """
        # 日付パターンのマッチング
        patterns = [
            # "8月16日"
            r'(\d{1,2})月(\d{1,2})日',
            # "8/16"
            r'(\d{1,2})/(\d{1,2})',
            # "2025-08-16"
            r'(\d{4})-(\d{2})-(\d{2})',
            # "2025年8月16日"
            r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                groups = match.groups()
                if len(groups) == 2:  # 月日のみ
                    month, day = int(groups[0]), int(groups[1])
                    # 現在の年を使用
                    year = datetime.now().year
                    try:
                        date_obj = date(year, month, day)
                        return date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
                elif len(groups) == 3:  # 年月日
                    try:
                        if len(groups[0]) == 4:  # YYYY-MM-DD形式
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        else:  # 年月日形式
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        date_obj = date(year, month, day)
                        return date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
        
        return None
    
    async def search_archive_races_with_priority(self, race_info: Dict[str, Any], current_date: Optional[str] = None) -> Dict[str, Any]:
        """
        アーカイブレースを検索（日付優先順位付き）
        最大5件を返す（未来優先、その後新しい順）
        """
        if not current_date:
            current_date = datetime.now().strftime("%Y-%m-%d")
        
        current_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
        
        # フロントエンドAPIから検索
        from services.frontend_archive_client import frontend_archive_client
        frontend_result = await frontend_archive_client.search_archive_races(
            race_info.get("venue"),
            race_info.get("race_number"),
            race_info.get("date")
        )
        
        if frontend_result.get("found"):
            # フロントエンドからのデータをフォーマット
            matches = []
            for race in frontend_result.get("races", []):
                match = {
                    "date": race.get("race_date"),
                    "venue": race.get("venue"),
                    "race_number": race.get("race_number"),
                    "race_name": race.get("race_name"),
                    "archive_url": f"/archive/{race.get('race_date')}",
                    "has_jockey_data": bool(race.get("jockeys")),
                    "grade": race.get("grade", ""),
                    "is_future": race.get("is_future", False),
                    "days_diff": race.get("days_diff", 0),
                    "weekday": race.get("weekday", "")
                }
                matches.append(match)
            
            return {
                "found": True,
                "matches": matches,  # すでに優先順位付けされている
                "count": frontend_result.get("total_count", len(matches)),
                "limited_count": len(matches),
                "need_selection": len(matches) > 1,
                "has_more": frontend_result.get("has_more", False)
            }
        
        # フォールバック: 既存のsearch_archive_racesを使用
        search_result = await self.base_handler.search_archive_races(race_info)
        
        if not search_result["found"]:
            return search_result
        
        # 日付情報を追加して優先順位を計算
        matches_with_priority = []
        for match in search_result["matches"]:
            match_date = datetime.strptime(match["date"], "%Y-%m-%d")
            days_diff = (match_date - current_date_obj).days
            
            match_with_priority = match.copy()
            match_with_priority["is_future"] = days_diff > 0
            match_with_priority["days_diff"] = days_diff
            
            # 曜日を追加
            weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
            match_with_priority["weekday"] = weekday_names[match_date.weekday()]
            
            matches_with_priority.append(match_with_priority)
        
        # ソート: 未来優先、その後新しい順
        matches_with_priority.sort(key=lambda x: (
            not x["is_future"],  # 未来のレースを先に（True -> False）
            -x["days_diff"] if x["is_future"] else x["days_diff"]  # 未来は近い順、過去は新しい順
        ))
        
        # 最大5件に制限
        limited_matches = matches_with_priority[:5]
        
        return {
            "found": True,
            "matches": limited_matches,
            "count": len(search_result["matches"]),  # 総数
            "limited_count": len(limited_matches),   # 表示数
            "need_selection": len(limited_matches) > 1,
            "has_more": len(search_result["matches"]) > 5
        }
    
    def format_selection_message_with_priority(self, matches: List[Dict[str, Any]], has_more: bool = False) -> str:
        """
        優先順位付きの選択メッセージを生成
        """
        if not matches:
            return "該当するレースが見つかりませんでした。"
        
        if len(matches) == 1:
            match = matches[0]
            return f"📅 {match['date']} {match['venue']}{match['race_number']}R「{match['race_name']}」を分析します。"
        
        # 複数候補
        message = "複数のレースが見つかりました。どちらを分析しますか？\n\n"
        
        for i, match in enumerate(matches, 1):
            # 未来のレースには特別なマーク
            future_mark = "（未来のレース）" if match.get("is_future", False) else ""
            weekday = f"（{match.get('weekday', '')}曜日）" if match.get('weekday') else ""
            
            grade_badge = ""
            if match.get("grade") == "G1":
                grade_badge = "🏆 "
            elif match.get("grade") == "G2":
                grade_badge = "🥈 "
            elif match.get("grade") == "G3":
                grade_badge = "🥉 "
            
            message += f"{i}. 📅 {match['date']} {match['venue']}{match['race_number']}R「{grade_badge}{match['race_name']}」{weekday}{future_mark}\n"
        
        message += "\n番号を選択するか、"
        
        if has_more:
            message += "上記以外の日付をご希望の場合は、日付を直接入力してください（例：7月20日）。"
        else:
            message += "より詳しい情報（日付など）を教えてください。"
        
        return message
    
    async def search_specific_date_race(self, date_str: str, venue: str, race_number: int) -> Optional[Dict[str, Any]]:
        """
        特定の日付のレースを検索
        """
        # まずフロントエンドAPIから検索
        from services.frontend_archive_client import frontend_archive_client
        frontend_result = await frontend_archive_client.search_archive_races(
            venue,
            race_number,
            date_str
        )
        
        if frontend_result.get("found") and frontend_result.get("races"):
            race = frontend_result["races"][0]
            return {
                "date": race.get("race_date"),
                "venue": race.get("venue"),
                "race_number": race.get("race_number"),
                "race_name": race.get("race_name"),
                "archive_url": f"/archive/{race.get('race_date')}",
                "has_jockey_data": bool(race.get("jockeys")),
                "grade": race.get("grade", "")
            }
        
        # フォールバック: 既存の検索
        race_info = {
            "date": date_str,
            "venue": venue,
            "race_number": race_number,
            "action": "analyze"
        }
        
        search_result = await self.base_handler.search_archive_races(race_info)
        
        if search_result["found"] and len(search_result["matches"]) > 0:
            return search_result["matches"][0]
        
        return None

# シングルトンインスタンス
dynamic_archive_handler = DynamicArchiveHandler()