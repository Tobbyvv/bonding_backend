from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.utils.dateformat import DateFormat

from rest_framework.test import APITestCase

from rest_framework_simplejwt.tokens import RefreshToken

from profiles.models import Schedule, ScheduleTime, Profile

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class TestScheduleViewSet(APITestCase):
    def setUp(self):
        self.today = DateFormat(datetime.now()).format("Y-m-d")
        self.end_day = DateFormat(datetime.now() + timedelta(days=10)).format("Y-m-d")
        self.repeat_day = DateFormat(datetime.now() + timedelta(days=365)).format(
            "Y-m-d"
        )

        self.name = "schedule"
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

        self.user = User.objects.create(user_type="B")
        Profile.objects.create(user=self.user, gender=3, nickname="nickname")

        token = get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token["access"])

    def test_post_fields_missing(self):
        response = self.client.post("/user/schedules", data={})
        self.assertEqual(response.status_code, 400)

        response = self.client.post("/user/schedules", data={"name": self.name})
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/user/schedules",
            data={
                "name": self.name,
                "start_date": self.today,
                "end_date": self.end_day,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_post_success_repeat(self):
        response = self.client.post(
            "/user/schedules",
            {
                "name": self.name,
                "start_date": self.today,
                "end_date": self.repeat_day,
                "recurrence": True,
                "schedule_times": [self.time_repeat1, self.time_repeat2],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("data", response.data)
        self.assertIn("id", response.data["data"])
        self.assertIn("name", response.data["data"])
        self.assertIn("start_date", response.data["data"])
        self.assertIn("end_date", response.data["data"])
        self.assertIn("recurrence", response.data["data"])
        self.assertIn("schedule_times", response.data["data"])

        for schedule_time in response.data["data"]["schedule_times"]:
            self.assertIn("start_time", schedule_time)
            self.assertIn("end_time", schedule_time)
            self.assertIn("day", schedule_time)

    def test_post_success_unrepeat(self):
        response = self.client.post(
            "/user/schedules",
            {
                "name": self.name,
                "start_date": self.today,
                "end_date": self.end_day,
                "recurrence": False,
                "schedule_times": [self.time_unrepeat],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("data", response.data)
        self.assertIn("id", response.data["data"])
        self.assertIn("name", response.data["data"])
        self.assertIn("start_date", response.data["data"])
        self.assertIn("end_date", response.data["data"])
        self.assertIn("recurrence", response.data["data"])
        self.assertIn("schedule_times", response.data["data"])

        schedule_time = response.data["data"]["schedule_times"][0]
        self.assertIn("start_time", schedule_time)
        self.assertIn("end_time", schedule_time)
        self.assertIn("day", schedule_time)

    def test_put_to_repeat(self):
        schedule = Schedule.objects.create(
            user=self.user.profile,
            name="repeat",
            start_date=self.today,
            end_date=self.end_day,
            recurrence=False,
        )
        ScheduleTime.objects.create(
            schedule=schedule,
            start_time=self.start_time,
            end_time=self.end_time,
            day=None,
        )

        response = self.client.put(
            f"/user/schedules/{schedule.id}",
            {
                "name": self.name,
                "start_date": self.today,
                "end_date": self.end_day,
                "recurrence": True,
                "schedule_times": [self.time_repeat1, self.time_repeat2],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)
        self.assertIn("id", response.data["data"])
        self.assertIn("name", response.data["data"])
        self.assertIn("start_date", response.data["data"])
        self.assertIn("end_date", response.data["data"])
        self.assertIn("recurrence", response.data["data"])
        self.assertIn("schedule_times", response.data["data"])

        self.assertEqual(2, len(response.data["data"]["schedule_times"]))
        for schedule_time in response.data["data"]["schedule_times"]:
            self.assertIn("start_time", schedule_time)
            self.assertIn("end_time", schedule_time)
            self.assertIn("day", schedule_time)

    def test_put_to_unrepeat(self):
        schedule = Schedule.objects.create(
            user=self.user.profile,
            name="repeat",
            start_date=self.today,
            end_date=self.repeat_day,
            recurrence=True,
        )

        ScheduleTime.objects.create(
            schedule=schedule,
            start_time=self.start_time,
            end_time=self.end_time,
            day="월",
        )

        ScheduleTime.objects.create(
            schedule=schedule,
            start_time=self.start_time,
            end_time=self.end_time,
            day="수",
        )

        response = self.client.put(
            f"/user/schedules/{schedule.id}",
            {
                "name": self.name,
                "start_date": self.today,
                "end_date": self.end_day,
                "recurrence": False,
                "schedule_times": [self.time_unrepeat],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)
        self.assertIn("id", response.data["data"])
        self.assertIn("name", response.data["data"])
        self.assertIn("start_date", response.data["data"])
        self.assertIn("end_date", response.data["data"])
        self.assertIn("recurrence", response.data["data"])
        self.assertIn("schedule_times", response.data["data"])

        self.assertEqual(1, len(response.data["data"]["schedule_times"]))
        schedule_time = response.data["data"]["schedule_times"][0]
        self.assertIn("start_time", schedule_time)
        self.assertIn("end_time", schedule_time)
        self.assertIn("day", schedule_time)
