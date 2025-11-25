# core/views.py
import uuid
import os
import subprocess

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login
from datetime import timedelta
from django.db import transaction
from django.conf import settings

from rest_framework import generics, permissions,status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Lab, User,LabCompletion,ActiveInstance, CommunitySolution
from .serializers import (LabSerializer, LabDetailSerializer, UserRegisterSerializer,LabCompletionSerializer,ActiveInstanceSerializer,SubmissionSerializer, CommunitySolutionSerializer,MyTokenObtainPairSerializer,ReflectionSerializer)

from axes.decorators import axes_dispatch
from axes.handlers.proxy import AxesProxyHandler

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

#EE-8 獲取指定實驗的其他人解法
class CommunitySolutionListView(generics.ListAPIView):
    serializer_class = CommunitySolutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        lab_id = self.kwargs.get('id')

        #檢查使用者是否完成實驗
        is_completed = LabCompletion.objects.filter(
            user=user,
            lab_id=lab_id,
            status='completed').exists()
        
        if not is_completed:
            return CommunitySolution.objects.none()
        
        #過濾條件-只顯示關於目前實驗室的解法
        queryset = CommunitySolution.objects.filter(lab_id=lab_id)

        return queryset


#B1-登入驗證服務
# 定義使用者註冊的view

# EE-0 使用者註冊
class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

# EE-1 , EE-9 認證使用者與管理員登入並跳轉正確頁面
@method_decorator(axes_dispatch, name='dispatch')
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request=request, username=username, password=password)

        #帳號或密碼錯誤
        if user is None:
            
            #紀錄失敗紀錄
            AxesProxyHandler.user_login_failed(request=request, sender=self.__class__, credentials={'username': username})

            return Response({"detail": "username or password is wrong"}, status=status.HTTP_401_UNAUTHORIZED)

        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            
            # 根據使用者決定重導向的URL
            if user.is_staff:
                login(request, user)
                response.data["redirect_url"] = "/admin/"
            else:
                response.data["redirect_url"] = "/dashboard"

        return response
    

# B3-使用者資料服務
#定義使用者進度的view

#EE-2 查看使用者學習進度
class UserProgressView(generics.ListAPIView):
    serializer_class = LabCompletionSerializer
    permission_classes = [IsAuthenticated]

    #獲取完成實驗的狀況
    def get_queryset(self):
        user = self.request.user
        return LabCompletion.objects.filter(user=user)
    
# EE-7 提交防禦表單
class ReflectionView(generics.GenericAPIView):
    serializer_class = ReflectionSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        lab_id = self.kwargs.get('id')
        lab = get_object_or_404(Lab, id=lab_id)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        #確保資料全部寫入成功
        with transaction.atomic():
            try:
                completion = LabCompletion.objects.get(user=user, lab=lab)
                if completion.status not in ['pending_reflection', 'completed']:
                     raise serializers.ValidationError("error please try again")
            except LabCompletion.DoesNotExist:
                raise serializers.ValidationError("you have to submit the correct answer before reflection.")

            instance, created = CommunitySolution.objects.update_or_create(
                user=user,
                lab=lab,
                defaults=serializer.validated_data
            )

            if completion.status == 'pending_reflection':
                completion.status = 'completed'
                completion.save()

        response_serializer = self.get_serializer(instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


#B4-靶機分配服務
#定義啟動靶機的view
class LaunchInstanceView(generics.GenericAPIView):
    serializer_class = ActiveInstanceSerializer
    permission_classes = [IsAuthenticated]

    # 根據伺服器效能決定容器上限
    ACTIVEINSTANCE_LIMIT = 30
    
    def post(self, request, *args, **kwargs):
        #獲取啟動Lab的物件
        lab_id = self.kwargs.get('id')
        lab = get_object_or_404(Lab, id=lab_id)
        user = request.user

        #檢查靶機是否超過系統限制
        current_active_count = ActiveInstance.objects.count()
        if current_active_count >= self.ACTIVEINSTANCE_LIMIT:
            return Response(
                {"error": "instance launch failed please try again later if still not work contact admin william -> s1121717@mail.yzu.edu.tw"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        

        #檢查有沒有正在運行的靶機
        if ActiveInstance.objects.filter(user=user).exists():
            return Response(
                {"error": "you already have an active instance"},
                status = status.HTTP_409_CONFLICT
            )


        #在D3-資料庫服務中建立紀錄
        expires_at = timezone.now() + timedelta(minutes=30)
        instance = ActiveInstance.objects.create(
            user = user,
            lab = lab,
            instance_url = "waiting...",
            container_id = "waiting...",
            expires_at = expires_at
        )


        # D2-容器管理服務 生成 docker-compose.yml
        instance_id = instance.id
        compose_dir = settings.BASE_DIR /'instances'
        compose_dir.mkdir(exist_ok=True)
        compose_file_path = compose_dir / f"docker-compose-{instance_id}.yml"
        compose_content = f"""
services:
  web:
    image: {lab.docker_image} 
    ports:
      - "80"
    depends_on:
      - db
    environment:
      - DB_HOST=db
      - DB_USER=root
      - DB_PASSWORD=root
      - DB_NAME=security
  db:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: security
"""        
        with open(compose_file_path, 'w') as f:
            f.write(compose_content)


        # D2-容器管理服務 使用 docker-compose 啟動容器
        try:
            subprocess.run(
                ["docker-compose", "-f", str(compose_file_path), "up", "-d"],
                check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            os.remove(compose_file_path)
            instance.delete()
            return Response(
                {"error": "Launch instance failed, please try again or contact admin william"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

        # 獲取 D2-容器管理服務 產生的容器端口
        try:
            result = subprocess.run(
                ['docker-compose', '-f', str(compose_file_path), 'port', 'web', '80'],
                check=True, capture_output=True, text=True
            )
            host_port = result.stdout.strip().split(':')[-1]
            instance_url = f"http://127.0.0.1:{host_port}"
        except (subprocess.CalledProcessError, IndexError) as e:
            subprocess.run(
                ["docker-compose", "-f", str(compose_file_path), "down", "-v"],
                check=True
            )
            os.remove(compose_file_path)
            instance.delete()
            return Response(
                {"error": "Failed to get instance details, please try again or contact admin william"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

        # 獲取 D2-容器管理服務 產生的容器 ID
        try:
            result = subprocess.run(
                ['docker-compose', '-f', str(compose_file_path), 'ps', '-q', 'web'],
                check=True, capture_output=True, text=True
            )
            container_id = result.stdout.strip()
        except subprocess.CalledProcessError as e:
            subprocess.run(
                ["docker-compose", "-f", str(compose_file_path), "down", "-v"],
                check=True
            )
            os.remove(compose_file_path)
            instance.delete()
            return Response(
                {"error": "Failed to get instance details, please try again or contact admin william"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

        # 更新 D3-資料庫服務中的紀錄
        instance.instance_url = instance_url
        instance.container_id = container_id
        instance.save()
        

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


#B5-答案驗證服務
#定義答案驗證的view
class SubmitAnswerView(generics.GenericAPIView):
    #EE-6提交答案
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        lab_id = self.kwargs.get('id')
        lab = get_object_or_404(Lab, id=lab_id)
        user = request.user
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submitted_answer = serializer.validated_data['answer']

        #答案正確
        if submitted_answer == lab.solution:
            completion, created = LabCompletion.objects.get_or_create(
                user=user,
                lab=lab,
                defaults={'status': 'pending_reflection'}
            )

            #使用者已經完成過實驗
            if completion.status == 'completed':
                return Response(
                    {"status": "already_completed", "message": "You have already completed this lab."},
                    status=status.HTTP_200_OK
                )
            else:
                #使用者第一次提交正確答案
                if not created:
                    completion.status = 'pending_reflection'
                    completion.save()
                
                return Response(
                    {"status": "pending_reflection"},
                    status=status.HTTP_200_OK
                )
        #答案錯誤
        else:
            return Response(
                {"error": "wrong answer please try again"},
                status=status.HTTP_400_BAD_REQUEST
            )