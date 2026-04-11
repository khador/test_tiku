# practices/views.py
import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Exists, OuterRef
from django.utils import timezone
from .models import PracticeSession, ErrorBook, QuestionAttempt
from questions.models import Question
from questions.serializers import QuestionSerializer
from django.db.models import Avg, Sum, Count, Q
from users.models import ClassInfo, User

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




class SubmitPracticeView(APIView):
    """
    提交练习，自动判分并更新错题本
    """
    def post(self, request):
        student = request.user
        if student.role != 'student':
            return Response({"detail": "只有学生可以提交练习"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        session_id = data.get('session_id')
        answers_data = data.get('answers', []) # 前端传来的答案数组
        total_duration = data.get('duration', 0) # 前端统计的总用时

        try:
            session = PracticeSession.objects.get(id=session_id, student=student)
        except PracticeSession.DoesNotExist:
            return Response({"detail": "练习场次不存在或无权访问"}, status=status.HTTP_404_NOT_FOUND)

        if session.end_time is not None:
            return Response({"detail": "该练习已提交过，不能重复提交"}, status=status.HTTP_400_BAD_REQUEST)

        correct_count = 0
        total_count = len(answers_data)
        results = []

        # 遍历学生的每一道题的答案
        for ans_item in answers_data:
            q_id = ans_item.get('question_id')
            user_answer = ans_item.get('user_answer')
            time_spent = ans_item.get('time_spent', 0)

            try:
                question = Question.objects.get(id=q_id)
            except Question.DoesNotExist:
                continue 

            # 调用我们写的核心判分函数
            is_correct = self.check_answer(question.type, user_answer, question.answer)

            if is_correct:
                correct_count += 1

            # 1. 记录单题的答题明细
            QuestionAttempt.objects.create(
                session=session,
                question=question,
                user_answer=user_answer,
                is_correct=is_correct,
                time_spent=time_spent
            )

            # 2. 错题本智能逻辑
            # get_or_create 会查找错题记录，如果没有就新建一条默认 is_active=False 的记录
            error_record, created = ErrorBook.objects.get_or_create(
                student=student,
                question=question,
                defaults={'is_active': False, 'consecutive_correct': 0}
            )

            if not is_correct:
                # 答错了：激活错题本状态，连续正确次数清零
                error_record.is_active = True
                error_record.consecutive_correct = 0
                error_record.save()
            else:
                # 答对了：检查是否在活跃的错题本中
                if error_record.is_active:
                    error_record.consecutive_correct += 1
                    if error_record.consecutive_correct >= 2:
                        error_record.is_active = False # 连续做对两次，光荣移出错题本！
                    error_record.save()

            # 将这道题的结果放入返回列表（给前端展示解析用）
            results.append({
                "question_id": q_id,
                "is_correct": is_correct,
                "standard_answer": question.answer,
                "analysis": question.analysis
            })

        # 3. 更新总练习场次的数据
        session.end_time = timezone.now()
        if not total_duration:
            session.duration = (session.end_time - session.start_time).total_seconds()
        else:
            session.duration = total_duration
            
        session.accuracy = (correct_count / total_count) if total_count > 0 else 0
        session.save()

        # 返回最终成绩单给前端
        return Response({
            "session_id": session.id,
            "accuracy": session.accuracy,
            "correct_count": correct_count,
            "total_count": total_count,
            "details": results
        }, status=status.HTTP_200_OK)

    def check_answer(self, q_type, user_answer, std_answer):
        """
        核心辅助函数：判断前端传来的答案是否匹配数据库的标准 JSON 规则
        """
        if not user_answer:
            return False

        if q_type in ['choice', 'judge']:
            # 选择题判断：例如 {"correct_options": ["A", "C"]}
            user_opts = set(user_answer.get('correct_options', []))
            std_opts = set(std_answer.get('correct_options', []))
            return user_opts == std_opts

        elif q_type == 'fill':
            # 填空题复杂判断
            is_ordered = std_answer.get('is_ordered', True)
            std_blanks = std_answer.get('blanks', [])
            # 假设前端传回的格式是一个简单的数组 ["3分米", "5米"]
            user_blanks = user_answer.get('blanks', []) 

            if len(std_blanks) != len(user_blanks):
                return False

            if is_ordered:
                # 1. 顺序相关：一一对应比对
                for i in range(len(std_blanks)):
                    u_val = str(user_blanks[i]).strip()
                    accepted = [str(v).strip() for v in std_blanks[i].get('accepted_values', [])]
                    if u_val not in accepted:
                        return False
                return True
            else:
                # 2. 顺序无关：只要用户填的值都在 accepted_values 里，且不重复即可
                matched_std_indices = set()
                for u_val in user_blanks:
                    u_val = str(u_val).strip()
                    match_found = False
                    for i, std_b in enumerate(std_blanks):
                        if i in matched_std_indices: 
                            continue # 这个标准空位已经被匹配过了
                        accepted = [str(v).strip() for v in std_b.get('accepted_values', [])]
                        if u_val in accepted:
                            matched_std_indices.add(i)
                            match_found = True
                            break
                    if not match_found:
                        return False # 填了一个完全不在备选答案里的词
                return len(matched_std_indices) == len(std_blanks)

        elif q_type == 'draw':
            # 画图题前端通常暂不自动判分，这里默认当做让老师人工批改或跳过
            return True 
            
        return False
    




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