# practices/serializers.py
from rest_framework import serializers
from .models import PracticeSession, QuestionAttempt

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