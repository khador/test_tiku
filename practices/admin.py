from django.contrib import admin
from .models import PracticeSession, QuestionAttempt, ErrorBook

@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    # 列表页显示的字段
    list_display = ('id', 'student', 'start_time', 'duration', 'accuracy')
    # 右侧的过滤器
    list_filter = ('start_time',)
    # 顶部的搜索框（可以搜学生的账号或姓名）
    search_fields = ('student__username', 'student__real_name')

@admin.register(QuestionAttempt)
class QuestionAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'question', 'is_correct', 'time_spent')
    list_filter = ('is_correct',)
    # 可以搜题目 ID 或者学生账号
    search_fields = ('session__student__username', 'question__sn')

@admin.register(ErrorBook)
class ErrorBookAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'question', 'consecutive_correct', 'is_active', 'last_practiced')
    # 侧边栏过滤：快速查看“还在错题本中”的题目
    list_filter = ('is_active', 'last_practiced')
    search_fields = ('student__username', 'student__real_name', 'question__sn')