"""
ViewLogicデータマネージャー
展開予想用ナレッジファイルの管理とアクセスを提供
"""

import json
import os
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ViewLogicDataManager:
    """ViewLogicナレッジファイルの管理クラス"""
    
    def __init__(self):
        self.knowledge_data = None
        self.horses_dict = {}  # 馬名でアクセスするための辞書
        self.last_updated = None
        self.cache_ttl = timedelta(hours=24)  # 24時間キャッシュ
        # 統合ナレッジファイルを使用（2025-09-03更新版）
        self.cdn_url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json"
        self.local_cache_path = "/tmp/unified_knowledge_cache.json"
        
        # 初期化時にデータをロード
        self.load_knowledge()
    
    def load_knowledge(self) -> bool:
        """ナレッジファイルをロード"""
        try:
            # キャッシュをチェック
            if self._is_cache_valid():
                logger.info("ViewLogicナレッジをキャッシュから読み込み中...")
                return self._load_from_cache()
            
            # CDNからダウンロード
            logger.info("ViewLogicナレッジをCDNから取得中...")
            return self._download_from_cdn()
            
        except Exception as e:
            logger.error(f"ViewLogicナレッジファイルの読み込みエラー: {e}")
            # フォールバック: ローカルファイルから読み込み
            return self._load_from_local()
    
    def _is_cache_valid(self) -> bool:
        """キャッシュが有効かチェック"""
        if not os.path.exists(self.local_cache_path):
            return False
        
        # ファイルの更新時刻をチェック
        file_time = datetime.fromtimestamp(os.path.getmtime(self.local_cache_path))
        return datetime.now() - file_time < self.cache_ttl
    
    def _load_from_cache(self) -> bool:
        """キャッシュから読み込み"""
        try:
            with open(self.local_cache_path, 'r', encoding='utf-8') as f:
                self.knowledge_data = json.load(f)
            self._build_horses_dict()
            self.last_updated = datetime.now()
            logger.info(f"キャッシュから{len(self.horses_dict)}頭のデータを読み込みました")
            return True
        except Exception as e:
            logger.error(f"キャッシュ読み込みエラー: {e}")
            return False
    
    def _download_from_cdn(self) -> bool:
        """CDNからダウンロード"""
        try:
            response = requests.get(self.cdn_url, timeout=60)
            response.raise_for_status()
            
            self.knowledge_data = response.json()
            
            # キャッシュに保存
            try:
                with open(self.local_cache_path, 'w', encoding='utf-8') as f:
                    json.dump(self.knowledge_data, f)
                logger.info("CDNからのデータをキャッシュに保存しました")
            except Exception as e:
                logger.warning(f"キャッシュ保存エラー（処理は継続）: {e}")
            
            self._build_horses_dict()
            self.last_updated = datetime.now()
            logger.info(f"CDNから{len(self.horses_dict)}頭のデータを取得しました")
            return True
            
        except Exception as e:
            logger.error(f"CDNからのダウンロードエラー: {e}")
            return False
    
    def _load_from_local(self) -> bool:
        """ローカルファイルから読み込み（フォールバック）"""
        try:
            local_path = os.path.join(
                os.path.dirname(__file__), 
                '../data/unified_knowledge_20250903.json'
            )
            
            if not os.path.exists(local_path):
                logger.error("ローカルのViewLogicナレッジファイルが見つかりません")
                return False
            
            with open(local_path, 'r', encoding='utf-8') as f:
                self.knowledge_data = json.load(f)
            
            self._build_horses_dict()
            self.last_updated = datetime.now()
            logger.info(f"ローカルファイルから{len(self.horses_dict)}頭のデータを読み込みました")
            return True
            
        except Exception as e:
            logger.error(f"ローカルファイル読み込みエラー: {e}")
            return False
    
    def _build_horses_dict(self):
        """馬名でアクセスできる辞書を構築"""
        self.horses_dict = {}
        
        if not self.knowledge_data or 'horses' not in self.knowledge_data:
            return
        
        horses_data = self.knowledge_data['horses']
        
        # 統合ナレッジファイル形式 {馬名: {races: [...]}} の場合
        if isinstance(horses_data, dict):
            for horse_name, horse_data in horses_data.items():
                if isinstance(horse_data, dict):
                    # 統合形式: horse_nameをデータに追加
                    horse_data['horse_name'] = horse_name
                    self.horses_dict[horse_name] = horse_data
        
        # 従来のViewLogic形式 [{horse_name: ..., races: ...}, ...] の場合
        elif isinstance(horses_data, list):
            for horse_data in horses_data:
                if 'horse_name' in horse_data:
                    self.horses_dict[horse_data['horse_name']] = horse_data
    
    def get_horse_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """指定した馬のデータを取得"""
        return self.horses_dict.get(horse_name)
    
    def get_multiple_horses_data(self, horse_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """複数の馬のデータを取得"""
        result = {}
        for horse_name in horse_names:
            result[horse_name] = self.get_horse_data(horse_name)
        return result
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """メタデータを取得"""
        if self.knowledge_data and 'metadata' in self.knowledge_data:
            return self.knowledge_data['metadata']
        return None
    
    def get_running_style_distribution(self) -> Dict[str, int]:
        """脚質分布を取得"""
        distribution = {
            '逃げ': 0,
            '先行': 0,
            '中団': 0,
            '後方': 0,
            '不明': 0
        }
        
        for horse_data in self.horses_dict.values():
            if 'running_style' in horse_data and 'style' in horse_data['running_style']:
                style = horse_data['running_style']['style']
                if style in distribution:
                    distribution[style] += 1
                else:
                    distribution['不明'] += 1
        
        return distribution
    
    def is_loaded(self) -> bool:
        """データがロード済みかチェック"""
        return bool(self.horses_dict)
    
    def get_total_horses(self) -> int:
        """総馬数を取得"""
        return len(self.horses_dict)


# グローバルインスタンス（シングルトン）
_viewlogic_data_manager_instance = None


def get_viewlogic_data_manager() -> ViewLogicDataManager:
    """ViewLogicDataManagerのシングルトンインスタンスを取得"""
    global _viewlogic_data_manager_instance
    if _viewlogic_data_manager_instance is None:
        _viewlogic_data_manager_instance = ViewLogicDataManager()
    return _viewlogic_data_manager_instance
