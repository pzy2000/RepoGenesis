from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "password2",
            "email",
            "first_name",
            "last_name",
        ]

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Passwords must match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


