from datetime import datetime
from django.db.models import Q
from django.db import IntegrityError
from django.utils import timezone
from django.core.validators import MaxLengthValidator
from rest_framework import serializers

from .models import (
    MeetingInviteCode,
    Meeting,
    ConfirmedTime,
    Participant,
    AvailableTime,
)
from .exceptions import (
    OnlyOClockAvailableException,
    MeetingNotFoundException,
    InvalidInviteCodeException,
    InvalidAvailableTimeException,
    ParticipantNameExistException,
)
from teampang.exceptions import (
    StartTimeIsLaterThanEndTimeException,
    EmptyTimeException,
    UnAvailableTimeException,
)
from profiles.serializers import ScheduleTimeSerializer, NicknameValidator


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class MeetingInviteCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingInviteCode
        fields = ["code"]


class MeetingTimeSerializer(ScheduleTimeSerializer):
    def is_o_clock(self, time):
        return time.minute == 0 or time.microsecond != 0

    def is_divided_by_ten(self, time):
        return time.minute % 10 == 0

    def validate_start_time(self, value):
        if self.is_divided_by_ten(value) or self.is_last_minute(value):
            return value
        raise UnAvailableTimeException

    def validate_end_time(self, value):
        if self.is_divided_by_ten(value) or self.is_last_minute(value):
            return value
        raise UnAvailableTimeException


class ConfirmedTimeSerializer(DynamicFieldsModelSerializer):
    start_datetime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    end_datetime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    meeting_name = serializers.CharField(source="meeting.name", read_only=True)

    def validate(self, data):

        if "start_datetime" in data.keys():
            if data["start_datetime"] >= data["end_datetime"]:
                raise StartTimeIsLaterThanEndTimeException
        return data

    class Meta:
        model = ConfirmedTime
        fields = (
            "id",
            "meeting_name",
            "start_datetime",
            "end_datetime",
            "place",
            "link",
            "meeting",
        )

    def update(self, instance, validated_data):
        instance.start_datetime = validated_data.get(
            "start_datetime", instance.start_datetime
        )
        instance.end_datetime = validated_data.get(
            "end_datetime", instance.end_datetime
        )
        instance.place = validated_data.get("place", instance.place)
        instance.link = validated_data.get("link", instance.link)
        instance.save()

        return instance


class MeetingSerializer(MeetingTimeSerializer):
    name = serializers.CharField(validators=[MaxLengthValidator(15)])
    author = serializers.CharField(source="author.nickname", read_only=True)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    confirmed_times = ConfirmedTimeSerializer(
        read_only=True, many=True, fields=("id", "start_datetime", "place", "link")
    )

    def validate(self, data):
        if "start_date" in data:
            if data["start_date"] > data["end_date"]:
                raise StartTimeIsLaterThanEndTimeException
        return data

    class Meta:
        model = Meeting
        fields = (
            "id",
            "name",
            "author",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "confirmed_times",
        )


class AvailableTimeSerializer(MeetingTimeSerializer):
    class Meta:
        model = AvailableTime
        exclude = ["id", "participant"]

    def validate_time(self, value):
        if self.is_divided_by_ten(value):
            return value
        raise UnAvailableTimeException

    def validate(self, data):
        return data


class ParticipantSerializer(serializers.ModelSerializer):
    name = serializers.CharField(validators=[NicknameValidator])
    meeting_id = serializers.IntegerField(write_only=True)
    code = serializers.CharField(write_only=True, max_length=50)
    available_times = AvailableTimeSerializer(many=True)

    class Meta:
        model = Participant
        fields = ("id", "name", "available_times", "meeting_id", "code")

    def validate_times(self, available_times, meeting):
        # available_times 유효성 검사
        for time in available_times:
            # 날짜 유효성 검사
            if not meeting.start_date <= time["date"] <= meeting.end_date:
                raise InvalidAvailableTimeException

            # 시간 유효성 검사
            if meeting.start_time < meeting.end_time:
                if not meeting.start_time <= time["time"] < meeting.end_time:
                    raise InvalidAvailableTimeException
            else:
                if meeting.end_time <= time["time"] < meeting.start_time:
                    raise InvalidAvailableTimeException

    def create_particpant(self, name, meeting):
        # 생성

        if self.context["request"].user.is_authenticated:
            user = self.context["request"].user.profile
        else:
            user = None

        try:
            participant = Participant.objects.create(
                name=name,
                meeting=meeting,
                user=user,
            )
        except IntegrityError:
            raise ParticipantNameExistException

        return participant

    def create(self, validated_data):
        # 데이터 추출
        meeting_id = validated_data["meeting_id"]
        code = validated_data["code"]
        name = validated_data["name"]

        # meeting_id에 해당하는 meeting이 존재하는지
        try:
            meeting = Meeting.objects.get(
                Q(id=meeting_id) & Q(expired_at__gt=timezone.now())
            )
        except Meeting.DoesNotExist:
            raise MeetingNotFoundException

        # code가 meeting의 invite_code와 일치하는지
        if code != str(meeting.invite_code.code):
            raise InvalidInviteCodeException

        # 확정 후
        if meeting.confirmed_times.all().exists():
            participant = self.create_particpant(name, meeting)
        # 확정 전
        else:
            available_times = validated_data["available_times"]

            if len(available_times) == 0:
                raise EmptyTimeException

            self.validate_times(available_times, meeting)

            # create participant and availavle_times
            participant = self.create_particpant(name, meeting)
            for time in available_times:
                AvailableTime.objects.create(participant=participant, **time)

        return participant


class MeetingTabSerializer(serializers.ModelSerializer):
    confirmed_times = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = ["id", "name", "confirmed_times"]

    def get_confirmed_times(self, instance):
        confirmed_times = instance.confirmed_times.exclude(
            end_datetime__lt=datetime.now()
        ).order_by("start_datetime")
        return ConfirmedTimeSerializer(
            confirmed_times, many=True, fields=("id", "start_datetime", "place", "link")
        ).data


class MeetingDetailSerializer(serializers.ModelSerializer):
    participants = serializers.StringRelatedField(many=True)
    confirmed_times = ConfirmedTimeSerializer(
        many=True, fields=("id", "start_datetime", "place", "link")
    )
    code = serializers.UUIDField(source="invite_code.code")
    author = serializers.CharField(source="author.nickname", read_only=True)

    class Meta:
        model = Meeting
        fields = ["id", "code", "name", "author", "participants", "confirmed_times"]
