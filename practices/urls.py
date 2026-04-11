# practices/urls.py
from django.urls import path
from .views import (
    GeneratePracticeView, SubmitPracticeView, PracticeHistoryView, ErrorBookListView,
    TeacherClassListView, TeacherClassDashboardView, TeacherStudentHistoryView, TeacherQuestionStatsView
)

urlpatterns = [
    # ---- 学生端接口 ----
    path('generate/', GeneratePracticeView.as_view(), name='generate-practice'),
    path('submit/', SubmitPracticeView.as_view(), name='submit-practice'),
    path('history/', PracticeHistoryView.as_view(), name='practice-history'),
    path('error_book/', ErrorBookListView.as_view(), name='error-book-list'),

    # ---- 教师端接口 ----
    # 1. 班级列表
    path('teacher/classes/', TeacherClassListView.as_view(), name='teacher-classes'),
    # 2. 班级整体与学生明细 (这里的 <int:class_id> 表示接收一个整数ID)
    path('teacher/classes/<int:class_id>/', TeacherClassDashboardView.as_view(), name='teacher-class-dashboard'),
    # 3. 班级各题目正确率
    path('teacher/classes/<int:class_id>/questions/', TeacherQuestionStatsView.as_view(), name='teacher-class-questions'),
    # 4. 单个学生历史记录
    path('teacher/students/<int:student_id>/', TeacherStudentHistoryView.as_view(), name='teacher-student-history'),
]