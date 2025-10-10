# core/views.py

from django.shortcuts import render
from rest_framework import generics
from .models import Lab
from .serializers import LabSerializer, LabDetailSerializer

#B2-實驗內容服務
# 定義api請求時要回傳的view

# EE-3 獲取所有實驗清單
class LabListView(generics.ListAPIView):
    queryset = Lab.objects.all().order_by('title')
    serializer_class = LabSerializer


# EE-4 獲取指定的實驗詳情
class LabDetailView(generics.RetrieveAPIView):
    queryset = Lab.objects.all()
    serializer_class = LabDetailSerializer
    lookup_field = 'id'