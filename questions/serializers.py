# questions/serializers.py
from rest_framework import serializers
from .models import Question

class QuestionPublicSerializer(serializers.ModelSerializer):
    """供学生做题时使用的序列化器（脱敏，无答案和解析）"""
    class Meta:
        model = Question
        # 明确排除敏感字段
        exclude = ('answer', 'analysis', 'knowledge_points')

class QuestionDetailSerializer(serializers.ModelSerializer):
    """包含所有完整信息的序列化器（交卷后展示、教师查看）"""
    class Meta:
        model = Question
        fields = '__all__'