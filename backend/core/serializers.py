from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import Lab, User, LabCompletion, ActiveInstance, CommunitySolution
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer




class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, value):
        user = self.instance or User(username=self.initial_data.get("username"))
        validate_password(value, user)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"], password=validated_data["password"]
        )
        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["is_admin"] = user.is_staff
        return token




class LabSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = ["id", "title", "category"]


class LabDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = ["id", "title", "description", "category"]


class CommunitySolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunitySolution
        fields = ["reflection", "payload"]




class LabCompletionSerializer(serializers.ModelSerializer):
    lab_id = serializers.PrimaryKeyRelatedField(source="lab", read_only=True)
    lab_title = serializers.CharField(source="lab.title", read_only=True)

    class Meta:
        model = LabCompletion
        fields = ["id", "status", "user", "lab_id", "lab_title"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["lab"] = str(instance.lab.id)
        return data


class ReflectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunitySolution
        fields = ["id", "user", "lab", "payload", "reflection"]
        read_only_fields = ["id", "user", "lab"]




class ActiveInstanceSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    lab = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ActiveInstance
        fields = [
            "id",
            "user",
            "lab",
            "status",
            "instance_url",
            "extensions_used",
            "expires_at",
        ]
        read_only_fields = fields




class SubmissionSerializer(serializers.Serializer):
    answer = serializers.CharField(max_length=255)
