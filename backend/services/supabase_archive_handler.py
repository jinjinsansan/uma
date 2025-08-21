"""
Supabase専用アーカイブレース検索ハンドラー
TSファイル依存を排除し、Supabaseのみで動作
"""
import re
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from services.supabase_client import supabase_client

logger = logging.getLogger(__name__)

class SupabaseArchiveHandler:
    """Supabase専用のアーカイブ検索"""
    
    def __init__(self):
        # キャッシュ（メモリ内で頻繁にアクセスされるデータを保存）
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5分間キャッシュ
    
    def extract_race_info(self, message: str) -> Optional[Dict[str, Any]]:
        """メッセージからレース情報を抽出"""
        # 分析要求の判定
        is_analysis = any(word in message for word in ["分析", "予想", "診断", "解析", "して"])
        
        # 0. 完全な日付＋レース情報のパターン（例：2025-08-17 札幌6R）
        full_date_pattern = r'(\d{4}-\d{2}-\d{2})\s+(東京|中山|京都|阪神|中京|新潟|札幌|函館|福島|小倉)(\d+)[RrＲ]'
        full_match = re.search(full_date_pattern, message)
        if full_match:
            return {
                "date": full_match.group(1),
                "venue": full_match.group(2),
                "race_number": int(full_match.group(3)),
                "action": "analyze" if is_analysis else "info"
            }
        
        # 1. レース名での検索（G1レース、重賞レースなど）
        race_name_patterns = {
            # 2024年G1レース
            "フェブラリーステークス": {"venue": "東京", "race_number": 11},
            "高松宮記念": {"venue": "中京", "race_number": 11},
            "大阪杯": {"venue": "阪神", "race_number": 11},
            "桜花賞": {"venue": "阪神", "race_number": 11},
            "皐月賞": {"venue": "中山", "race_number": 11},
            "天皇賞春": {"venue": "京都", "race_number": 11},
            "天皇賞(春)": {"venue": "京都", "race_number": 11},
            "NHKマイルカップ": {"venue": "東京", "race_number": 11},
            "NHKマイルC": {"venue": "東京", "race_number": 11},
            "オークス": {"venue": "東京", "race_number": 11},
            "東京優駿": {"venue": "東京", "race_number": 11},
            "日本ダービー": {"venue": "東京", "race_number": 11},
            "ダービー": {"venue": "東京", "race_number": 11},
            "安田記念": {"venue": "東京", "race_number": 11},
            "宝塚記念": {"venue": "阪神", "race_number": 11},
            "スプリンターズステークス": {"venue": "中山", "race_number": 11},
            "スプリンターズS": {"venue": "中山", "race_number": 11},
            "秋華賞": {"venue": "京都", "race_number": 11},
            "菊花賞": {"venue": "京都", "race_number": 11},
            "天皇賞秋": {"venue": "東京", "race_number": 11},
            "天皇賞(秋)": {"venue": "東京", "race_number": 11},
            "エリザベス女王杯": {"venue": "京都", "race_number": 11},
            "マイルチャンピオンシップ": {"venue": "京都", "race_number": 11},
            "マイルCS": {"venue": "京都", "race_number": 11},
            "ジャパンカップ": {"venue": "東京", "race_number": 11},
            "ジャパンC": {"venue": "東京", "race_number": 11},
            "チャンピオンズカップ": {"venue": "中京", "race_number": 11},
            "チャンピオンズC": {"venue": "中京", "race_number": 11},
            "朝日杯フューチュリティステークス": {"venue": "阪神", "race_number": 11},
            "朝日杯FS": {"venue": "阪神", "race_number": 11},
            "有馬記念": {"venue": "中山", "race_number": 11},
            # 重賞レース
            "札幌記念": {"venue": "札幌", "race_number": 11},
            "新潟記念": {"venue": "新潟", "race_number": 11},
        }
        
        for race_name, info in race_name_patterns.items():
            if race_name in message:
                date_str = self.extract_specific_date(message)
                return {
                    "venue": info["venue"],
                    "race_number": info["race_number"],
                    "date": date_str,
                    "race_name": race_name,
                    "action": "analyze" if is_analysis else "info"
                }
        
        # 2. 開催場とレース番号のパターン
        venue_race_patterns = [
            r'(東京|中山|京都|阪神|中京|新潟|札幌|函館|福島|小倉)(\d+)[RrＲ]',
            r'(東京|中山|京都|阪神|中京|新潟|札幌|函館|福島|小倉)(\d+)レース',
            r'(東京|中山|京都|阪神|中京|新潟|札幌|函館|福島|小倉)第(\d+)レース'
        ]
        
        for pattern in venue_race_patterns:
            match = re.search(pattern, message)
            if match:
                venue = match.group(1)
                race_number = int(match.group(2))
                
                # 日付も含まれているか確認
                date_str = self.extract_specific_date(message)
                
                return {
                    "venue": venue,
                    "race_number": race_number,
                    "date": date_str,
                    "action": "analyze" if is_analysis else "info"
                }
        
        return None
    
    def extract_specific_date(self, message: str) -> Optional[str]:
        """メッセージから具体的な日付を抽出（相対日付も対応）"""
        today = datetime.now()
        
        # 相対的な日付表現
        if "今日" in message:
            return today.strftime("%Y-%m-%d")
        elif "明日" in message:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "昨日" in message:
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        elif "今週末" in message or "今週の" in message:
            # 次の土曜日を返す
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0 and today.hour >= 18:  # 土曜日の夕方以降は次週
                days_until_saturday = 7
            return (today + timedelta(days=days_until_saturday)).strftime("%Y-%m-%d")
        elif "先週" in message:
            return (today - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # 具体的な日付パターン
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
                            year = datetime.now().year
                            month, day = int(groups[0]), int(groups[1])
                        date_obj = date(year, month, day)
                        return date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
        
        return None
    
    async def search_archive_races_with_priority(self, race_info: Dict[str, Any], current_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Supabaseから優先順位付きでレースを検索
        """
        logger.info(f"search_archive_races_with_priority called with race_info: {race_info}, current_date: {current_date}")
        
        if not current_date:
            current_date = datetime.now().strftime("%Y-%m-%d")
        
        venue = race_info.get("venue")
        race_number = race_info.get("race_number")
        race_name = race_info.get("race_name")
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
            result = await self._search_from_supabase(venue, race_number, specific_date, race_name)
            if result['found']:
                self._update_cache(cache_key, result)
                return result
            
            return {"found": False, "matches": []}
        
        # 日付指定なしの場合：優先順位付き検索
        # 1. 未来のレース（今週末まで）
        # 2. 先週のレース
        # 3. それ以前（アーカイブページ誘導）
        
        all_matches = []
        current_date_obj = datetime.strptime(current_date, "%Y-%m-%d")
        
        # レース名が指定されている場合（G1レースなど）は、より広い範囲を検索
        if race_name:
            # G1レースの場合は過去2年分を検索
            future_matches = await self._search_date_range(venue, race_number, current_date_obj, 0, 30, race_name)
            past_matches = await self._search_date_range(venue, race_number, current_date_obj, -730, -1, race_name)  # 2年前まで
        else:
            # 通常のレースは未来7日間 + 過去7日間を検索
            future_matches = await self._search_date_range(venue, race_number, current_date_obj, 0, 7, race_name)
            past_matches = await self._search_date_range(venue, race_number, current_date_obj, -7, -1, race_name)
        
        all_matches = future_matches + past_matches
        
        # 優先順位付けして返却
        result = self._format_with_priority(all_matches[:5], current_date)
        self._update_cache(cache_key, result)
        return result
    
    async def _search_date_range(self, venue: str, race_number: int, base_date: datetime, start_offset: int, end_offset: int, race_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """指定された日付範囲でレースを検索"""
        if not supabase_client.is_available():
            return []
        
        start_date = (base_date + timedelta(days=start_offset)).strftime("%Y-%m-%d")
        end_date = (base_date + timedelta(days=end_offset)).strftime("%Y-%m-%d")
        
        try:
            query = supabase_client.client.table('archive_races') \
                .select('*') \
                .eq('venue', venue) \
                .eq('race_number', race_number) \
                .gte('race_date', start_date) \
                .lte('race_date', end_date)
            
            # レース名が指定されている場合は追加の絞り込み
            if race_name:
                query = query.ilike('race_name', f'%{race_name}%')
            
            query = query.order('race_date', desc=(start_offset < 0))
            
            response = query.execute()
            
            if response.data:
                matches = []
                for race in response.data:
                    match = self._format_race_data(race)
                    matches.append(match)
                return matches
        except Exception as e:
            logger.error(f"Supabase検索エラー: {e}")
        
        return []
    
    async def _search_from_supabase(self, venue: str, race_number: int, specific_date: Optional[str] = None, race_name: Optional[str] = None) -> Dict[str, Any]:
        """Supabaseから検索（レース名検索も対応）"""
        if not supabase_client.is_available():
            logger.error("Supabaseクライアントが利用できません。環境変数を確認してください: SUPABASE_URL, SUPABASE_ANON_KEY")
            return {
                "found": False, 
                "matches": [],
                "error": "データベース接続エラー: アーカイブデータにアクセスできません。管理者にお問い合わせください。"
            }
        
        try:
            # レース名が指定されている場合は、レース名で検索
            if race_name:
                # G1レース名の正規化（略称対応）
                normalized_names = []
                if race_name == "NHKマイルカップ" or race_name == "NHKマイルC":
                    normalized_names = ["NHKマイルカップ", "NHKマイルC"]
                elif race_name == "スプリンターズステークス" or race_name == "スプリンターズS":
                    normalized_names = ["スプリンターズステークス", "スプリンターズS"]
                elif race_name == "マイルチャンピオンシップ" or race_name == "マイルCS":
                    normalized_names = ["マイルチャンピオンシップ", "マイルCS"]
                elif race_name == "ジャパンカップ" or race_name == "ジャパンC":
                    normalized_names = ["ジャパンカップ", "ジャパンC"]
                elif race_name == "チャンピオンズカップ" or race_name == "チャンピオンズC":
                    normalized_names = ["チャンピオンズカップ", "チャンピオンズC"]
                elif race_name == "朝日杯フューチュリティステークス" or race_name == "朝日杯FS":
                    normalized_names = ["朝日杯フューチュリティステークス", "朝日杯FS"]
                else:
                    normalized_names = [race_name]
                
                # レース名で検索（部分一致）
                query = supabase_client.client.table('archive_races').select('*')
                
                # 複数の正規化された名前で検索
                if len(normalized_names) > 1:
                    # ORクエリを構築
                    or_conditions = []
                    for name in normalized_names:
                        or_conditions.append(f"race_name.ilike.%{name}%")
                    query = query.or_(','.join(or_conditions))
                else:
                    query = query.ilike('race_name', f'%{race_name}%')
                
                # 開催場とレース番号も条件に追加（より正確な絞り込み）
                query = query.eq('venue', venue).eq('race_number', race_number)
                
                if specific_date:
                    query = query.eq('race_date', specific_date)
                else:
                    # 新しい順にソート、最大5件
                    query = query.order('race_date', desc=True).limit(5)
            else:
                # レース名が指定されていない場合は従来通り
                query = supabase_client.client.table('archive_races') \
                    .select('*') \
                    .eq('venue', venue) \
                    .eq('race_number', race_number)
                
                if specific_date:
                    query = query.eq('race_date', specific_date)
                else:
                    # 新しい順にソート、最大5件
                    query = query.order('race_date', desc=True).limit(5)
            
            response = query.execute()
            
            logger.info(f"Supabase query executed for {venue} {race_number}R with race_name='{race_name}' on {specific_date or 'any date'}")
            logger.info(f"Supabase query response data count: {len(response.data) if response.data else 0}")
            if response.data:
                logger.info(f"Sample result: {response.data[0]['race_name'] if response.data else 'None'}")
            
            if response.data:
                matches = []
                for race in response.data:
                    match = self._format_race_data(race)
                    matches.append(match)
                
                logger.info(f"Found {len(matches)} matches from Supabase")
                return {
                    "found": True,
                    "matches": matches
                }
            else:
                logger.warning(f"No data found from Supabase for {venue} {race_number}R")
            
        except Exception as e:
            logger.error(f"Supabase検索エラー: {e}")
        
        return {"found": False, "matches": []}
    
    def _format_race_data(self, race: Dict[str, Any]) -> Dict[str, Any]:
        """Supabaseのデータを統一形式に変換"""
        return {
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
        if not matches or len(matches) == 0:
            return "該当するレースが見つかりませんでした。"
        
        if len(matches) == 1:
            match = matches[0]
            return f"📅 {match['date']} {match['venue']}{match['race_number']}R「{match['race_name']}」を分析します。"
        
        message = "複数のレースが見つかりました。以下のボタンから選択してください。\n\n"
        
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
            
            message += f"• 📅 {match['date']} {match['venue']}{match['race_number']}R「{grade_badge}{match['race_name']}」{weekday}{future_mark}\n"
        
        # 2週間以上前のレースの場合はアーカイブページ誘導
        if matches and len(matches) > 0:
            oldest_match = matches[-1]
            if oldest_match and oldest_match.get("days_diff", 0) < -14:
                message += "\n\n💡 2週間以上前のレースは、アーカイブページから直接分析することをお勧めします。"
        
        return message
    
    async def get_race_data(self, date: str, venue: str, race_number: int) -> Optional[Dict[str, Any]]:
        """特定のレースデータを取得"""
        if not supabase_client.is_available():
            return None
        
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
supabase_archive_handler = SupabaseArchiveHandler()