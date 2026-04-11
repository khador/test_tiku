# users/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, ClassInfo

# 班级序列化器
class ClassInfoSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.real_name', read_only=True)
    student_count = serializers.IntegerField(source='students.count', read_only=True)

    class Meta:
        model = ClassInfo
        fields = ['id', 'name', 'teacher', 'teacher_name', 'student_count']

# 管理员使用的教师序列化器
class TeacherManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'real_name', 'employee_id', 'phone', 'is_active']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['role'] = 'teacher'
        validated_data['is_staff'] = True
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

# 管理员使用的学生序列化器
class StudentManagementSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='class_info.name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'real_name', 'student_id', 'class_info', 'class_name', 'is_active']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['role'] = 'student'
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # 获取系统生成的标准 token
        token = super().get_token(user)

        # === 在这里添加我们自定义的字段 ===
        token['username'] = user.username
        token['role'] = user.role
        token['real_name'] = user.real_name
        
        # 根据角色带上特有字段
        if user.role == 'student' and user.student_id:
            token['student_id'] = user.student_id
            # 如果有班级，也可以把班级名字带上
            if user.class_info:
                token['class_name'] = user.class_info.name
                
        elif user.role == 'teacher' and user.employee_id:
            token['employee_id'] = user.employee_id

        return token