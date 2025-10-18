# core/views.py

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils import timezone

from datetime import timedelta

from rest_framework import generics, permissions,status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Lab, User,LabCompletion,ActiveInstance
from .serializers import (LabSerializer, LabDetailSerializer, UserRegisterSerializer,LabCompletionSerializer,ActiveInstanceSerializer)


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

    #獲取已完成的實驗
    def get_queryset(self):
        user = self.request.user
        return LabCompletion.objects.filter(user=user)
    

#B4-靶機分配服務
#定義啟動靶機的view
class LaunchInstanceView(generics.GenericAPIView):
    serializer_class = ActiveInstanceSerializer
    permission_classes = [IsAuthenticated]

    #獲取啟動Lab的物件
    def post(self, request, *args, **kwargs):
        lab_id = self.kwargs.get('id')
        lab = get_object_or_404(Lab, id=lab_id)
        user = request.user
    
        #檢查有沒有正在運行的靶機
        if ActiveInstance.objects.filter(user=user).exists():
            return Response(
                {"error": "你已經正在運行的靶機了"},
                status = status.HTTP_409_CONFLICT
            )

        test_instance_url = f"http://test/{user.username}/{lab.id}.com"
        test_container_id = "test_container_12345"

        #在D3-資料庫服務中建立紀錄
        expires_at = timezone.now() + timedelta(minutes=30)
        instance = ActiveInstance.objects.create(
            user = user,
            lab = lab,
            instance_url = test_instance_url,
            container_id = test_container_id,
            expires_at = expires_at
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)