import os
import json
from PIL import Image

def extract_images_from_json(json_path, basedir, tar_dir):
    """
    根据结果2的JSON截取配图并保存
    
    参数:
    json_path (str): 结果2的JSON文件路径
    basedir (str): 原始图片所在目录（如 "/scans"）
    tar_dir (str): 配图输出目录（如 "/extracted_images"）
    """
    # 创建输出目录
    os.makedirs(tar_dir, exist_ok=True)
    
    # 读取JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 处理每个配图
    for img_info in data.get("images", []):
        # 获取文件名和坐标
        img_filename = img_info["img_filename"]  # 如 p41_q2_optA.png
        parent_img = img_info["parent_img_filename"]  # 如 scan_41.jpg
        coords = img_info["cordinate"]  # [x1, y1, x2, y2]
        
        # 构建原始图片路径
        parent_path = os.path.join(basedir, parent_img)
        if not os.path.exists(parent_path):
            print(f"警告: 原始图片不存在 {parent_path}")
            continue
        
        # 验证坐标有效性
        if len(coords) != 4 or any(c < 0 for c in coords):
            print(f"警告: 无效坐标 {coords} for {img_filename}")
            continue
        
        x1, y1, x2, y2 = coords
        if x1 >= x2 or y1 >= y2:
            print(f"警告: 坐标顺序错误 {coords} for {img_filename}")
            continue
        
        # 打开原始图片并截取
        try:
            with Image.open(parent_path) as img:
                # 确保坐标在图片范围内
                img_w, img_h = img.size
                x1 = max(0, min(x1, img_w))
                y1 = max(0, min(y1, img_h))
                x2 = max(0, min(x2, img_w))
                y2 = max(0, min(y2, img_h))
                
                cropped = img.crop((x1, y1, x2, y2))
                
                # 保存配图
                output_path = os.path.join(tar_dir, img_filename)
                cropped.save(output_path, "PNG")
                print(f"已保存: {output_path}")
                
        except Exception as e:
            print(f"错误: 截取失败 {img_filename} - {str(e)}")

# 使用示例
if __name__ == "__main__":
    # 配置参数
    JSON_PATH = "result2.json"      # 结果2的JSON文件路径
    BASE_DIR = "/path/to/scans"     # 原始扫描图片目录
    TAR_DIR = "/path/to/extracted"  # 配图输出目录
    
    # 执行截取
    extract_images_from_json(JSON_PATH, BASE_DIR, TAR_DIR)