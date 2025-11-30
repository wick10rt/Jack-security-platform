"""
URL configuration for myproject project.

The urlpatterns list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from core.views import UserRegisterView, MyTokenObtainPairView

urlpatterns = [
    # EE-9 進入管理員頁面
    path("admin/", admin.site.urls),
    # EE-0 使用者註冊
    path("api/auth/register/", UserRegisterView.as_view(), name="register"),
    # EE-1 使用者登入
    path("api/auth/login/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    # C-1 需要 Token 認證的 API
    path("api/", include("core.urls")),
]
