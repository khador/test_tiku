# questions/models.py
from django.db import models

class Question(models.Model):
    """题库核心表"""
    TYPE_CHOICES = (
        ('choice', '选择题'),
        ('fill', '填空/解答题'),
        ('judge', '判断题'),
        ('draw', '画图题'),
    )
    sn = models.CharField(max_length=20, unique=True, verbose_name="题号", null=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="题型")
    stem = models.TextField(verbose_name="题干(支持富文本)")
    options = models.JSONField(null=True, blank=True, verbose_name="选项(JSON)")
    answer = models.JSONField(verbose_name="标准答案与规则(JSON)")
    analysis = models.TextField(blank=True, verbose_name="解析")
    difficulty = models.IntegerField(default=1, verbose_name="难度(1-5)")
    knowledge_points = models.JSONField(null=True, blank=True, verbose_name="知识点集合(JSON)")

    class Meta:
        verbose_name = "试题"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"[{self.get_type_display()}] ID:{self.id}"