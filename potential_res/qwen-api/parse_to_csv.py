import json
import csv
import os
import sys
import argparse

def process_jsonl_to_csv(jsonl_path):
    """
    处理单个 JSONL 文件，提取信息并存为对应的 CSV 文件。
    CSV 文件将与源文件在同一目录下。

    Args:
        jsonl_path (str): 输入的 JSONL 文件的完整路径。
    """
    # 1. 根据输入文件路径生成输出文件路径
    base_path = os.path.splitext(jsonl_path)[0]
    csv_path = base_path + '.csv'

    print(f"正在处理: {jsonl_path}")

    processed_lines = 0
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as infile, \
             open(csv_path, 'w', newline='', encoding='utf-8-sig') as outfile:

            csv_writer = csv.writer(outfile)
            # 写入表头
            csv_writer.writerow(['宏名字', '对于宏的解释'])

            # 逐行处理 JSONL 文件
            for line_num, line in enumerate(infile, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    # 解析最外层的 JSON
                    outer_data = json.loads(line)
                    raw_response = outer_data.get("raw_response", "")

                    # 清理 raw_response 字符串，去除代码块标记
                    if raw_response.startswith("```json"):
                        # strip() 移除首尾空白, [7:-3] 去除 ```json 和 ```
                        clean_json_str = raw_response.strip()[7:-3].strip()
                    else:
                        clean_json_str = raw_response

                    if not clean_json_str:
                        print(f"  -> 警告: 第 {line_num} 行的 'raw_response' 为空或格式不正确。")
                        continue

                    # 解析内嵌的 JSON
                    inner_data = json.loads(clean_json_str)

                    # 提取所需字段
                    macro_name = inner_data.get("Name", "N/A")
                    explanation = inner_data.get("reason", "N/A")

                    # 写入 CSV 行
                    csv_writer.writerow([macro_name, explanation])
                    processed_lines += 1

                except json.JSONDecodeError as e:
                    print(f"  -> 警告: 解析第 {line_num} 行时出错: {e}")
                except (KeyError, AttributeError) as e:
                    print(f"  -> 警告: 处理第 {line_num} 行时缺少预期的键: {e}")
        
        if processed_lines > 0:
            print(f"✓ 处理完成! {processed_lines} 条记录已保存到: {csv_path}\n")
        else:
            print(f"∅ 未处理任何记录。输出文件 '{csv_path}' 已创建但可能为空。\n")
            # 如果不希望保留空文件，可以取消下面这行注释
            # os.remove(csv_path)

    except FileNotFoundError:
        print(f"✗ 错误: 输入文件未找到 '{jsonl_path}'\n")
    except Exception as e:
        print(f"✗ 处理文件 '{jsonl_path}' 时发生意外错误: {e}\n")


def find_and_process_files(root_dir):
    """
    在指定目录及其子目录中递归查找所有 .jsonl 文件并处理它们。

    Args:
        root_dir (str): 要搜索的根目录路径。
    """
    print(f"--- 开始在目录 '{root_dir}' 中搜索 .jsonl 文件 ---")
    found_files = 0
    # os.walk 会递归遍历目录
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".jsonl"):
                found_files += 1
                jsonl_file_path = os.path.join(dirpath, filename)
                process_jsonl_to_csv(jsonl_file_path)
    
    if found_files == 0:
        print("未找到任何 .jsonl 文件。")
    print("--- 搜索处理完毕 ---")


def main():
    """
    主函数，用于解析命令行参数。
    """
    parser = argparse.ArgumentParser(
        description="递归搜索目录下的 .jsonl 文件，并将其内容转换为对应的 .csv 文件。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "directory",
        type=str,
        help="要搜索的根目录的路径。"
    )

    args = parser.parse_args()
    target_directory = args.directory

    if not os.path.isdir(target_directory):
        print(f"错误: 提供的路径 '{target_directory}' 不是一个有效的目录。")
        sys.exit(1) # 退出脚本并返回错误码

    find_and_process_files(target_directory)


# --- 脚本入口 ---
if __name__ == "__main__":
    main()