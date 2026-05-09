"""
合并json文件
"""

import os
import json
import re

# 如果你的 python 脚本和 json 文件在同一个文件夹，保持 "./" 即可
# 如果不在同一个文件夹，请修改为实际路径，例如 "E:/your_json_folder/"
folder_path = "json\gemini_tiku_20260425"

def main():
    # 获取所有 json 文件
    all_files = [f for f in os.listdir(folder_path) if f.endswith('.json') and 'res' in f]

    # 分离 res1 和 res2 的文件
    res1_files = [f for f in all_files if 'res1' in f]
    res2_files = [f for f in all_files if 'res2' in f]

    # 自定义排序函数，提取文件名中的起始页码进行数字排序
    # 例如：从 "s1e6_res1.json" 中提取出数字 1
    def extract_start_page(filename):
        match = re.search(r's(\d+)e', filename)
        if match:
            return int(match.group(1))
        return 0

    # 按真实的页码顺序对文件列表进行排序
    res1_files.sort(key=extract_start_page)
    res2_files.sort(key=extract_start_page)

    print("正在合并 res1 (题目数据) ...")
    merged_res1 = []
    for file in res1_files:
        filepath = os.path.join(folder_path, file)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    merged_res1.extend(data)
                else:
                    print(f"⚠️ 警告: {file} 的格式不是列表，已跳过。")
            except Exception as e:
                print(f"❌ 读取 {file} 失败: {e}")

    # 写入合并后的 res1.json
    with open(os.path.join(folder_path, 'res1_final.json'), 'w', encoding='utf-8') as f:
        json.dump(merged_res1, f, ensure_ascii=False, indent=2)
    print(f"✅ 成功合并 {len(res1_files)} 个文件到 res1_final.json，共包含 {len(merged_res1)} 道题！\n")

    print("正在合并 res2 (配图与错误元数据) ...")
    merged_res2 = {
        "errors": [],
        "images": []
    }
    for file in res2_files:
        filepath = os.path.join(folder_path, file)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    merged_res2["errors"].extend(data.get("errors", []))
                    merged_res2["images"].extend(data.get("images", []))
                else:
                    print(f"⚠️ 警告: {file} 的格式不是字典，已跳过。")
            except Exception as e:
                print(f"❌ 读取 {file} 失败: {e}")

    # 写入合并后的 res2.json
    with open(os.path.join(folder_path, 'res2_final.json'), 'w', encoding='utf-8') as f:
        json.dump(merged_res2, f, ensure_ascii=False, indent=2)
    
    total_errors = len(merged_res2['errors'])
    total_images = len(merged_res2['images'])
    print(f"✅ 成功合并 {len(res2_files)} 个文件到 res2_final.json，共收集到 {total_images} 张切图坐标，丢弃了 {total_errors} 道题！")

if __name__ == "__main__":
    main()