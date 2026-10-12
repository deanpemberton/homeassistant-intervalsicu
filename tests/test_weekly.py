"""Calendar boundaries, duration semantics and replacement aggregation."""
import importlib.util
from datetime import date
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('weekly', Path(__file__).parents[1] / 'custom_components/intervals_icu/weekly.py')
weekly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weekly)

class TestWeekly(unittest.TestCase):
    def aggregate(self, rows, today=date(2026, 10, 13)):
        return weekly.aggregate_weeks(rows, today, 'Pacific/Auckland', weeks=12)

    def row(self, id='1', type='Run', day='2026-10-12', **fields):
        return dict(id=id, type=type, start_date_local=day+'T09:00:00', **fields)

    def test_week_boundary_and_empty_weeks(self):
        result=self.aggregate([self.row(day='2026-10-11', moving_time=3600),self.row(id='2',moving_time=1800)])
        self.assertEqual(len(result['history']),12)
        self.assertEqual(result['history'][-2]['hours'],1)
        self.assertEqual(result['current_week']['hours'],0.5)
        self.assertEqual(result['current_week']['start'],'2026-10-12')
        self.assertEqual(result['history'][0]['hours'],0)

    def test_local_date_precedes_utc_and_dst_fallback(self):
        rows=[self.row(start_date='2026-10-11T10:00:00Z',moving_time=60),dict(id='2',type='Run',start_date='2026-10-11T11:30:00Z',moving_time=60)]
        self.assertEqual(self.aggregate(rows)['current_week']['sessions'],2)

    def test_duration_rest_and_virtual_distance(self):
        rows=[self.row(type='WeightTraining',elapsed_time=3600,moving_time=300,distance=20),self.row(id='2',type='Swim',elapsed_time=1800,moving_time=1000,distance=1000),self.row(id='3',type='VirtualRide',elapsed_time=4000,moving_time=3600,distance=40000)]
        s=self.aggregate(rows)['current_week']['sports']
        self.assertEqual(s['strength']['hours'],1)
        self.assertEqual(s['strength']['distance_m'],0)
        self.assertEqual(s['swimming']['hours'],0.5)
        self.assertEqual(s['cycling']['hours'],1)
        self.assertEqual(s['cycling']['virtual_distance_m'],40000)
        self.assertEqual(s['cycling']['indoor_seconds'],3600)

    def test_ids_and_recalculation(self):
        row=self.row(moving_time=3600,distance=10000)
        self.assertEqual(self.aggregate([row,row])['current_week']['sessions'],1)
        self.assertEqual(self.aggregate([self.row(moving_time=1800)])['current_week']['hours'],0.5)
        self.assertEqual(self.aggregate([])['current_week']['hours'],0)

    def test_missing_invalid_and_zero(self):
        rows=[self.row(moving_time=0,elapsed_time=100,distance=0),self.row(id='2',moving_time=-1,elapsed_time='nan',distance='bad')]
        s=self.aggregate(rows)['current_week']['sports']['running']
        self.assertEqual(s['seconds'],0)
        self.assertEqual(s['missing_duration'],1)
        self.assertEqual(s['missing_distance'],1)

    def test_exclude_future_old_and_placeholders(self):
        rows=[self.row(day='2026-10-14',moving_time=60),self.row(id='2',day='2020-01-01'),dict(id='3',name='Wellness'),self.row(id='4',day='bad')]
        result=self.aggregate(rows)
        self.assertEqual(result['current_week']['sessions'],0)
        self.assertEqual(result['invalid_dates'],1)

    def test_daily_and_ignored_time(self):
        r=self.aggregate([self.row(moving_time=3600), self.row(id='2',moving_time=999,icu_ignore_time=True),dict(id='3',name='Restricted')])
        self.assertEqual(r['daily'][0]['seconds'],3600)
        self.assertEqual(r['current_week']['sessions'],1)
        self.assertEqual(r['ignored_activities'],1)
        self.assertEqual(r['unclassified_activities'],1)

    def test_upstream_fitness_preserves_gaps_and_negative_form(self):
        r=weekly.fitness_history([{'id':'2026-10-12','ctl':50,'atl':75},{'id':'2026-10-13','ctl':51,'atl':None},{'id':'2026-10-14','ctl':99,'atl':100}],date(2026,10,13))
        self.assertEqual(len(r),2)
        self.assertEqual(r[0]['form'],-25)
        self.assertIsNone(r[1]['atl'])
        self.assertIsNone(r[1]['form'])

    def test_unnamed_activity_and_other_sport(self):
        result=self.aggregate([self.row(type='Walk',moving_time=900)])
        self.assertEqual(result['current_week']['sports']['other']['hours'],0.25)

if __name__ == '__main__': unittest.main()
