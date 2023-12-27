from rest_framework import permissions


class UpdateOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        if request.method in ["GET", "POST"]:
            return True

        return obj.user == request.user or request.user.is_admin


class IsOwnerOrAuthor(permissions.BasePermission):
    """
    request must have invite_code
    --Participant--
    --Available Time--
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        """
        --participant--
        --avalivable time-- edit together
        """
        if request.method == "GET":
            return True
        return bool(
            obj.user == request.user.profile
            or obj.meeting.author == request.user.profile
            or request.user.is_admin
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    --Meeting--
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        # 일정조회는 모두 허용(code, 참여자 검사->views)
        if request.method == "GET":
            return True
        if request.method == "POST":
            return bool(request.user.profile and request.user.is_authenticated)
        # 작성자, 관리자는 모든 권한 허용
        return request.user.profile == obj.author or request.user.is_admin


class IsAuthorOrAdmin(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return request.user.profile == obj.author or request.user.is_admin


class IsParticipant(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return obj.participants.filter(user=request.user.profile).exists()


class IsAuthorOrReadOnly(permissions.IsAuthenticated):
    """
    confirmed_times
    """

    def has_object_permission(self, request, view, obj):
        if request.method == "GET":
            return True
        return request.user.profile == obj.meeting.author or request.user.is_admin
