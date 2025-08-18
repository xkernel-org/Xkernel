# -*- coding: utf-8 -*-
import csv
import os
import time
from openai import AzureOpenAI
from azure.identity import ChainedTokenCredential, AzureCliCredential, ManagedIdentityCredential, get_bearer_token_provider

# --- 配置部分 ---

# 1. Azure OpenAI 认证和客户端设置
# (请确保您的环境已通过 'az login' 登录，或者配置了托管标识)
scope = "api://trapi/.default"
api_version = '2024-12-01-preview'  # 确保这是一个有效的 API 版本
deployment_name = 'gpt-4o_2024-11-20'  # 确保这是一个有效的部署名称
instance = 'gcr/preview' # 确保这是一个有效的实例名称
endpoint = f'https://trapi.research.microsoft.com/{instance}'

# 2. 文件路径设置
# 请将此路径修改为您实际的 CSV 文件路径
input_csv_path = '/home/spike/myXkernel/MACROS/extract_all/filtered_numerical/potential_res/potential_perf_ipc.csv'
# 输出文件将保存在与输入文件相同的目录下
output_csv_path = os.path.join(os.path.dirname(input_csv_path), 'ipc.csv')


# --- 脚本主逻辑 ---

def get_azure_openai_client():
    """获取并返回 Azure OpenAI 客户端"""
    try:
        credential = get_bearer_token_provider(ChainedTokenCredential(
            AzureCliCredential(),
            ManagedIdentityCredential(),
        ), scope)
        
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=credential,
            api_version=api_version,
        )
        print("Azure OpenAI 客户端初始化成功。")
        return client
    except Exception as e:
        print(f"错误：无法初始化 Azure OpenAI 客户端。请检查您的 Azure 登录状态和配置。")
        print(f"具体错误: {e}")
        return None

def analyze_macro(client, row_data):
    """
    构造请求并调用模型来分析单个宏。
    增加了自动重试机制以提高稳定性。
    """
    subsystem, file_path, line_number, macro_type, name, value, description = row_data
    
    prompt_content = f"""
    请以Linux内核专家的身份，分析以下宏：

    **宏信息:**
    - **名称 (Name):** `{name}`
    - **值 (Value):** `{value}`
    - **文件路径 (File Path):** `{file_path}`
    - **行号 (Line Number):** `{line_number}`
    - **内核子系统 (Subsystem):** `{subsystem}`

    **分析要求:**
    请提供一段专业且简洁的解释，严格按照以下三点进行说明：
    1.  **宏定义含义:** 这个宏本身代表什么？
    2.  **内核中作用:** 这个宏在内核中扮演什么角色？
    3.  **性能增益分析:** 修改这个宏的值是否有可能带来性能增益？如果可能，请说明是在什么特定场景下，并分析其权衡。

    请直接输出解释文本，不要添加任何额外的引言或总结。
    """
    
    # API 调用重试逻辑
    max_retries = 3
    delay = 5  # 初始延迟5秒
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "你是一位精通Linux内核的资深专家，擅长精确分析宏定义及其对系统性能的深远影响。"},
                    {"role": "user", "content": prompt_content},
                ],
                temperature=0.2,
                # --- 已修复 ---
                # 错误原因: 'max_tokens' 不被此模型支持
                # 解决方法: 使用 'max_completion_tokens' 代替
                max_completion_tokens=500,
            )
            explanation = response.choices[0].message.content.strip()
            return explanation
        except Exception as e:
            print(f"  -> 调用API时出错 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"  -> {delay}秒后重试...")
                time.sleep(delay)
                delay *= 2  # 指数退避
            else:
                error_message = f"API Error after {max_retries} retries: {e}"
                print(f"  -> 已达到最大重试次数。返回错误信息。")
                return error_message

def main():
    """主函数，负责读取、处理和写入CSV文件，并支持断点续传。"""
    print("--- 开始执行内核宏分析脚本 (增强版) ---")
    
    client = get_azure_openai_client()
    if not client:
        return

    if not os.path.exists(input_csv_path):
        print(f"错误: 输入文件未找到，请检查路径: {input_csv_path}")
        return

    # --- 断点续传逻辑 ---
    processed_macros = set()
    # 检查输出文件是否存在以确定是否可以续传
    if os.path.exists(output_csv_path):
        print("检测到已存在的输出文件，将进行断点续传...")
        try:
            with open(output_csv_path, 'r', encoding='utf-8') as f_out:
                reader_out = csv.reader(f_out)
                header_out = next(reader_out)  # 跳过表头
                # 使用 文件路径+行号+宏名称 作为唯一标识符
                for row in reader_out:
                    if len(row) > 4: # 确保行是完整的
                        unique_id = (row[1], row[2], row[4])
                        processed_macros.add(unique_id)
            print(f"已找到 {len(processed_macros)} 个已处理的宏记录。")
            file_mode = 'a'  # 如果文件存在，使用追加模式
        except (IOError, StopIteration) as e:
            print(f"警告：无法读取已存在的输出文件 '{output_csv_path}' (可能是空的或已损坏)。将重新创建文件。错误: {e}")
            file_mode = 'w' # 如果读取失败，则覆盖重写
    else:
        print("未找到输出文件，将创建新文件。")
        file_mode = 'w'  # 如果文件不存在，使用写入模式

    # --- 文件处理主循环 ---
    try:
        with open(input_csv_path, 'r', encoding='utf-8') as infile, \
             open(output_csv_path, file_mode, newline='', encoding='utf-8') as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            
            header_in = next(reader)
            # 如果是新文件，则写入表头
            if file_mode == 'w':
                writer.writerow(['Subsystem', 'File Path', 'Line Number', 'Type', 'Name', 'Value', 'Explanation'])

            total_rows = 0
            skipped_rows = 0
            for row in reader:
                total_rows += 1
                if len(row) != len(header_in):
                    print(f"警告: 第 {total_rows} 行数据格式不正确，已跳过。数据: {row}")
                    continue
                
                # 检查此宏是否已被处理过
                current_unique_id = (row[1], row[2], row[4])
                if current_unique_id in processed_macros:
                    skipped_rows += 1
                    continue
                
                macro_name = row[4]
                print(f"正在处理新宏 (总第 {total_rows} 行): {macro_name}...")
                
                explanation = analyze_macro(client, row)
                
                # 原始列是7列，新解释是第8列
                new_row = row[:7] + [explanation]
                writer.writerow(new_row)
                outfile.flush() # 立即将内容写入磁盘，确保进度安全
                
                print(f"  -> 成功处理并写入宏: {macro_name}")

    except FileNotFoundError:
        print(f"错误: 文件未找到 {input_csv_path}")
    except Exception as e:
        print(f"处理过程中发生未知错误: {e}")

    print("-" * 30)
    if skipped_rows > 0:
        print(f"本次运行跳过了 {skipped_rows} 个已处理的宏。")
    print(f"所有宏处理完毕！结果已保存至: {output_csv_path}")


if __name__ == "__main__":
    main()
