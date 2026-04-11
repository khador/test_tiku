# practices/models.py
from django.db import models
from users.models import User
from questions.models import Question

class PracticeSession(models.Model):
    """一次完整的练习场次（例如10道题）"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='practice_sessions', verbose_name="学生")
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="开始时间")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="交卷时间")
    duration = models.IntegerField(null=True, blank=True, verbose_name="总用时(秒)")
    accuracy = models.FloatField(null=True, blank=True, verbose_name="正确率")

    class Meta:
        verbose_name = "练习场次"
        verbose_name_plural = verbose_name

class QuestionAttempt(models.Model):
    """单道题的答题明细"""
    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, related_name='attempts')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user_answer = models.JSONField(verbose_name="学生提交的答案")
    is_correct = models.BooleanField(verbose_name="是否正确")
    time_spent = models.IntegerField(default=0, verbose_name="该题用时(秒)") # 扩展功能，记录单题用时

class ErrorBook(models.Model):
    """错题本"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='error_book')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    consecutive_correct = models.IntegerField(default=0, verbose_name="连续答对次数")
    is_active = models.BooleanField(default=True, verbose_name="是否仍在错题本中")
    add_time = models.DateTimeField(auto_now_add=True, verbose_name="首次做错时间")
    last_practiced = models.DateTimeField(auto_now=True, verbose_name="最后一次练习时间")
    is_active = models.BooleanField(default=True, verbose_name="是否仍在错题本中")

    class Meta:
        verbose_name = "错题本"
        verbose_name_plural = verbose_name
        # 添加联合索引：优化 "查找某学生活跃错题" 的查询速度
        indexes = [
            models.Index(fields=['student', 'is_active']),
        ]