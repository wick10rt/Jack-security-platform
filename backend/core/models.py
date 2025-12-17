import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


# S3 使用物件關聯對應定義資料庫的資料結構
# D3 資料庫服務


# User表 U1~U4
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


# Lab表 L1~L6
class Lab(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=100)
    solution = models.TextField()
    docker_image = models.CharField(max_length=255)

    def __str__(self):
        return self.title


# CommunitySolution表 CS1~CS5
class CommunitySolution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab = models.ForeignKey(
        Lab, on_delete=models.CASCADE, related_name="community_solutions"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payload = models.TextField(blank=False, null=False)
    reflection = models.TextField(blank=False, null=False)

    # 一個使用者對同一個實驗只能有一個解法
    class Meta:
        unique_together = ("lab", "user")

    def __str__(self):
        return f"{self.lab.title} other's solution"


# LabCompletion表 LC1~LC4
class LabCompletion(models.Model):
    status_choices = [
        ("pending_reflection", "Pending Reflection"),
        ("completed", "Completed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="completions")
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name="completions")
    status = models.CharField(max_length=50, choices=status_choices)

    # 一個使用者對同一個實驗只能有一個紀錄
    class Meta:
        unique_together = ("user", "lab")

    def __str__(self):
        return f"{self.user.username} - {self.lab.title} ({self.status})"


# ActiveInstance表 AI1~AI7
class ActiveInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="active_instances"
    )
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)
    instance_url = models.CharField(max_length=255)
    container_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} create a {self.lab.title} instance"
