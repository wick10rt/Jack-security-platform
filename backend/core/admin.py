# core/admin.py

from django.contrib import admin
from .models import User, Lab, CommunitySolution, LabCompletion, ActiveInstance

# D4-管理員後台服務 把資料庫模型註冊到管理員後台

# B1 –登入驗證服務 & D4-管理後台服務 User模型 
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_staff')
    search_fields = ('username',)

#B2 - 實驗內容服務 & D4 - 管理後台服務 Lab模型
@admin.register(Lab)
class LabAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'docker_image', 'description','solution')
    list_filter = ('category',)
    search_fields = ('title', 'description')

# B2 - 實驗內容服務 & D4 - 管理後台服務 CommunitySolution模型
@admin.register(CommunitySolution)
class CommunitySolutionAdmin(admin.ModelAdmin):
    list_display = ('lab', 'reflection')
    list_filter = ('lab',)

# B3 - 實驗進度服務 & D4 - 管理後台服務 LabCompletion模型
@admin.register(LabCompletion)
class LabCompletionAdmin(admin.ModelAdmin):
    list_display = ('user', 'lab', 'status')
    list_filter = ('status', 'lab')
    search_fields = ('user__username',)

# B4 - 實驗環境服務 & D4 - 管理後台服務 ActiveInstance模型
@admin.register(ActiveInstance)
class ActiveInstanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'lab', 'instance_url','container_id', 'expires_at','created_at')
    search_fields = ('user__username', 'lab__title')
