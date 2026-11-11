主要优点
- 问题具有明确的口腔修复学应用背景，FDG、VAE、Structure Flow 和 Feature Flow 的技术链条较完整。
- 同时考虑了牙位、颈缘、邻牙和对颌牙条件，消融实验覆盖较全面。
- 数据规模较大，并设置了独立技师评价和失败案例分析。
- 论文已意识到模型仅用于外部冠形态 CAD 草稿，未直接宣称可用于临床制作，这一边界应继续保持。
必须优先修正的问题
1. 数值结果的真实性和统计证据不足
   表格目前主要报告 mean ± SD，没有逐病例配对检验、95% CI、效应量或多重比较校正。正文却使用了 “achieved the highest”“improved”等确定性表述。
   特别是 table_hierarchical_ablation 中的 single-stage 数值和差值此前是根据上下文估计的。如果没有真实训练日志和逐病例预测结果，这些数值不能作为正式实验结果发表，必须替换为真实结果或删除。仅由两组均值相减得到的差值不能称为 paired difference。
2. Severe penetration 指标没有定义
   主表第 465 行和第 475 行使用了 Severe penetration，但没有说明：
   - 严重穿透的距离阈值；
   - 穿透深度、面积还是病例比例；
   - 正负距离的定义；
   - 参考对象和坐标配准方式；
   - 百分比的分母。
   测试集为 \(n=252\)，表中的 10.5%、7.8%、6.3% 等数值也不像简单的病例比例，必须说明它们是病例级比例、面积加权比例还是平均穿透率。
3. 表题和表注存在不一致
   主表 caption 写的是 “Generation coverage”，但表中没有 coverage 列；表注又写 “Completion rate uses the full test set”，却没有报告 completion rate。应补充每种方法的成功生成数、失败数和分母，或者删除这些表述。
4. 存在参考答案驱动的选择偏倚风险
   第 423 行使用参考 CAD 计算：
   - margin-to-reference 距离；
   - reference mesh 超出局部域的比例。
   如果这些条件在测试集筛选前使用，就可能造成标签驱动的样本选择偏倚。需要说明筛选和数据划分的先后顺序、各阶段排除数量，并最好补充仅依赖输入数据的质控或敏感性分析。
5. 参考 CAD 不能直接视为临床金标准
   参考模型是技师设计的历史 CAD 实例，不能等同于唯一正确的解剖形态或临床金标准。建议将：
   - “anatomically faithful”
   - “clinical usability”
   - “improved occlusal compatibility”
   统一降为“与参考 CAD 的几何一致性”或“初步的实验室 CAD 草稿可用性”。
6. 技师评价证据仍较弱
   第 485–491 行仅有 3 名技师、80 个病例和 240 条评分，但未说明：
   - 是否盲法和随机化；
   - 五级量表的具体 anchor；
   - 技师间一致性，如 weighted \(\kappa\) 或 ICC；
   - 是否按病例聚类分析；
   - 是否有基线或参考 CAD 对照；
   - 样本量依据。
   因此 79.2% 只能表述为“初步感知的实验室可用性”，不能作为临床有效性证据。
7. 数据伦理和来源说明不完整
   虽然文中称数据为 gypsum-model 数据且不含患者身份信息，但仍应补充数据提供方、实验室来源、数据使用授权以及伦理审批或豁免说明。还需要说明病例是否来自不同患者、是否存在重复扫描，以及不同实验室之间的数据分布。
8. 基线公平性和可复现性不足
   第 452–453 行仅说明 VF-Net、DMCv2、VBCD 和 MADCrowner 被重新实现和训练。建议补充每个基线的：
   - 输入条件；
   - 官方代码或权重来源；
   - 训练轮数、学习率和随机种子；
   - 输出表示转换方式；
   - 后处理流程；
   - 失败病例处理规则。
   目前“相同预处理”并不等于“公平比较”。
9. 训练和推理存在 support mismatch
   第 365 行中 Feature Flow 训练时使用真实 support \(O\)，推理时使用预测 support \(\hat O\)。需要报告 Structure Flow 的 support precision/recall，或增加 oracle-\(O\) 对照，以量化结构预测误差对 Feature Flow 的影响。
10. 方法细节仍不足以复现
    第 435 行缺少或不完整说明：
    - VAE 各损失项的权重；
    - 精确训练步数或 epochs；
    - occupancy 选择阈值；
    - classifier-free guidance 的条件 dropout；
    - flow 时间 \(t\) 的采样方式；
    - 模型参数量、显存和推理时间；
    - 多随机种子结果。
    每个病例只生成一个固定 seed 的候选，也无法评估生成稳定性，至少应在限制部分明确说明。
需要统一的内部表述
- 第 481 行提到 “improved normal accuracy”，但主表没有 normal accuracy，应删除或补充指标和数值。
- 第 481 行提到拓扑率和 mesh defects，但表中没有对应结果，也应补表或删除。
- 第 259 行存在 “Subsequently ... subsequently extended” 重复。
- 第 418 行的 Experimental and Discussions 建议改为 Experiments and Discussion。
- cervical margin 可在首次出现时定义为 preparation finish line。
- Margin P95 只能表示输入颈缘点到外表面的几何距离，不能代表临床 marginal adaptation 或内冠适合性。
- 静态扫描中的接触区域只能称为 geometric proximity 或 static geometric contact，不能推断动态咬合功能。
建议修订顺序是：先核实并锁定所有真实逐病例结果，再统一定义穿透和失败处理规则；随后补充统计推断、数据伦理、基线复现细节和技师评价方法；最后收缩临床结论并处理表格、标题和术语一致性。

如果当前部分消融数值确实只是估计值而非真实模型输出，这是投稿前必须解决的数据有效性问题；即使技术方法本身有创新，也不建议在现状下投稿。
