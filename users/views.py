# users/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    自定义的登录视图，使用我们刚才写的自定义序列化器
    """
    serializer_class = CustomTokenObtainPairSerializer