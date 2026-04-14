# practices/views.py
import re  # 引入正则库，用来处理复杂的符号分割
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Exists, OuterRef
from django.utils import timezone
from .models import PracticeSession, ErrorBook, QuestionAttempt
from questions.models import Question
from django.db.models import Avg, Sum, Count, Q
from users.models import ClassInfo, User
from django.db.models import Count, Avg, Q
from users.models import ClassInfo, User
from django.db.models import Case, When
from django.db import transaction
from .serializers import SubmitPracticeSerializer
from questions.serializers import QuestionPublicSerializer, QuestionDetailSerializer






class PracticeHistoryView(APIView):
    """
    学生查询自己的历史训练记录
    """
    def get(self, request):
        student = request.user
        if student.role != 'student':
            return Response({"detail": "只有学生可以查询训练记录"}, status=status.HTTP_403_FORBIDDEN)

        # 查询该学生所有已经交卷的练习场次，按时间倒序排列（最新的在最上面）
        sessions = PracticeSession.objects.filter(
            student=student, 
            end_time__isnull=False
        ).order_by('-start_time')
        
        history_data = []
        for s in sessions:
            # 统计这套题的对错数量
            correct_count = s.attempts.filter(is_correct=True).count()
            total_count = s.attempts.count()
            
            history_data.append({
                "session_id": s.id,
                "start_time": s.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": s.duration, # 用时（秒）
                "accuracy": round(s.accuracy * 100, 1) if s.accuracy is not None else 0, # 转为百分比
                "correct_count": correct_count,
                "total_count": total_count
            })
            
        return Response(history_data, status=status.HTTP_200_OK)


class ErrorBookListView(APIView):
    """
    学生查看自己当前的错题本
    """
    def get(self, request):
        student = request.user
        if student.role != 'student':
            return Response({"detail": "只有学生可以查看错题本"}, status=status.HTTP_403_FORBIDDEN)

        # 只查询还没被踢出错题本的题（is_active=True）
        error_records = ErrorBook.objects.filter(
            student=student, 
            is_active=True
        ).order_by('-add_time')
        
        error_data = []
        for record in error_records:
            q = record.question
            error_data.append({
                "question_id": q.id,
                "sn": q.sn,
                "stem": q.stem,
                "type": q.type,
                "consecutive_correct": record.consecutive_correct, # 连续做对的次数（还差几次能移出）
                "add_time": record.add_time.strftime("%Y-%m-%d")
            })
            
        return Response(error_data, status=status.HTTP_200_OK)





# ================= 教师端 API =================

class TeacherClassListView(APIView):
    """
    1. 教师获取自己所教的班级列表
    """
    def get(self, request):
        teacher = request.user
        if teacher.role != 'teacher':
            return Response({"detail": "无权限"}, status=status.HTTP_403_FORBIDDEN)
            
        classes = ClassInfo.objects.filter(teacher=teacher)
        data = [{"class_id": c.id, "class_name": c.name} for c in classes]
        return Response(data, status=status.HTTP_200_OK)


class TeacherClassDashboardView(APIView):
    """
    2. 教师查看某班级的整体学情，以及该班级下所有学生的统计
    """
    def get(self, request, class_id):
        teacher = request.user
        if teacher.role != 'teacher':
            return Response(status=status.HTTP_403_FORBIDDEN)
            
        try:
            class_info = ClassInfo.objects.get(id=class_id, teacher=teacher)
        except ClassInfo.DoesNotExist:
            return Response({"detail": "班级不存在或您不负责该班级"}, status=status.HTTP_404_NOT_FOUND)

        # 获取该班级所有学生已经提交的练习场次
        class_sessions = PracticeSession.objects.filter(
            student__student_profile__class_info=class_info,
            end_time__isnull=False
        )
        
        # 班级整体平均正确率
        avg_accuracy = class_sessions.aggregate(Avg('accuracy'))['accuracy__avg'] or 0

        # 获取该班级的学生列表，并统计每个人
        students = User.objects.filter(student_profile__class_info=class_info)
        student_data = []
        for st in students:
            st_sessions = class_sessions.filter(student=st)
            st_avg_acc = st_sessions.aggregate(Avg('accuracy'))['accuracy__avg'] or 0
            st_total_duration = st_sessions.aggregate(Sum('duration'))['duration__sum'] or 0
            
            student_data.append({
                "student_id": st.id,
                "real_name": st.real_name or st.username,
                "school_sn": st.student_profile.student_id, # 学号
                "completed_sessions": st_sessions.count(),
                "avg_accuracy": round(st_avg_acc * 100, 1),
                "total_duration": st_total_duration # 总用时(秒)
            })

        return Response({
            "class_name": class_info.name,
            "overall_accuracy": round(avg_accuracy * 100, 1),
            "total_sessions": class_sessions.count(),
            "students": student_data
        }, status=status.HTTP_200_OK)


class TeacherStudentHistoryView(APIView):
    """
    3. 教师查看某个具体学生的详细做题历史
    """
    def get(self, request, student_id):
        if request.user.role != 'teacher':
            return Response(status=status.HTTP_403_FORBIDDEN)
            
        # 确保这个学生是该老师教的
        is_my_student = User.objects.filter(
            id=student_id, 
            student_profile__class_info__teacher=request.user
        ).exists()
        
        if not is_my_student:
            return Response({"detail": "只能查看自己班级学生的记录"}, status=status.HTTP_403_FORBIDDEN)
            
        sessions = PracticeSession.objects.filter(
            student_id=student_id, 
            end_time__isnull=False
        ).order_by('-start_time')
        
        history_data = []
        for s in sessions:
            history_data.append({
                "session_id": s.id,
                "start_time": s.start_time.strftime("%Y-%m-%d %H:%M"),
                "duration": s.duration,
                "accuracy": round(s.accuracy * 100, 1) if s.accuracy else 0,
            })
        return Response(history_data, status=status.HTTP_200_OK)


class TeacherQuestionStatsView(APIView):
    """
    4. 教师查看某班级内，各个题目的正确率排行（重点抓错题）
    """
    def get(self, request, class_id):
        if request.user.role != 'teacher':
            return Response(status=status.HTTP_403_FORBIDDEN)
            
        # 检查权限
        if not ClassInfo.objects.filter(id=class_id, teacher=request.user).exists():
            return Response({"detail": "无权限"}, status=status.HTTP_403_FORBIDDEN)

        # 核心魔法：使用 annotate 对该班级做过的所有题目进行分组统计
        attempts = QuestionAttempt.objects.filter(
            session__student__student_profile__class_info_id=class_id
        )
        
        # 按照题目ID分组，统计总尝试次数 和 做对的次数
        stats = attempts.values('question__id', 'question__sn', 'question__stem', 'question__type').annotate(
            total_attempts=Count('id'),
            correct_attempts=Count('id', filter=Q(is_correct=True))
        )

        data = []
        for stat in stats:
            total = stat['total_attempts']
            correct = stat['correct_attempts']
            acc = (correct / total) if total > 0 else 0
            
            data.append({
                "question_id": stat['question__id'],
                "sn": stat['question__sn'],
                "type": stat['question__type'],
                "stem_preview": stat['question__stem'][:50] + "...", # 截取前50个字符作为预览
                "total_attempts": total,
                "accuracy": round(acc * 100, 1)
            })
            
        # 按照正确率从低到高排序（把学生错得最多的题放在最前面）
        data.sort(key=lambda x: x['accuracy'])
        
        return Response(data, status=status.HTTP_200_OK)
    



class TeacherDashboardView(APIView):
    """
    教师端 API 1：班级概览与学生学情统计
    """
    def get(self, request):
        teacher = request.user
        if teacher.role != 'teacher':
            return Response({"detail": "无权限，仅限教师访问"}, status=status.HTTP_403_FORBIDDEN)

        # 1. 统计该老师负责的班级及每个班的人数
        classes = ClassInfo.objects.filter(teacher=teacher).annotate(
            student_count=Count('students')
        )
        class_data = [{"id": c.id, "name": c.name, "student_count": c.student_count} for c in classes]

        # 2. 统计该老师名下所有学生的学习进度
        # 使用 annotate 批量计算每个学生的总练习场次和平均正确率
        students = User.objects.filter(
            role='student', 
            class_info__teacher=teacher
        ).annotate(
            total_sessions=Count('practice_sessions'),
            avg_accuracy=Avg('practice_sessions__accuracy')
        )

        student_data = []
        for s in students:
            student_data.append({
                "student_id": s.student_id,
                "real_name": s.real_name if s.real_name else s.username,
                "class_name": s.class_info.name if s.class_info else "未分配",
                "total_sessions": s.total_sessions,
                # 如果做过题则保留1位小数转百分比，否则为 0
                "avg_accuracy": round(s.avg_accuracy * 100, 1) if s.avg_accuracy else 0 
            })

        return Response({
            "classes": class_data,
            "students_performance": student_data
        }, status=status.HTTP_200_OK)


class TeacherQuestionAnalysisView(APIView):
    """
    教师端 API 2：高频错题排行榜（薄弱知识点分析）
    """
    def get(self, request):
        teacher = request.user
        if teacher.role != 'teacher':
            return Response({"detail": "无权限，仅限教师访问"}, status=status.HTTP_403_FORBIDDEN)

        # 【修改点】：在 values 里把 full stem, answer, analysis 都查出来
        attempts = QuestionAttempt.objects.filter(
            session__student__class_info__teacher=teacher
        ).values(
            'question__id', 'question__sn', 'question__stem', 'question__type',
            'question__answer', 'question__analysis' # 新增
        ).annotate(
            total_attempts=Count('id'),
            correct_attempts=Count('id', filter=Q(is_correct=True)) 
        )

        results = []
        for att in attempts:
            total = att['total_attempts']
            correct = att['correct_attempts']
            error_rate = ((total - correct) / total * 100) if total > 0 else 0

            # 题干太长的话，依然提供一个 preview 给前端列表用
            stem_full = att['question__stem']
            stem_preview = stem_full[:30] + "..." if len(stem_full) > 30 else stem_full

            results.append({
                "question_id": att['question__id'],
                "sn": att['question__sn'],
                "type": att['question__type'],
                "stem_preview": stem_preview,
                "stem_full": stem_full,          # 【新增】：完整题干
                "answer": att['question__answer'], # 【新增】：标准答案
                "analysis": att['question__analysis'], # 【新增】：解析
                "total_attempts": total,
                "error_rate": round(error_rate, 1) 
            })

        results = sorted(results, key=lambda x: x['error_rate'], reverse=True)[:10]
        return Response(results, status=status.HTTP_200_OK)


class GeneratePracticeView(APIView):
    def post(self, request):
        # 1. 从题库中获取所有题目，但【排除】画图题 (type='draw')
        all_q_ids = list(Question.objects.exclude(type='draw').values_list('id', flat=True))
        
        # 如果题库是空的，直接返回错误提示
        if not all_q_ids:
            return Response({"detail": "题库中没有题目，请先导入题库"}, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. 随机抽取 10 道题（如果题库不足 10 道，则全部抽出）
        sample_size = min(10, len(all_q_ids))
        final_question_ids = random.sample(all_q_ids, sample_size)

        # 3. 使用 Case When 在数据库层面保持打乱后的顺序
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(final_question_ids)])
        questions = Question.objects.filter(id__in=final_question_ids).order_by(preserved)

        # 4. 使用无答案的脱敏序列化器（防止学生提前看到答案）
        serializer = QuestionPublicSerializer(questions, many=True)

        # 5. 在数据库创建一条新的练习场次记录
        session = PracticeSession.objects.create(student=request.user)
        
        return Response({"session_id": session.id, "questions": serializer.data}, status=status.HTTP_200_OK)

class SubmitPracticeView(APIView):
    
    def check_answer(self, q_type, user_answer, standard_answer):
        if not user_answer:
            return False
            
        # 1. 选择题和判断题的判分逻辑
        if q_type in ['choice', 'judge']:
            correct_options = standard_answer.get('correct_options', [])
            return str(user_answer).strip() in [str(ans) for ans in correct_options]
            
        # 2. 填空题的判分逻辑（支持中英文逗号、空格混输）
        elif q_type == 'fill':
            # 使用正则：将中英文逗号、以及各种空格统一作为分隔符切块
            # 例如 "反比例， 30" -> ['反比例', '30']
            user_ans_list = re.split(r'[,\s，]+', str(user_answer).strip())
            user_ans_list = [ans for ans in user_ans_list if ans] # 过滤掉空字符串
            
            blanks = standard_answer.get('blanks', [])
            if not blanks:
                return False
                
            is_ordered = standard_answer.get('is_ordered', True)
            
            # 情况 A：有顺序要求（例如：填空1，填空2）
            if is_ordered:
                if len(user_ans_list) != len(blanks):
                    return False
                for i, blank in enumerate(blanks):
                    accepted = blank.get('accepted_values', [])
                    if user_ans_list[i] not in accepted:
                        return False
                return True
                
            # 情况 B：无顺序要求（比如写出任意两个比例）
            else:
                if len(user_ans_list) != len(blanks):
                    return False
                # 复制一份以防同一个答案被重复匹配
                matched_blanks = []
                for u_ans in user_ans_list:
                    matched = False
                    for i, blank in enumerate(blanks):
                        if i in matched_blanks:
                            continue
                        if u_ans in blank.get('accepted_values', []):
                            matched_blanks.append(i)
                            matched = True
                            break
                    if not matched:
                        return False
                return True
                
        return False
    
    def post(self, request):
        student = request.user
        
        # [优化点5]：使用序列化器严格校验前端传来的格式
        val_serializer = SubmitPracticeSerializer(data=request.data)
        val_serializer.is_valid(raise_exception=True)
        data = val_serializer.validated_data
        
        session_id = data['session_id']
        answers_data = data['answers']

        try:
            session = PracticeSession.objects.get(id=session_id, student=student)
        except PracticeSession.DoesNotExist:
            return Response({"detail": "练习场次不存在"}, status=status.HTTP_404_NOT_FOUND)

        if session.end_time:
            return Response({"detail": "已提交，不能重复提交"}, status=status.HTTP_400_BAD_REQUEST)

        # 提取所有的题号，一次性查询数据库，减少 I/O
        q_ids = [item['question_id'] for item in answers_data]
        question_objs = {q.id: q for q in Question.objects.filter(id__in=q_ids)}

        correct_count = 0
        attempts_to_create = []
        results = []

        # [优化点4]：使用事务，确保如果发生异常，数据不会只写一半
        with transaction.atomic():
            for ans_item in answers_data:
                q_id = ans_item['question_id']
                if q_id not in question_objs:
                    # 发现脏数据直接打断，拒绝提交
                    return Response({"detail": f"题目 ID {q_id} 不存在于题库中"}, status=status.HTTP_400_BAD_REQUEST)
                
                question = question_objs[q_id]
                user_answer = ans_item['user_answer']
                is_correct = self.check_answer(question.type, user_answer, question.answer)

                if is_correct: correct_count += 1

                # [优化点1]：加入待创建列表，而不是直接保存
                attempts_to_create.append(QuestionAttempt(
                    session=session,
                    question=question,
                    user_answer=user_answer,
                    is_correct=is_correct,
                    time_spent=ans_item['time_spent']
                ))

                # 错题本逻辑 (业务复杂，依然保留循环查询和更新)
                error_record, _ = ErrorBook.objects.get_or_create(
                    student=student, question=question, defaults={'is_active': False, 'consecutive_correct': 0}
                )
                if not is_correct:
                    error_record.is_active = True
                    error_record.consecutive_correct = 0
                else:
                    if error_record.is_active:
                        error_record.consecutive_correct += 1
                        if error_record.consecutive_correct >= 2:
                            error_record.is_active = False
                error_record.save()

                results.append({
                    "question": QuestionDetailSerializer(question).data, # 返回带答案的完整题目信息供查看
                    "user_answer": user_answer,
                    "is_correct": is_correct
                })

            # [优化点1]：批量插入答题明细
            QuestionAttempt.objects.bulk_create(attempts_to_create)

            session.end_time = timezone.now()
            session.duration = data['duration'] or (session.end_time - session.start_time).total_seconds()
            session.accuracy = (correct_count / len(answers_data)) if answers_data else 0
            session.save()

        return Response({
            "session_id": session.id,
            "accuracy": session.accuracy,
            "correct_count": correct_count,
            "total_count": len(answers_data),
            "details": results
        }, status=status.HTTP_200_OK)