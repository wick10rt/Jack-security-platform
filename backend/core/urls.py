# core/urls.py

from django.urls import path
from .views import LabListView, LabDetailView, UserProgressView


urlpatterns = [
    
    #B2-實驗內容服務
    # 定義B2的view的url路徑
    path('labs/', LabListView.as_view(), name='lab-list'),
    path('labs/<uuid:id>/', LabDetailView.as_view(), name='lab-detail'),

    #B3-使用者資料服務
    #定義B3的view的url路徑
    path('progress/', UserProgressView.as_view(), name='user-progress'),

]