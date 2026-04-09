# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """自定义用户表，区分角色"""
    ROLE_CHOICES = (
        ('student', '学生'),
        ('teacher', '教师'),
        ('admin', '管理员'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student', verbose_name="角色")
    real_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="真实姓名")

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name

class ClassInfo(models.Model):
    """班级表"""
    name = models.CharField(max_length=50, verbose_name="班级名称")
    # 一个老师可以教多个班级
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='taught_classes', verbose_name="负责教师")

    def __str__(self):
        return self.name

class StudentProfile(models.Model):
    """学生额外信息表（与 User 一对一关联）"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    class_info = models.ForeignKey(ClassInfo, on_delete=models.SET_NULL, null=True, related_name='students', verbose_name="所属班级")