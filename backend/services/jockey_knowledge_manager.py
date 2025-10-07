"""
騎手ナレッジファイルマネージャー
jockey_knowledge.jsonからデータを取得・管理
"""

import json
import os
import logging
import requests
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class JockeyKnowledgeManager:
    """騎手ナレッジファイルの管理クラス"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.jockey_data = {}
            self.last_updated = None
            self.cache_ttl = timedelta(hours=24)
            self.cdn_url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json"
            self.local_cache_path = "/tmp/jockey_knowledge_cache.json"
            self.initialized = True
            
            # 初期化時にデータをロード
            self.load_knowledge()
    
    def load_knowledge(self) -> bool:
        """騎手ナレッジファイルをロード"""
        try:
            # キャッシュをチェック
            if self._is_cache_valid():
                logger.info("騎手ナレッジをキャッシュから読み込み中...")
                if self._load_from_cache():
                    return True
                logger.warning("キャッシュ読み込みに失敗。CDNからの取得を試みます。")
            
            # CDNからダウンロード
            logger.info("騎手ナレッジをCDNから取得中...")
            if self._download_from_cdn():
                return True

            logger.warning("CDNからの取得に失敗。ローカルファイルにフォールバックします。")
            return self._load_from_local()
            
        except Exception as e:
            logger.error(f"騎手ナレッジファイルの読み込みエラー: {e}")
            return self._load_from_local()
    
    def _is_cache_valid(self) -> bool:
        """キャッシュが有効かチェック"""
        if not os.path.exists(self.local_cache_path):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(self.local_cache_path))
        return datetime.now() - file_time < self.cache_ttl
    
    def _load_from_cache(self) -> bool:
        """キャッシュから読み込み"""
        try:
            with open(self.local_cache_path, 'r', encoding='utf-8') as f:
                self.jockey_data = json.load(f)
            self.last_updated = datetime.now()
            logger.info(f"キャッシュから{len(self.jockey_data)}騎手のデータを読み込みました")
            return True
        except Exception as e:
            logger.error(f"キャッシュ読み込みエラー: {e}")
            return False
    
    def _download_from_cdn(self) -> bool:
        """CDNからダウンロード"""
        try:
            response = requests.get(self.cdn_url, timeout=60)
            response.raise_for_status()
            
            self.jockey_data = response.json()
            
            # キャッシュに保存
            try:
                with open(self.local_cache_path, 'w', encoding='utf-8') as f:
                    json.dump(self.jockey_data, f)
                logger.info("騎手データをキャッシュに保存しました")
            except Exception as e:
                logger.warning(f"キャッシュ保存エラー（処理は継続）: {e}")
            
            self.last_updated = datetime.now()
            logger.info(f"CDNから{len(self.jockey_data)}騎手のデータを取得しました")
            return True
            
        except Exception as e:
            logger.error(f"CDNからのダウンロードエラー: {e}")
            return False
    
    def _load_from_local(self) -> bool:
        """ローカルファイルから読み込み（フォールバック）"""
        try:
            local_path = os.path.join(
                os.path.dirname(__file__), 
                '../data/jockey_knowledge.json'
            )
            
            if os.path.exists(local_path):
                with open(local_path, 'r', encoding='utf-8') as f:
                    self.jockey_data = json.load(f)
                self.last_updated = datetime.now()
                logger.info(f"ローカルから{len(self.jockey_data)}騎手のデータを読み込みました")
                return True
            else:
                logger.warning("ローカルファイルが見つかりません")
                return False
                
        except Exception as e:
            logger.error(f"ローカルファイル読み込みエラー: {e}")
            return False
    
    def get_jockey_data(self, jockey_name: str) -> Optional[Dict[str, Any]]:
        """騎手のデータを取得"""
        data = self.jockey_data.get(jockey_name)
        # データが辞書でない場合はNoneを返す
        if data is not None and not isinstance(data, dict):
            logger.error(f"騎手 {jockey_name} のデータが辞書でない: {type(data)} = {data}")
            return None
        return data
    
    def get_post_position_stats(self, jockey_name: str) -> Optional[Dict[str, Any]]:
        """騎手の枠順別統計を取得"""
        jockey = self.get_jockey_data(jockey_name)
        if jockey and isinstance(jockey, dict):
            return jockey.get('post_position_stats', {})
        return None
    
    def get_jockey_post_position_fukusho_rates(self, jockey_names: list) -> Dict[str, Dict]:
        """複数騎手の枠順別複勝率を取得"""
        result = {}
        
        for jockey_name in jockey_names:
            post_stats = self.get_post_position_stats(jockey_name)
            if post_stats and isinstance(post_stats, dict):
                # 内枠、中枠、外枠に集約
                aggregated = {
                    '内枠（1-6）': {'fukusho_rate': 0, 'race_count': 0},
                    '中枠（7-12）': {'fukusho_rate': 0, 'race_count': 0},
                    '外枠（13-18）': {'fukusho_rate': 0, 'race_count': 0}
                }
                
                for waku_str, stats in post_stats.items():
                    # 枠番号を抽出（例: "枠4" -> 4）
                    try:
                        waku_num = int(waku_str.replace('枠', ''))
                        if 1 <= waku_num <= 3:
                            category = '内枠（1-6）'
                        elif 4 <= waku_num <= 6:
                            category = '中枠（7-12）'
                        else:
                            category = '外枠（13-18）'
                        
                        # 重み付き平均を計算
                        # statsが辞書でない場合（整数など）の対応
                        if not isinstance(stats, dict):
                            logger.error(f"騎手 {jockey_name} 枠 {waku_str} のデータが辞書でない: {type(stats)} = {stats}")
                            logger.error(f"post_stats全体: {post_stats}")
                            continue
                        race_count = stats.get('race_count', 0)
                        fukusho_rate = stats.get('fukusho_rate', 0)
                        
                        prev_count = aggregated[category]['race_count']
                        prev_rate = aggregated[category]['fukusho_rate']
                        
                        total_count = prev_count + race_count
                        if total_count > 0:
                            aggregated[category]['fukusho_rate'] = (
                                (prev_rate * prev_count + fukusho_rate * race_count) / total_count
                            )
                            # 実際の総レース数を保存（騎手ナレッジの実データに基づく）
                            aggregated[category]['race_count'] = total_count
                    except (ValueError, AttributeError, TypeError) as e:
                        logger.warning(f"騎手 {jockey_name} の枠順データ処理エラー: {e}, waku_str={waku_str}, stats={stats}")
                        continue
                
                result[jockey_name] = aggregated
        
        return result
    
    def is_loaded(self) -> bool:
        """データがロードされているか確認"""
        return len(self.jockey_data) > 0
    
    def get_total_jockeys(self) -> int:
        """騎手総数を取得"""
        return len(self.jockey_data)


# シングルトンインスタンスを取得する関数
def get_jockey_knowledge_manager() -> JockeyKnowledgeManager:
    """騎手ナレッジマネージャーのインスタンスを取得"""
    return JockeyKnowledgeManager()