# core/serializers.py

from rest_framework import serializers
from .models import Lab

#B2-實驗內容服務
# 定義Lab模型的序列化器

#實驗清單的序列化器
class LabSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = ['id', 'title', 'category']


#實驗詳情的序列化器
class LabDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = ['id', 'title', 'description', 'category']
