from django.contrib import admin
from .models import User, Lab, CommunitySolution, LabCompletion, ActiveInstance

# D4 管理員後台服務


# User Model
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "is_staff")
    search_fields = ("username",)


# Lab Model
@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "docker_image", "description", "solution",)
    list_filter = ("category",)
    search_fields = ("title", "description")


# CommunitySolution Model
@admin.register(CommunitySolution)
class CommunitySolutionAdmin(admin.ModelAdmin):
    list_display = ("lab", "reflection")
    list_filter = ("lab",)


# LabCompletion Model
@admin.register(LabCompletion)
class LabCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "lab", "status")
    list_filter = ("status", "lab")
    search_fields = ("user__username",)


# ActiveInstance Model
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
