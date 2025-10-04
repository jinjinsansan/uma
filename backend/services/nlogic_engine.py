"""
N-Logic Engine - netkeibaのQuerySoftmax手法を参考にしたレース予測エンジン
レース単位で力関係を考慮した支持率予測 → オッズ変換
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from datetime import datetime

# 特徴量の並び順（学習時と共通）
FEATURE_COLUMNS = [
    'knowledge_total_races',
    'knowledge_win_rate',
    'knowledge_place_rate',
    'knowledge_avg_finish',
    'knowledge_avg_popularity',
    'knowledge_avg_corner4',
    'knowledge_avg_kohan3f',
    'track_win_rate',
    'track_avg_finish',
    'distance_aptitude',
    'jockey_win_rate',
    'jockey_place_rate',
    'venue_code',
    'distance',
    'horse_count',
]

logger = logging.getLogger(__name__)

# CatBoostは学習時のみ使用、予測時は動的インポート
try:
    from catboost import CatBoost, Pool
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    logger.warning("CatBoost not available - N-Logic will not work without models")


class NLogicEngine:
    """
    N-Logic予測エンジン
    
    netkeibaの手法を参考に実装：
    1. Rank Model: 順位予測（CatBoost Ranker）
    2. Support Model: 支持率予測（CatBoost + QuerySoftmax）
    3. オッズ変換: 支持率 → オッズ
    """
    
    # 定数
    PAYBACK_RATE = 0.8  # 単勝払戻率
    
    def __init__(
        self,
        data_manager: Optional[Any] = None,
        model_prefix: str = 'nlogic',
    ):
        """初期化"""
        self.rank_model = None
        self.support_model = None
        self._models_loaded = False
        self.model_prefix = model_prefix
        self.rank_model_filename = f"{model_prefix}_rank_model.cbm"
        self.support_model_filename = f"{model_prefix}_support_model.cbm"
        self._model_base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

        # データマネージャー初期化
        self.viewlogic_manager = None
        self.knowledge_manager = None

        if data_manager is not None:
            self.viewlogic_manager = data_manager
            self.knowledge_manager = data_manager
            logger.info("N-Logic: custom data manager injected (%s)", type(data_manager).__name__)
        else:
            try:
                from services.viewlogic_data_manager import ViewLogicDataManager
                self.viewlogic_manager = ViewLogicDataManager()
                self.knowledge_manager = self.viewlogic_manager
                logger.info("N-Logic: ViewLogicDataManager initialized")
            except Exception as e:
                logger.error("N-Logic: ViewLogicDataManager initialization failed: %s", e)
                self.viewlogic_manager = None
                self.knowledge_manager = None

        self._load_models()
        logger.info("N-Logicエンジンを初期化しました (model_prefix=%s)", self.model_prefix)
    
    def _load_models(self):
        """学習済みモデルの読み込み"""
        try:
            if not CATBOOST_AVAILABLE:
                logger.warning("N-Logic: CatBoost未インストール、モデル読み込みスキップ")
                return
            
            rank_model_path = os.path.join(self._model_base_dir, self.rank_model_filename)
            support_model_path = os.path.join(self._model_base_dir, self.support_model_filename)
            
            if os.path.exists(rank_model_path):
                self.rank_model = CatBoost()
                self.rank_model.load_model(rank_model_path)
                logger.info(f"N-Logic: Rank Model読み込み完了: {rank_model_path}")
            else:
                logger.warning(f"N-Logic: Rank Modelが見つかりません: {rank_model_path}")
            
            if os.path.exists(support_model_path):
                self.support_model = CatBoost()
                self.support_model.load_model(support_model_path)
                logger.info(f"N-Logic: Support Model読み込み完了: {support_model_path}")
            else:
                logger.warning(f"N-Logic: Support Modelが見つかりません: {support_model_path}")
            
            if self.rank_model and self.support_model:
                self._models_loaded = True
                logger.info("N-Logic: 両モデル読み込み成功")
                
        except Exception as e:
            logger.error(f"N-Logic: モデル読み込みエラー: {e}")
    
    def predict_race(self, race_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        レース全体のオッズを予測
        
        Args:
            race_data: {
                'horses': ['馬A', '馬B', ...],
                'jockeys': ['騎手1', '騎手2', ...],
                'venue': '東京',
                'race_number': 11,
                'distance': 2000,
                ...
            }
        
        Returns:
            {
                'status': 'success',
                'predictions': {
                    '馬A': {'support_rate': 0.35, 'odds': 2.3, 'rank': 1},
                    '馬B': {'support_rate': 0.25, 'odds': 3.2, 'rank': 2},
                    ...
                },
                'venue': '東京',
                'race_number': 11,
            }
        """
        try:
            # モデル未読み込みチェック
            if not self._models_loaded:
                return {
                    'status': 'error',
                    'message': 'N-Logicモデルが読み込まれていません。学習を実行してください。'
                }
            
            horses = race_data.get('horses', [])
            if len(horses) < 3:
                return {
                    'status': 'error',
                    'message': 'レースには最低3頭の出走馬が必要です。'
                }
            
            # Step 1: 特徴量抽出
            logger.info(f"N-Logic: 特徴量抽出開始（{len(horses)}頭）")
            features_list = self._extract_features_for_race(race_data)
            if not features_list:
                return {
                    'status': 'error',
                    'message': '特徴量の抽出に失敗しました'
                }
            
            # Step 2: 順位予測（Rank Weight生成）
            logger.info("N-Logic: 順位予測開始")
            rank_weights = self._predict_rank_weights(features_list)
            
            # Step 3: 支持率予測
            logger.info("N-Logic: 支持率予測開始")
            support_rates = self._predict_support_rates(features_list, rank_weights)
            
            # Step 4: オッズ変換
            logger.info("N-Logic: オッズ変換開始")
            predictions = self._convert_to_odds(support_rates, horses)
            
            return {
                'status': 'success',
                'type': 'nlogic_prediction',
                'venue': race_data.get('venue', '不明'),
                'race_number': race_data.get('race_number', ''),
                'total_horses': len(horses),
                'predictions': predictions,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"N-Logic予測エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'message': f'予測に失敗しました: {str(e)}'
            }
    
    def _extract_features_for_race(self, race_data: Dict[str, Any]) -> List[Dict[str, float]]:
        """レース内全頭の特徴量抽出"""
        if not self.viewlogic_manager:
            logger.error("N-Logic: ViewLogicDataManager未初期化")
            return []
        
        horses = race_data.get('horses', [])
        jockeys = race_data.get('jockeys', [])
        venue = race_data.get('venue', '')
        distance = race_data.get('distance', 0)
        
        features_list = []
        
        for i, horse_name in enumerate(horses):
            # ナレッジデータ取得
            horse_data = self.viewlogic_manager.get_horse_data(horse_name)
            
            if horse_data and 'races' in horse_data:
                races = horse_data['races']
                
                # 基本統計を計算
                total_races = len(races)
                wins = sum(1 for r in races if self._safe_int(r.get('KAKUTEI_CHAKUJUN')) == 1)
                places = sum(1 for r in races if self._safe_int(r.get('KAKUTEI_CHAKUJUN')) <= 3)
                
                win_rate = wins / total_races if total_races > 0 else 0.0
                place_rate = places / total_races if total_races > 0 else 0.0
                
                # 平均着順
                finishes = [self._safe_int(r.get('KAKUTEI_CHAKUJUN')) for r in races 
                           if self._safe_int(r.get('KAKUTEI_CHAKUJUN')) > 0]
                avg_finish = sum(finishes) / len(finishes) if finishes else 10.0
                
                # 平均人気
                popularities = [self._safe_int(r.get('NINKIJUN')) for r in races 
                               if self._safe_int(r.get('NINKIJUN')) > 0]
                avg_popularity = sum(popularities) / len(popularities) if popularities else 8.0
                
                # 平均4コーナー順位
                corner4s = [self._safe_int(r.get('CORNER4_JUNI')) for r in races 
                           if self._safe_int(r.get('CORNER4_JUNI')) > 0]
                avg_corner4 = sum(corner4s) / len(corner4s) if corner4s else 8.0
                
                # 平均後半3F
                kohan3fs = [self._safe_int(r.get('KOHAN3F_TIME')) for r in races 
                           if self._safe_int(r.get('KOHAN3F_TIME')) > 0]
                avg_kohan3f = sum(kohan3fs) / len(kohan3fs) if kohan3fs else 400
                
                # コース別成績
                track_win_rate, track_avg_finish = self._get_track_stats(races, venue)
                
                # 距離適性
                distance_aptitude = self._calc_distance_aptitude(races, distance)
                
            else:
                # ナレッジがない場合のデフォルト値
                total_races = 0
                win_rate = 0.0
                place_rate = 0.0
                avg_finish = 10.0
                avg_popularity = 8.0
                avg_corner4 = 8.0
                avg_kohan3f = 400
                track_win_rate = 0.0
                track_avg_finish = 10.0
                distance_aptitude = 0.5
            
            # 騎手データ（簡易版）
            jockey_name = jockeys[i] if i < len(jockeys) else None
            jockey_win_rate = 0.12  # TODO: 騎手ナレッジ実装
            jockey_place_rate = 0.32
            
            # 特徴量辞書
            features = {
                'knowledge_total_races': total_races,
                'knowledge_win_rate': win_rate,
                'knowledge_place_rate': place_rate,
                'knowledge_avg_finish': avg_finish,
                'knowledge_avg_popularity': avg_popularity,
                'knowledge_avg_corner4': avg_corner4,
                'knowledge_avg_kohan3f': avg_kohan3f,
                'track_win_rate': track_win_rate,
                'track_avg_finish': track_avg_finish,
                'distance_aptitude': distance_aptitude,
                'jockey_win_rate': jockey_win_rate,
                'jockey_place_rate': jockey_place_rate,
                'venue_code': self._get_venue_code(venue),
                'distance': float(distance),
                'horse_count': len(horses),
            }
            
            features_list.append(features)
        
        return features_list
    
    def _safe_int(self, value, default=0) -> int:
        """安全に整数に変換"""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return default
    
    def _get_track_stats(self, races: List[Dict], venue: str) -> Tuple[float, float]:
        """コース別成績を取得"""
        # 競馬場コードマップ
        venue_code_map = {
            '札幌': '01', '函館': '02', '福島': '03', '新潟': '04',
            '東京': '05', '中山': '06', '中京': '07', '京都': '08',
            '阪神': '09', '小倉': '10'
        }
        
        target_code = venue_code_map.get(venue, '')
        if not target_code:
            return 0.0, 10.0
        
        # 同じ競馬場のレースを抽出
        track_races = [r for r in races 
                      if r.get('KEIBAJO_CODE', '').zfill(2) == target_code]
        
        if not track_races:
            return 0.0, 10.0
        
        # 勝率計算
        wins = sum(1 for r in track_races 
                  if self._safe_int(r.get('KAKUTEI_CHAKUJUN')) == 1)
        win_rate = wins / len(track_races)
        
        # 平均着順計算
        finishes = [self._safe_int(r.get('KAKUTEI_CHAKUJUN')) 
                   for r in track_races 
                   if self._safe_int(r.get('KAKUTEI_CHAKUJUN')) > 0]
        avg_finish = sum(finishes) / len(finishes) if finishes else 10.0
        
        return win_rate, avg_finish
    
    def _calc_distance_aptitude(self, races: List[Dict], target_distance: int) -> float:
        """距離適性を計算"""
        if not races or target_distance == 0:
            return 0.5
        
        # ±200m以内のレースを抽出
        similar_races = [r for r in races 
                        if abs(self._safe_int(r.get('KYORI')) - target_distance) <= 200]
        
        if not similar_races:
            return 0.5
        
        # 勝率を返す
        wins = sum(1 for r in similar_races 
                  if self._safe_int(r.get('KAKUTEI_CHAKUJUN')) == 1)
        
        return wins / len(similar_races)
    
    def _get_venue_code(self, venue: str) -> int:
        """競馬場コードを取得"""
        venue_map = {
            '札幌': 1, '函館': 2, '福島': 3, '新潟': 4,
            '東京': 5, '中山': 6, '中京': 7, '京都': 8,
            '阪神': 9, '小倉': 10
        }
        return venue_map.get(venue, 0)
    
    def _predict_rank_weights(self, features_list: List[Dict]) -> np.ndarray:
        """順位予測（Rank Weight生成）"""
        if not self.rank_model:
            logger.warning("N-Logic: Rank Model未読み込み、均等weightを返します")
            n = len(features_list)
            return np.ones(n) / n
        
        X = np.array([[features.get(key, 0.0) for key in FEATURE_COLUMNS] for features in features_list])
        predictions = self.rank_model.predict(X)
        exp_preds = np.exp(predictions - np.max(predictions))
        denom = np.sum(exp_preds)
        if denom <= 0:
            return np.ones_like(predictions) / len(predictions)
        return exp_preds / denom
    
    def _predict_support_rates(
        self, 
        features_list: List[Dict], 
        rank_weights: np.ndarray
    ) -> np.ndarray:
        """支持率予測（QuerySoftmax的手法）"""
        if not self.support_model:
            logger.warning("N-Logic: Support Model未読み込み、均等支持率を返します")
            n = len(features_list)
            return np.ones(n) / n
        
        X = []
        for i, features in enumerate(features_list):
            row = [features.get(key, 0.0) for key in FEATURE_COLUMNS]
            row.append(rank_weights[i])
            X.append(row)
        X = np.array(X)
        predictions = self.support_model.predict(X)
        exp_preds = np.exp(predictions - np.max(predictions))
        denom = np.sum(exp_preds)
        if denom <= 0:
            return np.ones_like(predictions) / len(predictions)
        return exp_preds / denom
    
    def _convert_to_odds(
        self,
        support_rates: np.ndarray,
        horse_names: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """支持率 → オッズ変換"""
        results = {}
        
        # 順位付け（支持率の高い順）
        ranked_indices = np.argsort(-support_rates)
        
        for i, horse_name in enumerate(horse_names):
            support_rate = support_rates[i]
            odds = self.PAYBACK_RATE / support_rate if support_rate > 0.001 else 999.9
            rank = int(np.where(ranked_indices == i)[0][0] + 1)
            
            results[horse_name] = {
                'support_rate': float(support_rate),
                'odds': round(odds, 1),
                'rank': rank,
                'probability': float(support_rate),
            }
        
        return results
