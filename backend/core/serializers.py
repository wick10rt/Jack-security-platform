# core/serializers.py

from rest_framework import serializers
from .models import Lab, User, LabCompletion

#B2-實驗內容服務
# 定義Lab模型的序列化器

#實驗清單的序列化器(/labs/)
class LabSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = ['id', 'title', 'category']

#實驗詳情的序列化器(/labs/{lab_id}/)
class LabDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = ['id', 'title', 'description', 'category']


#B1-登入驗證服務
# 定義user模型的序列化器

#使用者註冊的序列化器(/auth/register/)
class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self,validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user
    

#B3-使用者資料服務
#定義LabCompletion模型的序列化器

#使用者進度的序列化器(/progress/)
class LabCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabCompletion
        fields=['id','status','user','lab']