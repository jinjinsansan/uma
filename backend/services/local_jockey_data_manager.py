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
        # キャッシュファイルパス（Renderでは/tmpを使用）
        if os.environ.get('RENDER'):
            self.cache_file = '/tmp/local_jockey_knowledge.json'
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
        
        # CDNからダウンロード（ストリーミング対応）
        try:
            print(f"📥 地方騎手データをCDNからダウンロード開始: {cdn_url}")
            response = requests.get(cdn_url, stream=True, timeout=300)
            
            if response.status_code == 200:
                print("🔄 JSONパース中...")
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
    
    def is_loaded(self) -> bool:
        """データがロードされているか確認"""
        return bool(self.knowledge_data and self.knowledge_data.get('jockeys'))

# グローバルインスタンス
local_jockey_manager = LocalJockeyDataManager()