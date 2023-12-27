from datetime import datetime, timedelta, date, time

from django.utils import timezone
from django.utils.dateformat import DateFormat

from rest_framework.test import APITestCase

from meeting.serializers import (
    MeetingSerializer,
    ParticipantSerializer,
    AvailableTimeSerializer,
)
from meeting.models import Meeting, Participant, AvailableTime
from profiles.models import Profile

from teampang.exceptions import (
    StartTimeIsLaterThanEndTimeException,
    UnAvailableTimeException,
)


class TestMeetingSerializerTest(APITestCase):
    def setUp(self):
        self.today = DateFormat(datetime.now()).format("Y-m-d")
        self.end_day = DateFormat(datetime.now() + timedelta(days=10)).format("Y-m-d")
        self.start_time = time(14, 10, 0)
        self.end_time = time(20, 40, 0)

        self.start_time = "14:10:00"
        self.end_time = "20:40:00"

        self.profile = Profile.objects.create(gender=3, nickname="nickname")

        self.meeting = {
            "name": "meeting test",
            "author": self.profile,
            "start_date": self.today,
            "end_date": self.end_day,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "expired_at": timezone.now() + timedelta(days=10),
        }

    def test_create_meeting(self):
        s = MeetingSerializer(data=self.meeting)

        self.assertTrue(s.is_valid())

    def test_it_should_not_validate_if_start_later_end(self):
        s = MeetingSerializer(
            data={
                "name": "meeting test",
                "author": self.profile,
                "start_date": self.end_day,
                "end_date": self.today,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "expired_at": timezone.now() + timedelta(days=10),
            }
        )
        with self.assertRaises(StartTimeIsLaterThanEndTimeException):
            s.is_valid()


class TestAvailableTimeSerializerTest(APITestCase):
    def setUp(self):
        self.today = DateFormat(datetime.now()).format("Y-m-d")
        self.time1 = "14:10:00"
        self.time2 = "20:40:00"

        self.available_times_data1 = {"date": self.today, "time": self.time1}
        self.available_times_data2 = {"date": self.today, "time": self.time2}

    def test_success(self):
        s = AvailableTimeSerializer(data=self.available_times_data1)
        self.assertTrue(s.is_valid())

    def test_it_should_not_validate_if_not_ten_minute(self):
        s = AvailableTimeSerializer(data={"date": self.today, "time": "14:15:00"})

        with self.assertRaises(UnAvailableTimeException):
            s.is_valid()


class TestParticipantSerializerTest(APITestCase):
    def setUp(self):
        self.today = DateFormat(datetime.now()).format("Y-m-d")
        self.time1 = "14:10:00"
        self.time2 = "20:40:00"

        self.available_times_data = [
            {"date": self.today, "time": self.time1},
            {"date": self.today, "time": self.time2},
        ]

        self.participant_data = {
            "meeting_id": 1,
            "code": "justtestcode",
            "name": "member",
            "available_times": self.available_times_data,
        }

    def test_success(self):
        s = ParticipantSerializer(data=self.participant_data)
        self.assertTrue(s.is_valid())
