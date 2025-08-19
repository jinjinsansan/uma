"""
ハイブリッドアーカイブレース検索ハンドラー
TSファイル（高速）とSupabase（拡張性）の両方から検索
"""
import re
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from services.archive_race_handler import archive_race_handler
from services.supabase_client import supabase_client
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class HybridArchiveHandler:
    """TSファイルとSupabaseのハイブリッド検索"""
    
    def __init__(self):
        self.frontend_base_url = "https://www.dlogicai.in"
        self.base_handler = archive_race_handler
        
        # キャッシュ（メモリ内で頻繁にアクセスされるデータを保存）
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5分間キャッシュ
        
        # 最新5日間の日付（TSファイルで管理される想定）
        self._recent_dates = self._get_recent_dates()
    
    def _get_recent_dates(self) -> List[str]:
        """最新5日間の日付を取得（未来2日+過去3日）"""
        today = date.today()
        dates = []
        
        # 未来の2日間
        for i in range(2, 0, -1):
            future_date = today + timedelta(days=i)
            dates.append(future_date.strftime("%Y-%m-%d"))
        
        # 今日
        dates.append(today.strftime("%Y-%m-%d"))
        
        # 過去の2日間
        for i in range(1, 3):
            past_date = today - timedelta(days=i)
            dates.append(past_date.strftime("%Y-%m-%d"))
        
        return dates
    
    def extract_race_info(self, message: str) -> Optional[Dict[str, Any]]:
        """メッセージからレース情報を抽出"""
        return self.base_handler.extract_race_info(message)
    
    def extract_specific_date(self, message: str) -> Optional[str]:
        """メッセージから具体的な日付を抽出"""
        patterns = [
            r'(\d{1,2})月(\d{1,2})日',
            r'(\d{1,2})/(\d{1,2})',
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    month, day = int(groups[0]), int(groups[1])
                    year = datetime.now().year
                    try:
                        date_obj = date(year, month, day)
                        return date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
                elif len(groups) == 3:
                    try:
                        if len(groups[0]) == 4:
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        else:
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        date_obj = date(year, month, day)
                        return date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
        
        return None
    
    async def search_archive_races_with_priority(self, race_info: Dict[str, Any], current_date: Optional[str] = None) -> Dict[str, Any]:
        """
        ハイブリッド検索：TSファイル優先、不足分をSupabaseから取得
        """
        if not current_date:
            current_date = datetime.now().strftime("%Y-%m-%d")
        
        venue = race_info.get("venue")
        race_number = race_info.get("race_number")
        specific_date = race_info.get("date")
        
        # キャッシュチェック
        cache_key = f"{venue}_{race_number}_{specific_date or 'all'}"
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if datetime.now().timestamp() - cached_data['timestamp'] < self._cache_ttl:
                logger.info(f"キャッシュヒット: {cache_key}")
                return cached_data['data']
        
        # 特定の日付が指定されている場合
        if specific_date:
            # 最近の日付ならTSファイルから取得
            if specific_date in self._recent_dates:
                result = await self._search_from_frontend(venue, race_number, specific_date)
                if result['found']:
                    return result
            
            # Supabaseから取得
            result = await self._search_from_supabase(venue, race_number, specific_date)
            if result['found']:
                self._update_cache(cache_key, result)
                return result
            
            return {"found": False, "matches": []}
        
        # 日付指定なしの場合：ハイブリッド検索
        all_matches = []
        
        # 1. TSファイルから最新5件を検索（超高速）
        frontend_task = asyncio.create_task(self._search_recent_from_frontend(venue, race_number))
        
        # 2. 5件見つかったら即返却
        frontend_result = await frontend_task
        if frontend_result['found'] and len(frontend_result['matches']) >= 5:
            logger.info(f"TSファイルのみで5件取得完了")
            result = self._format_with_priority(frontend_result['matches'][:5], current_date)
            self._update_cache(cache_key, result)
            return result
        
        # 3. 不足分をSupabaseから取得
        needed_count = 5 - len(frontend_result.get('matches', []))
        if needed_count > 0:
            supabase_result = await self._search_from_supabase(
                venue, race_number, None, limit=needed_count,
                exclude_dates=self._recent_dates
            )
            
            # 結果をマージ
            all_matches = frontend_result.get('matches', []) + supabase_result.get('matches', [])
        else:
            all_matches = frontend_result.get('matches', [])
        
        # 優先順位付けして返却
        result = self._format_with_priority(all_matches[:5], current_date)
        self._update_cache(cache_key, result)
        return result
    
    async def _search_recent_from_frontend(self, venue: str, race_number: int) -> Dict[str, Any]:
        """最近の日付のTSファイルから検索"""
        from services.frontend_archive_client import frontend_archive_client
        
        matches = []
        
        # 並列検索のためのタスク
        tasks = []
        for date_str in self._recent_dates:
            task = frontend_archive_client.search_archive_races(venue, race_number, date_str)
            tasks.append(task)
        
        # すべてのタスクを並列実行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"フロントエンド検索エラー: {result}")
                continue
            
            if result.get('found') and result.get('races'):
                matches.extend(result['races'])
        
        return {
            "found": len(matches) > 0,
            "matches": matches
        }
    
    async def _search_from_frontend(self, venue: str, race_number: int, specific_date: str) -> Dict[str, Any]:
        """フロントエンドAPIから検索"""
        from services.frontend_archive_client import frontend_archive_client
        
        try:
            result = await frontend_archive_client.search_archive_races(venue, race_number, specific_date)
            if result.get('found'):
                return {
                    "found": True,
                    "matches": result.get('races', [])
                }
        except Exception as e:
            logger.error(f"フロントエンド検索エラー: {e}")
        
        return {"found": False, "matches": []}
    
    async def _search_from_supabase(self, venue: str, race_number: int, 
                                   specific_date: Optional[str] = None,
                                   limit: int = 5,
                                   exclude_dates: Optional[List[str]] = None) -> Dict[str, Any]:
        """Supabaseから検索"""
        if not supabase_client.is_available():
            logger.warning("Supabaseクライアントが利用できません")
            return {"found": False, "matches": []}
        
        try:
            # クエリ構築
            query = supabase_client.client.table('archive_races') \
                .select('*') \
                .eq('venue', venue) \
                .eq('race_number', race_number)
            
            if specific_date:
                query = query.eq('race_date', specific_date)
            else:
                # 除外する日付がある場合
                if exclude_dates:
                    for date_str in exclude_dates:
                        query = query.neq('race_date', date_str)
                
                # 新しい順にソート
                query = query.order('race_date', desc=True).limit(limit)
            
            # 実行
            response = query.execute()
            
            if response.data:
                matches = []
                for race in response.data:
                    match = {
                        "date": race['race_date'],
                        "venue": race['venue'],
                        "race_number": race['race_number'],
                        "race_name": race['race_name'],
                        "archive_url": f"/archive/{race['race_date']}",
                        "has_jockey_data": bool(race.get('jockeys')),
                        "grade": race.get('grade', ''),
                        "horses": race.get('horses', []),
                        "jockeys": race.get('jockeys'),
                        "posts": race.get('posts'),
                        "horse_numbers": race.get('horse_numbers'),
                        "distance": race.get('distance'),
                        "track_condition": race.get('track_condition', '良')
                    }
                    matches.append(match)
                
                return {
                    "found": True,
                    "matches": matches
                }
            
        except Exception as e:
            logger.error(f"Supabase検索エラー: {e}")
        
        return {"found": False, "matches": []}
    
    def _format_with_priority(self, matches: List[Dict[str, Any]], current_date: str) -> Dict[str, Any]:
        """日付優先順位を付けてフォーマット"""
        current_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
        
        matches_with_priority = []
        for match in matches:
            match_date = datetime.strptime(match["date"], "%Y-%m-%d")
            days_diff = (match_date - current_date_obj).days
            
            match_with_priority = match.copy()
            match_with_priority["is_future"] = days_diff > 0
            match_with_priority["days_diff"] = days_diff
            
            weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
            match_with_priority["weekday"] = weekday_names[match_date.weekday()]
            
            matches_with_priority.append(match_with_priority)
        
        # ソート: 未来優先、その後新しい順
        matches_with_priority.sort(key=lambda x: (
            not x["is_future"],
            -x["days_diff"] if x["is_future"] else x["days_diff"]
        ))
        
        # 最大5件に制限
        limited_matches = matches_with_priority[:5]
        
        return {
            "found": True,
            "matches": limited_matches,
            "count": len(matches),
            "limited_count": len(limited_matches),
            "need_selection": len(limited_matches) > 1,
            "has_more": len(matches) > 5
        }
    
    def _update_cache(self, key: str, data: Dict[str, Any]):
        """キャッシュを更新"""
        self._cache[key] = {
            'timestamp': datetime.now().timestamp(),
            'data': data
        }
    
    def format_selection_message_with_priority(self, matches: List[Dict[str, Any]], has_more: bool = False) -> str:
        """優先順位付きの選択メッセージを生成"""
        if not matches:
            return "該当するレースが見つかりませんでした。"
        
        if len(matches) == 1:
            match = matches[0]
            return f"📅 {match['date']} {match['venue']}{match['race_number']}R「{match['race_name']}」を分析します。"
        
        message = "複数のレースが見つかりました。どちらを分析しますか？\n\n"
        
        for i, match in enumerate(matches, 1):
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
    
    async def get_race_data(self, date: str, venue: str, race_number: int) -> Optional[Dict[str, Any]]:
        """特定のレースデータを取得（ハイブリッド）"""
        # 最近の日付ならフロントエンドから
        if date in self._recent_dates:
            from services.frontend_archive_client import frontend_archive_client
            race_data = await frontend_archive_client.get_race_data(date, venue, race_number)
            if race_data:
                return race_data
        
        # Supabaseから取得
        if supabase_client.is_available():
            try:
                response = supabase_client.client.table('archive_races') \
                    .select('*') \
                    .eq('race_date', date) \
                    .eq('venue', venue) \
                    .eq('race_number', race_number) \
                    .single() \
                    .execute()
                
                if response.data:
                    race = response.data
                    return {
                        'venue': race['venue'],
                        'race_number': race['race_number'],
                        'race_name': race['race_name'],
                        'grade': race.get('grade', ''),
                        'distance': race.get('distance', ''),
                        'track_condition': race.get('track_condition', '良'),
                        'horses': race.get('horses', []),
                        'jockeys': race.get('jockeys', []),
                        'posts': race.get('posts', []),
                        'horse_numbers': race.get('horse_numbers', [])
                    }
            except Exception as e:
                logger.error(f"Supabaseからのレースデータ取得エラー: {e}")
        
        return None

# シングルトンインスタンス
hybrid_archive_handler = HybridArchiveHandler()