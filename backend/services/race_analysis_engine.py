"""
レース分析統合エンジン
馬と騎手の総合評価を行う
"""
import logging
from typing import Dict, Any, List, Optional
from .modern_dlogic_engine import ModernDLogicEngine
from .jockey_data_manager import jockey_manager
from .jockey_name_mapper import normalize_jockey_name

logger = logging.getLogger(__name__)

class RaceAnalysisEngine:
    """レース全体を総合的に分析するエンジン"""
    
    # 馬と騎手の重み付け
    HORSE_WEIGHT = 0.7    # 70%
    JOCKEY_WEIGHT = 0.3   # 30%
    
    def __init__(self, fast_engine_instance=None):
        """初期化
        
        Args:
            fast_engine_instance: 既存のFastDLogicEngineインスタンス（オプション）
        """
        # fast_engine_instanceが渡されない場合は、ここで新規作成
        if fast_engine_instance is None:
            from .fast_dlogic_engine import FastDLogicEngine
            fast_engine_instance = FastDLogicEngine()
            logger.info("新しいFastDLogicEngineインスタンスを作成しました")
        else:
            logger.info("既存のFastDLogicEngineインスタンスを使用します")
            
        # モダンD-Logicエンジン（イクイノックス基準）
        try:
            self.modern_engine = ModernDLogicEngine(fast_engine_instance)
            logger.info("ModernDLogicEngineの初期化に成功しました")
        except Exception as e:
            logger.error(f"ModernDLogicEngineの初期化に失敗しました: {e}")
            # 拡張ナレッジデータが必須なので、エラーを再発生させる
            raise RuntimeError(f"レース分析エンジンの初期化に失敗しました: {e}")
            
        # 騎手データマネージャー
        self.jockey_manager = jockey_manager
        
        logger.info("レース分析エンジンを初期化しました")
    
    def analyze_race(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レース全体を分析
        
        Args:
            race_data: {
                'venue': '札幌',
                'race_number': 11,
                'race_name': '札幌記念',
                'grade': 'G3',
                'distance': '2000m',
                'track_condition': '良',
                'horses': ['ドウデュース', ...],
                'jockeys': ['武豊', ...],
                'posts': [1, 2, ...],
                'horse_numbers': [1, 2, ...]
            }
        
        Returns:
            {
                'race_info': レース情報,
                'results': 分析結果（順位付き）,
                'analysis_type': 'race_analysis_v2',
                'base_horse': 'イクイノックス'
            }
        """
        try:
            # 入力検証
            if not self._validate_race_data(race_data):
                return {
                    'error': 'レースデータが不正です',
                    'analysis_type': 'race_analysis_v2'
                }
            
            # レース情報の準備
            context = {
                'venue': race_data.get('venue', ''),
                'grade': race_data.get('grade', ''),
                'distance': race_data.get('distance', ''),
                'track_condition': race_data.get('track_condition', '良')
            }
            
            # デフォルトの12項目重み付け（各項目8.33%、IMLogicと同じ）
            default_item_weights = {
                '1_distance_aptitude': 8.33,
                '2_bloodline_evaluation': 8.33,
                '3_jockey_compatibility': 8.33,
                '4_trainer_evaluation': 8.33,
                '5_track_aptitude': 8.33,
                '6_weather_aptitude': 8.33,
                '7_popularity_factor': 8.33,
                '8_weight_impact': 8.33,
                '9_horse_weight_impact': 8.33,
                '10_corner_specialist': 8.33,
                '11_margin_analysis': 8.33,
                '12_time_index': 8.37  # 合計100になるよう調整
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
                    jockey_name = normalize_jockey_name(raw_jockey_name)
                    post = posts[i] if i < len(posts) else 1
                    horse_number = horse_numbers[i] if i < len(horse_numbers) else i + 1
                    
                    # IMLogicと同じ方法で馬のスコアを計算（12項目重み付け）
                    horse_score, has_data, estimation_method = self._calculate_horse_score_with_weights(
                        horse_name=horse_name,
                        context=context,
                        item_weights=default_item_weights
                    )
                    
                    # 騎手の評価
                    jockey_context = {
                        'venue': context['venue'],
                        'post': post,
                        'sire': self._get_horse_sire(horse_name)  # 父馬情報
                    }
                    jockey_analysis = self.jockey_manager.calculate_jockey_score(
                        jockey_name,
                        jockey_context
                    )
                    
                    jockey_score = jockey_analysis.get('total_score', 0)
                    
                    # 総合評価（馬70%、騎手30%）
                    if not has_data:
                        # データなしの馬はスキップまたは0点
                        total_score = 0
                        logger.info(f"{horse_name}: データなしのため0点")
                    else:
                        total_score = (
                            horse_score * self.HORSE_WEIGHT +
                            jockey_score * self.JOCKEY_WEIGHT
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
                        'has_data': has_data,  # データ有無フラグ追加
                        'estimation_method': estimation_method,  # 推定方法追加
                        'horse_details': {
                            'has_knowledge_data': has_data,
                            'estimation_method': estimation_method,
                            'data_status': 'no_data' if not has_data else ('bayesian' if estimation_method == 'bayesian' else 'full_data')
                        },
                        'jockey_details': {
                            'venue': jockey_analysis.get('venue_score', 0),
                            'post': jockey_analysis.get('post_score', 0),
                            'sire': jockey_analysis.get('sire_score', 0)
                        }
                    })
                    
                except Exception as e:
                    logger.error(f"馬の分析エラー（{horses[i]}）: {e}")
                    # エラーでも結果に含める
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
                    'grade': race_data.get('grade', ''),
                    'distance': race_data.get('distance', ''),
                    'track_condition': race_data.get('track_condition', '良')
                },
                'results': results,
                'summary': summary,
                'analysis_type': 'race_analysis_v2',
                'base_horse': 'イクイノックス基準（12項目均等重み）',
                'weights': {
                    'horse': self.HORSE_WEIGHT,
                    'jockey': self.JOCKEY_WEIGHT
                },
                'item_weights': default_item_weights  # 12項目の重み付けを返す
            }
            
        except Exception as e:
            logger.error(f"レース分析エラー: {e}")
            return {
                'error': f'分析中にエラーが発生しました: {str(e)}',
                'analysis_type': 'race_analysis_v2'
            }
    
    def _validate_race_data(self, race_data: Dict[str, Any]) -> bool:
        """レースデータの検証"""
        required_fields = ['horses']
        for field in required_fields:
            if field not in race_data or not race_data[field]:
                logger.warning(f"必須フィールドが不足: {field}")
                return False
        
        # 馬と騎手の数が一致しているか
        horses = race_data.get('horses', [])
        jockeys = race_data.get('jockeys', [])
        if jockeys and len(horses) != len(jockeys):
            logger.warning(f"馬と騎手の数が不一致: 馬{len(horses)}頭、騎手{len(jockeys)}人")
            return False
        
        return True
    
    def _calculate_horse_score_with_weights(
        self, 
        horse_name: str, 
        context: Dict[str, Any],
        item_weights: Dict[str, float]
    ) -> tuple[float, bool, str]:
        """
        IMLogicと同じ方法で馬のスコアを計算（12項目重み付け）
        
        Args:
            horse_name: 馬名
            context: レースコンテキスト
            item_weights: 12項目の重み付け
        
        Returns:
            (馬のスコア, データ有無, 推定方法) - データなしの場合は(0, False, 'no_data')
        """
        try:
            # ModernDLogicEngineで基本計算（イクイノックス基準）
            ilogic_result = self.modern_engine.calculate_horse_score(
                horse_name=horse_name,
                context=context,
                enable_bayesian=True
            )
            
            # データ状態の判定
            estimation_method = ilogic_result.get('estimation_method', 'unknown')
            data_confidence = ilogic_result.get('data_confidence', 'none')
            
            # データなしの馬は0を返す（IMLogicと同じ）
            if estimation_method == 'default' and data_confidence == 'none':
                logger.info(f"{horse_name}: ナレッジファイルにデータが存在しません")
                return 0, False, 'no_data'
            
            # ベイズ推定の場合（データ不足だが1走以上ある）
            if estimation_method == 'bayesian':
                logger.info(f"{horse_name}: データ不足のためベイズ推定を適用")
            
            base_score = ilogic_result.get('base_score', 50.0)
            venue_distance_bonus = ilogic_result.get('venue_distance_bonus', 0)
            track_bonus = ilogic_result.get('track_bonus', 0)
            class_factor = ilogic_result.get('class_factor', 1.0)
            
            # 12項目の個別スコアを取得またはデフォルト値を設定
            item_scores = {
                '1_distance_aptitude': base_score + 5,
                '2_bloodline_evaluation': base_score,
                '3_jockey_compatibility': base_score - 5,
                '4_trainer_evaluation': base_score - 5,
                '5_track_aptitude': base_score + 3,
                '6_weather_aptitude': base_score,
                '7_popularity_factor': base_score - 10,
                '8_weight_impact': base_score - 3,
                '9_horse_weight_impact': base_score - 3,
                '10_corner_specialist': base_score - 8,
                '11_margin_analysis': base_score - 2,
                '12_time_index': base_score + 2
            }
            
            # ユーザーの重み付けで12項目を計算
            weighted_score = 0.0
            for key, weight in item_weights.items():
                score = item_scores.get(key, base_score)
                normalized_weight = weight / 100.0
                contribution = score * normalized_weight
                weighted_score += contribution
            
            # 開催場・距離・馬場ボーナスを加算
            final_score = weighted_score + venue_distance_bonus + track_bonus
            
            # クラス補正を適用
            final_score *= class_factor
            
            # 最大150点まで可能（IMLogicと同じ）
            return min(150.0, max(0.0, final_score)), True, estimation_method
            
        except Exception as e:
            logger.error(f"馬スコア計算エラー ({horse_name}): {e}")
            return 0, False, 'error'
    
    def _get_horse_sire(self, horse_name: str) -> str:
        """馬の父馬を取得"""
        try:
            # ナレッジファイルから父馬情報を取得
            horse_data = self.modern_engine.knowledge.get(horse_name, {})
            # 父馬情報は将来的に追加予定
            # 現在はデフォルト値を返す
            return horse_data.get('sire', '')
        except Exception:
            return ''
    
    def _create_analysis_summary(self, results: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """分析結果のサマリーを作成"""
        if not results:
            return {}
        
        top3 = results[:3]
        
        summary = {
            'top_horse': {
                'name': top3[0]['horse'],
                'jockey': top3[0]['jockey'],
                'score': top3[0]['total_score'],
                'advantage': []
            },
            'key_points': [],
            'venue_specialists': [],
            'cautions': []
        }
        
        # トップ馬の優位性
        if top3[0]['horse_details'].get('venue_distance_bonus', 0) >= 5:
            summary['top_horse']['advantage'].append(f"{context['venue']}巧者")
        
        if top3[0]['jockey_details']['venue'] >= 5:
            summary['top_horse']['advantage'].append(f"騎手も{context['venue']}で好成績")
        
        # 開催場スペシャリスト
        for result in results:
            if result['horse_details'].get('venue_distance_bonus', 0) >= 7:
                venue_history = result['horse_details']['venue_history']
                summary['venue_specialists'].append({
                    'horse': result['horse'],
                    'record': f"{venue_history.get('wins', 0)}勝/{venue_history.get('total', 0)}戦"
                })
        
        # 注意点
        if context['track_condition'] != '良':
            summary['key_points'].append(f"{context['track_condition']}馬場での適性を重視")
        
        return summary

# グローバルインスタンス（遅延初期化）
_race_analysis_engine = None

def get_race_analysis_engine(fast_engine_instance=None):
    """レース分析エンジンのシングルトンインスタンスを取得
    
    Args:
        fast_engine_instance: 既存のFastDLogicEngineインスタンス（オプション）
                            chat.pyから渡される共有インスタンス
    """
    global _race_analysis_engine
    if _race_analysis_engine is None:
        _race_analysis_engine = RaceAnalysisEngine(fast_engine_instance)
    return _race_analysis_engine