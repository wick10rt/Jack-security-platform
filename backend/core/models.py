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
    solution = models.TextField(
        blank=True,
        default="",
        help_text="固定答案題要交回的 flag 字串；純跑靶機題（requires_answer 取消勾選）留空即可。",
    )
    requires_answer = models.BooleanField(
        default=True,
        help_text="是否需要提交答案。取消勾選＝純跑靶機沙盒：無答案、無防禦表單、不計完成、不進社群解法。",
    )
    docker_image = models.CharField(
        max_length=255,
        help_text="單一容器靶機的 web 鏡像。多服務題改用下方 compose_template。",
    )
    compose_template = models.TextField(
        blank=True,
        default="",
        help_text=(
            "留空 → 依 needs_db/db_image 自動產生 web(+mysql)。"
            "多服務（php+nginx、postgres…）在此貼完整 docker-compose YAML。"
            "對外服務設為 web_service；其餘自動內部互通。"
            "設定/程式碼需烤進鏡像（平台不掛主機檔），"
            "平台只對外開 web_service:web_port 並強制套用資源/安全限制。"
        ),
    )
    web_service = models.CharField(
        max_length=100,
        default="web",
        help_text="compose 中要對使用者開埠的服務名稱。",
    )
    web_port = models.PositiveIntegerField(
        default=80,
        help_text="對外服務在容器內監聽的埠。",
    )
    needs_db = models.BooleanField(
        default=True,
        help_text="compose_template 留空時是否附加一個 mysql 容器。不需 DB 的題取消勾選。",
    )
    db_image = models.CharField(
        max_length=255,
        default="mysql:8.0",
        help_text="compose_template 留空且 needs_db 時使用的 DB 鏡像（如 mysql:5.6）。",
    )

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
