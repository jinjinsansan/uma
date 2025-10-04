import math
from typing import Dict, Any, List, Tuple


from services.local_dlogic_raw_data_manager_v2 import local_dlogic_manager_v2
from services.local_nlogic_engine import LocalNLogicEngine


def _collect_sample_race(min_horses: int = 5) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    horse_names = local_dlogic_manager_v2.get_all_horse_names()
    race_groups: Dict[str, List[Dict[str, Any]]] = {}

    for horse_name in horse_names:
        horse_data = local_dlogic_manager_v2.get_horse_raw_data(horse_name)
        if not horse_data:
            continue
        for race in horse_data.get('races', []):
            kaisai_nen = str(race.get('KAISAI_NEN', '')).strip()
            kaisai_gappi = str(race.get('KAISAI_GAPPI', '')).strip()
            venue_code = str(race.get('KEIBAJO_CODE', '')).zfill(2)
            race_number = str(race.get('RACE_BANGO', '')).strip()

            if not (kaisai_nen and kaisai_gappi and venue_code and race_number):
                continue

            date = kaisai_nen + kaisai_gappi.zfill(4)
            race_id = f"{date}-{venue_code}-{race_number}"

            race_groups.setdefault(race_id, []).append({
                'horse_name': horse_name,
                'race': race,
            })

            if len(race_groups[race_id]) >= min_horses:
                race_meta = {
                    'date': date,
                    'venue_code': venue_code,
                    'race_number': int(race_number),
                    'distance': race.get('KYORI'),
                }
                return race_meta, race_groups[race_id]

    raise AssertionError("十分な頭数のレースが見つかりませんでした")


def _build_race_data(meta: Dict[str, Any], entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    code_to_name = {f"{v:02d}": k for k, v in LocalNLogicEngine.LOCAL_VENUE_CODE_MAP.items()}
    venue_name = code_to_name.get(meta['venue_code'], '大井')

    horses: List[str] = []
    jockeys: List[str] = []
    posts: List[Any] = []
    horse_numbers: List[Any] = []

    for entry in entries:
        race = entry['race']
        horses.append(entry['horse_name'])
        jockeys.append(race.get('KISHUMEI_RYAKUSHO') or '不明')
        posts.append(race.get('WAKU_BAN') or None)
        horse_numbers.append(race.get('UMABAN') or None)

    return {
        'venue': venue_name,
        'race_number': meta['race_number'],
        'race_date': meta['date'],
        'distance': meta.get('distance') or 1600,
        'horses': horses,
        'jockeys': jockeys,
        'posts': posts,
        'horse_numbers': horse_numbers,
    }


def test_local_nlogic_prediction_success():
    meta, entries = _collect_sample_race(min_horses=6)
    race_data = _build_race_data(meta, entries)

    engine = LocalNLogicEngine()
    result = engine.predict_race(race_data)

    assert result['status'] == 'success'
    predictions = result['predictions']
    assert len(predictions) == len(race_data['horses'])

    total_support = sum(pred['support_rate'] for pred in predictions.values())
    assert math.isclose(total_support, 1.0, rel_tol=1e-3)

    assert result['venue'] == race_data['venue']
