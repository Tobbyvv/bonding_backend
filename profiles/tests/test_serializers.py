from datetime import datetime, timedelta

from django.utils.dateformat import DateFormat

from rest_framework.test import APITestCase

from profiles.models import Schedule, ScheduleTime, Profile
from profiles.serializers import ScheduleSerializer, ScheduleTimeSerializer
from teampang.exceptions import (
    EmptyTimeException,
    StartTimeIsLaterThanEndTimeException,
    StartTimeIsEqualOrLaterThanEndTimeException,
    UnAvailableTimeException,
)


class TestScheduleSerializer(APITestCase):
    """Test module for Schedule Serializer"""

    def setUp(self):
        self.today = DateFormat(datetime.now()).format("Y-m-d")
        self.end_day = DateFormat(datetime.now() + timedelta(days=10)).format("Y-m-d")
        self.repeat_day = DateFormat(datetime.now() + timedelta(days=365)).format(
            "Y-m-d"
        )
        self.start_time = "10:30:00"
        self.end_time = "17:30:00"

        self.user = Profile.objects.create(gender=3, nickname="test")

        self.time_unrepeat = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "day": None,
        }

        self.time_repeat1 = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "day": "월",
        }

        self.time_repeat2 = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "day": "수",
        }

    def test_create_schedule_time_repeat(self):
        s1 = ScheduleTimeSerializer(data=self.time_repeat1)
        s2 = ScheduleTimeSerializer(data=self.time_repeat2)

        self.assertTrue(s1.is_valid())
        self.assertTrue(s2.is_valid())

    def test_create_schedule_time_unrepeat(self):
        s = ScheduleTimeSerializer(data=self.time_unrepeat)

        self.assertTrue(s.is_valid())

    def test_it_should_not_validate_if_schedule_times_empty(self):

        s = ScheduleSerializer(
            data={
                "schedule_times": [],
                "name": "test",
                "start_date": self.today,
                "end_date": self.today,
                "recurrence": False,
            }
        )

        with self.assertRaises(EmptyTimeException):
            s.is_valid()

    def test_it_should_not_validate_if_start_later_end(self):
        s = ScheduleSerializer(
            data={
                "schedule_times": [self.time_unrepeat],
                "name": "test",
                "start_date": self.end_day,
                "end_date": self.today,
                "recurrence": False,
            }
        )

        with self.assertRaises(StartTimeIsLaterThanEndTimeException):
            s.is_valid()

    def test_it_should_not_validate_if_start_later_end(self):
        s = ScheduleSerializer(
            data={
                "schedule_times": [self.time_unrepeat],
                "name": "test",
                "start_date": self.end_day,
                "end_date": self.today,
                "recurrence": False,
            }
        )

        with self.assertRaises(StartTimeIsLaterThanEndTimeException):
            s.is_valid()

    def test_update_to_repeat(self):
        s = ScheduleSerializer


class TestScheduleTimeSerializer(APITestCase):
    """Test module for Schedule Time Serializer"""

    def setUp(self):
        self.start_time = "10:30:00"
        self.end_time = "17:30:00"

        self.time_unrepeat = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "day": None,
        }

        self.time_repeat1 = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "day": "월",
        }

        self.time_repeat2 = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "day": "수",
        }

    def test_it_should_not_validate_if_start_equal_or_later_end(self):
        s1 = ScheduleTimeSerializer(
            data={
                "start_time": self.end_time,
                "end_time": self.start_time,
                "day": None,
            }
        )

        s2 = ScheduleTimeSerializer(
            data={
                "start_time": self.start_time,
                "end_time": self.start_time,
                "day": None,
            }
        )

        with self.assertRaises(StartTimeIsEqualOrLaterThanEndTimeException):
            s1.is_valid()
        with self.assertRaises(StartTimeIsEqualOrLaterThanEndTimeException):
            s2.is_valid()

    def test_it_should_not_validate_if_wrong_time_format(self):
        s = ScheduleTimeSerializer(
            data={
                "start_time": "12:15:15",
                "end_time": "15:14:30",
                "day": None,
            }
        )

        with self.assertRaises(UnAvailableTimeException):
            s.is_valid()

    def test_it_should_validate_if_23_59(self):
        s = ScheduleTimeSerializer(
            data={
                "start_time": self.start_time,
                "end_time": "23:59",
                "day": None,
            }
        )

        self.assertTrue(s.is_valid())
