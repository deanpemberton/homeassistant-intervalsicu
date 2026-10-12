"""Ensure aggregation uses a full local window and never turns errors into zeros."""
from datetime import datetime
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

from custom_components.intervals_icu.api import IntervalsIcuApiError
from custom_components.intervals_icu.coordinator import IntervalsIcuCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

class TestWeeklyRefresh(IsolatedAsyncioTestCase):
    def setUp(self):
        self.coordinator = object.__new__(IntervalsIcuCoordinator)
        self.coordinator.hass = MagicMock()
        self.coordinator.hass.config.time_zone = 'Pacific/Auckland'
        self.client = self.coordinator.client = MagicMock()
        self.client.get_athlete = AsyncMock(return_value={'id':'i123','name':'Test'})
        self.client.get_wellness = AsyncMock(return_value={})
        self.client.get_activities = AsyncMock(return_value=[])
        self.client.get_events = AsyncMock(return_value=[])
        self.client.get_pace_curves = AsyncMock(return_value={})
        self.clock = patch('custom_components.intervals_icu.coordinator.dt_util.now',return_value=datetime(2026,10,13,0,30,tzinfo=ZoneInfo('Pacific/Auckland')))
        self.clock.start()
        self.addCleanup(self.clock.stop)

    async def test_full_window_sorted_and_replaced(self):
        self.client.get_activities.return_value=[{'id':'old','type':'Run','name':'Old','start_date_local':'2026-10-11T09:00:00','moving_time':3600},{'id':'new','type':'Swim','name':'New','start_date_local':'2026-10-12T09:00:00','elapsed_time':1800}]
        result=await self.coordinator._async_update_data()
        self.assertEqual(result.activities[0]['id'],'new')
        self.assertEqual(result.weekly_training['current_week']['hours'],0.5)
        args=self.client.get_activities.call_args.kwargs
        self.assertEqual(args['oldest'].isoformat(),'2026-07-27')
        self.assertEqual(args['newest'].isoformat(),'2026-10-14')
        self.assertEqual(args['limit'],1000)
        self.client.get_activities.return_value=[]
        result=await self.coordinator._async_update_data()
        self.assertEqual(result.weekly_training['current_week']['hours'],0)

    async def test_error_withholds_totals(self):
        self.client.get_activities.side_effect=IntervalsIcuApiError('offline')
        with self.assertRaises(UpdateFailed):
            await self.coordinator._async_update_data()

    async def test_truncation_withholds_totals(self):
        self.client.get_activities.return_value=[{}]*1000
        with self.assertRaises(UpdateFailed):
            await self.coordinator._async_update_data()
