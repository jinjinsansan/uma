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
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初期化"""
        # すでに初期化済みの場合はスキップ
        if IMLogicEngine._initialized:
            return
            
        # ILogicと同じナレッジファイルを使用
        try:
            # 騎手データマネージャー（騎手データ：843騎手）
            from services.jockey_data_manager import jockey_manager
            self.jockey_manager = jockey_manager
            
            # 騎手名の正規化用
            from services.jockey_name_mapper import normalize_jockey_name
            self.normalize_jockey_name = normalize_jockey_name
            
            # 標準D-Logicマネージャー（12項目計算用）
            # 注: DLogicRawDataManagerはグローバルインスタンスを使用
            from services.dlogic_raw_data_manager import dlogic_manager
            self.dlogic_manager = dlogic_manager
            
            # I-Logicエンジンは遅延初期化（必要時に作成）
            self._modern_engine = None
            
            # 初期化完了フラグを設定
            IMLogicEngine._initialized = True
            
            logger.info("IMLogicエンジンを初期化しました（ILogicナレッジ使用）")
        except Exception as e:
            logger.error(f"IMLogicエンジンの初期化エラー: {e}")
            raise RuntimeError(f"IMLogicエンジンの初期化に失敗しました: {e}")
    
    @property
    def modern_engine(self):
        """ModernDLogicEngineの遅延初期化"""
        if self._modern_engine is None:
            from services.fast_dlogic_engine import fast_engine_instance
            from services.modern_dlogic_engine import ModernDLogicEngine
            self._modern_engine = ModernDLogicEngine(fast_engine_instance)
            logger.info("ModernDLogicEngineを遅延初期化しました")
        return self._modern_engine
    
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
                    horse_score, has_data = self._calculate_horse_score(
                        horse_name, 
                        context,
                        item_weights
                    )
                    
                    # データがない馬も結果に含める
                    if not has_data:
                        logger.info(f"{horse_name}: ナレッジファイルにデータなし")
                        results.append({
                            'rank': 999,  # 最下位扱い
                            'horse_number': horse_number,
                            'post': post,
                            'horse': horse_name,
                            'jockey': jockey_name,
                            'total_score': None,  # スコアなし
                            'horse_score': None,
                            'jockey_score': None,
                            'horse_weight_pct': horse_weight,
                            'jockey_weight_pct': jockey_weight,
                            'data_status': 'no_data'  # データなしフラグ
                        })
                        continue
                    
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
                        'jockey_weight_pct': jockey_weight,
                        'data_status': 'ok'  # データありフラグ
                    })
                    
                except Exception as e:
                    logger.warning(f"馬 {horses[i]} の分析中にエラー: {e}")
                    # エラーが発生した馬はスキップ
                    continue
            
            # データがある馬とない馬を分離
            data_available = [r for r in results if r.get('data_status') == 'ok']
            data_not_available = [r for r in results if r.get('data_status') == 'no_data']
            
            # データがある馬をスコアで降順ソート
            data_available.sort(key=lambda x: x['total_score'], reverse=True)
            
            # ランク付け（データがある馬のみ）
            for idx, result in enumerate(data_available):
                result['rank'] = idx + 1
            
            # 結果を結合（データある馬 → データなし馬の順）
            results = data_available + data_not_available
            
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
    ) -> tuple[float, bool]:
        """
        馬のスコアを計算（I-Logicベース + 12項目カスタマイズ）
        
        Args:
            horse_name: 馬名
            context: レースコンテキスト
            item_weights: 12項目の重み付け
        
        Returns:
            (馬のスコア, データ有無) - スコアは0-150、データなしの場合は(0, False)
        """
        try:
            # Step 1: I-Logicエンジンで計算（拡張ナレッジ使用）
            ilogic_result = self.modern_engine.calculate_horse_score(
                horse_name=horse_name,
                context=context,
                enable_bayesian=True
            )
            
            # I-Logicの計算結果から各種情報を取得
            estimation_method = ilogic_result.get('estimation_method', 'unknown')
            data_confidence = ilogic_result.get('data_confidence', 'none')
            
            # データなしの馬はFalseを返す
            if estimation_method == 'default' and data_confidence == 'none':
                # 拡張ナレッジにデータがない場合、標準ナレッジも確認
                standard_knowledge = self.dlogic_manager.knowledge_data.get('horses', {})
                if horse_name not in standard_knowledge:
                    logger.info(f"{horse_name}: ナレッジファイルにデータが存在しません")
                    return 0, False
            
            base_score = ilogic_result.get('base_score', 50.0)  # イクイノックス基準
            venue_distance_bonus = ilogic_result.get('venue_distance_bonus', 0)
            track_bonus = ilogic_result.get('track_bonus', 0)
            class_factor = ilogic_result.get('class_factor', 1.0)
            d_logic_scores = ilogic_result.get('d_logic_scores', {})
            
            # d_logic_scoresが空の場合、拡張ナレッジから計算
            if not d_logic_scores:
                # 拡張ナレッジを使って12項目を計算
                horse_data = self.modern_engine.knowledge.get(horse_name, [])
                if isinstance(horse_data, list) and len(horse_data) >= 3:
                    # 簡易的に12項目を推定（I-Logicの内部計算を模倣）
                    d_logic_scores = self._estimate_12_items_from_races(horse_data)
                else:
                    # データ不足の場合はデフォルト値
                    d_logic_scores = {f'{i+1}_item': 50.0 for i in range(12)}
            
            # デバッグ：12項目スコアを確認
            logger.info(f"\n{horse_name} のI-Logic 12項目スコア:")
            logger.info(f"  ベーススコア: {base_score:.1f}点")
            logger.info(f"  開催場・距離ボーナス: {venue_distance_bonus:.1f}点")
            logger.info(f"  馬場ボーナス: {track_bonus:.1f}点")
            logger.info(f"  クラス補正: {class_factor:.2f}倍")
            
            # Step 2: 12項目の個別スコアをマッピング
            item_scores = {
                '1_distance_aptitude': d_logic_scores.get('1_distance_aptitude', base_score),
                '2_bloodline_evaluation': d_logic_scores.get('2_bloodline_evaluation', base_score * 0.9),
                '3_jockey_compatibility': d_logic_scores.get('3_jockey_compatibility', base_score * 0.85),
                '4_trainer_evaluation': d_logic_scores.get('4_trainer_evaluation', base_score * 0.85),
                '5_track_aptitude': d_logic_scores.get('5_track_aptitude', base_score),
                '6_weather_aptitude': d_logic_scores.get('6_weather_aptitude', base_score * 0.95),
                '7_popularity_factor': d_logic_scores.get('7_popularity_factor', base_score * 0.8),
                '8_weight_impact': d_logic_scores.get('8_weight_impact', base_score * 0.9),
                '9_horse_weight_impact': d_logic_scores.get('9_horse_weight_impact', base_score * 0.9),
                '10_corner_specialist': d_logic_scores.get('10_corner_specialist_degree', base_score * 0.85),
                '11_margin_analysis': d_logic_scores.get('11_margin_analysis', base_score * 0.9),
                '12_time_index': d_logic_scores.get('12_time_index', base_score)
            }
            
            # Step 3: ユーザーの重み付けで12項目を再計算
            weighted_score = 0.0
            
            logger.info(f"\n{horse_name} のIMLogic重み付け計算:")
            for key, weight in item_weights.items():
                score = item_scores.get(key, base_score)
                # 重みを正規化（合計が100になるように）
                normalized_weight = weight / 100.0
                contribution = score * normalized_weight
                weighted_score += contribution
                logger.info(f"  {key}: {score:.1f}点 × {weight:.1f}% = {contribution:.2f}点")
            
            # Step 4: I-Logicと同じ補正を適用
            # 開催場・距離ボーナスを加算
            final_score = weighted_score + venue_distance_bonus + track_bonus
            
            # クラス補正を適用
            final_score *= class_factor
            
            logger.info(f"\n{horse_name} IMLogic最終スコア: {final_score:.2f}点")
            logger.info(f"  (内訳: 重み付け{weighted_score:.1f} + 開催場{venue_distance_bonus:.1f} + 馬場{track_bonus:.1f}) × クラス{class_factor:.2f}")
            
            # I-Logic同様150点まで可能
            return min(150.0, max(0.0, final_score)), True
            
        except Exception as e:
            logger.error(f"馬スコア計算エラー ({horse_name}): {e}")
            import traceback
            traceback.print_exc()
            return 50.0, True
    
    def _estimate_12_items_from_races(self, races: List[Dict]) -> Dict[str, float]:
        """レースデータから12項目を推定"""
        # 基本的な集計
        total_races = len(races)
        wins = sum(1 for race in races if race.get('finish') == 1)
        win_rate = wins / total_races if total_races > 0 else 0
        
        # 基本スコア（勝率ベース）
        base = min(100, 50 + win_rate * 100)
        
        return {
            '1_distance_aptitude': base + 5,
            '2_bloodline_evaluation': base,
            '3_jockey_compatibility': base - 5,
            '4_trainer_evaluation': base - 5,
            '5_track_aptitude': base + 3,
            '6_weather_aptitude': base,
            '7_popularity_factor': base - 10,
            '8_weight_impact': base - 3,
            '9_horse_weight_impact': base - 3,
            '10_corner_specialist_degree': base - 8,
            '11_margin_analysis': base - 2,
            '12_time_index': base + 2
        }
    
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


# グローバルインスタンスを作成（シングルトン）
def get_imlogic_engine() -> IMLogicEngine:
    """IMLogicEngineのシングルトンインスタンスを取得"""
    return IMLogicEngine()


# 互換性のためのインスタンス
imlogic_engine_instance = get_imlogic_engine()