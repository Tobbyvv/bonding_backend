from datetime import datetime, timedelta, time

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APITestCase

from rest_framework_simplejwt.tokens import RefreshToken

from profiles.models import Profile
from meeting.models import (
    Meeting,
    ConfirmedTime,
    MeetingInviteCode,
    AvailableTime,
    Participant,
)

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class TestMeetingViewSet(APITestCase):
    def setUp(self):
        pass


class TestParticipantViewSet(APITestCase):
    def setUp(self):
        self.today = datetime.now().date()
        self.tomorrow = self.today + timedelta(days=1)
        self.end_day = self.today + timedelta(days=10)
        self.start_time = time(14, 10, 0)
        self.end_time = time(20, 40, 0)

        self.user = User.objects.create(user_type="B")
        self.profile = Profile.objects.create(
            user=self.user, gender=3, nickname="nickname"
        )

        self.meeting_before_confirm = Meeting.objects.create(
            name="meeting test",
            author=self.profile,
            start_date=self.tomorrow,
            end_date=self.end_day,
            start_time=self.start_time,
            end_time=self.end_time,
            expired_at=timezone.now() + timedelta(days=10),
        )

        MeetingInviteCode.objects.create(meeting=self.meeting_before_confirm)

        self.meeting_confirm = Meeting.objects.create(
            name="meeting test",
            author=self.profile,
            start_date=self.tomorrow,
            end_date=self.end_day,
            start_time=self.start_time,
            end_time=self.end_time,
            expired_at=timezone.now() + timedelta(days=10),
        )

        ConfirmedTime.objects.create(
            meeting=self.meeting_confirm,
            start_datetime=datetime.combine(self.tomorrow, self.start_time),
            end_datetime=datetime.combine(self.end_day, self.end_time),
        )

        MeetingInviteCode.objects.create(meeting=self.meeting_confirm)

        token = get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token["access"])

        self.available_times_data = [
            {"date": self.tomorrow, "time": self.start_time},
            {"date": self.end_day, "time": self.start_time},
        ]

    def test_post_fields_missing(self):
        response = self.client.post("/participants", data={})
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/participants", data={"name": "member"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/participants",
            data={
                "name": "member",
                "code": str(self.meeting_before_confirm.invite_code.code),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/participants",
            data={
                "name": "member",
                "code": str(self.meeting_before_confirm.invite_code.code),
                "meeting_id": self.meeting_before_confirm.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_post_success_before_confirm(self):
        response = self.client.post(
            "/participants",
            data={
                "name": "member",
                "code": str(self.meeting_before_confirm.invite_code.code),
                "meeting_id": self.meeting_before_confirm.id,
                "available_times": self.available_times_data,
            },
            format="json",
        )
        # self.assertEqual(response.status_code, 201)
        self.assertIn("data", response.data)
        self.assertIn("id", response.data["data"])
        self.assertIn("name", response.data["data"])
        self.assertIn("available_times", response.data["data"])

        for available_time in response.data["data"]["available_times"]:
            self.assertIn("date", available_time)
            self.assertIn("time", available_time)

    def test_post_success_confirm(self):
        response = self.client.post(
            "/participants",
            data={
                "name": "member",
                "code": str(self.meeting_confirm.invite_code.code),
                "meeting_id": self.meeting_confirm.id,
                "available_times": [],
            },
            format="json",
        )
        # self.assertEqual(response.status_code, 201)
        self.assertIn("data", response.data)
        self.assertIn("id", response.data["data"])
        self.assertIn("name", response.data["data"])
        self.assertIn("available_times", response.data["data"])
        self.assertFalse(response.data["data"]["available_times"])

    def test_get_choosable_times_full_range(self):
        m = Meeting.objects.create(
            name="meeting",
            author=self.profile,
            start_date=self.tomorrow,
            end_date=self.end_day,
            start_time=time(14, 0, 0),
            end_time=time(15, 0, 0),
            expired_at=timezone.now() + timedelta(days=10),
        )

        response = self.client.get(f"/meetings/{m.id}/choosable-times")

        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)
        self.assertEqual(10, len(response.data["data"]))

        for date in response.data["data"]:
            self.assertIn("date", date)
            self.assertIn("detail", date)
            self.assertEqual(6, len(date["detail"]))

    def test_get_choosable_times_gethering_range(self):
        m = Meeting.objects.create(
            name="meeting",
            author=self.profile,
            start_date=self.tomorrow,
            end_date=self.end_day,
            start_time="14:00",
            end_time="15:00",
            expired_at=timezone.now() + timedelta(days=10),
        )

        p1 = Participant.objects.create(meeting=m, name="p1")
        p2 = Participant.objects.create(meeting=m, name="p2")
        p3 = Participant.objects.create(meeting=m, name="p3")

        AvailableTime.objects.create(participant=p1, date=self.tomorrow, time="14:00")
        AvailableTime.objects.create(participant=p1, date=self.tomorrow, time="14:10")
        AvailableTime.objects.create(participant=p1, date=self.tomorrow, time="14:20")
        AvailableTime.objects.create(participant=p1, date=self.tomorrow, time="14:30")

        AvailableTime.objects.create(participant=p2, date=self.tomorrow, time="14:10")
        AvailableTime.objects.create(participant=p2, date=self.tomorrow, time="14:20")
        AvailableTime.objects.create(participant=p2, date=self.tomorrow, time="14:30")

        AvailableTime.objects.create(participant=p3, date=self.tomorrow, time="14:20")
        AvailableTime.objects.create(participant=p3, date=self.tomorrow, time="14:30")

        response = self.client.get(f"/meetings/{m.id}/choosable-times")

        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)
        self.assertEqual(1, len(response.data["data"]))

        date = response.data["data"][-1]
        self.assertEqual(self.tomorrow.strftime("%Y-%m-%d"), date["date"])
        self.assertEqual(3, len(date["detail"]))

        for time in date["detail"]:
            self.assertIn("time", time)
            self.assertIn("unavailable_member", time)
