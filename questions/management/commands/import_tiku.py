import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from questions.models import Question

class Command(BaseCommand):
    help = '从 JSON 文件导入题库数据'

    def handle(self, *args, **kwargs):
        # 假设你把 JSON 文件改名为 tiku_data.json 并放在项目根目录
        print(settings.BASE_DIR)
        file_path = os.path.join(settings.BASE_DIR, 'test_tiku_20260409.json')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'找不到文件: {file_path}'))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        for item in data:
            # 使用 update_or_create 防止重复导入报错
            Question.objects.update_or_create(
                sn=item['id'], 
                defaults={
                    'type': item['type'],
                    'stem': item['stem'],
                    'options': item['options'],
                    'answer': item['answer'],
                    'analysis': item['analysis'],
                    'difficulty': item['difficulty'],
                    'knowledge_points': item['knowledge_points']
                }
            )
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'成功导入了 {count} 道题目！去 Admin 后台看看吧！'))