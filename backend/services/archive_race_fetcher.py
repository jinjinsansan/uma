"""
アーカイブページからレースデータを取得するサービス
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class ArchiveRaceFetcher:
    """アーカイブレースデータ取得サービス"""
    
    def __init__(self):
        """初期化"""
        # アーカイブデータの保存先（実際はフロントエンドのファイルを参照）
        self.archive_base_path = Path(__file__).parent.parent.parent.parent.parent / "front" / "d-logic-ai-frontend" / "src" / "app" / "archive"
        
        # キャッシュ
        self._cache = {}
        
        logger.info(f"ArchiveRaceFetcher initialized with base path: {self.archive_base_path}")
    
    def get_race_data(self, date: str, venue: str, race_number: int) -> Optional[Dict[str, Any]]:
        """
        指定された日付・開催場・レース番号のデータを取得
        
        Args:
            date: 日付（YYYY-MM-DD形式）
            venue: 開催場名
            race_number: レース番号
        
        Returns:
            レースデータまたはNone
        """
        cache_key = f"{date}_{venue}_{race_number}"
        
        # キャッシュチェック
        if cache_key in self._cache:
            logger.info(f"Cache hit for {cache_key}")
            return self._cache[cache_key]
        
        try:
            # アーカイブファイルのパスを構築
            # 例: /archive/2025-08-17/page.tsx
            archive_file = self.archive_base_path / date / "page.tsx"
            
            if not archive_file.exists():
                logger.warning(f"Archive file not found: {archive_file}")
                return None
            
            # TypeScriptファイルを読み込んでレースデータを抽出
            with open(archive_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # レースデータを抽出（簡易パーサー）
            races = self._extract_races_from_tsx(content)
            
            # 指定された開催場・レース番号のデータを検索
            for race in races:
                if race.get('venue') == venue and race.get('race_number') == race_number:
                    # キャッシュに保存
                    self._cache[cache_key] = race
                    logger.info(f"Found race data: {venue} {race_number}R on {date}")
                    return race
            
            logger.warning(f"Race not found: {venue} {race_number}R on {date}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching archive race data: {e}")
            return None
    
    def search_race_by_name(self, race_name: str, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        レース名でレースを検索
        
        Args:
            race_name: レース名（部分一致）
            date: 日付（指定しない場合は全日程から検索）
        
        Returns:
            マッチしたレースのリスト
        """
        matching_races = []
        
        try:
            if date:
                # 特定の日付のみ検索
                dates_to_search = [date]
            else:
                # 全アーカイブディレクトリを検索
                dates_to_search = []
                if self.archive_base_path.exists():
                    for item in self.archive_base_path.iterdir():
                        if item.is_dir() and item.name.startswith('20'):  # YYYY-MM-DD形式
                            dates_to_search.append(item.name)
            
            for search_date in dates_to_search:
                archive_file = self.archive_base_path / search_date / "page.tsx"
                
                if not archive_file.exists():
                    continue
                
                with open(archive_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                races = self._extract_races_from_tsx(content)
                
                for race in races:
                    if race_name in race.get('race_name', ''):
                        race['race_date'] = search_date
                        matching_races.append(race)
            
            logger.info(f"Found {len(matching_races)} races matching '{race_name}'")
            return matching_races
            
        except Exception as e:
            logger.error(f"Error searching races by name: {e}")
            return []
    
    def _extract_races_from_tsx(self, content: str) -> List[Dict[str, Any]]:
        """
        TypeScriptファイルからレースデータを抽出
        
        Args:
            content: TSXファイルの内容
        
        Returns:
            レースデータのリスト
        """
        races = []
        
        try:
            # const races = [ ... ] の部分を抽出
            import re
            
            # レース配列の開始位置を見つける
            races_match = re.search(r'const\s+races\s*=\s*\[(.*?)\]', content, re.DOTALL)
            
            if not races_match:
                logger.warning("Could not find races array in TSX file")
                return []
            
            races_content = races_match.group(1)
            
            # 各レースオブジェクトを抽出（ネストされた配列を含む）
            # より柔軟なパターンでレースオブジェクトを抽出
            race_objects = []
            
            # 開き括弧と閉じ括弧をカウントして、完全なオブジェクトを抽出
            brace_count = 0
            current_object = ""
            in_object = False
            
            for char in races_content:
                if char == '{':
                    if brace_count == 0:
                        in_object = True
                        current_object = ""
                    brace_count += 1
                
                if in_object:
                    current_object += char
                
                if char == '}':
                    brace_count -= 1
                    if brace_count == 0 and in_object:
                        race_objects.append(current_object)
                        in_object = False
            
            # 各レースオブジェクトを解析
            for race_obj in race_objects:
                # オブジェクトの中身を抽出（最初と最後の括弧を除く）
                race_str = race_obj[1:-1] if len(race_obj) > 2 else race_obj
                
                # レースデータを解析
                race_data = self._parse_race_object(race_str)
                if race_data:
                    races.append(race_data)
            
            logger.info(f"Extracted {len(races)} races from TSX file")
            return races
            
        except Exception as e:
            logger.error(f"Error extracting races from TSX: {e}")
            return []
    
    def _parse_race_object(self, race_str: str) -> Optional[Dict[str, Any]]:
        """
        レースオブジェクト文字列をパース
        
        Args:
            race_str: レースオブジェクトの文字列表現
        
        Returns:
            パースされたレースデータ
        """
        try:
            import re
            race_data = {}
            
            # 基本情報の抽出
            patterns = {
                'venue': r"venue:\s*['\"]([^'\"]+)['\"]",
                'race_number': r"race_number:\s*(\d+)",
                'race_name': r"race_name:\s*['\"]([^'\"]+)['\"]",
                'distance': r"distance:\s*['\"]([^'\"]+)['\"]",
                'grade': r"grade:\s*['\"]([^'\"]+)['\"]"
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, race_str)
                if match:
                    if key == 'race_number':
                        race_data[key] = int(match.group(1))
                    else:
                        race_data[key] = match.group(1)
            
            # 馬名配列の抽出
            horses_match = re.search(r"horses:\s*\[([^\]]+)\]", race_str)
            if horses_match:
                horses_str = horses_match.group(1)
                horses = re.findall(r"['\"]([^'\"]+)['\"]", horses_str)
                race_data['horses'] = horses
            
            # 騎手配列の抽出
            jockeys_match = re.search(r"jockeys:\s*\[([^\]]+)\]", race_str)
            if jockeys_match:
                jockeys_str = jockeys_match.group(1)
                jockeys = re.findall(r"['\"]([^'\"]+)['\"]", jockeys_str)
                race_data['jockeys'] = jockeys
            
            # 枠順配列の抽出
            posts_match = re.search(r"posts:\s*\[([^\]]+)\]", race_str)
            if posts_match:
                posts_str = posts_match.group(1)
                posts = [int(x.strip()) for x in posts_str.split(',') if x.strip().isdigit()]
                race_data['posts'] = posts
            
            # 馬番配列の抽出
            horse_numbers_match = re.search(r"horse_numbers:\s*\[([^\]]+)\]", race_str)
            if horse_numbers_match:
                horse_numbers_str = horse_numbers_match.group(1)
                horse_numbers = [int(x.strip()) for x in horse_numbers_str.split(',') if x.strip().isdigit()]
                race_data['horse_numbers'] = horse_numbers
            
            # 必須フィールドのチェック
            if 'venue' in race_data and 'race_number' in race_data and 'horses' in race_data:
                return race_data
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error parsing race object: {e}")
            return None

# グローバルインスタンス
archive_fetcher = ArchiveRaceFetcher()