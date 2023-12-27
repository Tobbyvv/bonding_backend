from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from teampang.permissions import UpdateOwnerOrAdmin
from .exceptions import (
    ProfileDoesNotExistException,
    NicknameParameterException,
)
from .serializers import ProfileSerializer, ScheduleSerializer
from .models import Profile


class ProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, UpdateOwnerOrAdmin]
    serializer_class = ProfileSerializer
    model = Profile
    queryset = Profile.objects.all()
    http_method_names = ["get", "post", "put"]

    def get_object(self, pk=None):
        try:
            if self.action == "update":
                obj = self.queryset.get(id=pk)
            elif self.action == "list":
                nickname = self.request.query_params.get("nickname", None)
                if nickname is not None:
                    obj = self.queryset.get(nickname=nickname)
                else:
                    raise NicknameParameterException
            self.check_object_permissions(self.request, obj)
            return obj

        except Profile.DoesNotExist:
            raise ProfileDoesNotExistException

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        data = {"message": "사용자 조회 성공"}
        data.update(serializer.data)
        return Response(data)

    def update(self, request, pk=None):
        instance = self.get_object(pk=pk)

        serializer = self.serializer_class(
            instance,
            data=request.data,
            partial=False,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        data = {"message": "사용자 정보 업데이트 성공"}
        data.update(serializer.data)
        return Response(data, status=200)

    @action(detail=False, methods=["get"], url_path="me")
    def get_my_profile(self, request):
        try:
            profile = self.request.user.profile
            serializer = self.get_serializer(profile)
            data = {"message": "사용자 조회 성공"}
            data.update(serializer.data)
            return Response(data=data, status=200)
        except Profile.DoesNotExist:
            raise ProfileDoesNotExistException


class ScheduleViewSet(viewsets.ModelViewSet):
    pagination_class = None
    serializer_class = ScheduleSerializer
    http_method_names = ["get", "post", "put", "delete"]
    lookup_field = "id"

    def get_queryset(self):
        try:
            user = self.request.user.profile
            return user.schedules.all()
        except Profile.DoesNotExist:
            raise ProfileDoesNotExistException
