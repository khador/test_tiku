# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
timeout = 30
preload_app = True
pythonpath = "/home/weiwei/python_projects/test_tiku"