"""
拡張ナレッジデータマネージャー
レース分析V2用の拡張データを管理
"""
import json
import os
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ExtendedKnowledgeManager:
    """拡張ナレッジデータの管理クラス"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        # 統合ナレッジファイルを使用
        self.knowledge_file = self.data_dir / "unified_knowledge_20250903.json"
        self.knowledge_data: Dict[str, Any] = {}
        self.is_loaded = False
        # CloudflareのCDN URL（統合ナレッジファイル用）
        self.cdn_url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/unified_knowledge_20250903.json"
        self._load_knowledge()
    
    def _load_knowledge(self) -> None:
        """拡張ナレッジデータを読み込む"""
        try:
            # ローカルファイルが存在しない場合はダウンロード
            if not self.knowledge_file.exists():
                logger.info("拡張ナレッジファイルが見つかりません。CDNからダウンロードします...")
                self._download_from_cdn()
            
            # ファイルを読み込む
            if self.knowledge_file.exists():
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    # データ構造を確認して適切に処理
                    if isinstance(raw_data, dict) and 'horses' in raw_data:
                        # 旧形式: {"horses": {...}}
                        self.knowledge_data = raw_data
                    else:
                        # 新形式: 馬名が直接キー
                        self.knowledge_data = {'horses': raw_data}
                    
                    horse_count = len(self.knowledge_data.get('horses', {}))
                    logger.info(f"拡張ナレッジデータを読み込みました: {horse_count}頭")
                    self.is_loaded = True
            else:
                logger.warning("拡張ナレッジファイルの読み込みに失敗しました")
                self.knowledge_data = {'horses': {}}
        
        except Exception as e:
            logger.error(f"拡張ナレッジデータの読み込みエラー: {e}")
            self.knowledge_data = {'horses': {}}
    
    def _download_from_cdn(self) -> None:
        """CDNから統合ナレッジファイルをダウンロード"""
        # 統合ナレッジファイルを使用（拡張データも含まれている）
        cdn_url = self.cdn_url  # unified_knowledge_20250903.json
        
        try:
            logger.info(f"CDNからダウンロード中: {cdn_url}")
            
            # ストリーミングダウンロード（大きなファイル対応）
            response = requests.get(cdn_url, stream=True, timeout=120)
            response.raise_for_status()
            
            # データディレクトリが存在しない場合は作成
            self.data_dir.mkdir(exist_ok=True)
            
            # ファイルに書き込む
            with open(self.knowledge_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"ダウンロード完了: {self.knowledge_file}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"CDNからのダウンロードに失敗しました: {e}")
            raise
        except Exception as e:
            logger.error(f"ファイル保存エラー: {e}")
            raise
    
    def get_horse_data(self, horse_name: str) -> Optional[Dict[str, Any]]:
        """馬のデータを取得"""
        if not self.is_loaded:
            self._load_knowledge()
        
        horses = self.knowledge_data.get('horses', {})
        return horses.get(horse_name)
    
    def get_all_horses(self) -> Dict[str, Any]:
        """全馬データを取得"""
        if not self.is_loaded:
            self._load_knowledge()
        
        return self.knowledge_data.get('horses', {})

# グローバルインスタンス（遅延初期化）
_extended_knowledge_manager_instance = None

def get_extended_knowledge_manager():
    """拡張ナレッジマネージャーのシングルトンインスタンスを取得"""
    global _extended_knowledge_manager_instance
    if _extended_knowledge_manager_instance is None:
        _extended_knowledge_manager_instance = ExtendedKnowledgeManager()
    return _extended_knowledge_manager_instance

# 互換性のため
extended_knowledge_manager = get_extended_knowledge_manager