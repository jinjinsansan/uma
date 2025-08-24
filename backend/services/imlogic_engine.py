"""
IMLogicエンジン
ILogic（レースアナリシス）のユーザーカスタマイズ版
馬と騎手の評価比率、12項目の重み付けを自由に設定可能
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class IMLogicEngine:
    """IMLogic計算エンジン（ILogicのカスタマイズ版）"""
    
    def __init__(self):
        """初期化"""
        # ILogicと同じナレッジファイルを使用
        try:
            # 拡張ナレッジマネージャー（馬データ：34,388頭）
            from .extended_knowledge_manager import get_extended_knowledge_manager
            self.extended_manager = get_extended_knowledge_manager()
            
            # 騎手データマネージャー（騎手データ：843騎手）
            from .jockey_data_manager import jockey_manager
            self.jockey_manager = jockey_manager
            
            # 騎手名の正規化用
            from .jockey_name_mapper import normalize_jockey_name
            self.normalize_jockey_name = normalize_jockey_name
            
            logger.info("IMLogicエンジンを初期化しました（ILogicナレッジ使用）")
        except Exception as e:
            logger.error(f"IMLogicエンジンの初期化エラー: {e}")
            raise RuntimeError(f"IMLogicエンジンの初期化に失敗しました: {e}")
    
    def analyze_race(
        self, 
        race_data: Dict[str, Any],
        horse_weight: int,
        jockey_weight: int,
        item_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        レースをIMLogic設定で分析
        
        Args:
            race_data: レースデータ（馬、騎手、枠順など）
            horse_weight: 馬の重み（0-100、10%単位）
            jockey_weight: 騎手の重み（0-100、10%単位）
            item_weights: 12項目の重み付け（合計100）
        
        Returns:
            分析結果
        """
        try:
            # 入力検証
            if horse_weight + jockey_weight != 100:
                raise ValueError(f"馬と騎手の重みの合計は100である必要があります（現在: {horse_weight + jockey_weight}）")
            
            # 12項目の合計チェック
            weights_sum = sum(item_weights.values())
            if not (99.9 <= weights_sum <= 100.1):
                raise ValueError(f"12項目の重みの合計は100である必要があります（現在: {weights_sum:.2f}）")
            
            # レース情報の準備
            context = {
                'venue': race_data.get('venue', ''),
                'grade': self._extract_grade(race_data.get('race_name', '')),
                'distance': race_data.get('distance', ''),
                'track_condition': race_data.get('track_condition', '良')
            }
            
            # 各馬の分析
            results = []
            horses = race_data.get('horses', [])
            jockeys = race_data.get('jockeys', [])
            posts = race_data.get('posts', [])
            horse_numbers = race_data.get('horse_numbers', [])
            
            for i in range(len(horses)):
                try:
                    horse_name = horses[i]
                    raw_jockey_name = jockeys[i] if i < len(jockeys) else ''
                    jockey_name = self.normalize_jockey_name(raw_jockey_name)
                    post = posts[i] if i < len(posts) else 1
                    horse_number = horse_numbers[i] if i < len(horse_numbers) else i + 1
                    
                    # 馬の評価（拡張ナレッジから）
                    horse_score = self._calculate_horse_score(
                        horse_name, 
                        context,
                        item_weights
                    )
                    
                    # 騎手の評価
                    jockey_context = {
                        'venue': context['venue'],
                        'post': post,
                        'sire': None  # 種牡馬情報（将来的に実装）
                    }
                    jockey_analysis = self.jockey_manager.calculate_jockey_score(
                        jockey_name,
                        jockey_context
                    )
                    jockey_score = jockey_analysis.get('total_score', 0)
                    
                    # 総合評価（カスタム比率）
                    total_score = (
                        horse_score * (horse_weight / 100.0) +
                        jockey_score * (jockey_weight / 100.0)
                    )
                    
                    results.append({
                        'rank': 0,  # 後でソート
                        'horse_number': horse_number,
                        'post': post,
                        'horse': horse_name,
                        'jockey': jockey_name,
                        'total_score': round(total_score, 2),
                        'horse_score': round(horse_score, 2),
                        'jockey_score': round(jockey_score, 2),
                        'horse_weight_pct': horse_weight,
                        'jockey_weight_pct': jockey_weight
                    })
                    
                except Exception as e:
                    logger.warning(f"馬 {horses[i]} の分析中にエラー: {e}")
                    # エラーが発生した馬はスキップ
                    continue
            
            # スコアで降順ソート
            results.sort(key=lambda x: x['total_score'], reverse=True)
            
            # ランク付け
            for idx, result in enumerate(results):
                result['rank'] = idx + 1
            
            return {
                'type': 'imlogic',
                'analysis_type': 'imlogic',
                'race_info': {
                    'venue': race_data.get('venue'),
                    'race_number': race_data.get('race_number'),
                    'race_name': race_data.get('race_name'),
                    'horses_count': len(horses)
                },
                'settings': {
                    'horse_weight': horse_weight,
                    'jockey_weight': jockey_weight,
                    'item_weights': item_weights
                },
                'results': results,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"IMLogic分析エラー: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"IMLogic分析に失敗しました: {e}")
    
    def _calculate_horse_score(
        self, 
        horse_name: str, 
        context: Dict[str, Any],
        item_weights: Dict[str, float]
    ) -> float:
        """
        馬のスコアを計算（拡張ナレッジ使用）
        
        Args:
            horse_name: 馬名
            context: レースコンテキスト
            item_weights: 12項目の重み付け
        
        Returns:
            馬のスコア（0-100）
        """
        try:
            # 拡張ナレッジから馬データを取得（リスト形式）
            races = self.extended_manager.get_horse_data(horse_name)
            
            if not races:
                logger.warning(f"馬データが見つかりません: {horse_name}")
                return 50.0  # デフォルトスコア
            
            # レースデータがリスト形式であることを確認
            if not isinstance(races, list) or len(races) == 0:
                return 50.0
            
            # 最新レースデータから各項目のスコアを計算
            recent_races = races[:5]  # 直近5走
            
            # デフォルトスコア
            base_scores = {
                '1_distance_aptitude': 70.0,
                '2_bloodline_evaluation': 75.0,  # 血統データなし
                '3_jockey_compatibility': 70.0,
                '4_trainer_evaluation': 70.0,
                '5_track_aptitude': 70.0,
                '6_weather_aptitude': 70.0,
                '7_popularity_factor': 70.0,
                '8_weight_impact': 70.0,
                '9_horse_weight_impact': 70.0,
                '10_corner_specialist': 70.0,
                '11_margin_analysis': 70.0,
                '12_time_index': 70.0
            }
            
            # 実際のレースデータから計算
            if recent_races:
                # 着順による基本評価
                avg_chakujun = sum(int(r.get('KAKUTEI_CHAKUJUN', '10')) for r in recent_races) / len(recent_races)
                if avg_chakujun <= 3:
                    base_adjustment = 85.0
                elif avg_chakujun <= 5:
                    base_adjustment = 75.0
                else:
                    base_adjustment = 65.0
                
                # 各項目をベース値から調整
                item_scores = {}
                for key in base_scores:
                    item_scores[key] = base_adjustment
            else:
                item_scores = base_scores
            
            # 重み付けを適用して総合スコアを計算
            total_score = 0.0
            for key, weight in item_weights.items():
                score = item_scores.get(key, 75.0)
                contribution = score * (weight / 100.0)
                total_score += contribution
            
            return min(100.0, max(0.0, total_score))
            
        except Exception as e:
            logger.error(f"馬スコア計算エラー: {e}")
            return 50.0
    
    def _calc_distance_score(self, races: List[Dict], distance: str) -> float:
        """距離適性スコア計算"""
        # 簡易実装
        return 75.0
    
    def _calc_bloodline_score(self, races: List[Dict]) -> float:
        """血統評価スコア計算"""
        # 簡易実装
        return 75.0
    
    def _calc_track_score(self, races: List[Dict], venue: str) -> float:
        """トラック適性スコア計算"""
        # 簡易実装
        return 75.0
    
    def _calc_weather_score(self, races: List[Dict], track_condition: str) -> float:
        """天候適性スコア計算"""
        # 簡易実装
        return 75.0
    
    def _calc_popularity_score(self, races: List[Dict]) -> float:
        """人気要因スコア計算"""
        # 簡易実装
        return 75.0
    
    def _calc_corner_score(self, races: List[Dict]) -> float:
        """コーナースペシャリスト度計算"""
        # 簡易実装
        return 75.0
    
    def _calc_margin_score(self, races: List[Dict]) -> float:
        """着差分析スコア計算"""
        # 簡易実装
        return 75.0
    
    def _calc_time_score(self, races: List[Dict]) -> float:
        """タイムインデックススコア計算"""
        # 簡易実装
        return 75.0
    
    def _extract_grade(self, race_name: str) -> str:
        """レース名からグレードを抽出"""
        if 'G1' in race_name or 'GⅠ' in race_name:
            return 'G1'
        elif 'G2' in race_name or 'GⅡ' in race_name:
            return 'G2'
        elif 'G3' in race_name or 'GⅢ' in race_name:
            return 'G3'
        else:
            return ''