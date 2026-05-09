import json
import os
import re

def process_json_files(res1_path, res2_path, subject_dir, book_id, output_dir):
    """
    处理题库 JSON，更新 ID 和 图片路径
    :param res1_path: 原始结果1 JSON 路径
    :param res2_path: 原始结果2 JSON 路径
    :param subject_dir: 学科分类 (如 'MAT')
    :param book_id: 书籍编号 (如 'MAT-G6B-WB')
    :param output_dir: 输出目录
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 替换 img src 的内部函数
    def replace_img_src(match):
        filename = match.group(1)
        # 防止重复添加前缀
        if not filename.startswith(f"{book_id}_"):
            filename = f"{book_id}_{filename}"
        return f'<img src="/images/workbook/{subject_dir}/{book_id}/{filename}" />'

    # ==========================================
    # 处理 Res1 (题目数据)
    # ==========================================
    if os.path.exists(res1_path):
        print(f"正在处理 {res1_path} ...")
        with open(res1_path, 'r', encoding='utf-8') as f:
            res1_data = json.load(f)

        for q in res1_data:
            # 1. 修改 ID (例如: "44-1" -> "MAT-G6B-WB-44-1")
            if "id" in q and not q["id"].startswith(f"{book_id}-"):
                q["id"] = f"{book_id}-{q['id']}"

            # 2. 修改 stem 中的图片路径
            if "stem" in q and q["stem"]:
                # 匹配原本的 <img src="/images/workbook/文件名.png" />
                q["stem"] = re.sub(
                    r'<img[^>]*src=["\']/images/workbook/([^"\'/]+)["\'][^>]*>', 
                    replace_img_src, 
                    q["stem"]
                )

            # 3. 修改 options 中的图片标签和路径
            if "options" in q and isinstance(q["options"], list):
                for opt in q["options"]:
                    img_val = opt.get("img")
                    if img_val and isinstance(img_val, str) and img_val.strip() != "":
                        # 如果已经是 img 标签，走正则替换路径
                        if "<img" in img_val:
                            opt["img"] = re.sub(
                                r'<img[^>]*src=["\']/images/workbook/([^"\'/]+)["\'][^>]*>', 
                                replace_img_src, 
                                img_val
                            )
                        # 如果只是光秃秃的文件名，直接组装成带学科/书本隔离目录的标准标签
                        else:
                            filename = img_val.strip()
                            if not filename.startswith(f"{book_id}_"):
                                filename = f"{book_id}_{filename}"
                            opt["img"] = f'<img src="/images/workbook/{subject_dir}/{book_id}/{filename}" />'

        # 保存处理后的 Res1
        res1_out = os.path.join(output_dir, f"formatted_res1.json")
        with open(res1_out, 'w', encoding='utf-8') as f:
            json.dump(res1_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Res1 处理完成，已保存至: {res1_out}")
    else:
        print(f"❌ 找不到 Res1 文件: {res1_path}")


    # ==========================================
    # 处理 Res2 (配图与错误元数据)
    # ==========================================
    if os.path.exists(res2_path):
        print(f"正在处理 {res2_path} ...")
        with open(res2_path, 'r', encoding='utf-8') as f:
            res2_data = json.load(f)

        # 修改 images 列表中的切图文件名
        if "images" in res2_data and isinstance(res2_data["images"], list):
            for img_meta in res2_data["images"]:
                old_filename = img_meta.get("img_filename", "")
                if old_filename and not old_filename.startswith(f"{book_id}_"):
                    # 为需要切图的记录更新前缀
                    img_meta["img_filename"] = f"{book_id}_{old_filename}"

        # 保存处理后的 Res2
        res2_out = os.path.join(output_dir, f"formatted_res2.json")
        with open(res2_out, 'w', encoding='utf-8') as f:
            json.dump(res2_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Res2 处理完成，已保存至: {res2_out}")
    else:
        print(f"❌ 找不到 Res2 文件: {res2_path}")


if __name__ == "__main__":
    # ================= 配置区 =================
    # 在这里填入你的参数
    SUBJECT_DIR = "MAT"                    # 学科目录，如 MAT, ENG, SCI
    BOOK_ID = "MAT-G6B-OP"                 # 书籍ID，如 MAT-G6B-OP (一课一练)
    
    INPUT_RES1 = "res1_final.json"         # AI 输出后合并的 res1 文件路径
    INPUT_RES2 = "res2_final.json"         # AI 输出后合并的 res2 文件路径
    
    OUTPUT_DIRECTORY = "./formatted_bank"  # 最终修改后的文件存放目录
    # ==========================================

    process_json_files(
        res1_path=INPUT_RES1,
        res2_path=INPUT_RES2,
        subject_dir=SUBJECT_DIR,
        book_id=BOOK_ID,
        output_dir=OUTPUT_DIRECTORY
    )