#!/usr/bin/env python3
"""
地方競馬版騎手データマネージャー
南関東騎手専用
"""
import json
import os
import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class LocalJockeyDataManager:
    """地方競馬版騎手データ管理クラス"""
    
    def __init__(self):
        """初期化"""
        # キャッシュファイルパス
        if os.environ.get('RENDER'):
            self.cache_file = '/var/data/local_jockey_knowledge.json'
        else:
            self.cache_file = os.path.join(
                os.path.dirname(__file__), '..', 'data', 'local_jockey_knowledge.json'
            )
        
        # ナレッジデータ読み込み
        self.knowledge_data = self._load_knowledge()
        jockey_count = len(self.knowledge_data.get('jockeys', {}))
        print(f"🏇 地方競馬版騎手マネージャー初期化: {jockey_count}騎手")
    
    def _load_knowledge(self) -> Dict[str, Any]:
        """騎手ナレッジファイル読み込み"""
        # CDN URL
        cdn_url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/nankan_jockey_knowledge_20250907.json"
        
        # キャッシュファイルがあれば読み込み
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # データ構造を確認（騎手名が直接キーになっている場合）
                    if isinstance(data, dict) and 'jockeys' not in data and len(data) > 0:
                        # 既にラップされている場合はそのまま使用
                        if list(data.keys())[0] not in ['jockeys', 'meta']:
                            print(f"✅ 地方騎手キャッシュ読み込み: {len(data)}騎手")
                            return {"jockeys": data}
                    elif 'jockeys' in data:
                        print(f"✅ 地方騎手キャッシュ読み込み: {len(data['jockeys'])}騎手")
                        return data
            except Exception as e:
                print(f"⚠️ キャッシュ読み込みエラー: {e}")
        
        # CDNからダウンロード
        try:
            print("📥 地方騎手データをCDNからダウンロード中...")
            response = requests.get(cdn_url, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                
                # データ構造を確認（騎手名が直接キーになっている）
                if isinstance(data, dict) and 'jockeys' not in data:
                    jockey_count = len(data)
                    print(f"✅ ダウンロード完了: {jockey_count}騎手")
                    # jockeysキーでラップ
                    wrapped_data = {"jockeys": data}
                    
                    # キャッシュに保存（ラップした形式で）
                    try:
                        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
                        with open(self.cache_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False)  # 元の形式で保存
                        print(f"💾 キャッシュ保存完了")
                    except Exception as e:
                        print(f"⚠️ キャッシュ保存失敗: {e}")
                    
                    return wrapped_data
                else:
                    # 既にjockeysキーがある場合
                    jockey_count = len(data.get('jockeys', {}))
                    print(f"✅ ダウンロード完了: {jockey_count}騎手")
                    return data
            else:
                print(f"❌ ダウンロード失敗: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ ダウンロードエラー: {e}")
        
        # フォールバック
        return {"jockeys": {}}
    
    def get_jockey_score(self, jockey_name: str) -> float:
        """騎手スコア取得"""
        jockey_data = self.knowledge_data.get('jockeys', {}).get(jockey_name)
        if jockey_data:
            return jockey_data.get('avg_score', 50.0)
        return 50.0  # デフォルト値
    
    def get_jockey_data(self, jockey_name: str) -> Optional[Dict[str, Any]]:
        """騎手データを取得"""
        return self.knowledge_data.get('jockeys', {}).get(jockey_name)
    
    def calculate_jockey_score(self, jockey_name: str) -> float:
        """騎手スコア計算（I-Logic用）"""
        jockey_data = self.get_jockey_data(jockey_name)
        if not jockey_data:
            return 50.0
        
        # 統計データから総合スコアを計算
        stats = jockey_data.get('statistics', {})
        if stats:
            win_rate = stats.get('win_rate', 0)
            top3_rate = stats.get('top3_rate', 0)
            # 勝率と複勝率を組み合わせてスコア化
            score = (win_rate * 0.6 + top3_rate * 0.4) * 100 / 30  # 30%を100点とする
            return min(100, max(0, score))
        
        return jockey_data.get('avg_score', 50.0)
    
    def is_loaded(self) -> bool:
        """データがロードされているか確認"""
        return bool(self.knowledge_data and self.knowledge_data.get('jockeys'))

# グローバルインスタンス
local_jockey_manager = LocalJockeyDataManager()