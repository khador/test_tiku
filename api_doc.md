# 题库系统后台 API 文档 
## 0. 全局状态码规范 (HTTP Status Codes)
- **200 OK**: 请求成功。
- **400 Bad Request**: 参数错误或业务逻辑拒绝（如：重复交卷）。
- **401 Unauthorized**: 未提供 Token 或 Token 已过期。前端需清除本地 Token 并跳转至登录页。
- **403 Forbidden**: 角色权限不足（如：学生尝试访问教师接口）。前端需拦截并提示“越权访问”，跳回所属角色的首页，**无需清除 Token**。

## 1. 认证模块
- **登录**: `POST /api/login/` (返回 JWT Token，内嵌 role, real_name 等)
- **刷新**: `POST /api/token/refresh/`

## 2. 管理员模块 (仅限 Admin 访问)
所有接口需携带 Admin 级别的 Token。前缀均为 `/api/admin-manage/`。

### 2.1 教师管理
- **列表**: `GET /teachers/`
- **创建**: `POST /teachers/` (含 username, password, real_name, employee_id, phone)
- **更新**: `PATCH /teachers/{id}/`
- **删除**: `DELETE /teachers/{id}/`

### 2.2 学生管理
- **列表**: `GET /students/`
- **创建**: `POST /students/` (含 username, password, real_name, student_id, class_info)
- **更新**: `PATCH /students/{id}/`
- **删除**: `DELETE /students/{id}/`

### 2.3 班级管理
- **列表**: `GET /classes/`
- **创建**: `POST /classes/` (含 name, teacher ID)
- **删除**: `DELETE /classes/{id}/`

## 3. 教师模块 (仅限 Teacher 访问)
- **班级概览**: `GET /api/practices/teacher/dashboard/`
- **错题分析**: `GET /api/practices/teacher/questions-analysis/`
  - **说明**: 返回本班错误率 Top 10 的题目。
  - **响应优化**: 单条记录已包含 `stem_preview` (列表展示用) 以及 `stem_full`, `answer`, `analysis` (点击查看详情用)，前端**无需额外请求接口**即可展示完整解析。

## 4. 学生模块 (仅限 Student 访问)
- **获取练习**: `POST /api/practices/generate/` (下发题目已脱敏，绝对不含 answer)
- **提交练习**: `POST /api/practices/submit/` (提交判分并更新错题本)
- **练习历史**: `GET /api/practices/history/`
- **我的错题**: `GET /api/practices/error_book/`