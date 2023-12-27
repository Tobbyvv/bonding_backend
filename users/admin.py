from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "is_active",
        "is_admin",
    )
    list_filter = ("is_admin",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("date_joined",)},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_admin",
                    "is_active",
                )
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("-date_joined",)
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.unregister(Site)
