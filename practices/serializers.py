# practices/serializers.py
from rest_framework import serializers
from .models import PracticeSession, QuestionAttempt

class PracticeSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeSession
        fields = '__all__'