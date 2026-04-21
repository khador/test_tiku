
# tiku_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from users.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # === JWT 登录与刷新接口 ===
    # 前端发 POST 请求到这个地址进行登录
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # 前端用 refresh_token 换取新的 access_token
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 业务接口
    path("api/practices/", include('practices.urls')),
    
    path("api/", include('users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)