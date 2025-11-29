# core/urls.py

from django.urls import path
from .views import LabListView, LabDetailView, UserProgressView, LaunchInstanceView, SubmitAnswerView, CommunitySolutionListView, ReflectionView, UserRegisterView, MyTokenObtainPairView, AccessInstanceView, TerminateInstanceView


urlpatterns = [
        
        
    #B2-實驗內容服務
    # 定義B2的view的url路徑
    path('labs/', LabListView.as_view(), name='lab-list'),
    path('labs/<uuid:id>/', LabDetailView.as_view(), name='lab-detail'),
    path('labs/<uuid:id>/solutions/', CommunitySolutionListView.as_view(), name='community-solutions'),


    #B3-使用者資料服務
    #定義B3的view的url路徑
    path('progress/', UserProgressView.as_view(), name='user-progress'),
    path('labs/<uuid:id>/reflection/', ReflectionView.as_view(), name='submit-reflection'),


    #B4-靶機分配服務
    #定義B4的view的url路徑
    path('labs/<uuid:id>/launch/',LaunchInstanceView.as_view(), name='launch-instance'),
    path('instances/<uuid:id>/access/', AccessInstanceView.as_view(), name='access-instance'),
    path('instances/terminate/', TerminateInstanceView.as_view(), name='terminate-instance'),

    #B5-答案驗證服務
    #定義B5的view的url路徑
    path('labs/<uuid:id>/submit/', SubmitAnswerView.as_view(), name='lab-submit'),
]
