from django.contrib.auth import get_user_model
from rest_framework import serializers


UserModel = get_user_model()


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = (
            "id",
            "email",
            "user_type",
        )
        read_only_fields = ("id", "email", "user_type")
