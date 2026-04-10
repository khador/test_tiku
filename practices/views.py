# practices/views.py
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Exists, OuterRef

from .models import PracticeSession, ErrorBook, QuestionAttempt
from questions.models import Question
from questions.serializers import QuestionSerializer

class GeneratePracticeView(APIView):
    """
    生成一次 10 道题的练习：包含错题复习和新题
    """
    def post(self, request):
        student = request.user
        if student.role != 'student':
            return Response({"detail": "只有学生可以生成练习"}, status=status.HTTP_403_FORBIDDEN)

        # 1. 抽取错题 (最多抽取 4 道尚未掌握的活跃错题)
        error_questions_ids = list(
            ErrorBook.objects.filter(student=student, is_active=True)
            .order_by('last_practiced') # 优先复习很久没做的
            .values_list('question_id', flat=True)[:4]
        )

        # 2. 抽取新题 (排除已经做过的题，补齐到 10 道)
        needed_new_count = 10 - len(error_questions_ids)
        
        # 找出该学生已经做过的题目 ID 列表
        attempted_ids = QuestionAttempt.objects.filter(
            session__student=student
        ).values_list('question_id', flat=True)

        # 找出没做过的新题
        new_questions_ids = list(
            Question.objects.exclude(id__in=attempted_ids)
            .values_list('id', flat=True)
        )
        # 随机抽取需要的新题数量 (如果题库不够了，就全拿出来)
        selected_new_ids = random.sample(new_questions_ids, min(len(new_questions_ids), needed_new_count))

        # 3. 合并题目并打乱顺序
        final_question_ids = error_questions_ids + selected_new_ids
        random.shuffle(final_question_ids)

        if not final_question_ids:
            return Response({"detail": "题库中没有可用的题目了"}, status=status.HTTP_404_NOT_FOUND)

        # 获取具体的题目对象并序列化
        questions = Question.objects.filter(id__in=final_question_ids)
        # 为了保持刚刚打乱的顺序，我们需要在内存中排序
        questions_dict = {q.id: q for q in questions}
        sorted_questions = [questions_dict[q_id] for q_id in final_question_ids]

        serializer = QuestionSerializer(sorted_questions, many=True)

        # 4. 在数据库中创建一次练习场次 (PracticeSession)
        session = PracticeSession.objects.create(student=student)

        # 返回生成的场次 ID 和 题目列表给前端
        return Response({
            "session_id": session.id,
            "questions": serializer.data
        }, status=status.HTTP_200_OK)