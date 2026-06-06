import uuid
import os
import subprocess
import logging
from .tasks import launch_instance_task, terminate_instance_task
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login
from datetime import timedelta
from django.db import transaction
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseForbidden
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.serializers import ValidationError
from .models import Lab, User, LabCompletion, ActiveInstance, CommunitySolution
from .serializers import (
    LabSerializer,
    LabDetailSerializer,
    UserRegisterSerializer,
    LabCompletionSerializer,
    ActiveInstanceSerializer,
    SubmissionSerializer,
    CommunitySolutionSerializer,
    MyTokenObtainPairSerializer,
    ReflectionSerializer,
)
from axes.decorators import axes_dispatch
from axes.handlers.proxy import AxesProxyHandler

logger = logging.getLogger(__name__)




class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


@method_decorator(axes_dispatch, name="dispatch")
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request=request, username=username, password=password)

        if user is None:
            AxesProxyHandler.user_login_failed(
                request=request,
                sender=self.__class__,
                credentials={"username": username},
            )
            return Response(
                {"detail": "帳號或密碼錯誤"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            if user.is_staff:
                login(request, user)
                response.data["redirect_url"] = "/admin/"
            else:
                response.data["redirect_url"] = "/dashboard"
        return response




class LabListView(generics.ListAPIView):
    queryset = Lab.objects.all().order_by("title")
    serializer_class = LabSerializer


class LabDetailView(generics.RetrieveAPIView):
    queryset = Lab.objects.all()
    serializer_class = LabDetailSerializer
    lookup_field = "id"


class CommunitySolutionListView(generics.ListAPIView):
    serializer_class = CommunitySolutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        lab_id = self.kwargs.get("id")

        is_completed = LabCompletion.objects.filter(
            user=user, lab_id=lab_id, status="completed"
        ).exists()

        if not is_completed:
            return CommunitySolution.objects.none()

        queryset = CommunitySolution.objects.filter(lab_id=lab_id)

        return queryset




class UserProgressView(generics.ListAPIView):
    serializer_class = LabCompletionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return LabCompletion.objects.filter(user=user)


class ReflectionView(generics.GenericAPIView):
    serializer_class = ReflectionSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        lab_id = self.kwargs.get("id")
        lab = get_object_or_404(Lab, id=lab_id)

        try:
            solution = CommunitySolution.objects.get(user=user, lab=lab)
            serializer = self.get_serializer(solution)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CommunitySolution.DoesNotExist:
            return Response(
                {"detail": "尚未提交防禦表單"}, status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request, *args, **kwargs):
        user = request.user
        lab_id = self.kwargs.get("id")
        lab = get_object_or_404(Lab, id=lab_id)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            try:
                completion = LabCompletion.objects.get(user=user, lab=lab)
                if completion.status not in ["pending_reflection", "completed"]:
                    raise ValidationError("錯誤狀態，無法提交防禦表單")
            except LabCompletion.DoesNotExist:
                raise ValidationError("你要先提交正確答案才能填寫防禦表單")

            instance, created = CommunitySolution.objects.update_or_create(
                user=user, lab=lab, defaults=serializer.validated_data
            )

            if completion.status == "pending_reflection":
                completion.status = "completed"
                completion.save()

        response_serializer = self.get_serializer(instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)




class LaunchInstanceView(generics.GenericAPIView):
    serializer_class = ActiveInstanceSerializer
    permission_classes = [IsAuthenticated]
    ACTIVEINSTANCE_LIMIT = 30

    def post(self, request, *args, **kwargs):
        lab_id = self.kwargs.get("id")
        lab = get_object_or_404(Lab, id=lab_id)
        user = request.user

        with transaction.atomic():
            qs = ActiveInstance.objects.select_for_update()

            if qs.filter(user=user, expires_at__gt=timezone.now()).exists():
                return Response(
                    {"error": "你已經有一個運行中的靶機了"},
                    status=status.HTTP_409_CONFLICT,
                )

            current_active_count = qs.filter(expires_at__gt=timezone.now()).count()
            if current_active_count >= self.ACTIVEINSTANCE_LIMIT:
                return Response(
                    {"error": "伺服器忙碌中，請稍後再試"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            expires_at = timezone.now() + timedelta(
                minutes=30
            )
            instance = ActiveInstance.objects.create(
                user=user,
                lab=lab,
                instance_url="creating...",
                container_id="creating...",
                expires_at=expires_at,
            )

        launch_instance_task.delay(
            instance_id_str=str(instance.id),
            lab_id_str=str(lab.id),
            user_id_str=str(user.id),
        )
        logger.info(f"{user.username} 創建 {instance.id}")

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class TerminateInstanceView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        instance = ActiveInstance.objects.filter(user=user).first()

        if not instance:
            return Response(
                {"message": "沒有找到你的靶機"},
                status=status.HTTP_404_NOT_FOUND,
            )

        instance_id_str = str(instance.id)
        container_id = instance.container_id

        terminate_instance_task.delay(instance_id_str, container_id)

        instance.delete()
        logger.info(f"{instance_id_str} 銷毀任務已排程")

        return Response(
            {"message": f"正在銷毀 {instance_id_str}"},
            status=status.HTTP_202_ACCEPTED,
        )


class InstanceStatusView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = ActiveInstance.objects.all()
    serializer_class = ActiveInstanceSerializer
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.user != request.user:
            return Response({"error": "禁止進入"}, status=status.HTTP_403_FORBIDDEN)

        return super().get(request, *args, **kwargs)


class AccessInstanceView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        instance_id = self.kwargs.get("id")
        instance = get_object_or_404(ActiveInstance, id=instance_id)

        if instance.user != request.user:
            return Response({"error": "禁止進入"}, status=status.HTTP_403_FORBIDDEN)

        return Response(
            {"target_url": instance.instance_url}, status=status.HTTP_200_OK
        )




class SubmitAnswerView(generics.GenericAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        lab_id = self.kwargs.get("id")
        lab = get_object_or_404(Lab, id=lab_id)
        user = request.user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submitted_answer = serializer.validated_data["answer"]

        if submitted_answer == lab.solution:
            completion, created = LabCompletion.objects.get_or_create(
                user=user, lab=lab, defaults={"status": "pending_reflection"}
            )

            if completion.status == "completed":
                return Response(
                    {
                        "status": "already_completed",
                        "message": "你已經完成過這個實驗了",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                if not created:
                    completion.status = "pending_reflection"
                    completion.save()

                return Response(
                    {"status": "pending_reflection"}, status=status.HTTP_200_OK
                )
        else:
            return Response(
                {"error": "答案錯誤，請再試一次"},
                status=status.HTTP_400_BAD_REQUEST,
            )
