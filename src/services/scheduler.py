"""Scheduler service — precise next-hour delay calculation."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pytz

logger = logging.getLogger(__name__)


def seconds_until_next_hour(timezone_str: str = "Europe/Madrid") -> float:
    """Calculate seconds until the next exact hour in the given timezone.

    Recalculates fresh each call to avoid drift accumulation.

    Args:
        timezone_str: IANA timezone string (e.g. 'Europe/Madrid').

    Returns:
        Seconds until the next hour boundary.
    """
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        logger.warning("Unknown timezone '%s', falling back to UTC", timezone_str)
        tz = pytz.UTC

    now = datetime.now(tz)
    # Next hour: current hour + 1, with minute/second/micro zeroed
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    delta = (next_hour - now).total_seconds()

    logger.debug(
        "Next hour in %s: %s (%.0f seconds away)",
        timezone_str,
        next_hour.strftime("%H:%M"),
        delta,
    )
    return delta


def get_current_hour(timezone_str: str = "Europe/Madrid") -> tuple[int, int]:
    """Get the current hour in both 24h and 12h formats.

    Args:
        timezone_str: IANA timezone string.

    Returns:
        Tuple of (hour_24, hour_12) where hour_12 is 1-12.
    """
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        logger.warning("Unknown timezone '%s', falling back to UTC", timezone_str)
        tz = pytz.UTC

    now = datetime.now(tz)
    hour_24 = now.hour
    hour_12 = hour_24 % 12
    if hour_12 == 0:
        hour_12 = 12
    return hour_24, hour_12
