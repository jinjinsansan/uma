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
        # 既存のレース分析エンジンを取得
        try:
            from .race_analysis_engine import get_race_analysis_engine
            from .fast_dlogic_engine import fast_engine_instance
            self.race_engine = get_race_analysis_engine(fast_engine_instance)
            logger.info("IMLogicエンジンを初期化しました")
        except Exception as e:
            logger.error(f"IMLogicエンジンの初期化エラー: {e}")
            raise RuntimeError(f"IMLogicエンジンの初期化に失敗しました: {e}")
    
    async def analyze_race(
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
                    jockey_name = jockeys[i] if i < len(jockeys) else ''
                    post = posts[i] if i < len(posts) else 1
                    horse_number = horse_numbers[i] if i < len(horse_numbers) else i + 1
                    
                    # 馬の評価（カスタム重み付けを適用）
                    horse_analysis = await self._analyze_horse_with_custom_weights(
                        horse_name, 
                        context,
                        item_weights
                    )
                    
                    # 騎手の評価（既存のエンジンを使用）
                    jockey_context = {
                        'venue': context['venue'],
                        'post': post,
                        'sire': ''  # 現在は未実装
                    }
                    jockey_analysis = self.race_engine.jockey_manager.calculate_jockey_score(
                        jockey_name,
                        jockey_context
                    )
                    
                    # IMLogicスコア計算（ユーザー設定の比率で）
                    horse_score = horse_analysis.get('final_score', 50.0)
                    jockey_score = jockey_analysis.get('total_score', 0)
                    
                    # パーセンテージに変換
                    horse_weight_ratio = horse_weight / 100.0
                    jockey_weight_ratio = jockey_weight / 100.0
                    
                    total_score = (
                        horse_score * horse_weight_ratio +
                        jockey_score * jockey_weight_ratio
                    )
                    
                    results.append({
                        'rank': 0,  # 後でソート
                        'horse_number': horse_number,
                        'post': post,
                        'horse': horse_name,
                        'jockey': jockey_name,
                        'total_score': round(total_score, 1),
                        'horse_score': round(horse_score, 1),
                        'jockey_score': round(jockey_score, 1),
                        'horse_contribution': round(horse_score * horse_weight_ratio, 1),
                        'jockey_contribution': round(jockey_score * jockey_weight_ratio, 1),
                        'custom_item_scores': horse_analysis.get('custom_item_scores', {}),
                        'horse_details': {
                            'base': round(horse_analysis.get('base_score', 50.0), 1),
                            'venue_distance_bonus': horse_analysis.get('venue_distance_bonus', 0),
                            'class_factor': horse_analysis.get('class_factor', 1.0),
                            'track_bonus': horse_analysis.get('track_bonus', 0)
                        },
                        'jockey_details': {
                            'venue': jockey_analysis.get('venue_score', 0),
                            'post': jockey_analysis.get('post_score', 0),
                            'sire': jockey_analysis.get('sire_score', 0)
                        }
                    })
                    
                except Exception as e:
                    logger.error(f"馬の分析エラー（{horses[i]}）: {e}")
                    results.append({
                        'rank': 999,
                        'horse_number': horse_numbers[i] if i < len(horse_numbers) else i + 1,
                        'post': posts[i] if i < len(posts) else 1,
                        'horse': horses[i],
                        'jockey': jockeys[i] if i < len(jockeys) else '',
                        'total_score': 0,
                        'horse_score': 0,
                        'jockey_score': 0,
                        'error': str(e)
                    })
            
            # スコア順にソート
            results.sort(key=lambda x: x['total_score'], reverse=True)
            
            # 順位付け
            for i, result in enumerate(results):
                result['rank'] = i + 1
            
            # 分析サマリーの作成
            summary = self._create_analysis_summary(results, context)
            
            return {
                'race_info': {
                    'venue': race_data.get('venue', ''),
                    'race_number': race_data.get('race_number', ''),
                    'race_name': race_data.get('race_name', ''),
                    'distance': race_data.get('distance', ''),
                    'track_condition': race_data.get('track_condition', '良')
                },
                'results': results,
                'summary': summary,
                'analysis_type': 'imlogic',
                'base_horse': 'IMLogic（カスタマイズ版）',
                'weights': {
                    'horse': horse_weight,
                    'jockey': jockey_weight,
                    'items': item_weights
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"IMLogic分析エラー: {e}")
            return {
                'error': f'分析中にエラーが発生しました: {str(e)}',
                'analysis_type': 'imlogic'
            }
    
    async def _analyze_horse_with_custom_weights(
        self,
        horse_name: str,
        context: Dict[str, Any],
        item_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """カスタム重み付けで馬を分析"""
        try:
            # まず通常のイクイノックス基準で計算
            horse_analysis = self.race_engine.modern_engine.calculate_horse_score(
                horse_name, 
                context,
                enable_bayesian=True
            )
            
            # D-Logic項目スコアを取得
            d_logic_scores = horse_analysis.get('d_logic_scores', {})
            if not d_logic_scores:
                # スコアがない場合はデフォルト値を使用
                d_logic_scores = self._get_default_scores()
            
            # カスタム重み付けを適用して基本スコアを再計算
            custom_base_score = self._calculate_custom_base_score(
                d_logic_scores,
                item_weights
            )
            
            # 開催場・クラス・馬場ボーナスは元のまま使用
            venue_distance_bonus = horse_analysis.get('venue_distance_bonus', 0)
            class_factor = horse_analysis.get('class_factor', 1.0)
            track_bonus = horse_analysis.get('track_bonus', 0)
            
            # 最終スコア計算
            final_score = (
                custom_base_score * class_factor +
                venue_distance_bonus +
                track_bonus
            )
            
            # スコアを0-150の範囲に制限
            final_score = max(0, min(150, final_score))
            
            return {
                'base_score': custom_base_score,
                'venue_distance_bonus': venue_distance_bonus,
                'class_factor': class_factor,
                'track_bonus': track_bonus,
                'final_score': final_score,
                'd_logic_scores': d_logic_scores,
                'custom_item_scores': self._calculate_item_contributions(
                    d_logic_scores,
                    item_weights
                )
            }
            
        except Exception as e:
            logger.error(f"カスタム馬分析エラー（{horse_name}）: {e}")
            return {
                'base_score': 50.0,
                'venue_distance_bonus': 0,
                'class_factor': 1.0,
                'track_bonus': 0,
                'final_score': 50.0,
                'error': str(e)
            }
    
    def _calculate_custom_base_score(
        self,
        d_logic_scores: Dict[str, float],
        item_weights: Dict[str, float]
    ) -> float:
        """カスタム重み付けで基本スコアを計算"""
        # フィールド名のマッピング（DBフィールド名 → D-Logicスコア名）
        field_mapping = {
            '1_distance_aptitude': '1_distance_aptitude',
            '2_bloodline_evaluation': '2_bloodline_evaluation',
            '3_jockey_compatibility': '3_jockey_compatibility',
            '4_trainer_evaluation': '4_trainer_evaluation',
            '5_track_aptitude': '5_track_aptitude',
            '6_weather_aptitude': '6_weather_aptitude',
            '7_popularity_factor': '7_popularity_factor',
            '8_weight_impact': '8_weight_impact',
            '9_horse_weight_impact': '9_horse_weight_impact',
            '10_corner_specialist': '10_corner_specialist_degree',
            '11_margin_analysis': '11_margin_analysis',
            '12_time_index': '12_time_index'
        }
        
        total_score = 0
        
        for db_field, d_logic_field in field_mapping.items():
            # 重みを取得（%）
            weight = item_weights.get(db_field, 8.33)
            
            # D-Logicスコアを取得（デフォルト50点）
            score = d_logic_scores.get(d_logic_field, 50.0)
            
            # 重み付けして加算（重みは%なので100で割る）
            contribution = score * (weight / 100.0)
            total_score += contribution
        
        return total_score
    
    def _calculate_item_contributions(
        self,
        d_logic_scores: Dict[str, float],
        item_weights: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """各項目の貢献度を計算"""
        field_mapping = {
            '1_distance_aptitude': ('1_distance_aptitude', '距離適性'),
            '2_bloodline_evaluation': ('2_bloodline_evaluation', '血統評価'),
            '3_jockey_compatibility': ('3_jockey_compatibility', '騎手相性'),
            '4_trainer_evaluation': ('4_trainer_evaluation', '調教師評価'),
            '5_track_aptitude': ('5_track_aptitude', 'トラック適性'),
            '6_weather_aptitude': ('6_weather_aptitude', '天候適性'),
            '7_popularity_factor': ('7_popularity_factor', '人気度要因'),
            '8_weight_impact': ('8_weight_impact', '重量影響'),
            '9_horse_weight_impact': ('9_horse_weight_impact', '馬体重影響'),
            '10_corner_specialist': ('10_corner_specialist_degree', 'コーナー適性'),
            '11_margin_analysis': ('11_margin_analysis', 'マージン分析'),
            '12_time_index': ('12_time_index', 'タイムインデックス')
        }
        
        contributions = {}
        
        for db_field, (d_logic_field, display_name) in field_mapping.items():
            weight = item_weights.get(db_field, 8.33)
            score = d_logic_scores.get(d_logic_field, 50.0)
            contribution = score * (weight / 100.0)
            
            contributions[display_name] = {
                'original_score': round(score, 1),
                'weight': round(weight, 1),
                'contribution': round(contribution, 1)
            }
        
        return contributions
    
    def _get_default_scores(self) -> Dict[str, float]:
        """デフォルトのD-Logicスコア"""
        return {
            '1_distance_aptitude': 50.0,
            '2_bloodline_evaluation': 50.0,
            '3_jockey_compatibility': 50.0,
            '4_trainer_evaluation': 50.0,
            '5_track_aptitude': 50.0,
            '6_weather_aptitude': 50.0,
            '7_popularity_factor': 50.0,
            '8_weight_impact': 50.0,
            '9_horse_weight_impact': 50.0,
            '10_corner_specialist_degree': 50.0,
            '11_margin_analysis': 50.0,
            '12_time_index': 50.0
        }
    
    def _extract_grade(self, race_name: str) -> str:
        """レース名からグレードを抽出"""
        if 'G1' in race_name or 'GⅠ' in race_name:
            return 'G1'
        elif 'G2' in race_name or 'GⅡ' in race_name:
            return 'G2'
        elif 'G3' in race_name or 'GⅢ' in race_name:
            return 'G3'
        elif 'オープン' in race_name:
            return 'オープン'
        elif 'L' in race_name or 'リステッド' in race_name:
            return 'L'
        elif '3勝' in race_name:
            return '3勝'
        elif '2勝' in race_name:
            return '2勝'
        elif '1勝' in race_name:
            return '1勝'
        elif '未勝利' in race_name:
            return '未勝利'
        elif '新馬' in race_name:
            return '新馬'
        else:
            return ''
    
    def _create_analysis_summary(
        self, 
        results: List[Dict[str, Any]], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析結果のサマリーを作成"""
        if not results:
            return {}
        
        top3 = results[:3]
        
        summary = {
            'top_horse': {
                'name': top3[0]['horse'],
                'jockey': top3[0]['jockey'],
                'score': top3[0]['total_score'],
                'key_factors': []
            },
            'score_distribution': {
                'highest': top3[0]['total_score'],
                'lowest': results[-1]['total_score'] if results else 0,
                'average': round(sum(r['total_score'] for r in results) / len(results), 1) if results else 0
            },
            'custom_weights_impact': []
        }
        
        # カスタム重み付けの影響を分析
        top_horse_items = top3[0].get('custom_item_scores', {})
        if top_horse_items:
            # 貢献度が高い項目トップ3
            sorted_items = sorted(
                top_horse_items.items(),
                key=lambda x: x[1]['contribution'],
                reverse=True
            )[:3]
            
            for item_name, item_data in sorted_items:
                if item_data['weight'] > 10:  # 10%以上の重みがある項目
                    summary['custom_weights_impact'].append({
                        'item': item_name,
                        'weight': item_data['weight'],
                        'contribution': item_data['contribution']
                    })
        
        return summary