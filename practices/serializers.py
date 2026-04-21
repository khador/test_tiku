# practices/serializers.py
from rest_framework import serializers
from .models import PracticeSession, QuestionAttempt, ErrorBook
from questions.models import Question 

# 1. 题目的只读序列化器
class QuestionPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'sn', 'type', 'stem', 'options', 'answer', 'analysis']

# 2. 错题本序列化器
class ErrorBookSerializer(serializers.ModelSerializer):
    # 强制嵌套完整的题目对象
    question = QuestionPublicSerializer(read_only=True)
    # 动态计算该学生在这道题上累计答错的次数
    error_count = serializers.SerializerMethodField()

    class Meta:
        model = ErrorBook
        fields = ['id', 'question', 'error_count', 'consecutive_correct', 'add_time']

    def get_error_count(self, obj):
        # 统计该学生这道题答错的总次数
        return QuestionAttempt.objects.filter(
            session__student=obj.student,
            question=obj.question,
            is_correct=False
        ).count()

# === 交卷相关序列化器（保持不动） ===
class PracticeSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeSession
        fields = '__all__'

class AnswerItemSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=True)
    user_answer = serializers.JSONField(required=True)
    time_spent = serializers.IntegerField(default=0)

class SubmitPracticeSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(required=True)
    duration = serializers.IntegerField(default=0)
    answers = AnswerItemSerializer(many=True, required=True, allow_empty=False)