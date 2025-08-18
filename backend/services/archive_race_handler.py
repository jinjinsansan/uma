"""
アーカイブレース認識・処理ハンドラー
チャットメッセージからアーカイブレースを認識し、適切に処理する
"""
import re
import logging
from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class ArchiveRaceHandler:
    """アーカイブレースの認識と処理を担当"""
    
    def __init__(self):
        self.venue_patterns = [
            "札幌", "函館", "福島", "新潟", "東京", 
            "中山", "中京", "京都", "阪神", "小倉"
        ]
        
    def extract_race_info(self, message: str) -> Optional[Dict[str, Any]]:
        """
        メッセージからレース情報を抽出
        
        Args:
            message: ユーザーのメッセージ
            
        Returns:
            {
                "venue": "新潟",
                "race_number": 7,
                "date": None,  # 日付が明示されていない場合
                "action": "analyze"  # 分析, 情報取得など
            }
        """
        try:
            # 分析要求の判定
            is_analysis = any(word in message for word in ["分析", "予想", "診断", "解析"])
            
            # 開催場の抽出
            venue = None
            for v in self.venue_patterns:
                if v in message:
                    venue = v
                    break
            
            # レース番号の抽出（複数パターン対応）
            race_number = None
            
            # パターン1: "7R", "7r", "７Ｒ"
            pattern1 = re.search(r'(\d+)[rRｒＲ]', message)
            if pattern1:
                race_number = int(pattern1.group(1))
            
            # パターン2: "7レース", "７レース"
            pattern2 = re.search(r'(\d+)レース', message)
            if pattern2:
                race_number = int(pattern2.group(1))
                
            # パターン3: "第7レース"
            pattern3 = re.search(r'第(\d+)レース', message)
            if pattern3:
                race_number = int(pattern3.group(1))
            
            # 日付の抽出（オプション）
            date = None
            # YYYY-MM-DD形式
            date_pattern1 = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', message)
            if date_pattern1:
                date = f"{date_pattern1.group(1)}-{date_pattern1.group(2).zfill(2)}-{date_pattern1.group(3).zfill(2)}"
            
            # MM/DD形式
            date_pattern2 = re.search(r'(\d{1,2})/(\d{1,2})', message)
            if date_pattern2:
                current_year = datetime.now().year
                date = f"{current_year}-{date_pattern2.group(1).zfill(2)}-{date_pattern2.group(2).zfill(2)}"
            
            # 8月16日形式
            date_pattern3 = re.search(r'(\d{1,2})月(\d{1,2})日', message)
            if date_pattern3:
                current_year = datetime.now().year
                date = f"{current_year}-{date_pattern3.group(1).zfill(2)}-{date_pattern3.group(2).zfill(2)}"
            
            # レース名での検索（札幌記念など）
            race_name = None
            if "札幌記念" in message:
                race_name = "札幌記念"
            elif "記念" in message or "特別" in message or "ステークス" in message:
                # より詳細なレース名抽出が必要な場合は実装
                pass
            
            if venue or race_number or race_name:
                return {
                    "venue": venue,
                    "race_number": race_number,
                    "date": date,
                    "race_name": race_name,
                    "action": "analyze" if is_analysis else "info"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"レース情報抽出エラー: {e}")
            return None
    
    async def search_archive_races(self, race_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        アーカイブレースを検索
        
        Returns:
            {
                "found": True/False,
                "matches": [...],
                "count": 数値,
                "need_selection": True/False
            }
        """
        try:
            # テスト環境や直接呼び出しの場合は、内部データを直接検索
            from api.archive_races import ARCHIVE_RACES_METADATA
            
            matches = []
            
            for archive in ARCHIVE_RACES_METADATA:
                # 日付フィルタ
                if race_info.get("date") and archive["date"] != race_info["date"]:
                    continue
                
                # 開催場フィルタ
                if race_info.get("venue") and archive["venue"] != race_info["venue"]:
                    continue
                
                # レース検索
                for race in archive["races"]:
                    # レース番号フィルタ
                    if race_info.get("race_number") and race["race_number"] != race_info["race_number"]:
                        continue
                    
                    # レース名フィルタ（部分一致）
                    if race_info.get("race_name") and race_info["race_name"] not in race["race_name"]:
                        continue
                    
                    # 条件に合致したレースを追加
                    matches.append({
                        "date": archive["date"],
                        "venue": archive["venue"],
                        "race_number": race["race_number"],
                        "race_name": race["race_name"],
                        "archive_url": f"/archive/{archive['date']}",
                        "has_jockey_data": archive["date"] == "2025-08-16" and archive["venue"] == "札幌" and race["race_number"] == 11,
                        "grade": race.get("grade", "")
                    })
            
            # 日付とレース番号でソート
            matches.sort(key=lambda x: (x["date"], x["race_number"]))
            
            return {
                "found": len(matches) > 0,
                "matches": matches,
                "count": len(matches),
                "need_selection": len(matches) > 1
            }
                    
        except Exception as e:
            logger.error(f"アーカイブレース検索エラー: {e}")
            return {
                "found": False,
                "matches": [],
                "count": 0,
                "need_selection": False
            }
    
    def format_selection_message(self, matches: List[Dict[str, Any]]) -> str:
        """
        複数の候補がある場合の選択メッセージを生成
        """
        if not matches:
            return "該当するレースが見つかりませんでした。"
        
        if len(matches) == 1:
            match = matches[0]
            return f"📅 {match['date']} {match['venue']}{match['race_number']}R「{match['race_name']}」を分析します。"
        
        # 複数候補
        message = "複数のレースが見つかりました。どちらを分析しますか？\n\n"
        
        for i, match in enumerate(matches, 1):
            grade_badge = ""
            if match.get("grade") == "G1":
                grade_badge = "🏆 "
            elif match.get("grade") == "G2":
                grade_badge = "🥈 "
            elif match.get("grade") == "G3":
                grade_badge = "🥉 "
            
            message += f"{i}. 📅 {match['date']} {match['venue']}{match['race_number']}R「{grade_badge}{match['race_name']}」\n"
        
        message += "\n番号を選択するか、より詳しい情報（日付など）を教えてください。"
        
        return message
    
    def format_race_analysis_request(self, race_match: Dict[str, Any]) -> Dict[str, Any]:
        """
        レース分析リクエストをフォーマット
        アーカイブページのレース分析ボタンと同じ形式にする
        """
        # アーカイブページのボタンが送信する形式と同じにする
        return {
            "analysis_type": "race_v2",
            "race_data": {
                "date": race_match["date"],
                "venue": race_match["venue"], 
                "race_number": race_match["race_number"],
                "race_name": race_match["race_name"]
            },
            "source": "chat_archive_recognition"
        }

# グローバルインスタンス
archive_race_handler = ArchiveRaceHandler()