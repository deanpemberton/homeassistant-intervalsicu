"""Pure activity aggregation; no credentials, HA state or recorder dependency."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from math import isfinite
from typing import Any
from zoneinfo import ZoneInfo

SPORTS = ("strength", "swimming", "cycling", "running", "other")
SPORT_TYPES = {
    "WeightTraining": "strength", "StrengthTraining": "strength",
    "Swim": "swimming", "OpenWaterSwim": "swimming",
    "Ride": "cycling", "VirtualRide": "cycling", "EBikeRide": "cycling",
    "EMountainBikeRide": "cycling", "Run": "running", "VirtualRun": "running",
    "TrailRun": "running",
}


def number(value: Any) -> float | None:
    """Accept finite nonnegative measurements, preserving missing vs zero."""
    try:
        result = float(value)
    except (ValueError, TypeError):
        return None
    return result if isfinite(result) and result >= 0 else None


def activity_day(activity: dict[str, Any], timezone: str) -> date | None:
    """Prefer recorded local calendar date, including near-midnight activities."""
    local = activity.get("start_date_local")
    if local:
        try:
            return date.fromisoformat(str(local)[:10])
        except ValueError:
            return None
    try:
        stamp = datetime.fromisoformat(str(activity["start_date"]).replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            return None
        return stamp.astimezone(ZoneInfo(timezone)).date()
    except (KeyError, ValueError, TypeError):
        return None


def aggregate_weeks(activities: list[dict[str, Any]], today: date,
                    timezone: str, weeks: int = 12) -> dict[str, Any]:
    """Rebuild Monday-based buckets from current API rows; edits replace totals."""
    monday = today - timedelta(days=today.weekday())
    oldest = monday - timedelta(weeks=weeks - 1)
    buckets = []
    for i in range(weeks):
        start = oldest + timedelta(weeks=i)
        buckets.append({"start": start.isoformat(), "end": (start + timedelta(days=6)).isoformat(),
                        "partial": start == monday,
                        "sports": {sport: {"seconds": 0.0, "distance_m": 0.0,
                                           "sessions": 0, "indoor_seconds": 0.0,
                                           "virtual_distance_m": 0.0, "missing_duration": 0,
                                           "missing_distance": 0} for sport in SPORTS}})
    seen = set()
    invalid_dates = 0
    for activity in activities:
        if not activity.get("type") or activity.get("id") is None:
            continue  # wellness placeholders are not completed activities
        identifier = str(activity["id"])
        if identifier in seen:
            continue
        seen.add(identifier)
        day = activity_day(activity, timezone)
        if day is None:
            invalid_dates += 1
            continue
        if not oldest <= day <= today:
            continue
        kind = str(activity["type"])
        sport = SPORT_TYPES.get(kind, "other")
        metric = buckets[(day - oldest).days // 7]["sports"][sport]
        metric["sessions"] += 1
        keys = ("elapsed_time", "moving_time") if sport in ("strength", "swimming") else ("moving_time", "elapsed_time")
        duration = next((number(activity.get(key)) for key in keys if number(activity.get(key)) is not None), None)
        distance = number(activity.get("distance"))
        if duration is None:
            metric["missing_duration"] += 1
        else:
            metric["seconds"] += duration
            if kind.startswith("Virtual") or activity.get("trainer") is True:
                metric["indoor_seconds"] += duration
        if sport != "strength":
            if distance is None:
                metric["missing_distance"] += 1
            else:
                metric["distance_m"] += distance
                if kind.startswith("Virtual"):
                    metric["virtual_distance_m"] += distance
    for bucket in buckets:
        bucket["hours"] = round(sum(s["seconds"] for s in bucket["sports"].values()) / 3600, 4)
        bucket["sessions"] = sum(s["sessions"] for s in bucket["sports"].values())
        for metric in bucket["sports"].values():
            metric["hours"] = round(metric["seconds"] / 3600, 4)
            metric["distance_km"] = round(metric["distance_m"] / 1000, 4)
    return {"schema_version": 1, "timezone": timezone, "week_start": "Monday",
            "as_of_date": today.isoformat(), "history": buckets,
            "current_week": buckets[-1], "invalid_dates": invalid_dates,
            "duration_basis": {"strength": "elapsed_time", "swimming": "elapsed_time",
                               "cycling": "moving_time", "running": "moving_time"}}
