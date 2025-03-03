# Writeup_check

本项目分为`hash检测工具`和`图片特征分析工具`

**注意：图片特征分析工具得到的报告一定要进行人工复核，目前的准确度大概在30%**

---

## hash检测工具

### 简介
通过计算图片的MD5哈希值来识别重复图片，并生成包含重复图片信息的可视化报告。

### 功能特点
- 遍历指定目录中的所有PDF文件。
- 检测PDF文件中的重复图片。
- 生成包含重复图片信息的报告，包括图片出现的文件路径、页码和引用ID。
- 提取并保存重复图片到指定目录。

### 使用方法

#### 安装依赖
确保已安装以下依赖库：
```bash
pip install PyMuPDF
```

#### 运行脚本
1. 将脚本保存为 `hash_check.py`。
2. 在终端中运行以下命令：
   ```bash
   python hash_check.py <PDF目录>
   ```
   其中 `<PDF目录>` 是包含PDF文件的目录路径。

#### 输出结果
- 如果未发现重复图片，脚本将输出提示信息。
- 如果发现重复图片，脚本将在当前目录下生成一个名为 `duplicates` 的文件夹，其中包含：
  - 每组重复图片的子文件夹（如 `group_1`）。
  - 每个子文件夹中的 `report.txt` 文件，包含重复图片的详细信息。
  - 提取的重复图片文件。

### 示例
假设目录结构如下：
```
example_dir/
├── doc1.pdf
├── doc2.pdf
└── doc3.pdf
```
运行脚本：
```bash
python hash_check.py example_dir
```
如果发现重复图片，输出目录结构可能如下：
```
duplicates/
├── group_1/
│   ├── report.txt
│   ├── doc1_1_xref1.png
│   └── doc2_2_xref2.png
└── group_2/
    ├── report.txt
    ├── doc2_3_xref3.jpg
    └── doc3_1_xref4.jpg
```

### 注意事项
- 该脚本仅支持PDF文件。
- 确保指定目录中包含有效的PDF文件，否则可能报错。
- 如果目录中文件较多，运行时间可能会较长。

---

## 图片特征分析工具

### 项目简介
通过提取图片的特征（如感知哈希值和ORB特征点），并比较这些特征来识别相似图片。检测结果会保存到指定目录，并生成详细的报告。

### 功能特点
- 支持多进程加速图片提取和特征计算。
- 使用感知哈希（Perceptual Hash）和ORB特征点匹配来检测相似图片。
- 自动生成包含相似图片的分组目录和说明文件。
- 输出检测结果的JSON报告。

### 使用方法

#### 安装依赖
确保已安装以下依赖库：
```bash
pip install PyMuPDF pillow imagehash opencv-python numpy tqdm
```

#### 运行脚本
1. 将脚本保存为 `characteristic_check.py`。
2. 在终端中运行以下命令：
   ```bash
   python 3.py
   ```
   脚本会自动从 `wp` 目录中读取PDF文件，并将结果输出到 `similar_results` 目录。

#### 输出结果
- 如果未发现相似图片，脚本将输出提示信息。
- 如果发现相似图片，脚本将在当前目录下生成以下内容：
  - `similar_results/`：包含每组相似图片的子文件夹（如 `group_0`）。
  - 每个子文件夹中的 `README.txt` 文件，包含相似图片的详细信息。
  - 提取的相似图片文件。
  - `similarity_report.json`：包含所有相似图片组的JSON报告。

### 示例
假设目录结构如下：
```
wp2/
├── doc1.pdf
├── doc2.pdf
└── doc3.pdf
```
运行脚本：
```bash
python characteristic_check.py
```
如果发现相似图片，输出目录结构可能如下：
```
similar_results/
├── group_0/
│   ├── README.txt
│   ├── doc1_img0.png
│   └── doc2_img1.png
└── group_1/
    ├── README.txt
    ├── doc2_img2.png
    └── doc3_img0.png
```

### 示例 `README.txt` 内容
```
相似图片组 #0
来源文件1: doc1.pdf
图片索引1: 0

来源文件2: doc2.pdf
图片索引2: 1
```

### 注意事项
- 该脚本仅支持PDF文件。
- 确保指定目录中包含有效的PDF文件，否则可能报错。
- 如果目录中文件较多，运行时间可能会较长。
- 感知哈希阈值（默认为5）和ORB匹配阈值（默认为20）可以根据需求调整。
