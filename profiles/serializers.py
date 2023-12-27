from datetime import datetime
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.validators import (
    MaxLengthValidator,
    MinLengthValidator,
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from rest_framework import serializers

from .models import Profile, University, Schedule, ScheduleTime
from .exceptions import (
    ScheduleConflictException,
    NicknameConflictException,
    ProfileConflictException,
)
from teampang.exceptions import (
    EmptyTimeException,
    StartTimeIsLaterThanEndTimeException,
    StartTimeIsEqualOrLaterThanEndTimeException,
    UnAvailableTimeException,
)


UserModel = get_user_model()


# validator
class NicknameValidator(RegexValidator):
    regex = r"^[ㄱ-ㅎ|가-힣|a-z|A-Z|0-9|\*]+$"
    message = "한글, 숫자, 영문만 입력해주세요."


def YearValidator(value):
    if value < 1900 or value > datetime.now().year + 1:
        raise ValidationError("올바른 입학년도를 입력해주세요.")


# Profile
class UniversitySerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        validators=[MaxLengthValidator(30)],
        required=True,
    )
    admission = serializers.IntegerField(
        validators=[YearValidator],
        required=True,
    )
    department = serializers.CharField(
        validators=[MaxLengthValidator(30)], required=True
    )
    grade = serializers.IntegerField(
        validators=[MaxValueValidator(6), MinValueValidator(1)], required=True
    )

    class Meta:
        model = University
        fields = (
            "name",
            "admission",
            "department",
            "grade",
        )


class ProfileSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(
        validators=[
            NicknameValidator(),
            MinLengthValidator(2),
            MaxLengthValidator(10),
        ]
    )
    gender = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)]
    )
    profile_image = serializers.SerializerMethodField(allow_null=True)
    university = UniversitySerializer(required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "nickname",
            "gender",
            "profile_image",
            "university",
        )

    def get_profile_image(self, obj):
        if obj.profile_image:
            return obj.profile_image
        return None

    def create(self, validated_data):
        queryset = self.Meta.model.objects.filter(  # 중복 검사
            nickname=validated_data["nickname"]
        )
        if queryset.exists():
            raise NicknameConflictException

        univ_data = validated_data.pop("university", None)

        try:
            profile = Profile.objects.create(**validated_data)
        except IntegrityError:
            raise ProfileConflictException

        if univ_data:
            University.objects.create(**univ_data, profile=profile)

        return profile

    def update(self, instance, validated_data):
        nickname = validated_data.get("nickname", None)
        if nickname:
            queryset = self.Meta.model.objects.exclude(
                user=instance.user
            ).filter(  # 중복 검사
                nickname=nickname
            )
            if queryset.exists():
                raise NicknameConflictException

        univ_data = validated_data.pop("university", None)
        instance = super().update(instance, validated_data)

        if univ_data:
            University.objects.update_or_create(profile=instance, defaults=univ_data)
        else:
            univ = University.objects.filter(profile=instance)
            univ.delete()

        return instance


class ScheduleTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleTime
        exclude = ["id", "schedule"]

    def is_experessed_in_minutes(self, time):
        return time.second == 0 and time.microsecond == 0

    def is_last_minute(self, time):
        return time.hour == 23 and time.minute == 59

    def validate_start_time(self, value):
        if self.is_experessed_in_minutes(value) or self.is_last_minute(value):
            return value
        raise UnAvailableTimeException

    def validate_end_time(self, value):
        if self.is_experessed_in_minutes(value) or self.is_last_minute(value):
            return value
        raise UnAvailableTimeException

    def validate(self, data):
        if data["start_time"] >= data["end_time"]:
            raise StartTimeIsEqualOrLaterThanEndTimeException
        return data


# Schedule
class ScheduleSerializer(serializers.ModelSerializer):
    schedule_times = ScheduleTimeSerializer(many=True)

    class Meta:
        model = Schedule
        exclude = ["user"]

    def check_recurrence(self, data):
        if data["recurrence"]:
            for time in data["schedule_times"]:
                if time["day"] is None:
                    raise ValidationError("올바른 값을 입력해주세요.")
        else:
            if (
                len(data["schedule_times"]) != 1
                or data["schedule_times"][-1]["day"] is not None
            ):
                raise ValidationError("올바른 값을 입력해주세요.")

    def validate(self, data):
        if data["start_date"] > data["end_date"]:
            raise StartTimeIsLaterThanEndTimeException
        self.check_recurrence(data)
        return data

    def validate_schedule_times(self, value):
        if len(value) == 0:
            raise EmptyTimeException
        return value

    def is_conflict(self, a_start, a_end, b_start, b_end):
        return (a_start <= b_start < a_end) or (b_start <= a_start < b_end)

    def check_all_conflicts(self, validated_data, schedule_id=None):
        # body의 schedule_times 리스트 내에서의 충돌 검사
        schedule_times = validated_data["schedule_times"]
        for i in range(len(schedule_times) - 1):
            a_start = schedule_times[i]["start_time"]
            a_end = schedule_times[i]["end_time"]
            a_day = schedule_times[i]["day"]

            for j in range(i + 1, len(schedule_times)):
                b_start = schedule_times[j]["start_time"]
                b_end = schedule_times[j]["end_time"]
                b_day = schedule_times[j]["day"]

                # 요일이 같을 때만
                if a_day == b_day:
                    if self.is_conflict(a_start, a_end, b_start, b_end):
                        raise ScheduleConflictException

        # DB와 충돌 검사
        user = self.context["request"].user.profile
        schedules = user.schedules.all()

        for schedule in schedules:
            # update 시 해당 스케줄은 통과
            if schedule.id == schedule_id:
                continue

            existing_times = schedule.schedule_times.all()
            for time in existing_times:
                a_start = time.start_time
                a_end = time.end_time
                a_day = time.day

                for input_time in schedule_times:
                    b_start = input_time["start_time"]
                    b_end = input_time["end_time"]
                    b_day = input_time["day"]

                    # 요일이 같을 때만
                    if a_day == b_day:
                        if self.is_conflict(a_start, a_end, b_start, b_end):
                            raise ScheduleConflictException

    def create(self, validated_data):
        # 한꺼번에 create
        schedule_times = validated_data.pop("schedule_times")
        schedule = Schedule.objects.create(
            user=self.context["request"].user.profile, **validated_data
        )
        for time in schedule_times:
            ScheduleTime.objects.create(schedule=schedule, **time)

        return schedule

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name")
        instance.start_date = validated_data.get("start_date")
        instance.end_date = validated_data.get("end_date")
        instance.recurrence = validated_data.get("recurrence")
        instance.save()

        # 기존의 시간을 모두 삭제 후
        for time in instance.schedule_times.all():
            time.delete()

        # 새로운 시간 추가
        schedule_times = validated_data["schedule_times"]
        for time in schedule_times:
            ScheduleTime.objects.create(schedule=instance, **time)

        return instance
