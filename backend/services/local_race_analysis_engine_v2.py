#!/usr/bin/env python3
"""
地方競馬版I-Logic（レース分析）エンジン V2
JRA版と完全に同じロジックで実装
"""
import logging
from typing import Dict, Any, List, Optional
from .local_fast_dlogic_engine_v2 import LocalFastDLogicEngineV2
from .local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
from .local_jockey_data_manager import local_jockey_manager

logger = logging.getLogger(__name__)

class LocalRaceAnalysisEngineV2:
    """地方競馬版I-Logic（レース分析）エンジン V2 - JRA版と同一実装"""
    
    # 馬と騎手の重み付け（JRA版と同じ）
    HORSE_WEIGHT = 0.7    # 70%
    JOCKEY_WEIGHT = 0.3   # 30%
    
    def __init__(self):
        """初期化：地方競馬版V2エンジンを使用"""
        # 地方競馬版V2エンジンを使用
        self.dlogic_engine = LocalFastDLogicEngineV2()
        
        # 地方競馬版マネージャー
        self.raw_manager = local_dlogic_manager_v2
        self.jockey_manager = local_jockey_manager
        
        # modern_engineも同じ参照（互換性のため）
        self.modern_engine = self.dlogic_engine
        
        # 基準馬（イクイノックス）
        self.baseline_horse = "イクイノックス"
        
        logger.info(f"🏇 地方競馬版I-Logic分析エンジンV2初期化完了")
    
    def get_engine_info(self) -> Dict[str, Any]:
        """エンジン情報を返す"""
        return {
            "engine_type": "LocalRaceAnalysisEngineV2",
            "venue": "南関東4場",
            "baseline_horse": self.baseline_horse,
            "knowledge_horses": len(self.raw_manager.knowledge_data.get('horses', {})),
            "manager_type": "V2"
        }
    
    def analyze_race(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レース全体を分析（JRA版と同じ実装）
        
        Args:
            race_data: レース情報
        
        Returns:
            分析結果
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
            
            # デフォルトの12項目重み付け（JRA版と同じ）
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
            posts = race_data.get('posts') or []  # Noneの場合は空リスト
            horse_numbers = race_data.get('horse_numbers') or []  # Noneの場合は空リスト
            
            for i in range(len(horses)):
                try:
                    horse_name = horses[i]
                    jockey_name = jockeys[i] if jockeys and i < len(jockeys) else ''
                    post = posts[i] if posts and i < len(posts) else i + 1
                    horse_number = horse_numbers[i] if horse_numbers and i < len(horse_numbers) else i + 1
                    
                    # 馬のスコアを計算（12項目重み付け）
                    horse_score, has_data = self._calculate_horse_score_with_weights(
                        horse_name=horse_name,
                        context=context,
                        item_weights=default_item_weights
                    )
                    
                    # 騎手の評価
                    jockey_context = {
                        'venue': context['venue'],
                        'post': post
                    }
                    jockey_score = self._calculate_jockey_score(
                        jockey_name,
                        jockey_context
                    )
                    
                    # 総合評価（馬70%、騎手30%）
                    if not has_data:
                        # データなしの馬は-1点
                        total_score = -1
                        logger.info(f"{horse_name}: データなしのため-1点")
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
                        'has_data': has_data,
                        'horse_details': {
                            'has_knowledge_data': has_data,
                            'data_status': 'no_data' if not has_data else 'full_data'
                        },
                        'jockey_details': {
                            'venue': jockey_score,
                            'post': 0,
                            'overall': jockey_score
                        }
                    })
                    
                except Exception as e:
                    logger.error(f"馬の分析エラー（{horses[i]}）: {e}")
                    results.append({
                        'rank': 999,
                        'horse_number': horse_numbers[i] if horse_numbers and i < len(horse_numbers) else i + 1,
                        'post': posts[i] if posts and i < len(posts) else i + 1,
                        'horse': horses[i],
                        'jockey': jockeys[i] if jockeys and i < len(jockeys) else '',
                        'total_score': -1,
                        'horse_score': -1,
                        'jockey_score': 0,
                        'error': str(e)
                    })
            
            # データがある馬のみでソート（-1を除外）
            valid_results = [r for r in results if r['total_score'] >= 0]
            invalid_results = [r for r in results if r['total_score'] < 0]
            
            # スコア順にソート
            valid_results.sort(key=lambda x: x['total_score'], reverse=True)
            
            # 順位付け
            for i, result in enumerate(valid_results):
                result['rank'] = i + 1
            
            # データなしの馬を最後に追加
            for result in invalid_results:
                result['rank'] = len(valid_results) + 1
            
            # 全結果を結合
            all_results = valid_results + invalid_results
            
            # 分析サマリーの作成
            summary = self._create_analysis_summary(all_results, context)
            
            return {
                'race_info': {
                    'venue': race_data.get('venue', ''),
                    'race_number': race_data.get('race_number', ''),
                    'race_name': race_data.get('race_name', ''),
                    'grade': race_data.get('grade', ''),
                    'distance': race_data.get('distance', ''),
                    'track_condition': race_data.get('track_condition', '良')
                },
                'results': all_results,
                'summary': summary,
                'analysis_type': 'race_analysis_v2',
                'base_horse': 'イクイノックス基準（12項目均等重み）',
                'weights': {
                    'horse': self.HORSE_WEIGHT,
                    'jockey': self.JOCKEY_WEIGHT
                },
                'item_weights': default_item_weights,
                'status': 'success',
                'scores': all_results,  # IMLogicEngineV2との互換性
                'top_horses': [r['horse'] for r in valid_results[:5]]  # 上位5頭
            }
            
        except Exception as e:
            logger.error(f"レース分析エラー: {e}")
            return {
                'error': f'分析中にエラーが発生しました: {str(e)}',
                'analysis_type': 'race_analysis_v2',
                'status': 'error'
            }
    
    def _validate_race_data(self, race_data: Dict[str, Any]) -> bool:
        """レースデータの検証（JRA版と同じ）"""
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
    ) -> tuple:
        """
        馬のスコアを12項目の重み付きで計算（JRA版と同じ）
        
        Returns:
            (score, has_data) のタプル
        """
        try:
            # D-Logicで詳細スコアを取得
            score_data = self.raw_manager.calculate_dlogic_realtime(horse_name)
            
            if score_data.get('error') or not score_data.get('data_available'):
                # データがない場合
                return (0, False)
            
            # 12項目のスコアを取得
            item_scores = score_data.get('d_logic_scores', {})
            
            # 重み付き平均を計算
            weighted_sum = 0
            weight_sum = 0
            
            for item_key, weight in item_weights.items():
                # D-Logicのキー形式と一致させる（数字付きのまま使用）
                # item_scoresのキーを確認（"1_distance_aptitude"形式）
                score = item_scores.get(item_key, 50.0)
                
                weighted_sum += score * weight
                weight_sum += weight
            
            # 重み付き平均（0-100の範囲）
            if weight_sum > 0:
                final_score = weighted_sum / weight_sum
            else:
                final_score = score_data.get('total_score', 50.0)
            
            return (final_score, True)
            
        except Exception as e:
            logger.error(f"馬スコア計算エラー（{horse_name}）: {e}")
            return (0, False)
    
    def _calculate_jockey_score(self, jockey_name: str, context: Dict[str, Any]) -> float:
        """
        騎手スコアを計算（JRA版と同じロジック）
        """
        try:
            if not jockey_name:
                return 0.0
            
            # 騎手データを取得
            jockey_data = self.jockey_manager.get_jockey_data(jockey_name)
            
            if not jockey_data:
                return 0.0
            
            # 基本スコア（勝率と複勝率から計算）
            overall_stats = jockey_data.get('overall_stats', {})
            win_rate = overall_stats.get('overall_win_rate', 0)
            place_rate = overall_stats.get('overall_fukusho_rate', 0)
            
            # 勝率と複勝率を組み合わせてスコア化（JRA版と同じ）
            base_score = (win_rate * 0.6 + place_rate * 0.4)
            
            # 会場別成績があれば加味
            venue = context.get('venue', '')
            if venue and 'venue_stats' in jockey_data:
                venue_stats = jockey_data['venue_stats'].get(venue, {})
                venue_win_rate = venue_stats.get('win_rate', 0)
                if venue_win_rate > 0:
                    # 会場成績で調整（最大±20%）
                    venue_adjustment = (venue_win_rate - win_rate) * 0.2
                    base_score = base_score * (1 + venue_adjustment / 100)
            
            # 0-100の範囲に正規化
            return min(100, max(0, base_score))
            
        except Exception as e:
            logger.error(f"騎手スコア計算エラー（{jockey_name}）: {e}")
            return 0.0
    
    def _create_analysis_summary(self, results: List[Dict], context: Dict) -> Dict[str, Any]:
        """分析サマリーを作成（JRA版と同じ）"""
        try:
            valid_results = [r for r in results if r.get('total_score', -1) >= 0]
            
            if not valid_results:
                return {
                    'top_3': [],
                    'data_quality': 'データなし',
                    'confidence': 0
                }
            
            return {
                'top_3': [r['horse'] for r in valid_results[:3]],
                'data_quality': '完全' if len(valid_results) == len(results) else '部分的',
                'confidence': min(95, 50 + len(valid_results) * 5),
                'total_horses': len(results),
                'analyzed_horses': len(valid_results)
            }
            
        except Exception as e:
            logger.error(f"サマリー作成エラー: {e}")
            return {
                'top_3': [],
                'data_quality': 'エラー',
                'confidence': 0
            }

# グローバルインスタンス
local_race_analysis_engine_v2 = LocalRaceAnalysisEngineV2()