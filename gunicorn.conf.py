# gunicorn.conf.py
import multiprocessing

# 服务器配置
bind = "0.0.0.0:8000"  # 🔥 关键：绑定到所有接口
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# 日志配置
loglevel = 'info'  # 日志级别: debug, info, warning, error, critical
accesslog = './logs/gunicorn_access.log'  # 访问日志
errorlog = './logs/gunicorn_error.log'    # 错误日志
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程管理
daemon = False  # 是否后台运行
pidfile = './logs/gunicorn.pid'  # PID 文件位置
preload_app = True

# 应用配置
max_requests = 1000
max_requests_jitter = 50

# 超时和缓冲
backlog = 2048
buffer_size = 8192
pythonpath = "/home/weiwei/python_projects/test_tiku"