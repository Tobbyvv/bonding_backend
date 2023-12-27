from datetime import datetime, timedelta
from django.utils.dateformat import DateFormat

from rest_framework.test import APITestCase

from profiles.models import Schedule, ScheduleTime, Profile


class TestSchedule(APITestCase):
    """Test module for Schedule model"""

    def setUp(self):
        self.today = DateFormat(datetime.now()).format("Y-m-d")
        self.end_day = DateFormat(datetime.now() + timedelta(days=10)).format("Y-m-d")
        self.repeat_day = DateFormat(datetime.now() + timedelta(days=365)).format(
            "Y-m-d"
        )
        self.start_time = "10:30:00"
        self.end_time = "17:30:00"

        user = Profile.objects.create(gender=3, nickname="test")

        self.schedule_one_day = Schedule.objects.create(
            user=user,
            name="One day",
            start_date=self.today,
            end_date=self.today,
            recurrence=False,
        )

        self.schedule_many_days = Schedule.objects.create(
            user=user,
            name="many days",
            start_date=self.today,
            end_date=self.end_day,
            recurrence=False,
        )

        self.schedule_repeat = Schedule.objects.create(
            user=user,
            name="repeat",
            start_date=self.today,
            end_date=self.repeat_day,
            recurrence=True,
        )

        self.schedule_time_repeat_M = ScheduleTime.objects.create(
            schedule=self.schedule_repeat,
            start_time=self.start_time,
            end_time=self.end_time,
            day="월",
        )

        self.schedule_time_repeat_W = ScheduleTime.objects.create(
            schedule=self.schedule_repeat,
            start_time=self.start_time,
            end_time=self.end_time,
            day="수",
        )

        self.schedule_time_unrepeat_one = ScheduleTime.objects.create(
            schedule=self.schedule_one_day,
            start_time=self.start_time,
            end_time=self.end_time,
            day=None,
        )

        self.schedule_time_unrepeat_many = ScheduleTime.objects.create(
            schedule=self.schedule_many_days,
            start_time=self.start_time,
            end_time=self.end_time,
            day=None,
        )

    def test_schedule_name(self):
        self.assertEqual(self.schedule_one_day.name, "One day")
        self.assertEqual(self.schedule_many_days.name, "many days")
        self.assertEqual(self.schedule_repeat.name, "repeat")

    def test_schedule_start_date(self):
        self.assertEqual(self.schedule_one_day.start_date, self.today)
        self.assertEqual(self.schedule_many_days.start_date, self.today)
        self.assertEqual(self.schedule_repeat.start_date, self.today)

    def test_schedule_end_date(self):
        self.assertEqual(self.schedule_one_day.end_date, self.today)
        self.assertEqual(self.schedule_many_days.end_date, self.end_day)
        self.assertEqual(self.schedule_repeat.end_date, self.repeat_day)

    def test_schedule_recurrence(self):
        self.assertFalse(self.schedule_one_day.recurrence)
        self.assertFalse(self.schedule_many_days.recurrence)
        self.assertTrue(self.schedule_repeat.recurrence)

    def test_schedule_time_schedule(self):
        self.assertEqual(self.schedule_time_repeat_M.schedule, self.schedule_repeat)
        self.assertEqual(self.schedule_time_repeat_W.schedule, self.schedule_repeat)
        self.assertEqual(
            self.schedule_time_unrepeat_one.schedule, self.schedule_one_day
        )
        self.assertEqual(
            self.schedule_time_unrepeat_many.schedule, self.schedule_many_days
        )

    def test_schedule_time_start_time(self):
        self.assertEqual(self.schedule_time_repeat_M.start_time, self.start_time)
        self.assertEqual(self.schedule_time_repeat_W.start_time, self.start_time)
        self.assertEqual(self.schedule_time_unrepeat_one.start_time, self.start_time)
        self.assertEqual(self.schedule_time_unrepeat_many.start_time, self.start_time)

    def test_schedule_time_end_time(self):
        self.assertEqual(self.schedule_time_repeat_M.end_time, self.end_time)
        self.assertEqual(self.schedule_time_repeat_W.end_time, self.end_time)
        self.assertEqual(self.schedule_time_unrepeat_one.end_time, self.end_time)
        self.assertEqual(self.schedule_time_unrepeat_many.end_time, self.end_time)

    def test_schedule_time_day(self):
        self.assertEqual(self.schedule_time_repeat_M.day, "월")
        self.assertEqual(self.schedule_time_repeat_W.day, "수")
        self.assertIsNone(self.schedule_time_unrepeat_one.day)
        self.assertIsNone(self.schedule_time_unrepeat_many.day)
