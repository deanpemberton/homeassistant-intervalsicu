"""DataUpdateCoordinator for Intervals.icu."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IntervalsIcuApiError, IntervalsIcuClient, IntervalsIcuNotFoundError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .weekly import aggregate_weeks, fitness_history

_LOGGER = logging.getLogger(__name__)


class IntervalsIcuData:
    """Container for data fetched from Intervals.icu."""

    def __init__(
        self,
        athlete: dict[str, Any],
        wellness: dict[str, Any] | None,
        activities: list[dict[str, Any]],
        events: list[dict[str, Any]],
        pace_curve: dict[str, Any] | None,
        weekly_training: dict[str, Any] | None = None,
    ) -> None:
        self.athlete = athlete
        self.wellness = wellness
        self.activities = activities
        self.events = events
        self.pace_curve = pace_curve
        self.weekly_training = weekly_training


class IntervalsIcuCoordinator(DataUpdateCoordinator[IntervalsIcuData]):
    """Coordinator to fetch data from Intervals.icu API."""

    def __init__(self, hass: HomeAssistant, client: IntervalsIcuClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> IntervalsIcuData:
        """Fetch data from the API."""
        today = dt_util.now().date()
        timezone = self.hass.config.time_zone
        oldest = today - timedelta(days=today.weekday(), weeks=51)
        try:
            athlete = await self.client.get_athlete()
        except IntervalsIcuApiError as err:
            raise UpdateFailed(f"Error fetching athlete data: {err}") from err

        try:
            wellness = await self.client.get_wellness(today)
        except IntervalsIcuNotFoundError:
            # Wellness data may not exist for today yet
            wellness = None
        except IntervalsIcuApiError as err:
            _LOGGER.warning("Error fetching wellness data: %s", err)
            wellness = None

        try:
            all_activities = await self.client.get_activities(
                oldest=oldest,
                newest=today + timedelta(days=1),
                limit=1000,
            )
            if len(all_activities) >= 1000:
                raise UpdateFailed("Activity history reached the 1000-row safety limit; totals withheld")
            weekly_training = aggregate_weeks(all_activities, today, timezone)
            weekly_training["last_synced"] = dt_util.utcnow().isoformat()
            activities = sorted(
                [a for a in all_activities if a.get("name") and a.get("type")],
                key=lambda a: a.get("start_date_local") or a.get("start_date") or "",
                reverse=True,
            )
        except IntervalsIcuNotFoundError as err:
            raise UpdateFailed("Activity history endpoint not found; totals withheld") from err
        except IntervalsIcuApiError as err:
            raise UpdateFailed(f"Error fetching activity history: {err}") from err

        try:
            fitness_rows = await self.client.get_wellness_range(oldest=oldest, newest=today)
            weekly_training["fitness_history"] = fitness_history(fitness_rows, today)
            weekly_training["fitness_history_status"] = "available"
        except IntervalsIcuApiError as err:
            _LOGGER.warning("Error fetching fitness history: %s", err)
            weekly_training["fitness_history"] = []
            weekly_training["fitness_history_status"] = "unavailable"

        try:
            events = await self.client.get_events(
                oldest=today,
                newest=today + timedelta(days=7),
            )
        except IntervalsIcuNotFoundError:
            events = []
        except IntervalsIcuApiError as err:
            _LOGGER.warning("Error fetching events: %s", err)
            events = []

        try:
            pace_curves = await self.client.get_pace_curves(sport="Run", curves="all")
            curve_list = pace_curves.get("list") or []
            pace_curve = curve_list[0] if curve_list else None
        except IntervalsIcuNotFoundError:
            pace_curve = None
        except IntervalsIcuApiError as err:
            _LOGGER.warning("Error fetching pace curves: %s", err)
            pace_curve = None

        return IntervalsIcuData(
            athlete=athlete,
            wellness=wellness,
            activities=activities,
            events=events,
            pace_curve=pace_curve,
            weekly_training=weekly_training,
        )
