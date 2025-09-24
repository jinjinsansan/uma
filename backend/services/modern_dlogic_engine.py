"""
モダンD-Logic計算エンジン（イクイノックス基準）
レースアナリシス専用の新しい計算システム
"""
import logging
from typing import Dict, Any, Optional, List
from .fast_dlogic_engine import FastDLogicEngine
from .extended_knowledge_manager import get_extended_knowledge_manager

logger = logging.getLogger(__name__)

class ModernDLogicEngine:
    """イクイノックスを基準（100点）とした新しいD-Logic計算エンジン"""
    
    # 基準馬（現代最強馬）
    BASE_HORSE = "イクイノックス"
    
    # トラックコード → 開催場マッピング
    TRACK_CODE_TO_VENUE = {
        '11': '東京',
        '12': '中山',
        '13': '京都',
        '14': '阪神',
        '15': '中京',
        '16': '新潟',
        '17': '札幌',
        '18': '函館',
        '19': '福島',
        '20': '小倉'
    }
    
    # クラス補正係数
    CLASS_FACTORS = {
        'G1': 1.30,
        'G2': 1.20,
        'G3': 1.15,
        'オープン': 1.10,
        'L': 1.08,  # リステッド
        '3勝': 1.05,
        '2勝': 1.00,
        '1勝': 0.95,
        '未勝利': 0.90,
        '新馬': 0.85
    }
    
    # 馬場状態補正
    TRACK_CONDITION_BONUS = {
        '良': 0,
        '稍重': 0,  # 馬によって変わるため、個別に計算
        '重': 0,
        '不良': 0
    }
    
    # ベイズ推定パラメータ
    PRIOR_MEAN = 72.0  # 全馬の平均的なスコア（やや控えめ）
    PRIOR_WEIGHT = 5   # 仮想的な5レース分の重み
    
    # 血統による事前分布調整
    TOP_SIRES = {
        'ディープインパクト': 5,
        'キタサンブラック': 4,
        'ロードカナロア': 3,
        'オルフェーヴル': 3,
        'ハーツクライ': 2,
        'エピファネイア': 2,
        'ドゥラメンテ': 2,
        'モーリス': 2
    }
    
    def __init__(self, base_engine: FastDLogicEngine):
        """
        Args:
            base_engine: 既存のD-Logicエンジン（ダンスインザダーク基準）
        """
        self.base_engine = base_engine
        # レース分析V2用の拡張ナレッジデータを使用
        try:
            # 拡張ナレッジマネージャーから取得（9回分のデータが必要）
            extended_manager = get_extended_knowledge_manager()
            self.knowledge = extended_manager.get_all_horses()
            logger.info(f"拡張ナレッジデータ取得成功: {len(self.knowledge)}頭")
            # データが空または少なすぎる場合はエラー
            if not self.knowledge or len(self.knowledge) < 1000:
                raise ValueError(f"拡張ナレッジデータが不正です。取得数: {len(self.knowledge)}頭")
        except Exception as e:
            # エラー: レース分析には拡張データが必須
            logger.error(f"拡張ナレッジデータの取得に失敗しました: {e}")
            logger.error("レース分析V2には9回分の過去データが含まれる拡張ナレッジファイルが必要です")
            logger.error("CDN URL: https://pub-059afaafefa84116b57d57e0a72b81bd.r2.dev/dlogic_extended_knowledge.json")
            # 絶対に通常ナレッジデータにフォールバックしない！
            raise RuntimeError("拡張ナレッジデータの取得に失敗しました。レース分析V2を使用できません。")
        
        # イクイノックスの基準スコアを取得
        self.equinox_base_score = self._get_equinox_base_score()
        logger.info(f"レースアナリシスV2基準: {self.equinox_base_score}")
    
    def _get_equinox_base_score(self) -> float:
        """イクイノックスの現行D-Logicスコアを取得"""
        try:
            # 拡張ナレッジにイクイノックスのデータがあるか確認
            if self.BASE_HORSE in self.knowledge:
                # 拡張データを使用して計算
                original_knowledge = self.base_engine.raw_manager.knowledge_data
                try:
                    # 拡張ナレッジデータを一時的に設定
                    extended_data = {}
                    for h_name, h_races in self.knowledge.items():
                        if isinstance(h_races, list):
                            # 拡張形式：直接レースリスト
                            extended_data[h_name] = {'races': h_races}
                        else:
                            # 既に辞書形式
                            extended_data[h_name] = h_races
                    
                    self.base_engine.raw_manager.knowledge_data = {'horses': extended_data}
                    # イクイノックスのスコアを計算
                    equinox_data = self.base_engine.analyze_single_horse(self.BASE_HORSE)
                    
                    if isinstance(equinox_data, dict) and 'total_score' in equinox_data:
                        return equinox_data['total_score']
                    else:
                        # デフォルト値（イクイノックスは通常90点以上）
                        return 92.0
                finally:
                    # 元のナレッジデータに戻す
                    self.base_engine.raw_manager.knowledge_data = original_knowledge
            else:
                # 通常のナレッジで試す
                equinox_data = self.base_engine.analyze_single_horse(self.BASE_HORSE)
                if isinstance(equinox_data, dict) and 'total_score' in equinox_data:
                    return equinox_data['total_score']
                else:
                    return 92.0
        except Exception as e:
            logger.warning(f"イクイノックスの基準スコア取得エラー: {e}")
            return 92.0  # デフォルト値
    
    def calculate_horse_score(self, horse_name: str, context: Dict[str, Any], enable_bayesian: bool = True) -> Dict[str, Any]:
        """
        馬の総合スコアを計算（イクイノックス基準）
        
        Args:
            horse_name: 馬名
            context: レース情報（venue, grade, track_condition, distance等）
        
        Returns:
            {
                'base_score': 基本スコア（イクイノックス基準）,
                'venue_bonus': 開催場適性ボーナス,
                'class_factor': クラス補正係数,
                'track_bonus': 馬場適性ボーナス,
                'final_score': 最終スコア,
                'details': 詳細情報
            }
        """
        # データ確認（新旧両形式に対応）
        horse_data = self.knowledge.get(horse_name, [])  # 拡張ナレッジは馬名が直接キーで値はリスト
        if isinstance(horse_data, list):
            # 新形式: 直接レースのリスト
            races = horse_data
            # 旧形式互換のため、辞書に包む（ただし後の処理でもリスト対応が必要）
        else:
            # 旧形式: {'races': [...]}
            races = horse_data.get('races', [])
        race_count = len(races)
        
        result = {
            'horse_name': horse_name,
            'base_score': 50.0,  # デフォルト
            'venue_bonus': 0,
            'venue_distance_bonus': 0,
            'class_factor': 1.0,
            'track_bonus': 0,
            'final_score': 50.0,
            'race_count': race_count,
            'data_confidence': 'none',
            'estimation_method': 'default',
            'details': {}
        }
        
        try:
            # データ量に応じた処理分岐
            if race_count >= 5 or not enable_bayesian:
                # 通常計算（データ十分 or ベイズ無効）
                result['estimation_method'] = 'full_data'
                result['data_confidence'] = 'high' if race_count >= 9 else 'medium'
                
                # 1. 基本スコア計算
                # 拡張ナレッジデータがある場合は、より多くのレースデータを使用して計算
                if race_count >= 5:
                    # 拡張データを使用してD-Logic計算（エンジンに拡張データを渡す）
                    # 注: base_engineのraw_managerを一時的に拡張データで置き換える
                    original_knowledge = self.base_engine.raw_manager.knowledge_data
                    try:
                        # 拡張ナレッジデータを一時的に設定
                        # 拡張ナレッジの形式に合わせて辞書形式に変換
                        extended_data = {}
                        for h_name, h_races in self.knowledge.items():
                            if isinstance(h_races, list):
                                # 拡張形式：直接レースリスト
                                extended_data[h_name] = {'races': h_races}
                            else:
                                # 既に辞書形式
                                extended_data[h_name] = h_races
                        
                        self.base_engine.raw_manager.knowledge_data = {'horses': extended_data}
                        # 拡張データで計算実行
                        original_data = self.base_engine.analyze_single_horse(horse_name)
                        
                        if isinstance(original_data, dict) and 'total_score' in original_data:
                            original_score = original_data['total_score']
                            # イクイノックス基準に変換（イクイノックス=100）
                            result['base_score'] = (original_score / self.equinox_base_score) * 100
                            result['d_logic_scores'] = original_data.get('d_logic_scores', {})
                    finally:
                        # 元のナレッジデータに戻す
                        self.base_engine.raw_manager.knowledge_data = original_knowledge
                else:
                    # データ不足の場合は通常のエンジンを使用
                    original_data = self.base_engine.analyze_single_horse(horse_name)
                    if isinstance(original_data, dict) and 'total_score' in original_data:
                        original_score = original_data['total_score']
                        result['base_score'] = (original_score / self.equinox_base_score) * 100
                    
            elif race_count > 0 and enable_bayesian:
                # ベイズ推定モード（1-4走）
                result['estimation_method'] = 'bayesian'
                result['data_confidence'] = 'low'
                result['base_score'] = self._calculate_bayesian_score(horse_name, horse_data, race_count)
                
            else:
                # データなし
                result['estimation_method'] = 'default'
                result['data_confidence'] = 'none'
                result['base_score'] = self._get_default_score(horse_data)
            
            # 2. 開催場・距離適性ボーナス（統合評価）
            venue = context.get('venue', '')
            distance = context.get('distance', '')
            if venue and distance:
                # 距離文字列から数値を抽出（例: "2000m" → 2000）
                try:
                    distance_num = int(''.join(filter(str.isdigit, distance)))
                    result['venue_distance_bonus'] = self._calculate_venue_distance_aptitude(horse_name, venue, distance_num)
                except:
                    result['venue_distance_bonus'] = 0
            else:
                result['venue_distance_bonus'] = 0
            
            # 3. クラス補正
            grade = context.get('grade', '')
            result['class_factor'] = self.CLASS_FACTORS.get(grade, 1.0)
            
            # 5. 馬場適性ボーナス
            track_condition = context.get('track_condition', '良')
            result['track_bonus'] = self._calculate_track_aptitude(horse_name, track_condition)
            
            # 4. 最終スコア計算
            result['final_score'] = (
                result['base_score'] * result['class_factor'] +
                result['venue_distance_bonus'] +
                result['track_bonus']
            )
            
            # スコアを0-150の範囲に制限（イクイノックス基準では高得点も可能）
            result['final_score'] = max(0, min(150, result['final_score']))
            
            # 6. 詳細情報
            if 'original_data' in locals():
                result['details'] = {
                    'original_system_score': original_data.get('total_score', 50.0),
                    'venue_history': self._get_venue_history(horse_name, venue),
                    'track_condition_history': self._get_track_condition_history(horse_name, track_condition)
                }
            else:
                result['details'] = {
                    'venue_history': self._get_venue_history(horse_name, venue),
                    'track_condition_history': self._get_track_condition_history(horse_name, track_condition)
                }
            
        except Exception as e:
            logger.error(f"馬スコア計算エラー（{horse_name}）: {e}")
        
        return result
    
    def _calculate_bayesian_score(self, horse_name: str, horse_data: Dict, race_count: int) -> float:
        """ベイズ推定による基本スコア計算"""
        try:
            # 1. 事前分布の調整
            prior_score = self._get_adjusted_prior(horse_data)
            
            # 2. 限定データからのスコア計算
            if isinstance(horse_data, list):
                races = horse_data
            else:
                races = horse_data.get('races', [])
            if races:
                # 既存D-Logicでの計算を試みる（拡張データを使用）
                try:
                    original_knowledge = self.base_engine.raw_manager.knowledge_data
                    try:
                        # 拡張ナレッジデータを一時的に設定
                        # 拡張ナレッジの形式に合わせて辞書形式に変換
                        extended_data = {}
                        for h_name, h_races in self.knowledge.items():
                            if isinstance(h_races, list):
                                # 拡張形式：直接レースリスト
                                extended_data[h_name] = {'races': h_races}
                            else:
                                # 既に辞書形式
                                extended_data[h_name] = h_races
                        
                        self.base_engine.raw_manager.knowledge_data = {'horses': extended_data}
                        # 拡張データで計算実行
                        original_data = self.base_engine.analyze_single_horse(horse_name)
                        
                        if isinstance(original_data, dict) and 'total_score' in original_data:
                            original_score = original_data['total_score']
                            # イクイノックス基準に変換
                            limited_score = (original_score / self.equinox_base_score) * 100
                        else:
                            # フォールバック：着順から推定
                            limited_score = self._estimate_from_results(races)
                    finally:
                        # 元のナレッジデータに戻す
                        self.base_engine.raw_manager.knowledge_data = original_knowledge
                except:
                    limited_score = self._estimate_from_results(races)
                
                # 3. ベイズ推定（加重平均）
                weight_actual = race_count
                weight_prior = self.PRIOR_WEIGHT
                
                bayesian_score = (
                    (limited_score * weight_actual + prior_score * weight_prior) /
                    (weight_actual + weight_prior)
                )
                
                return bayesian_score
            else:
                return prior_score
                
        except Exception as e:
            logger.error(f"ベイズ推定エラー（{horse_name}）: {e}")
            return self.PRIOR_MEAN
    
    def _get_default_score(self, horse_data: Dict) -> float:
        """デフォルトスコア（データなしの場合）"""
        return self._get_adjusted_prior(horse_data)
    
    def _get_adjusted_prior(self, horse_data: Dict) -> float:
        """馬の属性から事前分布を調整"""
        prior_score = self.PRIOR_MEAN
        
        # データ形式の確認
        if isinstance(horse_data, list):
            # 新形式: 直接レースのリスト
            races = horse_data
            # 血統情報は取得できない（レースデータのみ）
            sire = ''
        else:
            # 旧形式: {'races': [...], 'sire': ...}
            races = horse_data.get('races', [])
            sire = horse_data.get('sire', '')
        
        # 血統補正
        if sire in self.TOP_SIRES:
            prior_score += self.TOP_SIRES[sire]
        
        # 年齢補正（レースデータから推定）
        if races and len(races) > 0 and isinstance(races[0], dict) and races[0].get('BAREI'):
            try:
                age = int(races[0]['BAREI'])
                if age <= 3:
                    prior_score += 2  # 若馬は成長余地
                elif age >= 7:
                    prior_score -= 3  # 高齢馬
            except:
                pass
        
        # 性別補正
        if races and len(races) > 0 and isinstance(races[0], dict) and races[0].get('SEIBETSU_CODE'):
            sex_code = races[0]['SEIBETSU_CODE']
            if sex_code == '2':  # 牝馬
                prior_score -= 2
        
        return max(60, min(85, prior_score))  # 60-85の範囲に制限
    
    def _estimate_from_results(self, races: List[Dict]) -> float:
        """着順からスコアを推定"""
        if not races:
            return self.PRIOR_MEAN
            
        total_score = 0
        count = 0
        
        for race in races[:5]:  # 最新5走まで
            chakujun = race.get('KAKUTEI_CHAKUJUN', '99')
            try:
                position = int(chakujun) if chakujun != '00' else 99
                if position == 1:
                    total_score += 85
                elif position <= 3:
                    total_score += 75
                elif position <= 5:
                    total_score += 68
                else:
                    total_score += 60
                count += 1
            except:
                pass
        
        return total_score / count if count > 0 else self.PRIOR_MEAN
    
    def _calculate_venue_distance_aptitude(self, horse_name: str, venue: str, distance: int) -> float:
        """開催場・距離の複合適性を計算（-10～+10）"""
        try:
            horse_data = self.knowledge.get(horse_name, [])
            if isinstance(horse_data, list):
                past_races = horse_data
            else:
                past_races = horse_data.get('races', [])
            
            # 指定開催場かつ指定距離±200mでの成績を抽出
            distance_min = distance - 200
            distance_max = distance + 200
            
            venue_distance_races = []
            all_venue_races = []  # 開催場のみ一致
            all_distance_races = []  # 距離のみ一致
            
            for race in past_races:
                if isinstance(race, dict):
                    # トラックコードから開催場を判定
                    track_code = str(race.get('TRACK_CODE', ''))
                    race_venue = self.TRACK_CODE_TO_VENUE.get(track_code, '')
                    race_distance = int(race.get('KYORI', 0))
                    
                    # 着順を取得
                    chakujun = race.get('KAKUTEI_CHAKUJUN', '99')
                    try:
                        result = int(chakujun) if chakujun != '00' else 99
                    except:
                        result = 99
                    
                    # 開催場と距離の両方が一致
                    if race_venue == venue and distance_min <= race_distance <= distance_max:
                        venue_distance_races.append({'result': result})
                    
                    # 開催場のみ一致
                    if race_venue == venue:
                        all_venue_races.append({'result': result})
                    
                    # 距離のみ一致
                    if distance_min <= race_distance <= distance_max:
                        all_distance_races.append({'result': result})
            
            # 優先順位: 1. 開催場・距離両方一致、2. 開催場のみ、3. 距離のみ
            if venue_distance_races:
                # 開催場・距離の両方が一致するデータがある場合
                total_races = len(venue_distance_races)
                wins = sum(1 for r in venue_distance_races if r['result'] == 1)
                top3 = sum(1 for r in venue_distance_races if r['result'] <= 3)
                weight = 1.0  # 完全一致は重み1.0
                
            elif all_venue_races and all_distance_races:
                # 開催場と距離それぞれのデータがある場合は加重平均
                venue_wins = sum(1 for r in all_venue_races if r['result'] == 1)
                venue_top3 = sum(1 for r in all_venue_races if r['result'] <= 3)
                venue_total = len(all_venue_races)
                
                dist_wins = sum(1 for r in all_distance_races if r['result'] == 1)
                dist_top3 = sum(1 for r in all_distance_races if r['result'] <= 3)
                dist_total = len(all_distance_races)
                
                # 開催場60%、距離40%の重み付け
                total_races = venue_total * 0.6 + dist_total * 0.4
                wins = venue_wins * 0.6 + dist_wins * 0.4
                top3 = venue_top3 * 0.6 + dist_top3 * 0.4
                weight = 0.8  # 推定値なので重み0.8
                
            else:
                return 0  # データなし
            
            # 勝率と複勝率から適性スコアを計算
            win_rate = wins / total_races if total_races > 0 else 0
            place_rate = top3 / total_races if total_races > 0 else 0
            
            # 適性スコア（勝率重視）
            aptitude_score = (win_rate * 0.7 + place_rate * 0.3 - 0.3) * 20 * weight
            
            return max(-10, min(10, aptitude_score))  # -10～+10の範囲に制限
            
        except Exception as e:
            logger.error(f"開催場・距離適性計算エラー（{horse_name}, {venue}, {distance}）: {e}")
            return 0
    
    def _calculate_venue_aptitude(self, horse_name: str, venue: str) -> float:
        """開催場適性を計算（-10～+10）"""
        try:
            horse_data = self.knowledge.get(horse_name, [])
            if isinstance(horse_data, list):
                past_races = horse_data
            else:
                past_races = horse_data.get('races', [])
            
            # 指定開催場での成績を抽出
            venue_races = []
            for race in past_races:
                if isinstance(race, dict):
                    # トラックコードから開催場を判定
                    track_code = str(race.get('TRACK_CODE', ''))
                    race_venue = self.TRACK_CODE_TO_VENUE.get(track_code, '')
                    if race_venue == venue:
                        # 着順を取得（KAKUTEI_CHAKUJUNは文字列で00=未出走、01=1着...）
                        chakujun = race.get('KAKUTEI_CHAKUJUN', '99')
                        try:
                            result = int(chakujun) if chakujun != '00' else 99
                        except:
                            result = 99
                        venue_races.append({
                            'result': result,
                            'distance': race.get('KYORI', 0)
                        })
            
            if not venue_races:
                return 0  # データなし
            
            # 着順から適性を計算
            total_races = len(venue_races)
            wins = sum(1 for r in venue_races if r['result'] == 1)
            top3 = sum(1 for r in venue_races if r['result'] <= 3)
            
            # 勝率と複勝率から適性スコアを計算
            win_rate = wins / total_races
            place_rate = top3 / total_races
            
            # 適性スコア（勝率重視）
            aptitude_score = (win_rate * 0.7 + place_rate * 0.3 - 0.3) * 20
            
            return max(-10, min(10, aptitude_score))
            
        except Exception as e:
            logger.error(f"開催場適性計算エラー（{horse_name}, {venue}）: {e}")
            return 0
    
    def _calculate_track_aptitude(self, horse_name: str, track_condition: str) -> float:
        """馬場適性を計算（-5～+5）"""
        if track_condition == '良':
            return 0  # 良馬場は標準
        
        try:
            horse_data = self.knowledge.get(horse_name, [])
            if isinstance(horse_data, list):
                past_races = horse_data
            else:
                past_races = horse_data.get('races', [])
            
            # 指定馬場状態での成績を抽出
            condition_races = []
            for race in past_races:
                if isinstance(race, dict):
                    # 馬場状態コードから判定（1=良、2=稍重、3=重、4=不良）
                    shiba_code = int(race.get('SHIBA_BABAJOTAI_CODE', 0))
                    dirt_code = int(race.get('DIRT_BABAJOTAI_CODE', 0))
                    # 芝またはダートの馬場状態を取得
                    baba_code = shiba_code if shiba_code > 0 else dirt_code
                    
                    # 馬場状態の変換
                    baba_map = {1: '良', 2: '稍重', 3: '重', 4: '不良'}
                    race_condition = baba_map.get(int(baba_code), '良')
                    
                    if race_condition == track_condition:
                        chakujun = race.get('KAKUTEI_CHAKUJUN', '99')
                        try:
                            result = int(chakujun) if chakujun != '00' else 99
                        except:
                            result = 99
                        condition_races.append({'result': result})
            
            if not condition_races:
                return 0  # データなし
            
            # 成績から適性を計算
            total_races = len(condition_races)
            top3 = sum(1 for r in condition_races if int(r['result']) <= 3)
            
            place_rate = top3 / total_races
            
            # 適性スコア（複勝率30%を基準）
            aptitude_score = (place_rate - 0.3) * 10
            
            return max(-5, min(5, aptitude_score))
            
        except Exception as e:
            logger.error(f"馬場適性計算エラー（{horse_name}, {track_condition}）: {e}")
            return 0
    
    def _get_venue_history(self, horse_name: str, venue: str) -> Dict[str, Any]:
        """開催場での過去成績を取得"""
        try:
            horse_data = self.knowledge.get(horse_name, [])
            if isinstance(horse_data, list):
                past_races = horse_data
            else:
                past_races = horse_data.get('races', [])
            
            venue_races = []
            for race in past_races:
                if isinstance(race, dict):
                    track_code = str(race.get('TRACK_CODE', ''))
                    race_venue = self.TRACK_CODE_TO_VENUE.get(track_code, '')
                    if race_venue == venue:
                        chakujun = race.get('KAKUTEI_CHAKUJUN', '99')
                        try:
                            result = int(chakujun) if chakujun != '00' else 99
                        except:
                            result = 99
                        venue_races.append({'result': result})
            
            if not venue_races:
                return {'total': 0, 'wins': 0, 'places': 0}
            
            return {
                'total': len(venue_races),
                'wins': sum(1 for r in venue_races if int(r['result']) == 1),
                'places': sum(1 for r in venue_races if int(r['result']) <= 3)
            }
            
        except Exception:
            return {'total': 0, 'wins': 0, 'places': 0}
    
    def _get_track_condition_history(self, horse_name: str, track_condition: str) -> Dict[str, Any]:
        """馬場状態別の過去成績を取得"""
        try:
            horse_data = self.knowledge.get(horse_name, [])
            if isinstance(horse_data, list):
                past_races = horse_data
            else:
                past_races = horse_data.get('races', [])
            
            condition_races = []
            for race in past_races:
                if isinstance(race, dict):
                    # 馬場状態コードから判定
                    shiba_code = int(race.get('SHIBA_BABAJOTAI_CODE', 0))
                    dirt_code = int(race.get('DIRT_BABAJOTAI_CODE', 0))
                    baba_code = shiba_code if shiba_code > 0 else dirt_code
                    
                    baba_map = {1: '良', 2: '稍重', 3: '重', 4: '不良'}
                    race_condition = baba_map.get(int(baba_code), '良')
                    
                    if race_condition == track_condition:
                        chakujun = race.get('KAKUTEI_CHAKUJUN', '99')
                        try:
                            result = int(chakujun) if chakujun != '00' else 99
                        except:
                            result = 99
                        condition_races.append({'result': result})
            
            if not condition_races:
                return {'total': 0, 'wins': 0, 'places': 0}
            
            return {
                'total': len(condition_races),
                'wins': sum(1 for r in condition_races if int(r['result']) == 1),
                'places': sum(1 for r in condition_races if int(r['result']) <= 3)
            }
            
        except Exception:
            return {'total': 0, 'wins': 0, 'places': 0}