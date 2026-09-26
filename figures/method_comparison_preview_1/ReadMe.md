# 通过以下网址可以压缩网格大小 https://www.meshy.ai/zh/3d-tools/file-compressor/stl

# Step 1 确定观察视角
### 调整视角，读取指定目录下的gt.stl, 输出gt_rt.json
python3 step1_stl_pose_editor.py <id path>

# Step 2 生成视角
### 读取指定目录下的our.stl、gt_rt.json、真值gt.stl ，输出 id.png
python3 step2_render_stl_rt.py <id path>

# Step 3 合并图片
python3 step3_merge_imgs.py

# 遍历当前文件夹中的所有文件夹，删除png文件
python rm_png.py
