# core/urls.py

from django.urls import path
from .views import LabListView, LabDetailView

#B2-實驗內容服務
# 定義B2的view的url路徑

urlpatterns = [
    path('labs/', LabListView.as_view(), name='lab-list'),
    path('labs/<uuid:id>/', LabDetailView.as_view(), name='lab-detail'),
]