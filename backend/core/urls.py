from django.urls import path
from .views import (
    LabListView,
    LabDetailView,
    UserProgressView,
    LaunchInstanceView,
    SubmitAnswerView,
    CommunitySolutionListView,
    ReflectionView,
    UserRegisterView,
    MyTokenObtainPairView,
    AccessInstanceView,
    TerminateInstanceView,
    InstanceStatusView,
)


urlpatterns = [
    # EE-2 查看學習進度
    path("progress/", UserProgressView.as_view(), name="user-progress"),
    # EE-3 查看實驗清單
    path("labs/", LabListView.as_view(), name="lab-list"),
    # EE-4 查看實驗詳情
    path("labs/<uuid:id>/", LabDetailView.as_view(), name="lab-detail"),
    # EE-5 啟動靶機
    path("labs/<uuid:id>/launch/", LaunchInstanceView.as_view(), name="launch-instance"),
    # 取得靶機地址
    path("instances/<uuid:id>/access/", AccessInstanceView.as_view(), name="access-instance"),
    # 取得靶機狀態
    path('instances/<uuid:id>/status/', InstanceStatusView.as_view(), name='instance-status'),
    # EE-6 提交答案
    path("labs/<uuid:id>/submit/", SubmitAnswerView.as_view(), name="answer-submit"),
    # EE-7 提交防禦表單
    path("labs/<uuid:id>/reflection/", ReflectionView.as_view(), name="submit-reflection"),
    # EE-8 查看他人解法
    path("labs/<uuid:id>/solutions/", CommunitySolutionListView.as_view(), name="community-solutions"),
    # EE-11 手動關閉靶機
    path("instances/terminate/", TerminateInstanceView.as_view(), name="terminate-instance"),
    
]
