import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser




class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Lab(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=100)
    solution = models.TextField()
    docker_image = models.CharField(max_length=255)
    compose_template = models.TextField(blank=True, default="")
    web_service = models.CharField(max_length=100, default="web")
    web_port = models.PositiveIntegerField(default=80)

    def __str__(self):
        return self.title


class CommunitySolution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lab = models.ForeignKey(
        Lab, on_delete=models.CASCADE, related_name="community_solutions"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payload = models.TextField(blank=False, null=False)
    reflection = models.TextField(blank=False, null=False)

    class Meta:
        unique_together = ("lab", "user")

    def __str__(self):
        return f"{self.lab.title} other's solution"


class LabCompletion(models.Model):
    status_choices = [
        ("pending_reflection", "Pending Reflection"),
        ("completed", "Completed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="completions")
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name="completions")
    status = models.CharField(max_length=50, choices=status_choices)

    class Meta:
        unique_together = ("user", "lab")

    def __str__(self):
        return f"{self.user.username} - {self.lab.title} ({self.status})"


class ActiveInstance(models.Model):
    status_choices = [
        ("creating", "Creating"),
        ("running", "Running"),
        ("error", "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="active_instances"
    )
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=status_choices, default="creating", db_index=True
    )
    instance_url = models.CharField(max_length=255, blank=True, default="")
    container_id = models.CharField(max_length=255, blank=True, default="")
    extensions_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)

    def __str__(self):
        return f"{self.user.username} create a {self.lab.title} instance"
