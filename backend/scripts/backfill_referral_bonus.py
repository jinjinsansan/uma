"""Backfill missing referral bonuses for line-connected referrals.

This script scans `v2_referral_history` for records that reached
`status = 'line_connected'` but never created a corresponding
`referral_line_bonus` transaction. For those cases we re-run the
standard bonus logic via `process_referral_bonus_on_line_connect` so
that the correct tiered points are awarded and counters updated.

Usage:
    python -m scripts.backfill_referral_bonus

The script prints a summary of processed, skipped, and failed records.
Ensure environment variables (Supabase keys) are configured before
running.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from dotenv import load_dotenv

# Reuse the existing bonus processing logic and Supabase client
from api.v2.line_referral_improved import (  # type: ignore
    process_referral_bonus_on_line_connect,
    supabase,
)


load_dotenv()


async def backfill_missing_referral_bonuses() -> None:
    """Process all line-connected referrals lacking bonus transactions."""

    print("[Backfill] Fetching line-connected referrals …")
    response = supabase.table("v2_referral_history") \
        .select("id, referrer_id, referred_id, line_connected_at") \
        .eq("status", "line_connected") \
        .execute()

    records: list[Dict[str, Any]] = response.data or []
    print(f"[Backfill] Total line-connected records: {len(records)}")

    processed = 0
    skipped = 0
    failed = 0

    for record in records:
        referred_id = record.get("referred_id")
        if not referred_id:
            skipped += 1
            continue

        # Skip if a referral bonus transaction already exists
        bonus_check = supabase.table("v2_point_transactions") \
            .select("id") \
            .eq("transaction_type", "referral_line_bonus") \
            .eq("related_entity_id", referred_id) \
            .limit(1) \
            .execute()

        if bonus_check.data:
            skipped += 1
            continue

        try:
            result = await process_referral_bonus_on_line_connect(referred_id)
            if result:
                processed += 1
            else:
                # No bonus issued (likely already granted previously)
                skipped += 1
        except Exception as exc:  # pragma: no cover - safety net
            failed += 1
            print(f"[Backfill] Failed for referred_id={referred_id}: {exc}")

    print("[Backfill] Summary")
    print(f"  Processed : {processed}")
    print(f"  Skipped   : {skipped}")
    print(f"  Failed    : {failed}")


def main() -> None:
    asyncio.run(backfill_missing_referral_bonuses())


if __name__ == "__main__":
    main()
