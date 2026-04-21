# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', '学生'),
        ('teacher', '教师'),
        ('admin', '管理员'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student', verbose_name="角色")
    real_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="姓名")

    # === 学生专属字段 ===
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="学号")
    # 保留原来的 class_info
    class_info = models.ForeignKey('ClassInfo', on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="所属班级")

    # === 教师专属字段 ===
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name="工号")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="电话")

    # === 【新增】老师管理的班级 (多对多) ===
    teaches_classes = models.ManyToManyField(
        'ClassInfo', 
        blank=True, 
        related_name='teachers'
    )
    
    class Meta:
        verbose_name = "总账户(管理员)"
        verbose_name_plural = verbose_name

# 【核心魔法】：强制将 Django 自带的 username 标签改成“账号”
User._meta.get_field('username').verbose_name = '账号'


class ClassInfo(models.Model):
    name = models.CharField(max_length=50, verbose_name="班级名称")
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'teacher'}, related_name='taught_classes', verbose_name="负责教师")

    class Meta:
        verbose_name = "班级管理"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

# === 代理模型（专门用来骗过 Admin，生成两个独立菜单） ===
class StudentAccount(User):
    class Meta:
        proxy = True
        verbose_name = "学生管理"
        verbose_name_plural = verbose_name

class TeacherAccount(User):
    class Meta:
        proxy = True
        verbose_name = "教师管理"
        verbose_name_plural = verbose_name