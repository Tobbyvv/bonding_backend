from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import ugettext_lazy as _
from rest_framework.authtoken.models import Token

from .managers import UserManager


TokenModel = Token


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    USER_TYPE_CHOICES = (
        ("K", "KAKAO"),
        ("G", "GOOGLE"),
        ("N", "NAVER"),
        ("A", "APPLE"),
    )
    user_type = models.CharField(choices=USER_TYPE_CHOICES, max_length=1)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    social_id = models.CharField(max_length=100, null=True)
    deleted_at = models.DateField(null=True, default=None)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ("-date_joined",)
        # abstract = True

    def __str__(self):
        return str(self.email)

    def deactivate(self):
        self.is_active = False
        self.save(update_fields=["is_active"])

    def delete(self, using=None, keep_parents=False):
        # self.deleted_at = timezone.now()
        self.hard_delete()

    def hard_delete(self):
        super(User, self).delete()

    def restore(self):
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=["deleted_at", "is_active"])

    @property
    def is_staff(self):
        return self.is_admin

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def has_perm(self, perm_list, obj=None):
        """
        Returns True if the user has each of the specified permissions. If
        object is passed, it checks if the user has all required perms for this
        object.
        """
        for perm in perm_list:
            if not self.is_admin:
                if not self.has_perm(perm, obj):
                    return False
        return True

    def has_module_perms(self, app_label):
        return self.is_admin
