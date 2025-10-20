"""Trial API for 2025-10-21 Oi races (N-Logic & MetaLogic preview)."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header


router = APIRouter(prefix="/trial", tags=["Trial Experiences"])


# Allowed race numbers for the trial
ALLOWED_RACES = {9, 10, 11, 12}


class TrialConfigError(Exception):
    """Raised when configuration for the trial API is invalid."""


def _load_race_archive() -> List[Dict[str, Any]]:
    """Load local archive data for 2025-10-21 Oi races.

    The file is shared with the frontend (Next.js) implementation and lives in
    `front/d-logic-ai-frontend/src/data/archive/local/`.
    """

    archive_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "supplied",
        "races-20251021-oi.json",
    )

    if not os.path.exists(archive_path):
        raise TrialConfigError(
            "Archive JSON for 2025-10-21 Oi not found."
        )

    with open(archive_path, "r", encoding="utf-8") as fp:
        content = json.load(fp)

    if not isinstance(content, list):
        raise TrialConfigError("Archive JSON must contain a list of races.")

    return content


@lru_cache(maxsize=1)
def get_race_archive() -> Dict[int, Dict[str, Any]]:
    """Return a map of race_number -> race data."""

    archive_list = _load_race_archive()
    mapped: Dict[int, Dict[str, Any]] = {}

    for race in archive_list:
        try:
            race_number = int(race.get("race_number"))
        except (TypeError, ValueError):
            continue

        if race_number not in ALLOWED_RACES:
            continue

        mapped[race_number] = race

    missing = ALLOWED_RACES - mapped.keys()
    if missing:
        raise TrialConfigError(
            f"Missing races in archive JSON: {sorted(missing)}"
        )

    return mapped


def get_trial_api_key() -> str:
    api_key = os.getenv("TRIAL_API_KEY")
    if not api_key:
        raise TrialConfigError("TRIAL_API_KEY environment variable not set.")
    return api_key


async def require_trial_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    expected = get_trial_api_key()
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _load_local_race_data(race_number: int) -> Dict[str, Any]:
    archive = get_race_archive()
    return archive[race_number]


def _normalize_race_data(raw_race: Dict[str, Any]) -> Dict[str, Any]:
    """Extract fields required by engines."""

    def _fallback_distance(value: Any) -> int:
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            digits = "".join(ch for ch in value if ch.isdigit())
            return int(digits) if digits else 0
        return 0

    return {
        "race_id": raw_race.get("race_id"),
        "race_date": raw_race.get("race_date"),
        "venue": raw_race.get("venue"),
        "race_number": raw_race.get("race_number"),
        "race_name": raw_race.get("race_name"),
        "horses": raw_race.get("horses", []),
        "jockeys": raw_race.get("jockeys", []),
        "posts": raw_race.get("posts", []),
        "horse_numbers": raw_race.get("horse_numbers", []),
        "odds": raw_race.get("odds", []),
        "popularities": raw_race.get("popularities", []),
        "distance": _fallback_distance(raw_race.get("distance")),
        "track_condition": raw_race.get("track_condition", "良"),
        "track_type": "ダート",
        "sex_ages": raw_race.get("sex_ages", []),
        "weights": raw_race.get("weights", []),
        "trainers": raw_race.get("trainers", []),
    }


def _build_metadata(raw_race: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "race_number": raw_race.get("race_number"),
        "race_name": raw_race.get("race_name"),
        "race_date": raw_race.get("race_date"),
        "venue": raw_race.get("venue"),
        "distance": raw_race.get("distance"),
    }


def _extract_top_nlogic_predictions(predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not predictions:
        return []

    sorted_preds = sorted(
        predictions.items(),
        key=lambda item: item[1].get("rank", 999),
    )

    top_two = []
    for horse, data in sorted_preds[:2]:
        top_two.append(
            {
                "horse": horse,
                "rank": data.get("rank"),
                "score": data.get("support_rate"),
            }
        )

    return top_two


def _extract_top_metalogic_rankings(rankings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not rankings:
        return []

    result = []
    for item in rankings[:2]:
        result.append(
            {
                "horse": item.get("horse"),
                "rank": item.get("rank"),
                "score": item.get("meta_score"),
            }
        )

    return result


def _analyze_nlogic(race_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    from services.local_nlogic_engine import LocalNLogicEngine

    engine = LocalNLogicEngine()
    result = engine.predict_race(race_data)

    if result.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=f"N-Logic analysis failed: {result.get('message', 'unknown error')}",
        )

    return _extract_top_nlogic_predictions(result.get("predictions", {}))


def _analyze_metalogic(race_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    from services.local_metalogic_engine_v2 import local_metalogic_engine_v2

    result = local_metalogic_engine_v2.analyze_race(race_data)

    if result.get("status") != "success":
        raise HTTPException(
            status_code=500,
            detail=f"MetaLogic analysis failed: {result.get('message', 'unknown error')}",
        )

    return _extract_top_metalogic_rankings(result.get("rankings", []))


@router.get("/oi-20251021")
async def get_oi_trial(
    race: int,
    _: None = Depends(require_trial_api_key),
) -> Dict[str, Any]:
    """Return limited trial prediction for the specified race."""

    if race not in ALLOWED_RACES:
        raise HTTPException(status_code=400, detail="Race not available in trial")

    raw_race = _load_local_race_data(race)
    metadata = _build_metadata(raw_race)
    normalized_race = _normalize_race_data(raw_race)

    nlogic_top = _analyze_nlogic(normalized_race)
    metalogic_top = _analyze_metalogic(normalized_race)

    return {
        "status": "success",
        "race": metadata,
        "nlogic": nlogic_top,
        "metalogic": metalogic_top,
    }
