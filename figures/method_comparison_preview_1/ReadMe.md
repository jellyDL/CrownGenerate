
# Step 1 确定观察视角
### 调整视角，读取指定目录下的gt.stl, 输出gt_rt.json
python step1_stl_post_editor.py <id path>

# Step 2 生成视角
### 读取指定目录下的our.stl、gt_rt.json、真值gt.stl ，输出 id.png
python step2_stl_post_editor.py <id path>