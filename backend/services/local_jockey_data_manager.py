#!/usr/bin/env python3
"""
地方競馬版騎手データマネージャー
南関東騎手専用
"""
import json
import os
import logging
import threading
import datetime
from collections import OrderedDict
from typing import Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)

class LocalJockeyDataManager:
    """地方競馬版騎手データ管理クラス"""
    
    def __init__(self):
        """初期化"""
        # キャッシュファイルパス（Renderでは/tmpを使用）
        base_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        if os.environ.get('RENDER'):
            base_dir = '/tmp'

        self.cache_file = os.path.join(base_dir, 'local_jockey_knowledge.json')
        self.cache_dir = os.path.join(base_dir, 'local_jockey_cache')
        self.index_file = os.path.join(self.cache_dir, 'index.json')
        self._jockey_index: Dict[str, Dict[str, str]] = {}
        self._meta_info: Dict[str, Any] = {}
        self._shard_cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self._shard_lock = threading.Lock()
        self._max_shard_cache = int(os.environ.get("LOCAL_JOCKEY_SHARD_CACHE", "4"))
        self._shard_size = int(os.environ.get("LOCAL_JOCKEY_SHARD_SIZE", "250"))
        self._download_timeout = int(os.environ.get("LOCAL_JOCKEY_DOWNLOAD_TIMEOUT", "180"))

        self._knowledge_data: Optional[Dict[str, Any]] = None
        self._load_lock = threading.Lock()
        self._last_loaded_at: Optional[datetime.datetime] = None

        logger.info("🏇 地方騎手ナレッジ初期化: cache=%s", self.cache_file)
    
    def _write_full_cache(self, data: Dict[str, Any]):
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.warning("⚠️ 地方騎手ナレッジ: フルキャッシュ保存失敗 (%s)", e)

    def _shard_filename(self, shard_id: int) -> str:
        return f"shard_{shard_id:05d}.json"

    def _write_shard(self, shard_id: int, shard_data: Dict[str, Any]):
        os.makedirs(self.cache_dir, exist_ok=True)
        shard_path = os.path.join(self.cache_dir, self._shard_filename(shard_id))
        with open(shard_path, 'w', encoding='utf-8') as f:
            json.dump(shard_data, f, ensure_ascii=False)

    def _save_sharded_cache(self, data: Dict[str, Any]):
        jockeys = data.get('jockeys', {})
        if not jockeys:
            return

        os.makedirs(self.cache_dir, exist_ok=True)

        for entry in os.listdir(self.cache_dir):
            if entry.endswith('.json'):
                try:
                    os.remove(os.path.join(self.cache_dir, entry))
                except OSError:
                    logger.warning("⚠️ 地方騎手ナレッジ: 古いシャード削除に失敗 (%s)", entry)

        index: Dict[str, Dict[str, str]] = {}
        shard: Dict[str, Any] = {}
        shard_id = 0
        count = 0

        for jockey_name, payload in jockeys.items():
            if count > 0 and count % self._shard_size == 0:
                self._write_shard(shard_id, shard)
                shard_id += 1
                shard = {}
            shard[jockey_name] = payload
            index[jockey_name] = {"file": self._shard_filename(shard_id)}
            count += 1

        if shard:
            self._write_shard(shard_id, shard)

        index_content = {
            "meta": data.get('meta', {}),
            "generated_at": datetime.datetime.now().isoformat(),
            "shard_count": shard_id + 1,
            "jockeys": index
        }

        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index_content, f, ensure_ascii=False)

        self._jockey_index = index
        self._meta_info = index_content.get('meta', {})

    def _load_index(self) -> bool:
        if not os.path.exists(self.index_file):
            return False
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            jockeys = index_data.get('jockeys', {})
            if not jockeys:
                return False
            self._jockey_index = jockeys
            self._meta_info = index_data.get('meta', {})
            logger.info("📂 地方騎手ナレッジ: シャードインデックス読込 (%s騎手)", len(self._jockey_index))
            return True
        except Exception as e:
            logger.warning("⚠️ 地方騎手ナレッジ: シャードインデックス読込失敗 (%s)", e)
            return False

    def _load_shard(self, shard_file: str) -> Dict[str, Any]:
        with self._shard_lock:
            if shard_file in self._shard_cache:
                self._shard_cache.move_to_end(shard_file)
                return self._shard_cache[shard_file]

            shard_path = os.path.join(self.cache_dir, shard_file)
            try:
                with open(shard_path, 'r', encoding='utf-8') as f:
                    shard_data = json.load(f)
            except FileNotFoundError:
                logger.warning("⚠️ 地方騎手ナレッジ: シャード %s が見つかりません。再構築を試みます", shard_file)
                self._knowledge_data = None
                self._jockey_index = {}
                self._meta_info = {}
                self._shard_cache.clear()
                if os.path.exists(self.cache_file):
                    data = self._load_knowledge()
                    self._knowledge_data = data
                    self._last_loaded_at = datetime.datetime.now()
                    if not self._jockey_index:
                        self._load_index()
                    return self._load_shard(shard_file)
                raise

            self._shard_cache[shard_file] = shard_data
            self._shard_cache.move_to_end(shard_file)
            if len(self._shard_cache) > self._max_shard_cache:
                self._shard_cache.popitem(last=False)
            return shard_data

    def _get_jockey_entry(self, jockey_name: str) -> Optional[Dict[str, Any]]:
        self._ensure_loaded()
        if self._knowledge_data is not None:
            return self._knowledge_data.get('jockeys', {}).get(jockey_name)

        shard_info = self._jockey_index.get(jockey_name)
        if not shard_info:
            return None

        shard_file = shard_info.get('file')
        if not shard_file:
            return None

        shard_data = self._load_shard(shard_file)
        return shard_data.get(jockey_name)

    def _load_knowledge(self) -> Dict[str, Any]:
        """騎手ナレッジファイル読み込み"""
        # CDN URL
        cdn_url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_jockey_knowledge_20250907.json"
        
        # キャッシュファイルがあれば読み込み
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict) and 'jockeys' not in data and len(data) > 0:
                    if list(data.keys())[0] not in ['jockeys', 'meta']:
                        logger.info("✅ 地方騎手ナレッジ: キャッシュ読み込み (%s騎手)", len(data))
                        wrapped = {"jockeys": data}
                        self._save_sharded_cache(wrapped)
                        return wrapped
                elif 'jockeys' in data:
                    logger.info("✅ 地方騎手ナレッジ: キャッシュ読み込み (%s騎手)", len(data['jockeys']))
                    self._save_sharded_cache(data)
                    return data
            except Exception as e:
                logger.warning("⚠️ 地方騎手ナレッジ: キャッシュ読み込みエラー (%s)", e)
        
        # CDNからダウンロード（ストリーミング対応）
        try:
            logger.info("📥 地方騎手ナレッジ: CDNダウンロード開始 (%s)", cdn_url)
            response = requests.get(cdn_url, stream=True, timeout=(10, self._download_timeout))

            if response.status_code == 200:
                logger.info("🔄 地方騎手ナレッジ: JSONパース中")
                data = response.json()

                if isinstance(data, dict) and 'jockeys' not in data:
                    jockey_count = len(data)
                    logger.info("✅ 地方騎手ナレッジ: ダウンロード完了 (%s騎手)", jockey_count)

                    wrapped_data = {"jockeys": data}

                    try:
                        self._write_full_cache(wrapped_data)
                        self._save_sharded_cache(wrapped_data)
                        logger.info("💾 地方騎手ナレッジ: キャッシュ保存完了")
                    except Exception as e:
                        logger.warning("⚠️ 地方騎手ナレッジ: キャッシュ保存失敗 (%s)", e)

                    return wrapped_data

                jockey_count = len(data.get('jockeys', {}))
                logger.info("✅ 地方騎手ナレッジ: ダウンロード完了 (%s騎手)", jockey_count)
                self._write_full_cache(data)
                self._save_sharded_cache(data)
                return data

            logger.error("❌ 地方騎手ナレッジ: ダウンロード失敗 HTTP %s", response.status_code)
        except Exception as e:
            logger.error("❌ 地方騎手ナレッジ: ダウンロードエラー (%s)", e)
        
        # フォールバック
        logger.warning("⚠️ 地方騎手ナレッジ: 取得失敗のため空データで初期化")
        return {"jockeys": {}}
    
    def _ensure_loaded(self):
        if self._knowledge_data is not None:
            return

        with self._load_lock:
            if self._knowledge_data is not None:
                return

            if self._load_index():
                self._last_loaded_at = datetime.datetime.now()
                logger.info("✅ 地方騎手ナレッジ: インデックスのみロード完了 (%s騎手)", len(self._jockey_index))
                return

            data = self._load_knowledge()
            self._knowledge_data = data
            self._last_loaded_at = datetime.datetime.now()

            jockey_count = len(data.get('jockeys', {}))
            logger.info("✅ 地方騎手ナレッジ: フルデータロード完了 (%s騎手)", jockey_count)

            if not self._jockey_index:
                self._load_index()

    @property
    def knowledge_data(self) -> Dict[str, Any]:
        self._ensure_loaded()
        if self._knowledge_data is None and self._jockey_index:
            logger.debug("地方騎手ナレッジ: シャードからインメモリデータを構築しています")
            jockeys: Dict[str, Any] = {}
            loaded_files = set()
            for info in self._jockey_index.values():
                shard_file = info.get('file')
                if not shard_file or shard_file in loaded_files:
                    continue
                shard_data = self._load_shard(shard_file)
                jockeys.update(shard_data)
                loaded_files.add(shard_file)

            self._knowledge_data = {
                "meta": self._meta_info,
                "jockeys": jockeys
            }

        return self._knowledge_data or {"jockeys": {}}

    def get_jockey_score(self, jockey_name: str) -> float:
        """騎手スコア取得"""
        jockey_data = self._get_jockey_entry(jockey_name)
        if jockey_data:
            return jockey_data.get('avg_score', 50.0)
        return 50.0  # デフォルト値
    
    def get_jockey_data(self, jockey_name: str) -> Optional[Dict[str, Any]]:
        """騎手データを取得"""
        return self._get_jockey_entry(jockey_name)
    
    def calculate_venue_aptitude(self, jockey_name: str, venue: str) -> float:
        """騎手の開催場適性を計算"""
        jockey_data = self.get_jockey_data(jockey_name)
        if not jockey_data:
            return 0.0
        
        venue_stats = jockey_data.get('venue_course_stats', {})
        
        # 開催場名を含むすべてのキーを集計
        total_races = 0
        total_fukusho = 0
        
        for key, stats in venue_stats.items():
            if venue in key:  # 「川崎」が「川崎_1500m」にマッチ
                race_count = stats.get('race_count', 0)
                if race_count > 0:
                    total_races += race_count
                    fukusho_rate = stats.get('fukusho_rate', 0)
                    total_fukusho += (fukusho_rate * race_count / 100)
        
        if total_races == 0:
            return 0.0
        
        # 総合複勝率を計算
        overall_fukusho_rate = total_fukusho / total_races
        
        # 複勝率30%を基準（0点）として計算（-10～+10）
        aptitude_score = (overall_fukusho_rate - 0.3) * 20
        
        return max(-10, min(10, aptitude_score))  # -10～+10の範囲に制限
    
    def calculate_post_position_aptitude(self, jockey_name: str, post: int) -> float:
        """騎手の枠順適性を計算"""
        jockey_data = self.get_jockey_data(jockey_name)
        if not jockey_data:
            return 0.0
        
        post_stats = jockey_data.get('post_position_stats', {})
        # 「枠1」形式のキーに対応
        post_key = f'枠{post}'
        post_data = post_stats.get(post_key, {})
        
        # race_countまたはtotal_racesをチェック
        race_count = post_data.get('race_count', post_data.get('total_races', 0))
        if not post_data or race_count == 0:
            return 0.0
        
        # 複勝率を基準に適性スコアを計算
        fukusho_rate = post_data.get('fukusho_rate', 0) / 100
        aptitude_score = (fukusho_rate - 0.3) * 15  # 枠順の影響は少し小さめ
        
        return max(-7.5, min(7.5, aptitude_score))
    
    def calculate_sire_aptitude(self, jockey_name: str, sire: str) -> float:
        """騎手の種牡馬適性を計算"""
        jockey_data = self.get_jockey_data(jockey_name)
        if not jockey_data:
            return 0.0
        
        sire_stats = jockey_data.get('sire_stats', {})
        sire_data = sire_stats.get(sire, {})
        
        if not sire_data or sire_data.get('total_races', 0) == 0:
            return 0.0
        
        # 複勝率を基準に適性スコアを計算
        fukusho_rate = sire_data.get('fukusho_rate', 0) / 100
        aptitude_score = (fukusho_rate - 0.3) * 15
        
        return max(-7.5, min(7.5, aptitude_score))
    
    def calculate_jockey_score(self, jockey_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """騎手の総合スコアを計算"""
        # 騎手データの存在確認
        jockey_data = self.get_jockey_data(jockey_name)
        if not jockey_data:
            logger.warning(f"騎手データが見つかりません: {jockey_name}")
        
        venue_score = self.calculate_venue_aptitude(jockey_name, context.get('venue', ''))
        post_score = self.calculate_post_position_aptitude(jockey_name, context.get('post', 1))
        sire_score = self.calculate_sire_aptitude(jockey_name, context.get('sire', ''))
        
        total_score = venue_score + post_score + sire_score
        
        return {
            'total_score': round(total_score, 1),
            'venue_score': round(venue_score, 1),
            'post_score': round(post_score, 1),
            'sire_score': round(sire_score, 1),
            'breakdown': {
                'venue': f"{venue_score:+.1f}",
                'post_position': f"{post_score:+.1f}",
                'sire': f"{sire_score:+.1f}"
            }
        }
    
    def get_jockey_post_position_fukusho_rates(self, jockey_names: list) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        騎手の枠順別複勝率を取得（地方競馬版）
        
        Args:
            jockey_names: 騎手名のリスト
        
        Returns:
            {騎手名: {カテゴリ: {'fukusho_rate': 複勝率, 'race_count': レース数}}}
            地方競馬用カテゴリ: '内枠（1-3）', '中枠（4-6）', '外枠（7-8）'
        """
        result = {}
        
        for jockey_name in jockey_names:
            jockey_data = self.get_jockey_data(jockey_name)
            
            if not jockey_data or 'post_position_stats' not in jockey_data:
                # データがない場合はデフォルト値
                result[jockey_name] = {
                    '内枠（1-3）': {'fukusho_rate': 0.0, 'race_count': 0},
                    '中枠（4-6）': {'fukusho_rate': 0.0, 'race_count': 0},
                    '外枠（7-8）': {'fukusho_rate': 0.0, 'race_count': 0}
                }
                continue
            
            post_stats = jockey_data['post_position_stats']
            
            # カテゴリ別に集計（地方競馬は1-8枠）
            categories = {
                '内枠（1-3）': [f'枠{i}' for i in range(1, 4)],
                '中枠（4-6）': [f'枠{i}' for i in range(4, 7)],
                '外枠（7-8）': [f'枠{i}' for i in range(7, 9)]
            }
            
            jockey_result = {}
            for category, post_keys in categories.items():
                total_races = 0
                fukusho_count = 0
                
                for post_key in post_keys:
                    if post_key in post_stats:
                        stats = post_stats[post_key]
                        race_count = stats.get('race_count', 0)
                        fukusho_rate = stats.get('fukusho_rate', 0)
                        
                        total_races += race_count
                        fukusho_count += int(race_count * fukusho_rate / 100)
                
                # 複勝率を計算
                if total_races > 0:
                    category_fukusho_rate = round((fukusho_count / total_races) * 100, 1)
                else:
                    category_fukusho_rate = 0.0
                
                jockey_result[category] = {
                    'fukusho_rate': category_fukusho_rate,
                    'race_count': total_races
                }
            
            result[jockey_name] = jockey_result
        
        return result
    
    def is_loaded(self) -> bool:
        """データがロードされているか確認"""
        return bool(self.knowledge_data and self.knowledge_data.get('jockeys'))

# グローバルインスタンス
local_jockey_manager = LocalJockeyDataManager()
