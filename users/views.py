# users/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework import viewsets, permissions
from .models import User, ClassInfo
from .serializers import (
    ClassInfoSerializer, TeacherManagementSerializer, StudentManagementSerializer
)

# 自定义管理员权限
class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class ClassInfoViewSet(viewsets.ModelViewSet):
    queryset = ClassInfo.objects.all()
    serializer_class = ClassInfoSerializer
    permission_classes = [IsAdminRole]

class TeacherManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role='teacher')
    serializer_class = TeacherManagementSerializer
    permission_classes = [IsAdminRole]

class StudentManagementViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role='student')
    serializer_class = StudentManagementSerializer
    permission_classes = [IsAdminRole]



class CustomTokenObtainPairView(TokenObtainPairView):
    """
    自定义的登录视图，使用我们刚才写的自定义序列化器
    """
    serializer_class = CustomTokenObtainPairSerializer