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
from rest_framework import generics, permissions, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.serializers import ValidationError
from .models import Lab, User, LabCompletion, ActiveInstance, CommunitySolution
from .permissions import IsInstanceOwner
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




class HealthCheckView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = []

    def get(self, request, *args, **kwargs):
        db_ok = True
        try:
            from django.db import connection

            connection.ensure_connection()
        except Exception:
            db_ok = False

        redis_ok = True
        try:
            import redis

            redis.from_url(
                settings.CELERY_BROKER_URL, socket_connect_timeout=1
            ).ping()
        except Exception:
            redis_ok = False

        healthy = db_ok and redis_ok
        http_status = (
            status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response(
            {
                "status": "ok" if healthy else "error",
                "database": db_ok,
                "redis": redis_ok,
            },
            status=http_status,
        )


class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "register"


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




class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"error": "缺少 refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response(
                {"error": "無效的 token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "已登出"}, status=status.HTTP_200_OK)


class LabListView(generics.ListAPIView):
    serializer_class = LabSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["title", "category"]
    ordering = ["title"]

    def get_queryset(self):
        qs = Lab.objects.all()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs


class LabCategoriesView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        categories = list(
            Lab.objects.order_by("category")
            .values_list("category", flat=True)
            .distinct()
        )
        return Response(categories, status=status.HTTP_200_OK)


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
        qs = LabCompletion.objects.filter(user=self.request.user).select_related(
            "lab"
        )
        lab = self.request.query_params.get("lab")
        if lab:
            qs = qs.filter(lab_id=lab)
        return qs


class ProgressStatsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        qs = LabCompletion.objects.filter(user=request.user)
        total = qs.count()
        completed = qs.filter(status="completed").count()
        return Response(
            {"total": total, "completed": completed, "pending": total - completed},
            status=status.HTTP_200_OK,
        )


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

        if not lab.requires_answer:
            return Response(
                {"error": "此實驗為純跑靶機題，沒有防禦表單"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

    def post(self, request, *args, **kwargs):
        lab_id = self.kwargs.get("id")
        lab = get_object_or_404(Lab, id=lab_id)
        user = request.user

        with transaction.atomic():
            qs = ActiveInstance.objects.select_for_update()

            qs.filter(user=user, status="error").delete()

            if (
                qs.filter(user=user, expires_at__gt=timezone.now())
                .exclude(status="error")
                .exists()
            ):
                return Response(
                    {"error": "你已經有一個運行中的靶機了"},
                    status=status.HTTP_409_CONFLICT,
                )

            current_active_count = (
                qs.filter(expires_at__gt=timezone.now())
                .exclude(status="error")
                .count()
            )
            if current_active_count >= settings.ACTIVEINSTANCE_LIMIT:
                return Response(
                    {"error": "伺服器忙碌中，請稍後再試"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            expires_at = timezone.now() + timedelta(
                minutes=settings.INSTANCE_EXPIRY_MINUTES
            )
            instance = ActiveInstance.objects.create(
                user=user,
                lab=lab,
                status="creating",
                expires_at=expires_at,
            )

        try:
            launch_instance_task.delay(
                instance_id_str=str(instance.id),
                lab_id_str=str(lab.id),
                user_id_str=str(user.id),
            )
        except Exception as e:
            logger.error(f"派送 launch 任務失敗（broker 不可用？）: {e}")
            instance.delete()
            return Response(
                {"error": "服務暫時無法處理請求，請稍後再試"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        logger.info(f"{user.username} 創建 {instance.id}")

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class ExtendInstanceView(generics.GenericAPIView):
    serializer_class = ActiveInstanceSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        with transaction.atomic():
            instance = (
                ActiveInstance.objects.select_for_update()
                .filter(user=user)
                .exclude(status="error")
                .first()
            )
            if not instance:
                return Response(
                    {"error": "沒有找到你的靶機"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if instance.extensions_used >= settings.INSTANCE_MAX_EXTENSIONS:
                return Response(
                    {"error": "已達延長次數上限"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            base = max(instance.expires_at, timezone.now())
            instance.expires_at = base + timedelta(
                minutes=settings.INSTANCE_EXTENSION_MINUTES
            )
            instance.extensions_used += 1
            instance.save(update_fields=["expires_at", "extensions_used"])

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TerminateInstanceView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        instance = (
            ActiveInstance.objects.filter(user=user)
            .order_by("-created_at")
            .first()
        )

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
    permission_classes = [IsAuthenticated, IsInstanceOwner]
    queryset = ActiveInstance.objects.all()
    serializer_class = ActiveInstanceSerializer
    lookup_field = "id"


class CurrentInstanceView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ActiveInstanceSerializer

    def get(self, request, *args, **kwargs):
        instance = (
            ActiveInstance.objects.filter(
                user=request.user, expires_at__gt=timezone.now()
            )
            .exclude(status="error")
            .order_by("-created_at")
            .first()
        )
        if instance is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AccessInstanceView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsInstanceOwner]
    queryset = ActiveInstance.objects.all()
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response(
            {"target_url": instance.instance_url}, status=status.HTTP_200_OK
        )




class SubmitAnswerView(generics.GenericAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    throttle_scope = "submit_answer"

    def post(self, request, *args, **kwargs):
        lab_id = self.kwargs.get("id")
        lab = get_object_or_404(Lab, id=lab_id)
        user = request.user

        if not lab.requires_answer:
            return Response(
                {"error": "此實驗為純跑靶機題，不需提交答案"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submitted_answer = serializer.validated_data["answer"]

        if submitted_answer.strip() == lab.solution.strip():
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
