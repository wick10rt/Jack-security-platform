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
    
    path("admin/", admin.site.urls),
    

    #B1-登入驗證服務
    #EE-0 註冊api
    path("api/auth/register/", UserRegisterView.as_view(), name="register"),
    #EE-1,EE-9 登入api
    path("api/auth/login/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),


    path("api/", include("core.urls")),
]