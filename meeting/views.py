from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.exceptions import NotAuthenticated
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from .exceptions import (
    InvalidInviteCodeException,
    NotParticipantException,
    NotAuthorException,
    ParticipantNameExistException,
)
from profiles.exceptions import ProfileDoesNotExistException
from teampang.exceptions import UnprocessableEntityException
from teampang.permissions import (
    IsOwnerOrReadOnly,
    IsAuthorOrAdmin,
    IsOwnerOrAuthor,
    IsAuthorOrReadOnly,
    IsParticipant,
)
from .serializers import (
    MeetingSerializer,
    MeetingInviteCodeSerializer,
    ParticipantSerializer,
    MeetingDetailSerializer,
    MeetingTabSerializer,
    ConfirmedTimeSerializer,
)
from .models import (
    Meeting,
    MeetingInviteCode,
    ConfirmedTime,
    Participant,
)


class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)
    lookup_field = "id"

    def get_serializer_class(self):
        if self.action == "list":
            return MeetingTabSerializer
        return MeetingSerializer

    def get_author(self):
        try:
            profile = self.request.user.profile
            return profile
        except ObjectDoesNotExist:
            raise ProfileDoesNotExistException

    def perform_create(self, serializer):
        # 선택 가능 끝 시간을 일정 만료시간으로 설정
        expired_time = datetime.combine(
            serializer.validated_data["end_date"], serializer.validated_data["end_time"]
        )
        aware_expired_time = timezone.make_aware(expired_time)

        serializer.save(author=self.get_author(), expired_at=aware_expired_time)

    def list(self, request, *args, **kwargs):

        # 일정 참가를 위해 코드로 접근 시 참여 정보 반환
        code = request.query_params.get("code", None)
        if code:
            try:
                invite_code = MeetingInviteCode.objects.get(code=code)
                meeting = invite_code.meeting
                serializer = MeetingSerializer(meeting)
                return Response(serializer.data)
            except MeetingInviteCode.DoesNotExist:
                raise InvalidInviteCodeException
            except ValidationError:
                raise InvalidInviteCodeException
        else:
            if not request.user.is_authenticated:
                raise NotAuthenticated

        # 팀원이거나 팀장인 일정 조회
        author = self.get_author()
        queryset = (
            self.queryset.filter(Q(author=author) | Q(participants__user=author))
            .distinct()
            .exclude(expired_at__lt=timezone.now())
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        meeting = self.get_object()

        if not request.user.is_authenticated:
            raise NotAuthenticated

        # 일정 조회를 위해 팀원, 팀장 접근 시 일정 정보 반환
        author = self.get_author()
        if author != meeting.author:
            participant = meeting.participants.filter(user=author)
            if not bool(participant):
                raise NotParticipantException
        serializer = MeetingDetailSerializer(meeting)
        return Response(serializer.data)

    # 일정 초대(공유) 코드 가져오기
    @action(
        detail=True,
        methods=["GET"],
        url_path="invite-code",
        permission_classes=[IsAuthorOrAdmin],
    )
    def get_invite_code(self, request, *args, **kwargs):
        meeting = self.get_object()

        if hasattr(meeting, "invite_code"):
            invite_code = meeting.invite_code
        else:
            # 기존 코드가 존재하지 않으면 새로운 코드 생성
            invite_code = MeetingInviteCode(meeting=meeting)
            invite_code.save()
        serializer = MeetingInviteCodeSerializer(invite_code)
        return Response(data=serializer.data, status=200)

    def ten_minutes(self, hour, min_start=0, min_end=60):

        detail = []
        for i in range(min_start, min_end, 10):
            detail_data = {
                "time": f"{hour:02d}:{i:<02d}:00",
                "unavailable_member": None,
            }
            detail.append(detail_data)
        return detail

    def start_end(self, start_time, end_time):
        detail = []

        detail.extend(
            self.ten_minutes(hour=start_time.hour, min_start=start_time.minute)
        )

        for time in range(start_time.hour + 1, end_time.hour - 1):
            detail.extend(self.ten_minutes(time))

        detail.extend(self.ten_minutes(hour=end_time.hour, min_end=end_time.minute))

        return detail

    def end_start(self, start_time, end_time):
        detail = []

        for time in range(0, end_time.hour):
            detail.extend(self.ten_minutes(time))

        detail.extend(self.ten_minutes(hour=end_time.hour, min_end=end_time.minute))
        detail.extend(
            self.ten_minutes(hour=start_time.hour, min_start=start_time.minute)
        )

        for time in range(start_time.hour + 1, 24):
            detail.extend(self.ten_minutes(time))

        return detail

    def combine_date_detail(self, meeting, detail):
        choosable_times = []
        # construct full available data detail
        start_date = meeting.start_date
        end_date = meeting.end_date

        delta = end_date - start_date
        for day in range(delta.days + 1):
            date_data = start_date + timedelta(days=day)
            date = {"date": date_data, "detail": detail}
            choosable_times.append(date)

        return choosable_times

    def confirm_full_range(self, meeting):

        # construct full available time detail
        start_time = meeting.start_time
        end_time = meeting.end_time

        if (end_time.hour == 23) and (end_time.minute == 59):
            end_time = 24

        if start_time < end_time:
            # list
            detail = self.start_end(start_time, end_time)
        else:
            # dictionary
            detail = self.end_start(start_time, end_time)

        return self.combine_date_detail(meeting, detail)

    def gather_choosable_times(self, choosable_times, mem_num, member):
        for i, choosable_time in enumerate(choosable_times):
            detail = []
            for time in choosable_time["detail"]:
                if len(time["member"]) >= (mem_num - 1):
                    unavailable_member = set(member) - set(time["member"])
                    time["unavailable_member"] = (
                        unavailable_member.pop()
                        if len(unavailable_member) != 0
                        else None
                    )
                    del time["member"]
                    detail.append(time)

            choosable_times[i]["detail"] = detail

        result_times = []
        for choosable_time in choosable_times:
            if choosable_time["detail"]:
                result_times.append(choosable_time)

        return result_times

    def confirm_gatherging_range(self, serializer):
        member = []
        choosable_times = []
        mem_num = 0
        # available_times 수합하는 로직
        for participant in serializer.data:
            if participant["available_times"]:
                for time_data in participant["available_times"]:
                    # 해당 날짜가 이미 choosable_times 리스트에 있는 지 확인
                    i = next(
                        (
                            i
                            for i, date_item in enumerate(choosable_times)
                            if date_item["date"] == time_data["date"]
                        ),
                        None,
                    )

                    if i is None:
                        date = {
                            "date": time_data["date"],
                            "detail": [
                                {
                                    "time": time_data["time"],
                                    "member": [participant["name"]],
                                }
                            ],
                        }
                        choosable_times.append(date)
                    else:
                        # 해당 시간이 이미 detail 리스트에 있는 지 확인
                        j = next(
                            (
                                j
                                for j, time_item in enumerate(
                                    choosable_times[i]["detail"]
                                )
                                if time_item["time"] == time_data["time"]
                            ),
                            None,
                        )
                        if j is None:
                            choosable_times[i]["detail"].append(
                                {
                                    "time": time_data["time"],
                                    "member": [participant["name"]],
                                }
                            )
                        else:
                            choosable_times[i]["detail"][j]["member"].append(
                                participant["name"]
                            )
                mem_num += 1
                member.append(participant["name"])

        return self.gather_choosable_times(choosable_times, mem_num, member)

    # 선택 가능한 일정 목록 가져오기
    @action(
        detail=True,
        methods=["GET"],
        url_path="choosable-times",
        permission_classes=[IsAuthorOrAdmin],
    )
    def get_choosable_times(self, request, *args, **kwargs):
        meeting = self.get_object()
        # 참여 가능 시간이 없는 참여자 제외
        participants = meeting.participants.filter(
            available_times__isnull=False
        ).distinct()
        serializer = ParticipantSerializer(participants, many=True)

        # 참여자 없이 팀장이 일정 확정하는 경우
        if len(serializer.data) == 0:
            choosable_times = self.confirm_full_range(meeting)
            return Response(data=choosable_times, status=200)

        # 참여자가 존재하는 경우
        result_times = self.confirm_gatherging_range(serializer)

        return Response(data=result_times, status=200)

    # 일정 확정하기
    @action(
        detail=True,
        methods=["POST"],
        url_path="confirmed-times",
        permission_classes=[IsAuthorOrAdmin],
    )
    def create_confirmed_times(self, request, *args, **kwargs):
        meeting = self.get_object()

        if self.get_author() != meeting.author:
            raise NotAuthorException

        expired_time = (
            meeting.expired_at if meeting.confirmed_times.all().exists() else None
        )
        validated_times = []

        for data in request.data["confirmed_times"]:
            data["meeting"] = kwargs["id"]

            confirmed_time = ConfirmedTimeSerializer(data=data)
            confirmed_time.is_valid(raise_exception=True)
            if (
                expired_time is None
                or confirmed_time.validated_data["end_datetime"] > expired_time
            ):
                expired_time = confirmed_time.validated_data["end_datetime"]
            validated_times.append(confirmed_time)

        for time in validated_times:
            time.save()

        meeting.expired_at = expired_time
        meeting.save()

        return Response(data={"message": "일정 확정 성공"}, status=201)

    # 일정 나가기
    @action(
        detail=True,
        methods=["DELETE"],
        url_path="participants",
        permission_classes=[IsParticipant],
    )
    def exit_participant(self, request, *args, **kwargs):
        meeting = self.get_object()
        participant = meeting.participants.filter(user__user=request.user)

        participant.delete()
        return Response(status=204)


class ParticipantViewset(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Participant.objects.all()
    pagination_class = None
    serializer_class = ParticipantSerializer
    permission_classes = (IsOwnerOrAuthor,)
    lookup_field = "id"

    def list(self, request, *args, **kwargs):

        name = request.query_params.get("name")
        meeting_id = request.query_params.get("meeting_id")
        if name and meeting_id:
            if Participant.objects.filter(name=name, meeting__id=meeting_id):
                raise ParticipantNameExistException
            else:
                return Response(data={"message": "사용 가능"}, status=200)
        else:
            raise UnprocessableEntityException


class ConfirmedTimesViewset(viewsets.ModelViewSet):
    pagination_class = None
    serializer_class = ConfirmedTimeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    http_method_names = ("patch", "get", "delete")
    lookup_field = "id"

    def get_author(self):
        try:
            profile = self.request.user.profile
            return profile
        except ObjectDoesNotExist:
            raise ProfileDoesNotExistException

    def get_queryset(self):
        # 팀장 또는 참가자인 meeting의 confiremd_times 조회
        author = self.get_author()
        result = (
            ConfirmedTime.objects.filter(
                Q(meeting__author=author) | Q(meeting__participants__user=author)
            )
            .distinct()
            .exclude(end_datetime__lt=timezone.now())
        )

        return result

    def list(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            self.get_queryset(),
            many=True,
            fields=("id", "meeting", "meeting_name", "start_datetime", "end_datetime"),
        )
        return Response(data=serializer.data, status=200)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # only patch place/link
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
            fields=("place", "link", "start_datetime", "end_datetime"),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
