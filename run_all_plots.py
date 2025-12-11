#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键运行所有绘图脚本，并将输出保存到BUILD文件夹（多线程版本）
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()
BUILD_DIR = PROJECT_ROOT / "BUILD"

# 创建BUILD目录
BUILD_DIR.mkdir(exist_ok=True)

# 排除的文件和目录
EXCLUDE_PATTERNS = [
    'plot_common.py',
    'run_all_plots.py',
    'legacy',
    '__pycache__',
    '.git',
    'BUILD',
]

# 线程锁，用于输出同步
print_lock = threading.Lock()

def should_exclude(filepath):
    """检查文件是否应该被排除"""
    path_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str:
            return True
    return False

def find_plot_files():
    """查找所有绘图文件"""
    plot_files = []
    
    # 查找所有plot*.py文件
    for pattern in ['**/plot*.py', '**/plot_*.py']:
        for filepath in PROJECT_ROOT.glob(pattern):
            if not should_exclude(filepath):
                plot_files.append(filepath)
    
    # 去重并排序
    plot_files = sorted(set(plot_files))
    return plot_files

def run_plot_script(script_path):
    """运行单个绘图脚本"""
    script_dir = script_path.parent
    script_name = script_path.name
    
    with print_lock:
        print(f"\n{'='*60}")
        print(f"运行: {script_path.relative_to(PROJECT_ROOT)}")
        print(f"{'='*60}")
    
    try:
        # 切换到脚本所在目录
        original_cwd = os.getcwd()
        os.chdir(script_dir)
        
        # 确保项目根目录在 Python 路径中，以便导入 plot_common
        env = os.environ.copy()
        python_path = str(PROJECT_ROOT)
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{python_path}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = python_path
        
        # 运行脚本
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300,  # 5分钟超时
            env=env,
            cwd=str(script_dir)
        )
        
        if result.returncode == 0:
            with print_lock:
                print(f"✓ 成功: {script_name}")
                if result.stdout:
                    # 只打印关键输出，避免过多信息
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if any(keyword in line.lower() for keyword in ['saved', 'done', 'graph', 'plot']):
                            print(f"  {line}")
            return True, script_path, None
        else:
            error_msg = ""
            if result.stderr:
                error_msg = result.stderr
            elif result.stdout:
                error_msg = result.stdout
            
            with print_lock:
                print(f"✗ 失败: {script_name}")
                if error_msg:
                    # 只打印关键错误信息
                    error_lines = error_msg.strip().split('\n')
                    for line in error_lines[-5:]:  # 只显示最后5行
                        if line.strip():
                            print(f"  {line}")
            
            return False, script_path, error_msg
            
    except subprocess.TimeoutExpired:
        with print_lock:
            print(f"✗ 超时: {script_name} (超过5分钟)")
        return False, script_path, "Timeout"
    except Exception as e:
        with print_lock:
            print(f"✗ 异常: {script_name}")
            print(f"  错误: {str(e)}")
        return False, script_path, str(e)
    finally:
        os.chdir(original_cwd)

def collect_pdf_files():
    """收集所有生成的PDF文件（排除-crop.pdf文件）"""
    pdf_files = []
    
    # 查找所有PDF文件（排除BUILD目录和-crop.pdf文件）
    for pdf_path in PROJECT_ROOT.rglob("*.pdf"):
        if "BUILD" not in str(pdf_path):
            # 过滤掉已经是-crop.pdf的文件
            if "-crop.pdf" not in pdf_path.name:
                pdf_files.append(pdf_path)
    
    return pdf_files

def copy_pdf_to_build(pdf_path):
    """将PDF文件复制到BUILD目录，保持目录结构"""
    relative_path = pdf_path.relative_to(PROJECT_ROOT)
    
    # 构建目标路径
    target_path = BUILD_DIR / relative_path
    
    # 创建目标目录
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 复制文件
    shutil.copy2(pdf_path, target_path)
    return target_path

def crop_pdf(pdf_path):
    """使用 pdf-crop-margins 裁剪PDF文件"""
    # 如果已经是-crop.pdf文件，跳过
    if "-crop.pdf" in pdf_path.name:
        return None
    
    pdf_crop_path = Path.home() / "plot" / "python" / "bin" / "pdf-crop-margins"
    
    # 检查 pdf-crop-margins 是否存在
    if not pdf_crop_path.exists():
        with print_lock:
            print(f"  ⚠ pdf-crop-margins 未找到: {pdf_crop_path}")
        return None
    
    # 生成裁剪后的文件名
    pdf_dir = pdf_path.parent
    pdf_name = pdf_path.stem
    cropped_pdf_path = pdf_dir / f"{pdf_name}-crop.pdf"
    
    try:
        # 运行 pdf-crop-margins 命令
        result = subprocess.run(
            [str(pdf_crop_path), "-a0", str(pdf_path), "-o", str(cropped_pdf_path)],
            capture_output=True,
            text=True,
            timeout=60  # 60秒超时
        )
        
        if result.returncode == 0 and cropped_pdf_path.exists():
            return cropped_pdf_path
        else:
            with print_lock:
                if result.stderr:
                    print(f"  ⚠ 裁剪失败: {pdf_path.name}")
            return None
    except subprocess.TimeoutExpired:
        with print_lock:
            print(f"  ⚠ 裁剪超时: {pdf_path.name}")
        return None
    except Exception as e:
        with print_lock:
            print(f"  ⚠ 裁剪异常: {pdf_path.name}, 错误: {str(e)}")
        return None

def main():
    """主函数"""
    print("="*60)
    print("开始运行所有绘图脚本（多线程版本）")
    print("="*60)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"输出目录: {BUILD_DIR}")
    
    # 查找所有绘图文件
    plot_files = find_plot_files()
    
    if not plot_files:
        print("\n未找到任何绘图文件！")
        return
    
    print(f"\n找到 {len(plot_files)} 个绘图文件:")
    for i, plot_file in enumerate(plot_files, 1):
        print(f"  {i}. {plot_file.relative_to(PROJECT_ROOT)}")
    
    # 使用多线程运行所有绘图脚本
    print(f"\n开始运行绘图脚本（使用多线程）...")
    print(f"最大线程数: {min(16, len(plot_files))}")  # 最多16个线程
    
    success_count = 0
    fail_count = 0
    failed_scripts = []
    results = {}
    
    # 使用线程池执行
    max_workers = min(16, len(plot_files))  # 最多8个并发线程
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_script = {
            executor.submit(run_plot_script, plot_file): plot_file 
            for plot_file in plot_files
        }
        
        # 收集结果
        for future in as_completed(future_to_script):
            script_path = future_to_script[future]
            try:
                success, path, error = future.result()
                results[path] = (success, error)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    failed_scripts.append(path.relative_to(PROJECT_ROOT))
            except Exception as e:
                with print_lock:
                    print(f"✗ 执行异常: {script_path.relative_to(PROJECT_ROOT)}")
                    print(f"  错误: {str(e)}")
                fail_count += 1
                failed_scripts.append(script_path.relative_to(PROJECT_ROOT))
    
    # 收集并复制PDF文件
    print(f"\n{'='*60}")
    print("收集生成的PDF文件...")
    print(f"{'='*60}")
    
    pdf_files = collect_pdf_files()
    
    if not pdf_files:
        print("未找到任何PDF文件！")
    else:
        print(f"找到 {len(pdf_files)} 个PDF文件:")
        copied_count = 0
        cropped_count = 0
        
        for pdf_path in pdf_files:
            try:
                # 复制原始PDF文件
                target_path = copy_pdf_to_build(pdf_path)
                print(f"  ✓ {pdf_path.relative_to(PROJECT_ROOT)} -> {target_path.relative_to(BUILD_DIR)}")
                copied_count += 1
                
                # 裁剪PDF文件
                cropped_pdf_path = crop_pdf(pdf_path)
                if cropped_pdf_path:
                    # 复制裁剪后的PDF文件到BUILD目录
                    try:
                        cropped_target_path = copy_pdf_to_build(cropped_pdf_path)
                        print(f"  ✓ {cropped_pdf_path.relative_to(PROJECT_ROOT)} -> {cropped_target_path.relative_to(BUILD_DIR)}")
                        cropped_count += 1
                    except Exception as e:
                        print(f"  ✗ 复制裁剪文件失败: {cropped_pdf_path.relative_to(PROJECT_ROOT)}")
                        print(f"    错误: {str(e)}")
            except Exception as e:
                print(f"  ✗ 复制失败: {pdf_path.relative_to(PROJECT_ROOT)}")
                print(f"    错误: {str(e)}")
        
        print(f"\n成功复制 {copied_count}/{len(pdf_files)} 个原始PDF文件到BUILD目录")
        print(f"成功裁剪并复制 {cropped_count}/{len(pdf_files)} 个PDF文件到BUILD目录")
    
    # 输出总结
    print(f"\n{'='*60}")
    print("运行总结")
    print(f"{'='*60}")
    print(f"总文件数: {len(plot_files)}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    
    if failed_scripts:
        print(f"\n失败的脚本:")
        for script in failed_scripts:
            print(f"  - {script}")
    
    print(f"\n所有PDF文件已保存到: {BUILD_DIR}")
    print("="*60)

if __name__ == "__main__":
    main()
