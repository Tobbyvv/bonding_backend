from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import GroupManager as BaseGroupManager


class GroupManager(BaseGroupManager):
    use_in_migrations = False


class UserManager(BaseUserManager):

    use_for_related_fields = True

    def _base_queryset(self, *args, **kwargs):
        return super().get_queryset()

    def get_queryset(self, *args, **kwargs):
        queryset = self._base_queryset()
        # with_deleted = True
        # if with_deleted:
        #    return queryset
        return queryset

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("이메일을 반드시 포함해야 합니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_admin", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_admin", True)

        return self._create_user(email, password, **extra_fields)
