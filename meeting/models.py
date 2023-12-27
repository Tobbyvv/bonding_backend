import uuid
from django.db import models

from profiles.models import Profile


class Meeting(models.Model):
    id = models.BigAutoField(primary_key=True)
    author = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        null=True,
        related_name="profile",
    )
    name = models.CharField(max_length=15, null=False)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)
    start_time = models.TimeField(null=False)
    end_time = models.TimeField(null=False)
    expired_at = models.DateTimeField(null=False)

    def __str__(self):
        return "%s의 %s" % (self.author.nickname, self.name)


class ConfirmedTime(models.Model):
    id = models.BigAutoField(primary_key=True)
    meeting = models.ForeignKey(
        Meeting,
        related_name="confirmed_times",
        on_delete=models.CASCADE,
    )
    start_datetime = models.DateTimeField(null=False)
    end_datetime = models.DateTimeField(null=False)
    place = models.CharField(max_length=18, null=True)
    link = models.URLField(null=True)

    def __str__(self):
        return "%s(%d)" % (self.meeting, self.id)


class MeetingInviteCode(models.Model):
    meeting = models.OneToOneField(
        Meeting,
        related_name="invite_code",
        on_delete=models.CASCADE,
        primary_key=True,
    )
    code = models.UUIDField(default=uuid.uuid4)

    def __str__(self):
        return "meeting: %s, code: %s" % (self.meeting, self.code)


class Participant(models.Model):
    id = models.BigAutoField(primary_key=True)
    meeting = models.ForeignKey(
        Meeting,
        related_name="participants",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        null=True,
        related_name="participants",
    )
    name = models.CharField(max_length=10, null=False)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = [["meeting", "name"]]


class AvailableTime(models.Model):
    id = models.BigAutoField(primary_key=True)
    participant = models.ForeignKey(
        Participant,
        related_name="available_times",
        on_delete=models.CASCADE,
    )
    date = models.DateField()
    time = models.TimeField()
