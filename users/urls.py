# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClassInfoViewSet, TeacherManagementViewSet, StudentManagementViewSet

router = DefaultRouter()
router.register(r'classes', ClassInfoViewSet, basename='admin-classes')
router.register(r'teachers', TeacherManagementViewSet, basename='admin-teachers')
router.register(r'students', StudentManagementViewSet, basename='admin-students')

urlpatterns = [
    path('admin-manage/', include(router.urls)),
]