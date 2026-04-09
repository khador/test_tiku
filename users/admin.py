from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ClassInfo, StudentProfile

# 注册自定义 User 并增加自定义字段的显示
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'real_name', 'role', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('角色与信息', {'fields': ('role', 'real_name')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(ClassInfo)
admin.site.register(StudentProfile)