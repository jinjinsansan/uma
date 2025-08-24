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
        馬のスコアを計算（I-Logicベース + 12項目カスタマイズ）
        
        Args:
            horse_name: 馬名
            context: レースコンテキスト
            item_weights: 12項目の重み付け
        
        Returns:
            馬のスコア（0-100）
        """
        try:
            # Step 1: I-Logicのベース計算（イクイノックス基準、開催適性、クラス補正など）
            ilogic_result = self.modern_engine.calculate_horse_score(
                horse_name=horse_name,
                context=context,
                enable_bayesian=True
            )
            
            # I-Logicのベーススコア（開催適性、クラス補正込み）
            ilogic_base_score = ilogic_result.get('final_score', 50.0)
            
            # Step 2: 標準D-Logicから12項目の詳細を取得
            # 注: get_horse_raw_dataメソッドを使う
            horse_data = self.dlogic_manager.get_horse_raw_data(horse_name)
            
            if not horse_data:
                # データがない場合はI-Logicのスコアをそのまま返す
                logger.warning(f"12項目データが見つかりません: {horse_name}")
                return ilogic_base_score
            
            # 12項目の詳細スコアを計算
            dlogic_details = self.dlogic_manager.calculate_dlogic_score(horse_data)
            
            if 'error' in dlogic_details:
                return ilogic_base_score
            
            # Step 3: 12項目の個別スコアを取得
            item_scores = {
                '1_distance_aptitude': dlogic_details.get('1_distance_aptitude', 50.0),
                '2_bloodline_evaluation': dlogic_details.get('2_bloodline_evaluation', 50.0),
                '3_jockey_compatibility': dlogic_details.get('3_jockey_compatibility', 50.0),
                '4_trainer_evaluation': dlogic_details.get('4_trainer_evaluation', 50.0),
                '5_track_aptitude': dlogic_details.get('5_track_aptitude', 50.0),
                '6_weather_aptitude': dlogic_details.get('6_weather_aptitude', 50.0),
                '7_popularity_factor': dlogic_details.get('7_popularity_factor', 50.0),
                '8_weight_impact': dlogic_details.get('8_weight_impact', 50.0),
                '9_horse_weight_impact': dlogic_details.get('9_horse_weight_impact', 50.0),
                '10_corner_specialist': dlogic_details.get('10_corner_specialist_degree', 50.0),
                '11_margin_analysis': dlogic_details.get('11_margin_analysis', 50.0),
                '12_time_index': dlogic_details.get('12_time_index', 50.0)
            }
            
            # Step 4: ユーザーの重み付けで12項目を再計算
            weighted_12_score = 0.0
            for key, weight in item_weights.items():
                score = item_scores.get(key, 50.0)
                contribution = score * (weight / 100.0)
                weighted_12_score += contribution
                logger.debug(f"{key}: {score:.1f}点 × {weight:.1f}% = {contribution:.2f}")
            
            # Step 5: I-Logicの要素とユーザーカスタマイズの融合
            # I-Logicのベース要素（クラス補正、開催適性など）は維持しつつ、
            # 12項目の評価はユーザーの重み付けで調整
            
            # 標準D-Logicの総合スコアに対する、ユーザーカスタマイズ後のスコアの比率
            original_total = dlogic_details.get('total_score', 75.0)
            if original_total > 0:
                custom_ratio = weighted_12_score / original_total
            else:
                custom_ratio = 1.0
            
            # I-Logicベーススコアにカスタマイズ比率を適用
            final_score = ilogic_result.get('base_score', 75.0) * custom_ratio
            
            # I-Logic固有のボーナスを加算（開催適性、馬場適性）
            final_score += ilogic_result.get('venue_distance_bonus', 0)
            final_score += ilogic_result.get('track_bonus', 0)
            
            # クラス補正を適用
            final_score *= ilogic_result.get('class_factor', 1.0)
            
            logger.info(f"{horse_name} IMLogicスコア: {final_score:.2f}点 (ベース:{ilogic_base_score:.1f}, カスタマイズ比率:{custom_ratio:.2f})")
            
            return min(150.0, max(0.0, final_score))  # I-Logic同様150点まで可能
            
        except Exception as e:
            logger.error(f"馬スコア計算エラー: {e}")
            import traceback
            traceback.print_exc()
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