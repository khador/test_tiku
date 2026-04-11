# practices/urls.py
from django.urls import path
from .views import GeneratePracticeView, SubmitPracticeView

urlpatterns = [
    # 路径映射到我们刚刚写的 View
    path('generate/', GeneratePracticeView.as_view(), name='generate-practice'),
    path('submit/', SubmitPracticeView.as_view(), name='submit-practice'),
]