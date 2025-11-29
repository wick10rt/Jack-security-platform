from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import Lab, User, LabCompletion, ActiveInstance, CommunitySolution
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


# B2 實驗內容服務


# IE-3 實驗清單的序列化器
class LabSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = ["id", "title", "category"]


# IE-4 實驗詳情的序列化器
class LabDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = ["id", "title", "description", "category"]


# IE-8 他人解法的序列化器
class CommunitySolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunitySolution
        fields = ["reflection", "payload"]


# B1 登入驗證服務


# IE-0 使用者註冊的序列化器
class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    # 驗證密碼強度
    def validate_password(self, value):
        user = self.instance or User(username=self.initial_data.get("username"))
        validate_password(value, user)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"], password=validated_data["password"]
        )
        return user


# IE-1 使用者身份驗證的序列化器
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["is_admin"] = user.is_staff
        return token


# B3 使用者資料服務


# IE-2 學習進度的序列化器
class LabCompletionSerializer(serializers.ModelSerializer):
    lab = serializers.StringRelatedField(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = LabCompletion
        fields = ["id", "status", "user", "lab"]


# IE-7 防禦表單的序列化器
class ReflectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunitySolution
        fields = ["id", "user", "lab", "payload", "reflection"]
        read_only_fields = ["id", "user", "lab"]


# B4 靶機分配服務


# IE-5 啟動靶機的序列化器
class ActiveInstanceSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    lab = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ActiveInstance
        fields = ["id", "user", "lab", "instance_url", "expires_at"]
        read_only_fields = ["id", "user", "lab", "instance_url", "expires_at"]


# B5 答案驗證服務


# IE-6 提交答案的序列化器
class SubmissionSerializer(serializers.Serializer):
    answer = serializers.CharField(max_length=255)
