# core/serializers.py

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import Lab, User, LabCompletion, ActiveInstance, CommunitySolution
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


#B2-實驗內容服務
# 定義Lab模型的序列化器

#實驗清單的序列化器(/api/labs/)
class LabSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = ['id', 'title', 'category']

#實驗詳情的序列化器(/api/labs/{lab_id}/)
class LabDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = ['id', 'title', 'description', 'category']

#其他人解法的序列化器(/api/labs/{lab_id}/solutions/)
class CommunitySolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunitySolution
        fields = ['reflection','payload']


#B1-登入驗證服務
# 定義user模型的序列化器

#使用者註冊的序列化器(/auth/register/)
class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    #確保密碼強度
    def validate_password(self, value):
        user = self.instance or User(username=self.initial_data.get('username'))
        validate_password(value, user)
        return value
    
    def create(self,validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user
    
#區分一般user跟管理員的token
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['is_admin'] = user.is_staff
        return token
    
    
#B3-使用者資料服務
#定義LabCompletion模型的序列化器

#使用者進度的序列化器(/api/progress/)
class LabCompletionSerializer(serializers.ModelSerializer):
    lab = serializers.StringRelatedField(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = LabCompletion
        fields=['id','status','user','lab']

#提交防禦表單的序列化器(/api/labs/{lab_id}/reflections/)
class ReflectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunitySolution
        fields = ['id', 'user', 'lab', 'payload', 'reflection']
        read_only_fields = ['id', 'user', 'lab']


#B4-靶機分配服務
#定義ActiveInstance模型的序列化器

#使用者啟動靶機的序列化器(/api/labs/<id>/launch/)
class ActiveInstanceSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    lab = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ActiveInstance
        fields = ['id','user','lab','instance_url','expires_at']  
        read_only_fields = ['id','user','lab','instance_url','expires_at']  


#B5-答案驗證服務
#定義答案提交的序列化器沒有模型

#使用者提交答案的序列化器(/api/labs/<id>/submit/)
class SubmissionSerializer(serializers.Serializer):
    answer = serializers.CharField(max_length=255)


