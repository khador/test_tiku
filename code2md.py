import os
from datetime import datetime

def get_code_extensions():
    """返回常见的代码文件扩展名列表"""
    return {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', 
        '.cs', '.go', '.rb', '.php', '.html', '.css', '.scss', '.less',
        '.sql', '.json', '.yaml', '.yml', '.xml', '.sh', '.bash', '.pl',
        '.pm', '.lua', '.r', '.swift', '.m', '.mm', '.kt', '.dart',
        '.rs', '.scala', '.clj', '.ex', '.exs', '.erl', '.hrl',
        '.vim', '.cfg', '.ini', '.toml', '.dockerfile', 'dockerfile'
    }

def is_text_file(file_path):
    """检查文件是否为文本文件"""
    text_extensions = get_code_extensions()
    _, ext = os.path.splitext(file_path)
    return ext.lower() in text_extensions

def read_file_safely(file_path, encodings=['utf-8', 'gbk', 'gb2312', 'latin-1']):
    """安全地读取文件内容，尝试多种编码"""
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content, encoding
        except UnicodeDecodeError:
            continue
        except Exception:
            continue
    return None, None

def create_markdown_from_folder(folder_path, output_file='project_summary.md', max_file_size=1024*1024):
    """
    遍历文件夹并将所有代码文件内容输出到Markdown文件
    
    Args:
        folder_path: 要遍历的文件夹路径
        output_file: 输出的Markdown文件名
        max_file_size: 最大文件大小（字节），超过此大小的文件将跳过
    """
    code_extensions = get_code_extensions()
    
    with open(output_file, 'w', encoding='utf-8') as md_file:
        # 写入标题和基本信息
        md_file.write(f"# Project Code Summary\n\n")
        md_file.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        md_file.write(f"Source Folder: `{folder_path}`\n\n")
        md_file.write("## File Structure\n\n")
        
        # 收集所有代码文件
        all_files = []
        for root, dirs, files in os.walk(folder_path):
            # 排除常见的非必要目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git', '.vscode', 'build', 'dist', 'target']]
            
            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                
                if ext.lower() in code_extensions:
                    relative_path = os.path.relpath(file_path, folder_path)
                    all_files.append((relative_path, file_path))
        
        # 按文件路径排序
        all_files.sort(key=lambda x: x[0])
        
        # 写入文件结构
        for relative_path, _ in all_files:
            indent_level = relative_path.count(os.sep)
            indent = "  " * indent_level
            md_file.write(f"{indent}- `{os.path.basename(relative_path)}`\n")
        
        md_file.write("\n## File Contents\n\n")
        
        # 写入每个文件的内容
        for relative_path, file_path in all_files:
            file_size = os.path.getsize(file_path)
            if file_size > max_file_size:
                print(f"Skipping large file: {relative_path} ({file_size} bytes)")
                md_file.write(f"\n### `{relative_path}`\n\n")
                md_file.write(f"> File too large to include ({file_size} bytes)\n\n")
                continue
            
            content, encoding_used = read_file_safely(file_path)
            if content is not None:
                md_file.write(f"\n### `{relative_path}`\n\n")
                # 获取文件扩展名以确定代码高亮语言
                _, ext = os.path.splitext(file_path)
                lang = ext.lower()[1:] if ext.lower()[1:] in ['py', 'js', 'ts', 'java', 'cpp', 'c', 'html', 'css', 'json', 'xml', 'yaml', 'yml', 'sql', 'sh', 'go', 'rb', 'php'] else 'text'
                
                md_file.write(f"```{lang}\n")
                md_file.write(content)
                md_file.write("\n```\n\n")
            else:
                print(f"Could not read file: {relative_path}")
                md_file.write(f"\n### `{relative_path}`\n\n")
                md_file.write("> Could not read file content (binary file or encoding issues)\n\n")

if __name__ == "__main__":
    # 使用示例
    folder_path = input("请输入要遍历的文件夹路径: ").strip()
    
    if not os.path.isdir(folder_path):
        print(f"错误: '{folder_path}' 不是一个有效的文件夹路径")
    else:
        output_file = input("请输入输出的Markdown文件名 (默认: project_summary.md): ").strip()
        if not output_file:
            output_file = "project_summary.md"
        
        print("正在处理...")
        create_markdown_from_folder(folder_path, output_file)
        print(f"完成! 输出文件: {output_file}")