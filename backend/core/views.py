# core/views.py

from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Lab, User,LabCompletion
from .serializers import LabSerializer, LabDetailSerializer, UserRegisterSerializer,LabCompletionSerializer
from rest_framework.permissions import IsAuthenticated


#B2-實驗內容服務
# 定義實驗資料的view

# EE-3 獲取所有實驗清單
class LabListView(generics.ListAPIView):
    queryset = Lab.objects.all().order_by('title')
    serializer_class = LabSerializer

# EE-4 獲取指定的實驗詳情
class LabDetailView(generics.RetrieveAPIView):
    queryset = Lab.objects.all()
    serializer_class = LabDetailSerializer
    lookup_field = 'id'



#B1-登入驗證服務
# 定義使用者註冊的view

# EE-0 使用者註冊
class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


#B3-使用者資料服務
#定義使用者進度的view

#EE-2 查看使用者學習進度
class UserProgressView(generics.ListAPIView):
    serializer_class = LabCompletionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return LabCompletion.objects.filter(user=user)