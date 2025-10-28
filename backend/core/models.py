# core/models.py

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

# 定義整個系統的數據庫結構實現 D3 - 資料庫服務
# 每個class對應資料庫的一張表

# B1 - 登入驗證服務 & D4 - 管理後台服務 
# 儲存所有與使用者身份、角色和認證相關的數據

class User(AbstractUser):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)

# B2 - 實驗內容服務
# 儲存所有實驗內容相關的數據

class Lab(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description=models.TextField()
    category=models.CharField(max_length=100)
    solution = models.TextField()
    docker_image = models.CharField(max_length=255)

    def __str__(self):
        return self.title

#儲存其他人的解法跟防禦省思

class CommunitySolution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name='community_solutions')
    reflection = models.TextField(blank=False, null=False)

    def __str__(self):
        return f"{self.lab.title} other's solution"

# B3 - 實驗環境服務
# 儲存所以與使用者學習進度相關的數據

class LabCompletion(models.Model):
    status_choices = [
        ('pending_reflection', 'Pending Reflection'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completions')
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name='completions')
    status = models.CharField(max_length=50,choices=status_choices)

    class Meta:
        unique_together=('user','lab')

    def __str__(self):
        return f"{self.user.username} - {self.lab.title} ({self.status})"

# B4-靶機分配服務
# 儲存當前運行的容器狀態跟資訊

class ActiveInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_instances')
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)
    instance_url = models.CharField(max_length=255)
    container_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} create a {self.lab.title} instance"