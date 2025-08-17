import os
import json
import requests
from typing import Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class JockeyDataManager:
    """騎手ナレッジデータの管理クラス"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.knowledge_file = self.data_dir / "jockey_knowledge.json"
        self.jockey_knowledge: Dict[str, Any] = {}
        self.load_knowledge()
    
    def load_knowledge(self) -> None:
        """騎手ナレッジデータを読み込む"""
        try:
            # ローカルファイルが存在しない場合はダウンロード
            if not self.knowledge_file.exists():
                logger.info("騎手ナレッジファイルが見つかりません。CDNからダウンロードします...")
                self.download_knowledge_from_cdn()
            
            # ファイルを読み込む
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                self.jockey_knowledge = json.load(f)
                logger.info(f"騎手ナレッジデータを読み込みました: {len(self.jockey_knowledge)}騎手")
        
        except Exception as e:
            logger.error(f"騎手ナレッジデータの読み込みに失敗しました: {e}")
            self.jockey_knowledge = {}
    
    def download_knowledge_from_cdn(self) -> None:
        """CDNから騎手ナレッジファイルをダウンロード"""
        cdn_url = "https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/jockey_knowledge.json"
        
        try:
            logger.info(f"CDNからダウンロード中: {cdn_url}")
            
            # ストリーミングダウンロード（大きなファイル対応）
            response = requests.get(cdn_url, stream=True)
            response.raise_for_status()
            
            # データディレクトリが存在しない場合は作成
            self.data_dir.mkdir(exist_ok=True)
            
            # ファイルに書き込む
            with open(self.knowledge_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info("騎手ナレッジファイルのダウンロードが完了しました")
            
        except Exception as e:
            logger.error(f"CDNからのダウンロードに失敗しました: {e}")
            raise
    
    def get_jockey_data(self, jockey_name: str) -> Optional[Dict[str, Any]]:
        """指定された騎手のデータを取得"""
        return self.jockey_knowledge.get(jockey_name)
    
    def calculate_venue_aptitude(self, jockey_name: str, venue: str) -> float:
        """騎手の開催場適性を計算"""
        jockey_data = self.get_jockey_data(jockey_name)
        if not jockey_data:
            return 0.0
        
        venue_stats = jockey_data.get('venue_course_stats', {})
        venue_data = venue_stats.get(venue, {})
        
        if not venue_data or venue_data.get('total_races', 0) == 0:
            return 0.0
        
        # 複勝率を基準に適性スコアを計算（-10～+10）
        fukusho_rate = venue_data.get('fukusho_rate', 0) / 100  # パーセントを小数に
        # 複勝率30%を基準（0点）として計算
        aptitude_score = (fukusho_rate - 0.3) * 20
        
        return max(-10, min(10, aptitude_score))  # -10～+10の範囲に制限
    
    def calculate_post_position_aptitude(self, jockey_name: str, post: int) -> float:
        """騎手の枠順適性を計算"""
        jockey_data = self.get_jockey_data(jockey_name)
        if not jockey_data:
            return 0.0
        
        post_stats = jockey_data.get('post_position_stats', {})
        post_data = post_stats.get(str(post), {})
        
        if not post_data or post_data.get('total_races', 0) == 0:
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

# グローバルインスタンス
jockey_manager = JockeyDataManager()