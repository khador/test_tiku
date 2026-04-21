# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ClassInfo, StudentAccount, TeacherAccount

@admin.register(ClassInfo)
class ClassInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher')

# ======== 学生管理后台 ========
@admin.register(StudentAccount)
class StudentAdmin(UserAdmin):
    # 过滤器：这个列表只显示学生
    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='student')

    # 【重要】：重写新建/编辑表单的字段布局，剔除无关字段
    fieldsets = (
        ('登录信息', {'fields': ('username', 'password')}),
        ('学生档案', {'fields': ('real_name', 'student_id', 'class_info')}),
        ('权限状态', {'fields': ('is_active',)}),
    )
    # 列表展示的列
    list_display = ('username', 'real_name', 'student_id', 'class_info', 'is_active')
    search_fields = ('username', 'real_name', 'student_id')

    # 后台保存时，自动强制赋角色
    def save_model(self, request, obj, form, change):
        if not change: # 如果是新建
            obj.role = 'student'
        super().save_model(request, obj, form, change)


# ======== 教师管理后台 ========
@admin.register(TeacherAccount)
class TeacherAdmin(UserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='teacher')

    fieldsets = (
        ('登录信息', {'fields': ('username', 'password')}),
        # 【核心修改】：把 teaches_classes 加进教师档案里
        ('教师档案', {'fields': ('real_name', 'employee_id', 'phone', 'teaches_classes')}),
        ('权限状态', {'fields': ('is_active', 'is_staff')}),
    )
    list_display = ('username', 'real_name', 'employee_id', 'phone', 'is_active')
    search_fields = ('username', 'real_name', 'employee_id')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.role = 'teacher'
            obj.is_staff = True # 教师通常需要登录后台查看报表
        super().save_model(request, obj, form, change)


# ======== 保留原始的总账户管理(供超级管理员使用) ========
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(role='admin')
    list_display = ('username', 'role', 'is_superuser')