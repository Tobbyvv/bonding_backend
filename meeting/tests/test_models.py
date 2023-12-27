from datetime import datetime, timedelta, time, date

from django.utils import timezone
from django.utils.dateformat import DateFormat

from rest_framework.test import APITestCase

from profiles.models import Schedule, ScheduleTime, Profile
from meeting.models import (
    Meeting,
    MeetingInviteCode,
    Participant,
    ConfirmedTime,
    AvailableTime,
)


class TestMeeting(APITestCase):
    """Test module for Meeting model"""

    def setUp(self):
        self.today = DateFormat(datetime.now()).format("Y-m-d")
        self.end_day = DateFormat(datetime.now() + timedelta(days=10)).format("Y-m-d")
        self.start_time = time(14, 10, 0)
        self.end_time = time(20, 40, 0)

        self.start_time = "14:10:00"
        self.end_time = "20:40:00"

        self.profile = Profile.objects.create(gender=3, nickname="nickname")

        self.meeting = Meeting.objects.create(
            name="meeting test",
            author=self.profile,
            start_date=self.today,
            end_date=self.end_day,
            start_time=self.start_time,
            end_time=self.end_time,
            expired_at=timezone.now() + timedelta(days=10),
        )

    def test_meeting_name_max_length(self):
        max_length = self.meeting._meta.get_field("name").max_length
        self.assertEquals(max_length, 15)

    def test_expired_time_is_aware(self):
        self.assertTrue(timezone.is_aware(self.meeting.expired_at))

    def test_object_name_is_meeting_of_nickname(self):
        expected_object_name = f"{self.meeting.author.nickname}의 {self.meeting.name}"
        self.assertEquals(expected_object_name, f"{str(self.profile)}의 meeting test")


class TestAvailableTime(APITestCase):
    """Test module for AvailableTime model"""

    def setUp(self):
        self.today = DateFormat(datetime.now()).format("Y-m-d")
        self.end_day = DateFormat(datetime.now() + timedelta(days=10)).format("Y-m-d")
        self.start_time = time(14, 10, 0)
        self.end_time = time(20, 40, 0)

        self.start_time = "14:10:00"
        self.end_time = "20:40:00"

        self.meeting = Meeting.objects.create(
            name="meeting test",
            author=self.profile,
            start_date=self.today,
            end_date=self.end_day,
            start_time=self.start_time,
            end_time=self.end_time,
            expired_at=timezone.now(),
        )
        self.profile = Profile.objects.create(gender=3, nickname="nickname")
        self.participant = Participant.objects.create(
            meeting=self.meeting, user=self.profile, name="member"
        )

        self.date = datetime.date()
        self.time = time(12, 10, 0)
