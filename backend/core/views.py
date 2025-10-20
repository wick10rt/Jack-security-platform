# core/views.py

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils import timezone

from datetime import timedelta

from rest_framework import generics, permissions,status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Lab, User,LabCompletion,ActiveInstance
from .serializers import (LabSerializer, LabDetailSerializer, UserRegisterSerializer,LabCompletionSerializer,ActiveInstanceSerializer,SubmissionSerializer)


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

    def post(self, request, *args, **kwargs):
        #獲取啟動Lab的物件
        lab_id = self.kwargs.get('id')
        lab = get_object_or_404(Lab, id=lab_id)
        user = request.user
    
        #檢查有沒有正在運行的靶機
        if ActiveInstance.objects.filter(user=user).exists():
            return Response(
                {"error": "你已經正在運行的靶機了"},
                status = status.HTTP_409_CONFLICT
            )

        #測試用
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


#B5-答案驗證服務
#定義答案驗證的view
class SubmitAnswerView(generics.GenericAPIView):
    #EE-6提交答案
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        #獲取Lab物件
        lab_id = self.kwargs.get('id')
        lab = get_object_or_404(Lab, id=lab_id)
        user = request.user
        
        #驗證格式
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submitted_answer = serializer.validated_data['answer']

        #驗證答案
        #答案正確
        if submitted_answer == lab.solution:
            completion, created = LabCompletion.objects.get_or_create(
                user=user,
                lab=lab,
                defaults={'status': 'pending_reflection'}
            )
            #如果已有提交成功紀錄,直接更新狀態
            if not created and completion.status != 'completed':
                completion.status = 'pending_reflection'
                completion.save()
            return Response(
                {"status" : "pending_reflection"},
                status = status.HTTP_200_OK
            )
        #答案錯誤
        else:
            return Response(
                {"error" : "答案錯誤,請重試"},
                status = status.HTTP_400_BAD_REQUEST
            )
