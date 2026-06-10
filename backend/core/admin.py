from django import forms
from django.contrib import admin
from .models import User, Lab, CommunitySolution, LabCompletion, ActiveInstance


COMPOSE_PLACEHOLDER = """# 多服務範例（php-fpm + nginx + mysql）。對外服務設為 web_service=web、web_port=80。
# 設定/程式碼需烤進鏡像，平台不掛主機檔，且只對外開 web_service。
services:
  web:                         # 對使用者開的就是這個（nginx）
    image: myorg/lab-nginx:1.0 # nginx 設定烤進鏡像，fastcgi_pass php:9000
    depends_on:
      php:
        condition: service_started
      db:
        condition: service_healthy
  php:                         # 內部：php-fpm + 應用程式碼
    image: myorg/lab-php:1.0
    environment: [DB_HOST=db, DB_USER=root, DB_PASSWORD=root, DB_NAME=app]
  db:
    image: mysql:8.0
    environment: { MYSQL_ROOT_PASSWORD: root, MYSQL_DATABASE: app }
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-proot"]
      interval: 5s
      retries: 24
"""


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "is_staff")
    search_fields = ("username",)


@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "docker_image", "needs_db", "requires_answer")
    list_filter = ("category", "needs_db", "requires_answer")
    search_fields = ("title", "description")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "compose_template":
            formfield.widget = forms.Textarea(
                attrs={
                    "rows": 18,
                    "cols": 80,
                    "style": "font-family: monospace;",
                    "placeholder": COMPOSE_PLACEHOLDER,
                }
            )
        return formfield


@admin.register(CommunitySolution)
class CommunitySolutionAdmin(admin.ModelAdmin):
    list_display = ("lab", "reflection")
    list_filter = ("lab",)


@admin.register(LabCompletion)
class LabCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "lab", "status")
    list_filter = ("status", "lab")
    search_fields = ("user__username",)


@admin.register(ActiveInstance)
class ActiveInstanceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "lab",
        "instance_url",
        "container_id",
        "expires_at",
        "created_at",
    )
    search_fields = ("user__username", "lab__title")
