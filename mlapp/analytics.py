"""Aggregate analytics for the dashboard from AnalyticsEvent rows."""

from __future__ import annotations

import datetime

from django.utils import timezone

from .models import AnalyticsEvent


def log_event(
    event_type: AnalyticsEvent.EventType | str,
    *,
    region_id: str = "",
) -> AnalyticsEvent:
    return AnalyticsEvent.objects.create(
        event_type=event_type,
        region_id=region_id or "",
    )


def get_daily_activity_series(days: int = 7) -> tuple[list[dict], int, int]:
    """
    Returns (series, week_total, peak_day_count).
    Each series item: label, date_short, count, height_pct (0–100 for bar chart).
    """
    today = timezone.localdate()
    series: list[dict] = []
    total = 0
    counts: list[int] = []

    for i in range(days - 1, -1, -1):
        day = today - datetime.timedelta(days=i)
        c = AnalyticsEvent.objects.filter(created_at__date=day).count()
        counts.append(c)
        total += c
        series.append(
            {
                "label": day.strftime("%a"),
                "date_short": day.strftime("%d %b"),
                "count": c,
                "height_pct": 0,
            }
        )

    peak = max(counts) if counts else 0
    for row, c in zip(series, counts, strict=True):
        row["height_pct"] = round(100 * c / peak) if peak else 0

    return series, total, peak


def get_event_totals_by_type() -> dict[str, int]:
    """Counts per event_type (all time)."""
    from django.db.models import Count

    rows = (
        AnalyticsEvent.objects.values("event_type")
        .annotate(n=Count("id"))
        .order_by()
    )
    return {r["event_type"]: r["n"] for r in rows}
