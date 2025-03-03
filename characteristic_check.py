import os
import io
import fitz
import shutil
from PIL import Image
import imagehash
import cv2
import numpy as np
import json
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

def extract_images_from_pdf(pdf_path):
    """提取PDF中的所有图片并转换为RGB格式"""
    doc = fitz.open(pdf_path)
    images = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        image_list = page.get_images(full=True)
        for img_info in image_list:
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_data = base_image["image"]
            try:
                image = Image.open(io.BytesIO(image_data)).convert('RGB')
                images.append(image)
            except Exception as e:
                print(f"Error processing image in {pdf_path}: {e}")
    return images

def compute_features(image):
    """计算图片特征并调整尺寸"""
    try:
        resized_img = image.resize((256, 256))
        phash = imagehash.phash(resized_img)
        img_cv = cv2.cvtColor(np.array(resized_img), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        orb = cv2.ORB_create()
        keypoints, descriptors = orb.detectAndCompute(gray, None)
        return phash, descriptors
    except Exception as e:
        print(f"Error computing features: {e}")
        return None, None

def process_single_pdf(args):
    """处理单个PDF并保存临时图片"""
    pdf_path, temp_dir = args
    features = []
    try:
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        images = extract_images_from_pdf(pdf_path)
        for idx, img in enumerate(images):
            # 保存图片到临时目录
            img_name = f"{pdf_name}_img{idx}.png"
            img_path = os.path.join(temp_dir, img_name)
            img.save(img_path, 'PNG')
            # 计算特征
            phash, descriptors = compute_features(img)
            if phash and descriptors is not None:
                features.append({
                    'pdf': os.path.basename(pdf_path),
                    'img_idx': idx,
                    'phash': str(phash),
                    'descriptors': descriptors.tolist(),
                    'img_path': img_path
                })
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
    return features

def are_images_similar(feat1, feat2):
    """比较两张图片的相似性"""
    # PHash比较
    hamming_dist = imagehash.hex_to_hash(feat1['phash']) - imagehash.hex_to_hash(feat2['phash'])
    if hamming_dist > 5:  # 感知哈希阈值
        return False
    
    # ORB特征匹配
    desc1 = np.array(feat1['descriptors'], dtype=np.uint8)
    desc2 = np.array(feat2['descriptors'], dtype=np.uint8)
    
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    try:
        matches = bf.match(desc1, desc2)
        return len(matches) >= 20  # ORB匹配阈值
    except:
        return False

def main():
    # 初始化目录
    PDF_DIR = 'wp'
    TEMP_DIR = 'temp_images'
    OUTPUT_DIR = 'similar_results'
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 获取所有PDF文件
    pdf_files = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
    
    # 多进程处理提取特征
    print("提取图片和特征中...")
    all_features = []
    with Pool(cpu_count()) as pool:
        args = [(pdf, TEMP_DIR) for pdf in pdf_files]
        for result in tqdm(pool.imap_unordered(process_single_pdf, args), total=len(pdf_files)):
            all_features.extend(result)

    # 检测相似图片
    print("\n正在比对图片相似性...")
    similar_groups = []
    group_id = 0
    
    # 遍历所有可能的图片对
    for i in tqdm(range(len(all_features))):
        for j in range(i+1, len(all_features)):
            if are_images_similar(all_features[i], all_features[j]):
                # 创建独立文件夹
                group_dir = os.path.join(OUTPUT_DIR, f"group_{group_id}")
                os.makedirs(group_dir, exist_ok=True)
                
                # 复制图片文件
                img1_path = all_features[i]['img_path']
                img2_path = all_features[j]['img_path']
                shutil.copy(img1_path, os.path.join(group_dir, os.path.basename(img1_path)))
                shutil.copy(img2_path, os.path.join(group_dir, os.path.basename(img2_path)))
                
                # 创建说明文件
                info_content = f"""相似图片组 #{group_id}
来源文件1: {all_features[i]['pdf']}
图片索引1: {all_features[i]['img_idx']}

来源文件2: {all_features[j]['pdf']}
图片索引2: {all_features[j]['img_idx']}
"""
                with open(os.path.join(group_dir, 'README.txt'), 'w') as f:
                    f.write(info_content)
                
                similar_groups.append({
                    'group_id': group_id,
                    'pdf1': all_features[i]['pdf'],
                    'img1': all_features[i]['img_idx'],
                    'pdf2': all_features[j]['pdf'],
                    'img2': all_features[j]['img_idx'],
                    'directory': group_dir
                })
                group_id += 1

    # 保存检测结果
    with open('similarity_report.json', 'w') as f:
        json.dump(similar_groups, f, indent=2)
    
    # 清理临时文件（可选）
    shutil.rmtree(TEMP_DIR)
    
    print(f"\n检测完成！发现 {len(similar_groups)} 组相似图片，结果保存在 {OUTPUT_DIR} 目录")

if __name__ == '__main__':
    main()