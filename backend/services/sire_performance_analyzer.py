"""
種牡馬（父・母父）産駒成績分析エンジン
高速化のためインデックスを使用（O(n) → O(1)）
シングルトンパターンで起動時に1回だけ初期化
"""

import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class SirePerformanceAnalyzer:
    """種牡馬産駒成績を高速に分析するクラス"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初期化（シングルトンなので1回だけ実行）"""
        if self._initialized:
            return

        logger.info("🏇 種牡馬産駒成績分析エンジン初期化開始...")

        # DLogicRawDataManagerからデータ取得
        from services.dlogic_raw_data_manager import DLogicRawDataManager
        self.dlogic_manager = DLogicRawDataManager()

        # インデックス
        self.sire_index = defaultdict(list)  # 父名 → 産駒情報リスト
        self.broodmare_sire_index = defaultdict(list)  # 母父名 → 産駒情報リスト

        # インデックスを構築
        self._build_index()

        self._initialized = True
        logger.info(f"✅ 種牡馬産駒成績分析エンジン初期化完了（父: {len(self.sire_index)}頭、母父: {len(self.broodmare_sire_index)}頭）")

    def _build_index(self):
        """血統インデックスを構築（起動時に1回だけ）"""
        try:
            horses_data = self.dlogic_manager.knowledge_data.get('horses', {})

            # 全馬データを1回だけスキャン
            for horse_name, horse_data in horses_data.items():
                races = horse_data.get('races', [])
                if not races:
                    continue

                # 最新レースから血統情報を取得
                latest_race = races[0]
                sire = latest_race.get('sire')
                broodmare_sire = latest_race.get('broodmare_sire')

                # 産駒情報を保存（レースデータ付き）
                offspring_info = {
                    'name': horse_name,
                    'races': races  # 全レースデータを保持
                }

                # 父のインデックスに追加
                if sire:
                    self.sire_index[sire].append(offspring_info)

                # 母父のインデックスに追加
                if broodmare_sire:
                    self.broodmare_sire_index[broodmare_sire].append(offspring_info)

            logger.info(f"📊 血統インデックス構築完了: {len(horses_data)}頭を処理")

        except Exception as e:
            logger.error(f"血統インデックス構築エラー: {e}")

    def analyze_sire_performance(self, sire_name: str, venue_code: str, distance: str) -> Dict:
        """
        種牡馬の産駒成績を高速分析

        Args:
            sire_name: 種牡馬名
            venue_code: 会場コード（例: '06' for 中山）
            distance: 距離（文字列、例: '2200'）

        Returns:
            産駒成績の辞書
        """
        try:
            # インデックスから産駒リストを即座に取得（O(1)）
            offspring_list = self.sire_index.get(sire_name, [])

            if not offspring_list:
                return {'message': 'データなし'}

            # 該当コース・距離の成績を集計
            total_races = 0
            wins = 0
            places = 0  # 1-3着

            # 馬場状態別の集計
            by_condition = {
                '良': {'races': 0, 'wins': 0, 'places': 0},
                '稍重': {'races': 0, 'wins': 0, 'places': 0},
                '重': {'races': 0, 'wins': 0, 'places': 0},
                '不良': {'races': 0, 'wins': 0, 'places': 0}
            }

            # 産駒のレースデータを分析
            for offspring in offspring_list:
                for race in offspring['races']:
                    # 会場と距離が一致するかチェック
                    if race.get('KEIBAJO_CODE') != venue_code:
                        continue
                    if race.get('KYORI') != distance:
                        continue

                    total_races += 1

                    # 着順を取得
                    order = race.get('KAKUTEI_CHAKUJUN', '')
                    try:
                        order_num = int(order)
                        if order_num == 1:
                            wins += 1
                            places += 1
                        elif order_num <= 3:
                            places += 1
                    except (ValueError, TypeError):
                        continue

                    # 馬場状態別に集計（芝とダートで別フィールド）
                    track_condition = race.get('SHIBA_BABAJOTAI_CODE', race.get('DIRT_BABAJOTAI_CODE', ''))
                    condition_name = self._get_track_condition(track_condition)

                    if condition_name in by_condition:
                        by_condition[condition_name]['races'] += 1
                        try:
                            if int(order) == 1:
                                by_condition[condition_name]['wins'] += 1
                            if int(order) <= 3:
                                by_condition[condition_name]['places'] += 1
                        except:
                            pass

            # 結果がない場合
            if total_races == 0:
                return {'message': 'データなし'}

            # 率を計算
            win_rate = (wins / total_races * 100) if total_races > 0 else 0
            place_rate = (places / total_races * 100) if total_races > 0 else 0

            # 馬場状態別の率を計算
            for condition in by_condition.values():
                if condition['races'] > 0:
                    condition['win_rate'] = condition['wins'] / condition['races'] * 100
                    condition['place_rate'] = condition['places'] / condition['races'] * 100
                else:
                    condition['win_rate'] = 0
                    condition['place_rate'] = 0

            return {
                'sire_name': sire_name,
                'total_races': total_races,
                'wins': wins,
                'win_rate': win_rate,
                'places': places,
                'place_rate': place_rate,
                'by_condition': [
                    {
                        'condition': cond_name,
                        'races': cond_data['races'],
                        'wins': cond_data['wins'],
                        'win_rate': cond_data['win_rate'],
                        'places': cond_data['places'],
                        'place_rate': cond_data['place_rate']
                    }
                    for cond_name, cond_data in by_condition.items()
                ]
            }

        except Exception as e:
            logger.error(f"産駒成績分析エラー（{sire_name}）: {e}")
            return {'message': 'エラー発生'}

    def analyze_broodmare_sire_performance(self, broodmare_sire_name: str, venue_code: str, distance: str) -> Dict:
        """
        母父の産駒成績を高速分析

        Args:
            broodmare_sire_name: 母父名
            venue_code: 会場コード
            distance: 距離

        Returns:
            産駒成績の辞書
        """
        try:
            # インデックスから産駒リストを即座に取得（O(1)）
            offspring_list = self.broodmare_sire_index.get(broodmare_sire_name, [])

            if not offspring_list:
                return {'message': 'データなし'}

            # 同じロジックで集計（コピーを避けるため別メソッドにすることも可能）
            total_races = 0
            wins = 0
            places = 0

            by_condition = {
                '良': {'races': 0, 'wins': 0, 'places': 0},
                '稍重': {'races': 0, 'wins': 0, 'places': 0},
                '重': {'races': 0, 'wins': 0, 'places': 0},
                '不良': {'races': 0, 'wins': 0, 'places': 0}
            }

            for offspring in offspring_list:
                for race in offspring['races']:
                    if race.get('KEIBAJO_CODE') != venue_code:
                        continue
                    if race.get('KYORI') != distance:
                        continue

                    total_races += 1

                    order = race.get('KAKUTEI_CHAKUJUN', '')
                    try:
                        order_num = int(order)
                        if order_num == 1:
                            wins += 1
                            places += 1
                        elif order_num <= 3:
                            places += 1
                    except (ValueError, TypeError):
                        continue

                    track_condition = race.get('SHIBA_BABAJOTAI_CODE', race.get('DIRT_BABAJOTAI_CODE', ''))
                    condition_name = self._get_track_condition(track_condition)

                    if condition_name in by_condition:
                        by_condition[condition_name]['races'] += 1
                        try:
                            if int(order) == 1:
                                by_condition[condition_name]['wins'] += 1
                            if int(order) <= 3:
                                by_condition[condition_name]['places'] += 1
                        except:
                            pass

            if total_races == 0:
                return {'message': 'データなし'}

            win_rate = (wins / total_races * 100) if total_races > 0 else 0
            place_rate = (places / total_races * 100) if total_races > 0 else 0

            for condition in by_condition.values():
                if condition['races'] > 0:
                    condition['win_rate'] = condition['wins'] / condition['races'] * 100
                    condition['place_rate'] = condition['places'] / condition['races'] * 100
                else:
                    condition['win_rate'] = 0
                    condition['place_rate'] = 0

            return {
                'sire_name': broodmare_sire_name,
                'total_races': total_races,
                'wins': wins,
                'win_rate': win_rate,
                'places': places,
                'place_rate': place_rate,
                'by_condition': [
                    {
                        'condition': cond_name,
                        'races': cond_data['races'],
                        'wins': cond_data['wins'],
                        'win_rate': cond_data['win_rate'],
                        'places': cond_data['places'],
                        'place_rate': cond_data['place_rate']
                    }
                    for cond_name, cond_data in by_condition.items()
                ]
            }

        except Exception as e:
            logger.error(f"母父産駒成績分析エラー（{broodmare_sire_name}）: {e}")
            return {'message': 'エラー発生'}

    def _get_track_condition(self, code: str) -> str:
        """馬場状態コードから名称を取得"""
        condition_map = {
            '1': '良', '2': '稍重', '3': '重', '4': '不良',
            1: '良', 2: '稍重', 3: '重', 4: '不良'
        }
        return condition_map.get(code, str(code))


# シングルトンインスタンス取得用
def get_sire_performance_analyzer() -> SirePerformanceAnalyzer:
    """シングルトンインスタンスを取得"""
    return SirePerformanceAnalyzer()