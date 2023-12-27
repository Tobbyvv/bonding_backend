from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

UserModel = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(
        UserModel, related_name="profile", on_delete=models.CASCADE, null=True
    )
    GENDER_CHOICES = [
        (1, "male"),
        (2, "female"),
        (3, "any"),
    ]
    gender = models.PositiveSmallIntegerField(
        choices=GENDER_CHOICES,
        null=False,
    )
    nickname = models.CharField(unique=True, max_length=10, null=False)
    profile_image = models.URLField(null=True, blank=True, default=None)

    def __str__(self):
        return self.nickname


class University(models.Model):
    profile = models.OneToOneField(
        Profile, related_name="university", on_delete=models.CASCADE, primary_key=True
    )
    name = models.CharField(_("name"), max_length=30, null=False)
    admission = models.IntegerField(null=False)
    department = models.CharField(max_length=30, null=False)
    grade = models.PositiveSmallIntegerField(null=False)

    def __str__(self):
        return str(self.name)


class Schedule(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        Profile,
        related_name="schedules",
        on_delete=models.CASCADE,
    )
    name = models.CharField(_("schedule name"), max_length=10, null=False)
    start_date = models.DateField()
    end_date = models.DateField()
    recurrence = models.BooleanField(default=False)

    def __str__(self):
        return self.user.nickname + ": " + self.name


class ScheduleTime(models.Model):
    id = models.BigAutoField(primary_key=True)
    schedule = models.ForeignKey(
        Schedule,
        related_name="schedule_times",
        on_delete=models.CASCADE,
    )
    start_time = models.TimeField(_("schedule start time"), null=False)
    end_time = models.TimeField(_("schedule end time"), null=False)
    DAY_CHOICES = (
        ("월", "월요일"),
        ("화", "화요일"),
        ("수", "수요일"),
        ("목", "목요일"),
        ("금", "금요일"),
        ("토", "토요일"),
        ("일", "일요일"),
    )
    day = models.CharField(
        _("schedule day"),
        max_length=1,
        null=True,
        choices=DAY_CHOICES,
    )

    def __str__(self):
        schedule_name = self.schedule.name
        start_time_format = self.start_time.strftime("%H:%M")
        end_time_format = self.end_time.strftime("%H:%M")
        time_interval = start_time_format + "~" + end_time_format
        return schedule_name + ": " + self.day + " " + time_interval
