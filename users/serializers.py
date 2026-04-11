# users/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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