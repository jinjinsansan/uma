"""
MetaLogic（メタ予想システム）エンジン
D-Logic、I-Logic、ViewLogicの統合 + 市場オッズによるアンサンブル学習
既存エンジンに影響を与えない独立実装
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

class MetaLogicEngine:
    """
    MetaLogic独立型エンジン
    3つのエンジンを内部で実行し、メタスコアを計算
    """
    
    def __init__(self):
        """初期化（遅延ロード方式で既存システムへの影響を最小化）"""
        self.engine_weight = 0.7  # エンジンスコアの重み
        self.odds_weight = 0.3    # オッズファクターの重み
        
        # 各エンジンの重み付け（I-Logic重視のバランス配分）
        self.dlogic_weight = 0.3    # D-Logic: 30%
        self.ilogic_weight = 0.4    # I-Logic: 40%（最高性能エンジン）
        self.viewlogic_weight = 0.3  # ViewLogic: 30%
        
        # エンジンインスタンスは使用時に初期化（遅延ロード）
        self._dlogic = None
        self._ilogic = None
        self._viewlogic = None
        
        logger.info("MetaLogicエンジンを初期化しました（I-Logic 40%重視）")
    
    @property
    def dlogic_engine(self):
        """D-Logicエンジンの遅延初期化"""
        if self._dlogic is None:
            try:
                from services.fast_dlogic_engine import fast_engine_instance
                self._dlogic = fast_engine_instance
                logger.info("MetaLogic: D-Logicエンジンを初期化")
            except Exception as e:
                logger.error(f"D-Logicエンジン初期化エラー: {e}")
                raise
        return self._dlogic
    
    @property
    def ilogic_engine(self):
        """I-Logicエンジンの遅延初期化"""
        if self._ilogic is None:
            try:
                from services.fast_dlogic_engine import fast_engine_instance
                from services.modern_dlogic_engine import ModernDLogicEngine
                self._ilogic = ModernDLogicEngine(fast_engine_instance)
                logger.info("MetaLogic: I-Logicエンジンを初期化")
            except Exception as e:
                logger.error(f"I-Logicエンジン初期化エラー: {e}")
                raise
        return self._ilogic
    
    @property
    def viewlogic_engine(self):
        """ViewLogicエンジンの遅延初期化"""
        if self._viewlogic is None:
            try:
                from services.viewlogic_engine import ViewLogicEngine
                self._viewlogic = ViewLogicEngine()
                logger.info("MetaLogic: ViewLogicエンジンを初期化")
            except Exception as e:
                logger.error(f"ViewLogicエンジン初期化エラー: {e}")
                raise
        return self._viewlogic
    
    async def calculate_dlogic_scores(self, horses: List[str], context: Dict) -> Dict[str, float]:
        """D-Logicスコアを内部計算（JRA/南関東対応）"""
        try:
            venue = context.get('venue', '')
            
            # 南関東競馬場判定
            local_venues = ['大井', '川崎', '船橋', '浦和']
            
            if venue in local_venues:
                # 南関東地方競馬版
                from services.local_fast_dlogic_engine_v2 import local_fast_dlogic_engine_v2
                logger.info(f"MetaLogic: 南関東版D-Logicを使用 ({venue})")
                
                scores = {}
                for horse in horses:
                    score_data = local_fast_dlogic_engine_v2.raw_manager.calculate_dlogic_realtime(horse)
                    if score_data and not score_data.get('error'):
                        scores[horse] = round(score_data.get('total_score', 0), 1)
                return scores
            else:
                # JRA版
                from api.v2.dlogic import calculate_dlogic_batch
                logger.info(f"MetaLogic: JRA版D-Logicを使用 ({venue})")
                
                result = await calculate_dlogic_batch(horses)
                scores = {}
                if result:
                    for horse in horses:
                        if horse in result:
                            horse_data = result[horse]
                            if horse_data.get('data_available') and 'score' in horse_data:
                                scores[horse] = round(horse_data['score'], 1)
                return scores
            
        except Exception as e:
            logger.error(f"D-Logicスコア計算エラー: {e}")
            return {}
    
    def calculate_ilogic_scores(
        self,
        horses: List[str],
        jockeys: List[str],
        posts: List[int],
        context: Dict
    ) -> Dict[str, float]:
        """I-Logicスコアを内部計算"""
        try:
            # 騎手データマネージャー
            from services.jockey_data_manager import jockey_manager
            from services.jockey_name_mapper import normalize_jockey_name
            
            scores = {}
            for i, horse in enumerate(horses):
                # 馬の評価（I-Logic）
                horse_result = self.ilogic_engine.calculate_horse_score(
                    horse_name=horse,
                    context=context,
                    enable_bayesian=True
                )
                
                # データがある場合のみスコアを計算
                if 'base_score' not in horse_result:
                    continue  # データがない場合はスキップ
                    
                base_score = horse_result['base_score']
                venue_bonus = horse_result.get('venue_distance_bonus', 0)
                track_bonus = horse_result.get('track_bonus', 0)
                class_factor = horse_result.get('class_factor', 1.0)
                
                horse_score = (base_score + venue_bonus + track_bonus) * class_factor
                
                # 騎手の評価
                if i < len(jockeys):
                    jockey_name = normalize_jockey_name(jockeys[i])
                    post = posts[i] if i < len(posts) else 1
                    
                    jockey_context = {
                        'venue': context.get('venue'),
                        'post': post,
                        'sire': None
                    }
                    jockey_analysis = jockey_manager.calculate_jockey_score(
                        jockey_name,
                        jockey_context
                    )
                    jockey_score = jockey_analysis.get('total_score', 0)
                else:
                    jockey_score = 0
                
                # I-Logic総合（馬70% + 騎手30%）
                total_score = (horse_score * 0.7) + (jockey_score * 0.3)
                scores[horse] = round(total_score, 1)
            
            return scores
            
        except Exception as e:
            logger.error(f"I-Logicスコア計算エラー: {e}")
            return {}
    
    def calculate_viewlogic_scores(
        self,
        horses: List[str],
        jockeys: List[str],
        posts: List[int],
        context: Dict
    ) -> Dict[str, float]:
        """ViewLogicスコアを内部計算（JRA/南関東対応）"""
        try:
            venue = context.get('venue', '')
            
            # 南関東競馬場判定
            local_venues = ['大井', '川崎', '船橋', '浦和']
            
            if venue in local_venues:
                # 南関東地方競馬版
                from services.local_viewlogic_engine_v2 import local_viewlogic_engine_v2
                viewlogic_engine = local_viewlogic_engine_v2
                logger.info(f"MetaLogic: 南関東版ViewLogicを使用 ({venue})")
            else:
                # JRA版
                from services.viewlogic_engine import ViewLogicEngine
                viewlogic_engine = ViewLogicEngine()
                logger.info(f"MetaLogic: JRA版ViewLogicを使用 ({venue})")
            
            # レースデータを準備
            race_data = {
                'horses': horses,
                'jockeys': jockeys,
                'posts': posts,
                'venue': venue,
                'track_type': context.get('track_type', '芝'),
                'distance': context.get('distance', '2000'),
                'track_condition': context.get('track_condition', '良')
            }
            
            # 展開予想（高度な分析版）を使用
            result = viewlogic_engine.predict_race_flow_advanced(race_data)
            
            scores = {}
            if result and result.get('status') == 'success':
                # flow_matchingから各馬のスコアを抽出
                flow_matching = result.get('flow_matching', {})
                for horse, score in flow_matching.items():
                    if score > 0:
                        scores[horse] = round(score, 1)
            
            return scores
            
        except Exception as e:
            logger.error(f"ViewLogicスコア計算エラー: {e}")
            # エラー時は空の辞書を返す（データなし）
            return {}
    
    def calculate_meta_scores(
        self,
        dlogic_scores: Dict[str, float],
        ilogic_scores: Dict[str, float],
        viewlogic_scores: Dict[str, float],
        odds: List[float],
        horses: List[str]
    ) -> List[Tuple[str, float, Dict]]:
        """メタスコアを計算"""
        meta_results = []
        
        for i, horse in enumerate(horses):
            # 各エンジンのスコア取得（データがある場合のみ）
            d_score = dlogic_scores.get(horse)
            i_score = ilogic_scores.get(horse)
            v_score = viewlogic_scores.get(horse)
            
            # 有効なスコアをカウント
            valid_scores = []
            weights = []
            
            if d_score is not None:
                valid_scores.append(d_score)
                weights.append(self.dlogic_weight)
            
            if i_score is not None:
                valid_scores.append(i_score)
                weights.append(self.ilogic_weight)
                
            if v_score is not None:
                valid_scores.append(v_score)
                weights.append(self.viewlogic_weight)
            
            # 少なくとも1つのエンジンでデータがある場合のみ計算
            if not valid_scores:
                continue  # データがない馬はスキップ
            
            # 重み付け平均（データがあるエンジンのみで計算）
            total_weight = sum(weights)
            if total_weight > 0:
                weighted_sum = sum(score * weight for score, weight in zip(valid_scores, weights))
                engine_avg = weighted_sum / total_weight
            else:
                continue
            
            # オッズファクター
            horse_odds = odds[i] if i < len(odds) else None
            if horse_odds is None or horse_odds <= 0:
                odds_factor = 0  # オッズがない場合は0
            else:
                odds_factor = 100 / (1 + horse_odds)
            
            # メタスコア
            meta_score = (engine_avg * self.engine_weight) + (odds_factor * self.odds_weight)
            
            # エンジン評価数
            engine_count = len(valid_scores)
            
            details = {
                'd_logic': d_score if d_score is not None else 0,
                'i_logic': i_score if i_score is not None else 0,
                'view_logic': v_score if v_score is not None else 0,
                'engine_avg': round(engine_avg, 1),
                'odds': horse_odds if horse_odds else 0,
                'odds_factor': round(odds_factor, 1),
                'engine_count': engine_count
            }
            
            meta_results.append((horse, meta_score, details))
        
        # スコア順にソート
        meta_results.sort(key=lambda x: x[1], reverse=True)
        return meta_results[:5]
    
    async def analyze_race(
        self,
        race_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        レース分析のメインメソッド
        
        Args:
            race_data: {
                'horses': List[str],
                'jockeys': List[str],
                'posts': List[int],
                'odds': List[float],
                'venue': str,
                'distance': str,
                'track_type': str,
                'track_condition': str
            }
        """
        try:
            logger.info("MetaLogic: レース分析開始")
            
            # 入力データ検証
            horses = race_data.get('horses', [])
            if not horses:
                return {
                    'status': 'error',
                    'message': '馬データがありません'
                }
            
            # コンテキスト準備
            context = {
                'venue': race_data.get('venue', ''),
                'distance': race_data.get('distance', ''),
                'track_type': race_data.get('track_type', '芝'),
                'track_condition': race_data.get('track_condition', '良')
            }
            
            # 各エンジンのスコア計算
            logger.info("MetaLogic: D-Logic計算中...")
            dlogic_scores = await self.calculate_dlogic_scores(horses, context)
            
            logger.info("MetaLogic: I-Logic計算中...")
            ilogic_scores = self.calculate_ilogic_scores(
                horses,
                race_data.get('jockeys', []),
                race_data.get('posts', []),
                context
            )
            
            logger.info("MetaLogic: ViewLogic計算中...")
            viewlogic_scores = self.calculate_viewlogic_scores(
                horses,
                race_data.get('jockeys', []),
                race_data.get('posts', []),
                context
            )
            
            # メタスコア計算
            logger.info("MetaLogic: メタスコア計算中...")
            meta_results = self.calculate_meta_scores(
                dlogic_scores,
                ilogic_scores,
                viewlogic_scores,
                race_data.get('odds', []),
                horses
            )
            
            # 結果フォーマット
            rankings = []
            for rank, (horse, score, details) in enumerate(meta_results, 1):
                rankings.append({
                    'rank': rank,
                    'horse': horse,
                    'meta_score': round(score, 1),
                    'details': details
                })
            
            logger.info(f"MetaLogic: 分析完了 - 上位馬: {rankings[0]['horse'] if rankings else 'なし'}")
            
            return {
                'status': 'success',
                'type': 'metalogic',
                'rankings': rankings,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"MetaLogic分析エラー: {e}")
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'分析中にエラーが発生しました: {str(e)}'
            }

# グローバルインスタンス（遅延初期化のため影響最小）
metalogic_engine = MetaLogicEngine()