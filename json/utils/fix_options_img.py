"""
已在md中修改，后面应该用不到了
"""


import json
import os

def fix_options_img(input_filename=r"json\gemini_tiku_20260425\res1_final.json", output_filename=r"json\gemini_tiku_20260425\res1_final_fixed.json"):
    if not os.path.exists(input_filename):
        print(f"❌ 找不到文件 {input_filename}，请检查路径。")
        return

    print(f"正在读取 {input_filename} ...")
    with open(input_filename, 'r', encoding='utf-8') as f:
        try:
            questions = json.load(f)
        except Exception as e:
            print(f"❌ JSON 解析失败: {e}")
            return

    fixed_count = 0

    # 遍历所有题目
    for q in questions:
        if "options" in q and isinstance(q["options"], list):
            for opt in q["options"]:
                img_val = opt.get("img")
                # 如果 img 字段有字符串值，且没有被 <img 标签包裹
                if isinstance(img_val, str) and img_val.strip() != "":
                    if not img_val.strip().startswith("<img"):
                        # 将单纯的文件名包裹为标准的 img 标签
                        opt["img"] = f'<img src="/images/workbook/{img_val.strip()}" />'
                        fixed_count += 1

    # 写回新的 JSON 文件
    print(f"正在保存到 {output_filename} ...")
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"✅ 修复完成！共修复了 {fixed_count} 个选项中的图片标签。")

if __name__ == "__main__":
    fix_options_img()