import os
import hashlib
import fitz
import shutil
from collections import defaultdict
import sys

def extract_and_save_images(pdf_path, output_dir, hash_group, hash_info):
    """提取并保存指定哈希组的图片"""
    doc = fitz.open(pdf_path)
    for page_num, xref in hash_info[pdf_path]:
        try:
            # 提取图片数据
            base_image = doc.extract_image(xref)
            image_data = base_image["image"]
            ext = base_image["ext"]
            
            # 生成唯一文件名
            fname = f"{os.path.basename(pdf_path)}_{page_num+1}_xref{xref}.{ext}"
            output_path = os.path.join(output_dir, fname)
            
            # 保存图片文件
            with open(output_path, "wb") as f:
                f.write(image_data)
                
        except Exception as e:
            print(f"无法提取 {pdf_path} 中图片: {str(e)}")
    doc.close()

def process_duplicates(duplicates, hash_map, output_base="duplicates"):
    """处理重复图片并创建可视化结果"""
    # 创建输出根目录
    if os.path.exists(output_base):
        shutil.rmtree(output_base)
    os.makedirs(output_base)

    # 遍历所有重复组
    for group_id, (hash_val, pdf_infos) in enumerate(duplicates.items(), 1):
        group_dir = os.path.join(output_base, f"group_{group_id}")
        os.makedirs(group_dir, exist_ok=True)

        # 生成报告文件
        report_path = os.path.join(group_dir, "report.txt")
        with open(report_path, "w", encoding="utf-8") as report:
            report.write(f"重复图片组 ID: {group_id}\n")
            report.write(f"MD5 哈希值: {hash_val}\n")
            report.write("包含该图片的文件列表:\n\n")
            
            # 保存所有重复实例
            seen_pdf = set()
            for pdf_path, locations in pdf_infos.items():
                report.write(f"文件路径: {pdf_path}\n")
                report.write("出现位置:\n")
                
                # 写入页码信息
                for page_num, xref in locations:
                    report.write(f"  - 第 {page_num+1} 页 (图片引用ID: {xref})\n")
                
                # 提取并保存图片
                if pdf_path not in seen_pdf:
                    extract_and_save_images(
                        pdf_path, 
                        group_dir,
                        hash_val,
                        {pdf_path: locations}
                    )
                    seen_pdf.add(pdf_path)
                
                report.write("\n")

def find_duplicate_images(directory):
    """查找并整理重复图片"""
    hash_map = defaultdict(lambda: defaultdict(list))  # {hash: {pdf: [(page_num, xref)]}}

    # 第一阶段：收集所有图片信息
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                try:
                    doc = fitz.open(pdf_path)
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        for img in page.get_images(full=True):
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            image_data = base_image["image"]
                            hash_val = hashlib.md5(image_data).hexdigest()
                            hash_map[hash_val][pdf_path].append( (page_num, xref) )
                    doc.close()
                except Exception as e:
                    print(f"处理 {pdf_path} 失败: {str(e)}")

    # 筛选重复项
    duplicates = {h: v for h, v in hash_map.items() if len(v) > 1}
    return duplicates, hash_map  # 返回 duplicates 和 hash_map

def main():
    if len(sys.argv) != 2:
        print("使用方法: python check_images.py <PDF目录>")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"错误: 目录 {directory} 不存在")
        sys.exit(1)

    # 获取重复图片信息和 hash_map
    duplicates, hash_map = find_duplicate_images(directory)  # 接收返回的 duplicates 和 hash_map
    
    if not duplicates:
        print("未发现重复图片")
        return

    print(f"\n发现 {len(duplicates)} 组重复图片，正在生成可视化报告...")
    # 将 hash_map 作为参数传递给 process_duplicates
    process_duplicates(duplicates, hash_map)
    print(f"报告已生成到: {os.path.abspath('duplicates')}")

if __name__ == "__main__":
    main()