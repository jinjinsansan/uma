"""地方競馬向けN-Logicエンジン"""

import logging
from typing import Dict

from services.nlogic_engine import NLogicEngine

logger = logging.getLogger(__name__)


class LocalNLogicEngine(NLogicEngine):
    """地方競馬版N-Logicエンジン"""

    LOCAL_VENUE_CODE_MAP: Dict[str, int] = {
        '門別': 31, '北見': 32, '岩見沢': 33, '帯広': 34,
        '旭川': 35, '札幌': 36, '函館': 37, '三条': 38,
        '新潟': 39, '足利': 40, '宇都宮': 41, '高崎': 42,
        '前橋': 43, '大井': 44, '川崎': 45, '船橋': 46,
        '浦和': 47, '水沢': 48, '盛岡': 49, '上山': 50,
        '三条2': 51, '新潟2': 52, '福山': 53, '益田': 54,
        '高知': 55, '佐賀': 56, '荒尾': 57, '中津': 58,
        '園田': 59, '姫路': 60, '名古屋': 61, '笠松': 62,
        '帯広ば': 63, '金沢': 64, '札幌ば': 65, '旭川ば': 66,
    }

    def __init__(self):
        from services.local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2

        super().__init__(
            data_manager=local_dlogic_manager_v2,
            model_prefix='nlogic_nar',
        )
        logger.info("Local N-Logic engine initialized (%s venues)", len(self.LOCAL_VENUE_CODE_MAP))

    def _get_venue_code(self, venue: str) -> int:
        return self.LOCAL_VENUE_CODE_MAP.get(venue, 0)

    def _get_track_stats(self, races, venue: str):  # type: ignore[override]
        target_code_int = self._get_venue_code(venue)
        if target_code_int == 0:
            return 0.0, 10.0
        target_code = str(target_code_int).zfill(2)

        track_races = [r for r in races if str(r.get('KEIBAJO_CODE', '')).zfill(2) == target_code]
        if not track_races:
            return 0.0, 10.0

        wins = sum(1 for r in track_races if self._safe_int(r.get('KAKUTEI_CHAKUJUN')) == 1)
        win_rate = wins / len(track_races)

        finishes = [
            self._safe_int(r.get('KAKUTEI_CHAKUJUN'))
            for r in track_races
            if self._safe_int(r.get('KAKUTEI_CHAKUJUN')) > 0
        ]
        avg_finish = sum(finishes) / len(finishes) if finishes else 10.0

        return win_rate, avg_finish
