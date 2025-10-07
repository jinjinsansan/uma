"""
種牡馬（父・母父）産駒成績分析エンジン
高速化のためインデックスを使用（O(n) → O(1)）
シングルトンパターンで起動時に1回だけ初期化
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
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

        print(f"🏇 種牡馬産駒成績分析エンジン初期化開始... (instance={id(self)})")

        # DLogicRawDataManagerからデータ取得
        from services.dlogic_raw_data_manager import DLogicRawDataManager
        self.dlogic_manager = DLogicRawDataManager()

        # インデックス
        self.sire_index = defaultdict(list)  # 父名 → 産駒情報リスト
        self.broodmare_sire_index = defaultdict(list)  # 母父名 → 産駒情報リスト

        # インデックスを構築
        self._build_index()

        self._initialized = True
        print(f"✅ 種牡馬産駒成績分析エンジン初期化完了（父: {len(self.sire_index)}頭、母父: {len(self.broodmare_sire_index)}頭）")

    def _build_index(self):
        """血統インデックスを構築（起動時に1回だけ）"""
        try:
            horses_data = self.dlogic_manager.knowledge_data.get('horses', {})
            
            skipped_no_sire = 0
            skipped_no_broodmare = 0

            # 全馬データを1回だけスキャン
            for horse_name, horse_data in horses_data.items():
                races = horse_data.get('races', [])
                if not races:
                    continue

                # 全レースから血統情報を探す（最新レースから順に）
                sire = None
                broodmare_sire = None
                
                for race in races:
                    if not sire:
                        sire_candidate = self._normalize_bloodline_name(race.get('sire'))
                        if sire_candidate:
                            sire = sire_candidate
                    if not broodmare_sire:
                        broodmare_candidate = self._normalize_bloodline_name(race.get('broodmare_sire'))
                        if broodmare_candidate:
                            broodmare_sire = broodmare_candidate
                    # 両方見つかったら終了
                    if sire and broodmare_sire:
                        break
                
                # デバッグ：ディープインパクト産駒を追跡
                
                # デバッグ: 血統情報がない場合をカウント
                if not sire:
                    skipped_no_sire += 1
                if not broodmare_sire:
                    skipped_no_broodmare += 1

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

            print(f"📊 血統インデックス構築完了: {len(horses_data)}頭を処理")
            print(f"⚠️ 父情報なし: {skipped_no_sire}頭, 母父情報なし: {skipped_no_broodmare}頭")

        except Exception as e:
            logger.error(f"血統インデックス構築エラー: {e}")

    def analyze_sire_performance(
        self,
        sire_name: str,
        venue_code: str,
        distance: str,
        track_type: Optional[str] = None
    ) -> Dict:
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
            sire_key = self._normalize_bloodline_name(sire_name) or sire_name

            normalized_track_type = self._normalize_track_type(track_type)
            normalized_distance = None
            if distance not in (None, ''):
                if isinstance(distance, (int, float)) and not isinstance(distance, bool):
                    normalized_distance = str(int(distance))
                else:
                    raw_distance = str(distance).strip()
                    if raw_distance:
                        # 末尾のm/Mを除去し、数字のみを抽出
                        if raw_distance.lower().endswith('m'):
                            raw_distance = raw_distance[:-1].strip()
                        digit_only = ''.join(ch for ch in raw_distance if ch.isdigit())
                        normalized_distance = digit_only or raw_distance

            # インデックスから産駒リストを即座に取得（O(1)）
            offspring_list = self.sire_index.get(sire_key, [])
            
            # デバッグログ：インデックス内の産駒数
            total_races_in_list = sum(len(o['races']) for o in offspring_list) if offspring_list else 0

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

            # デバッグカウンター
            debug_matched_count = 0
            debug_venue_mismatch = 0
            debug_distance_mismatch = 0
            debug_track_mismatch = 0

            # 産駒のレースデータを分析
            for offspring in offspring_list:
                for race in offspring['races']:
                    # 会場と距離が一致するかチェック
                    if race.get('KEIBAJO_CODE') != venue_code:
                        debug_venue_mismatch += 1
                        continue
                    if normalized_distance:
                        race_distance = race.get('KYORI')
                        compared_distance = None
                        if race_distance not in (None, ''):
                            try:
                                compared_distance = str(int(race_distance))
                            except (ValueError, TypeError):
                                compared_distance = str(race_distance).strip()
                        if not compared_distance or compared_distance != normalized_distance:
                            debug_distance_mismatch += 1
                            continue
                    elif distance not in (None, '') and race.get('KYORI') != distance:
                        debug_distance_mismatch += 1
                        continue

                    race_track_type = self._get_track_type(race)
                    if normalized_track_type and race_track_type and normalized_track_type != race_track_type:
                        debug_track_mismatch += 1
                        continue

                    debug_matched_count += 1
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
                    shiba_condition = race.get('SHIBA_BABAJOTAI_CODE', '')
                    dirt_condition = race.get('DIRT_BABAJOTAI_CODE', '')
                    if shiba_condition in [None, '', '0', 0]:
                        track_condition = dirt_condition
                    else:
                        track_condition = shiba_condition

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

            # デバッグログ：最終結果と除外統計
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

    def analyze_broodmare_sire_performance(
        self,
        broodmare_sire_name: str,
        venue_code: str,
        distance: str,
        track_type: Optional[str] = None
    ) -> Dict:
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
            normalized_name = self._normalize_bloodline_name(broodmare_sire_name)
            broodmare_sire_key = normalized_name or broodmare_sire_name

            normalized_track_type = self._normalize_track_type(track_type)
            normalized_distance = None
            if distance not in (None, ''):
                if isinstance(distance, (int, float)) and not isinstance(distance, bool):
                    normalized_distance = str(int(distance))
                else:
                    raw_distance = str(distance).strip()
                    if raw_distance:
                        if raw_distance.lower().endswith('m'):
                            raw_distance = raw_distance[:-1].strip()
                        digit_only = ''.join(ch for ch in raw_distance if ch.isdigit())
                        normalized_distance = digit_only or raw_distance

            # インデックスから産駒リストを即座に取得（O(1)）
            offspring_list = self.broodmare_sire_index.get(broodmare_sire_key, [])

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

            debug_matched_count = 0
            debug_venue_mismatch = 0
            debug_distance_mismatch = 0
            debug_track_mismatch = 0

            for offspring in offspring_list:
                for race in offspring['races']:
                    if race.get('KEIBAJO_CODE') != venue_code:
                        debug_venue_mismatch += 1
                        continue
                    if normalized_distance:
                        race_distance = race.get('KYORI')
                        compared_distance = None
                        if race_distance not in (None, ''):
                            try:
                                compared_distance = str(int(race_distance))
                            except (ValueError, TypeError):
                                compared_distance = str(race_distance).strip()
                        if not compared_distance or compared_distance != normalized_distance:
                            debug_distance_mismatch += 1
                            continue
                    elif distance not in (None, '') and race.get('KYORI') != distance:
                        debug_distance_mismatch += 1
                        continue

                    race_track_type = self._get_track_type(race)
                    if normalized_track_type and race_track_type and normalized_track_type != race_track_type:
                        debug_track_mismatch += 1
                        continue

                    debug_matched_count += 1
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

                    shiba_condition = race.get('SHIBA_BABAJOTAI_CODE', '')
                    dirt_condition = race.get('DIRT_BABAJOTAI_CODE', '')
                    if shiba_condition in [None, '', '0', 0]:
                        track_condition = dirt_condition
                    else:
                        track_condition = shiba_condition

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
                'sire_name': broodmare_sire_key,
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

    def _normalize_bloodline_name(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return None
        if not isinstance(name, str):
            name = str(name)
        normalized = name.replace('\u3000', ' ').strip()
        return normalized or None

    def _normalize_track_type(self, track_type: Optional[str]) -> Optional[str]:
        if not track_type:
            return None
        if isinstance(track_type, str):
            normalized = track_type.strip()
            if not normalized:
                return None
            lower = normalized.lower()
            if '芝' in normalized or 'turf' in lower:
                return '芝'
            if 'ダート' in normalized or '砂' in normalized or 'dirt' in lower:
                return 'ダート'
            if '障害' in normalized or 'steeple' in lower:
                return '障害'
        return None

    def _get_track_type(self, race: Dict[str, Any]) -> Optional[str]:
        track_code = race.get('TRACK_CODE')
        if track_code is not None and track_code != '':
            try:
                track_code_int = int(track_code)
            except (TypeError, ValueError):
                track_code_int = None
            if track_code_int is not None:
                if 11 <= track_code_int <= 19:
                    return '芝'
                if 21 <= track_code_int <= 29:
                    return 'ダート'
                if 31 <= track_code_int <= 39:
                    return '障害'

        shiba_condition = race.get('SHIBA_BABAJOTAI_CODE')
        if shiba_condition not in [None, '', '0', 0]:
            return '芝'

        dirt_condition = race.get('DIRT_BABAJOTAI_CODE')
        if dirt_condition not in [None, '', '0', 0]:
            return 'ダート'

        return None

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