# 牙冠生成文献的消融实验整理

核对目录：`/Users/jelly/Desktop/牙冠生成/`；整理日期：2026-09-13。

目录包含 **18 份 PDF：17 篇文章及 1 部学位论文**。其中，12 篇文章及学位论文包含模块、损失、输入条件、训练数据或阶段设置的对照；另外 5 篇未发现明确的内部组件消融，主要开展方法比较、重建算法比较或缺损场景评价。上述分类依据本地 PDF，不将未随文件提供的补充材料视为已核查内容。

下文页码统一指 **PDF 文件页码（从 1 开始）**，并附原文节号、表号或图号供定位。文献编号为本报告独立编号，不对应 manuscript 中的参考文献编号。学位论文与独立发表文章存在内容重复，不能将其计为相互独立的验证证据。

## 一、全部文献总览

| 编号 | 文章／方法 | 消融及相关对照内容 | 实验性质 | 原文定位 |
|---|---|---|---|---|
| [1] | MADCrowner | 冠体模板、模板变形、颈缘约束；曲率权重；重建算法 | 模块／输入先验消融、参数分析、重建器比较 | §4.5，表5–6，图9–11、13；第21–27页 |
| [2] | VBCD | PCR、牙位提示、CMPL | 模块／条件／损失组合消融 | 表1(b)；第8页 |
| [3] | DCrownFormer（会议版） | MCAM与SAM、MRL与SAP路径、CPL曲率权重 | 注意力替换、损失与重建路径对照、参数分析 | 表2、图4；第7–9页 |
| [4] | DCrownFormer+（期刊扩展版） | IGRN、GFD、PTE、MCAM；CPL与GPL权重 | 模块删除、模块替换、损失与参数分析 | §5.2–5.3，表5–7；第10–14页 |
| [5] | From Mesh Completion to AI Designed Crown（DMC） | PoinTr、PoinTr+SAP、DMC无MSE、完整DMC | 重建路径对照、损失消融 | §4.4，表2；第8–9页 |
| [6] | Personalized Dental Crown Design: A Point-to-Mesh Completion Network | 颈缘损失；CD/DCD/HyperCD/InfoCD；重建模块 | 损失消融、重建器比较 | §4.4，表4–5，图9–10；第10页及后续图页 |
| [7] | 3D Shape Generation…（学位论文） | 第4–7章：颈缘输入、DMC、颈缘／距离损失、邻牙交叠及对颌交互约束 | 多章消融及功能验证，部分与[5][6]重复 | 表4.2、5.2、6.4–6.5、7.1–7.5；详见下文 |
| [8] | CrownGen | 边界预测、DITA、伪牙冠数据扩增 | 模块／条件消融、训练数据对照 | 第7、19、32–36页，补充表2–6（已收录于本地PDF） |
| [9] | DCPR-GAN | Stage-I、Stage-I GroNet_OF、完整两阶段网络 | 阶段对照、联合约束消融 | §III-C/D，表III，图8–11；第6–9页 |
| [10] | From Synthetic Data to Real Restorations（ToothCraft） | Normal、Antag、Classifier Free | 输入条件与训练／采样策略对照 | §4.3，表1；第5–6页 |
| [11] | INN-based single maxillary molar study | POCO-only／POCO-PointMLP × 12,000／50,000输入点 | 局部分支消融、采样规模分析 | 图2、表3；第3–5页 |
| [12] | A Dual Discriminator Adversarial Learning Approach…（DentalRecNet） | 三阶段训练、普通／空洞卷积、增强因子α | 阶段对照、模块替换、参数分析 | §3.3–3.5，表1，图8–11；第8–11页 |
| [13] | ToothGAN | 有／无对颌输入、自然牙／混合数据、特征判别器、延长训练、几何后处理 | 条件消融、结构与数据对照、训练预算检查、后处理分析 | §3.6、§4.1–4.2，表1–4，图3–5；第5–10页 |
| [14] | ToothCR | 点云补全网络比较、Alpha Shapes/Ball Pivoting/Screened Poisson比较 | 未见内部模块消融；含重建器比较 | §4，表1，图3–4；第7–10页 |
| [15] | Tooth3dNet | 与六种补全网络比较、按牙型分析 | 未见内部模块消融 | §3，表1–2；第12–18页 |
| [16] | A Latent Variable Deep Generative Model for 3D Anterior Tooth Shape | 不同checkpoint、三类人工缺损 | 模型选择与缺损场景评价，非模块消融 | 表1–2，图2–4；第3–5页 |
| [17] | AI-driven Crown Generation: A Comparative Analysis… | PF-Net、PCN、PoinTr | 普通方法比较，非模块消融 | 结果部分、表1；第5–7页 |
| [18] | Precise Tooth Design Using Deep Learning-based Templates | DIT/TSL/ATT、不同缺损程度、其他形状补全网络 | 模板／方法比较和场景分析，非模块消融 | §2.4–2.7、§3，图7–9，表1–2；第5–9页 |

## 二、包含消融或内部设置对照的文章

### [1] MADCrowner

**实验目的：** 分离初始形状先验、粗变形和颈缘条件对冠体生成的贡献，并考察质量与推理成本的关系。

| 消融对象 | 对照设置 | 指标与主要观察 |
|---|---|---|
| 初始冠体模板与模板变形 | 图9给出五组：半球模板且无变形；半球模板且有变形；冠体模板且无变形；无颈缘约束；完整模型。半球半径为7.5 mm | 表5报告CD-L2、Fidelity Distance、HD、F-score，以及显存和推理时间；合理模板及模板变形改善生成质量 |
| 颈缘约束 | 保持冠体模板和变形模块，对比有／无颈缘约束 | 总体HD从1.160降至1.027 mm；总体CD-L2从0.193降至0.175 mm²；说明颈缘条件有助于控制极端局部偏差 |
| CMPL曲率权重λ | 改变曲率权重，比较CD-L2和HD曲线 | 原文测试范围内λ=1最好；属于参数敏感性分析，不能等同于分别删除CPL和MPL的完整损失消融 |
| 网格重建方法 | 对MADCrowner生成点云分别使用Point2Mesh、NKSR及本文重建方法 | 表6使用CD-L2、Fidelity Distance、HD、F-score；本文重建结果最好。属于重建器／后处理比较 |

**可借鉴之处：** 在同一消融表中同时报告几何误差和效率；以HD和颈缘可视化说明局部适配效果。表5与表6分别涉及生成组件与重建结果，不宜直接混用数值。

### [2] VBCD

PCR的全称为 **Point Cloud Refiner（点云细化器）**；TP Prompt为Tooth Position Prompt（牙位提示）；CMPL为Curvature and Margin Penalty Loss（曲率与颈缘惩罚损失）。

表1(b)包含以下五组，已对照PDF原表核实勾选关系：

| 组别 | PCR | TP Prompt | CMPL | CD-L2 | Fidelity | F-score |
|---|---|---|---|---|---|---|
| 基线UNet | 无 | 无 | 无 | 0.230 | 0.314 | 0.896 |
| 基线+PCR | 有 | 无 | 无 | 0.198 | 0.231 | 0.929 |
| 基线+PCR+CMPL | 有 | 无 | 有 | 0.154 | 0.216 | 0.934 |
| 基线+PCR+TP Prompt | 有 | 有 | 无 | 0.156 | 0.219 | 0.932 |
| 完整模型 | 有 | 有 | 有 | 0.140 | 0.213 | 0.957 |

**关键控制：** 不使用CMPL时，采用CPL作为距离监督，而非去掉全部距离损失。完整模型三项指标最佳，PCR、牙位提示和颈缘惩罚均有增益。原表1(b)将CD-L2单位标为mm，与表1(a)的mm²不一致，因此这里仅转录数值，不沿用存在冲突的单位。

**可借鉴之处：** 采用“基础模块+两个可组合组件”的五组设计，同时观察单项增益与联合效果。

### [3] DCrownFormer（会议版）

| 消融对象 | 对照设置 | 评价方法与结论 |
|---|---|---|
| 形态感知交叉注意力MCAM | Baseline（无MCAM）；Baseline+SAM；Baseline+MCAM | 表2(a)：CD、F-score、NC、MAE、R²、SDE；MCAM的CD、F-score、R²和SDE较优，并用注意力图显示对邻牙、对颌和颈缘的关注 |
| 网格重建损失MRL | Ours w/o MRL + SAP；Ours w/ MRL | 表2(b)：相同六项指标；加入MRL后SDE由8.03降至6.47、MAE由4.74降至1.84（原文显示值均有×10³缩放） |
| 曲率惩罚损失CPL | λ=0时为普通Chamfer Distance Loss（CDL）；与λ=1的CPL及其他λ比较 | 图4(b)(c)：主要观察CD、SDE；λ=1较优，继续增大权重会降低性能 |

**解释边界：** MRL是 **Mesh Reconstruction Loss**，不是“Mesh Refinement Layer”。MAE和R²衡量DPSR指示网格，不能解释为表面点坐标误差。MCAM并非所有指标最优：SAM的NC和MAE优于MCAM；有MRL时NC也略低于SAP对照。MRL实验同时涉及监督及重建路径变化，不是完全保持推理路径不变的单因素删除实验。

### [4] DCrownFormer+（期刊扩展版）

| 消融对象 | 原文对照设置 | 主要指标与结论 |
|---|---|---|
| 隐式网格细化网络IGRN | 完整模型 vs w/o IGRN | 表5(a)、6(a)：CD、F-score、RMSE、IGSC、SDE、HD、NC，以及GN、孔洞总数和平均曲率MC；孔洞总数从116降至7，说明细化对完整性贡献突出 |
| 几何特征描述GFD | 完整模型 vs w/o GFD；移除后仅使用面中心点输入 | 相同指标；加入GFD后整体形态与局部细节改善，孔洞总数从20降至7。该对照同时改变可用几何信息 |
| 位置与牙号嵌入PTE | 完整模型 vs w/o PTE，即联合去掉PoE和ToE | 表5(a)、6(a)：联合嵌入改善多项误差指标。本地正文表中未见PoE-only和ToE-only两组，不能声称已分离两者贡献 |
| MCAM | 用MLP替换；用SAM替换；保留MCAM | 表5(b)、6(b)及注意力图：MCAM的表面误差更低；MLP虽有较低MC，但对应过度平滑，因此MC并非越低越好 |
| 曲率及梯度加权损失 | CPL（Curvature-penalty Chamfer Distance Loss）与GPL（Gradient-penalty Mesh Reconstruction Loss）的权重组合 | 表7列出(α,α′)=(0,0)、(0.5,0.5)、(1,0.5)、(0.5,1)、(1,1)、(1.5,1)、(1,1.5)、(1.5,1.5)、(2,2)；(1,1)最佳，(2,2)明显下降 |

**解释边界：** 权重为零时分别退化为CDL和MRL，即取消加权，并非取消对应监督。表7使用α、α′记号，方法段GPL公式另以β表示梯度权重。RMSE和IGSC用于指示网格；GN及孔洞统计用于完整性，MC用于表面曲率。功能性穿透分析虽在相邻章节出现，但未对全部消融变体重复，不能把它当作每个组件的独立功能证据。

### [5] From Mesh Completion to AI Designed Crown（DMC）

**四组设置：** PoinTr → PoinTr+SAP → DMC without MSE → DMC Full Model。前两组考察点云生成与独立网格重建路径；后两组直接检验MSE监督的作用。

**指标：** CD-L1、CD-L2、MSE、F-score@0.3。表2中，DMC无MSE至完整模型的CD-L1由0.0641降至0.0623，CD-L2由0.015降至0.011，F-score由0.65升至0.70。完整模型MSE为0.0028，但无MSE组该指标未填，不能补造其数值或改善比例。

**结论与借鉴：** 以“分离式重建→端到端重建→加入指示场监督”的递进方式验证方案；保持“训练损失MSE”和“评价指标MSE”的概念区分。

### [6] Personalized Dental Crown Design: A Point-to-Mesh Completion Network

| 消融对象 | 对照设置 | 评价及结论 |
|---|---|---|
| Margin line loss | 同一框架有／无颈缘损失 | §4.4.1、图9主要给出颈缘叠加可视化；加入后更贴合预备体边缘，减少尺寸外扩 |
| 点云距离损失 | CD、DCD、HyperCD、InfoCD | 表4使用CD-L1、CD-L2、EMD；InfoCD分别为57.61、9.45、77.67，优于其余三种损失（原表数值×1000） |
| 网格重建／补全路径 | Point Transformer；PT+SAP；PT+NKSR；PT+Point2Mesh；本文模型 | 表5使用相同三项指标；本文模型为54.39、8.41、75.31（×1000），在该组比较中最好 |

**解释边界：** §4.4.1引用表4，但表4实际上列的是距离损失替换，并没有明确“有／无颈缘损失”两行；因此颈缘损失的独立证据主要来自图9，不应据此编造定量增益。表3的左右邻牙距离／交叠面积MSE属于完整模型空间关系评价，不是交叠损失的有／无消融。重建比较中NKSR额外输入法向，需保留这一设置差异。

### [7] 学位论文：3D Shape Generation—Geometrical and Functional Methods for Dental Crown Design

本论文应按章节拆分，其中第5、6章与[5][6]重合。

| 章节 | 消融方法与组别 | 指标、观察及出处 |
|---|---|---|
| 第4章：Transformer-based crown generation | 有／无颈缘线输入；从生成冠壳重建表面并提取颈缘，再与真实颈缘比较 | 颈缘最大、最小、平均及标准差距离；表4.2中平均距离由2105.3221降至372.2782 μm。第57–60页，表4.2、图4.6–4.7 |
| 第5章：DMC | PoinTr、PoinTr+SAP、DMC无MSE、完整DMC | CD-L1、CD-L2、MSE、F-score@0.3；第69–70页，表5.2。与[5]重复 |
| 第6章：Personalized framework | 颈缘损失有／无；CD/DCD/HyperCD/InfoCD替换；SAP/NKSR/Point2Mesh重建路径比较 | CD-L1、CD-L2、EMD及颈缘可视化；第93–98页，表6.4–6.5、图6.9–6.10。与[6]重复 |
| 第7章：颈缘输入 | 输入主颌与对颌，或额外加入颈缘线；同时比较前期框架到增强框架的递进结果 | CD-L1、CD-L2、L1、MSE，以及提取颈缘的最大／最小／平均／标准差距离；第114–118页，表7.1、7.4 |
| 第7章：邻牙交叠损失 | 基线 vs 加入Intersection Loss；图7.7另比较250 epochs基线训练与在epoch 170后启用约束的训练 | 表7.2报告整体几何指标；图7.7报告左侧、右侧、总交叠面积MSE，图7.8提供邻接接触分类。第114–115、123–125页 |
| 第7章：对颌交互损失 | 基线 vs 加入Antagonist Interaction Loss；功能分析另纳入真实冠体作为参照 | 表7.2整体几何指标；表7.5报告穿透率、平均接触点数、接触比例。穿透率由62.5%降至37.5%，但接触点数与接触比例也下降。第114–115、119–123页 |

**重要限制：** 原文说明受计算资源限制，重点单独评估交叠与对颌损失；表7.3最终增强组合明确写作“Margin + Antagonist”，不能改写成已完成“颈缘+邻牙+对颌+对抗细化”的全组合实验。邻牙Intersection Loss的目标是匹配合理邻接接触，而非简单消除全部交叠。表7.5“Contact Area”实际上由阈值内冠体点的比例表示，不能无说明地视为三角形实际面积。论文称面积MSE采用mm²，若按面积差平方定义应进一步核对实现及量纲。

### [8] CrownGen

**四组设置：** 完整CrownGen；w/o boundary prediction；w/o DITA（移除显式牙间注意力）；w/o pseudo-crown data expansion（仅使用完整牙列训练）。

**评价分两层：** 原始点云使用CD-L1、EMD和不同距离阈值的F1；最终网格使用Average Surface Distance（ASD）和Normal Consistency（NC）。还按牙型与缺失牙数量分层检验，不把点云优势直接视为网格优势。

**主要结果：** 第36页补充表6中，完整模型ASD为0.267；去边界、去DITA、去数据扩增分别为0.411、0.333、0.438。对应NC为0.925、0.887、0.915、0.884。三项设计均有贡献，去掉数据扩增的总体影响最大；牙间注意力对EMD也有明显作用。

**可借鉴之处：** 用完整模型逐项删除设计；分别验证点云和最终网格；数据扩增对照应注明训练集规模与来源同时改变，不能仅解释为某一种增强算子的净效应。

### [9] DCPR-GAN

**实际对照组：** Stage-I GAN；Stage-I GroNet_OF（在Stage-I联合加入GroNet损失与occlusal fingerprint constraint）；完整DCPR-GAN（两阶段）。图8同时展示第一、第二阶段的冠体、咬合沟与咬合指纹。

**指标：** 方法比较表III中的PSNR、RMSE、SSIM、FSIM；另以三维RMS及偏差图评价冠体表面，并报告生成时间。

**结论：** 第一阶段恢复总体结构，第二阶段进一步改善尖、窝、沟及咬合指纹；Stage-I GroNet_OF比原Stage-I具有更合理的功能形态，完整两阶段框架进一步改善结果。

**解释边界：** 两个约束是在同一变体中联合加入，不能推导出GroNet损失和指纹约束各自的独立增益。该论文的“两个生成阶段”也不能与DentalRecNet[12]的“三个训练阶段”混为一谈。

### [10] From Synthetic Data to Real Restorations（ToothCraft）

**三组设置：** Normal不输入对颌；Antag输入对颌；Classifier Free采用10%的条件丢弃，推理混合因子w=2.0。原文将其置于Model Validation，而非独立的模块消融章节。

**指标：** 全体积与缺损区域的L1/mL1、CD/mCD、IoU/mIoU，以及预测冠体与对颌的交叠IoU；真实冠体与对颌的交叠IoU作为参照。

**结果：** Normal的全体积L1最低，但Antag的整体IoU更高、对颌交叠IoU从0.38%降至0.10%；Classifier Free在多项指标上的标准差较小。不存在一组在全部指标上同时最优。

**可借鉴之处：** 在移除对颌输入后同时检查形态与咬合干扰；单列缺损区域指标。该三组实验未扫描条件丢弃率或w，不能表述为已完成两者的参数敏感性分析。

### [11] INN-based single maxillary molar study

**2×2设计：** POCO-only（仅全局分支）及POCO-PointMLP（全局+局部分支），分别使用12,000和50,000个输入采样点，共四组。

**指标：** CD、F-score、Volumetric IoU。局部分支在两种采样规模下均改善CD和F-score；50,000点总体优于12,000点。POCO-PointMLP+50,000点的CD与F-score最好，但该规模下POCO-only的IoU略高。

**可借鉴之处：** 将模块贡献与输入密度分开比较，比只报告“更复杂网络+更多输入点”的一组增益更有解释力。后续与技师设计冠比较的RMS、正／负偏差属于临床形态比较，不属于这四组结构消融。

### [12] DentalRecNet：A Dual Discriminator Adversarial Learning Approach for Dental Occlusal Surface Reconstruction

| 实验 | 设置 | 指标与结论 |
|---|---|---|
| 分阶段训练 | Stage I：用空间、形态约束与L1训练生成器；Stage II：固定生成器，以MSE和感知损失训练双判别器；Stage III：联合训练生成器与双判别器 | 表1：PSNR、FSIM、SSIM；Stage III优于前两阶段，例如PSNR由27.833升至34.264 dB。属于训练阶段对照，非各损失的独立删除 |
| 卷积层替换 | General Convolution替换Dilated Convolution | 图11：三维表面SD、RMS与咬合指纹；示例RMS由0.216降至0.135 mm。该数值来自示例图，不能当作整批病例均值 |
| 增强因子α | 比较0.5、1.0、1.5、2.0、2.5、3.0、3.5 | 图10：PSNR、FSIM、SSIM；α=2.0最好。属于深度图增强参数分析 |

### [13] ToothGAN

该文虽未以统一的“Ablation Study”标题组织结果，但包含明确的控制变量对照，不应归为“无消融”。

| 对照对象 | 设置与原文位置 | 指标及结论 |
|---|---|---|
| 对颌输入 | 同一ResUnet-WGANGP有／无antagonist；表3、§4.2.4 | 2D RMSE、SSIM、3D RMSE、SMCR、VA；加入对颌后3D RMSE由0.478降至0.340，形态细节更完整 |
| 特征判别器及相应约束 | 同一自然牙数据条件下，ResUnet-WGANGP与ResUnet-ToothGAN比较；表2 | ToothGAN引入第二个特征判别器及LoG相关约束，提升沟窝与表面质量；这是联合结构／目标变化，不能单独归因于判别器数量 |
| 训练数据 | 467份自然牙数据设置 vs 额外加入347份技师设计冠的814份混合数据设置；在两种架构上比较，表4 | 同上指标；混合数据有助于沟窝表达，WGANGP的SMCR失败病例由21/25降至12/25，但并非全部指标改善都有统计显著性。467为整体自然牙数据设置，表中实际训练为427、测试为40 |
| 训练时长对照 | ResUnet-WGANGP先训练200 epochs，再额外训练200 epochs，与采用预训练的ToothGAN比较；§4.2.1、图5 | 主要观察沟窝细节；延长训练未产生与ToothGAN相当的改善，用于检查增益是否仅来自更多训练 |
| 几何后处理 | 深度图直接重建网格 vs 加入几何处理；§4.2.2、图4 | 主要为网格表面可视化，说明滤波有助于减少粗糙和噪声，非独立网络模块消融 |
| 特征提取参数 | 不同Gaussian σ与LoG响应设置；§4.1、图3 | 依据沟窝形态可视化选择σ=0.8且LoG>0；属于定性参数选择 |

**需保留的局限：** 表3的SMCR与正文“每项指标均改善”的表述存在冲突。按§3.7.4的定义及表中下降箭头，SMCR表示不合格表面比例；有对颌组21/25、无对颌组0/25，因此不能复述成“对颌输入使所有指标都变好”。更合理的结论是对颌输入改善形态与三维精度，但可能暴露更多粗糙细节，需结合特征判别器和后处理分析。

## 三、未发现明确内部模块消融的5篇文章

| 文献 | 实际做了什么 | 使用的评价及结论范围 |
|---|---|---|
| [14] ToothCR | 与PCN、PF-Net、VRCNet、PoinTr比较；另以少量真实点样本比较Alpha Shapes、Ball Pivoting、Screened Poisson及本文重建算法 | 点云比较使用CD-L1、CD-L2、EMD、F-score；重建主要展示孔洞、冗余面与表面形态。可支持方法／重建器优势，不能分离内部KNN、八叉树等模块贡献 |
| [15] Tooth3dNet | 与PoinTr、GRNet、PMPNet++、PCN、SnowFlakeNet、AdaPoinTr比较，并分析不同牙型 | CD-L1/CD-L2、EMD、HD、MRE及形态图；说明整体方法性能与牙型差异，没有明确逐个删除模块的实验 |
| [16] Latent Variable Model／PointFlow | 比较不同指标最优checkpoint与最终checkpoint；20颗牙分别构造斜切、水平切和垂直切，形成60个重建案例 | 生成用JSD、MMD、COV、1-NNA；缺损重建按可见／缺失区域报告CD。属于模型选择与缺损场景评价，没有删除latent flow等组件 |
| [17] AI-driven Crown Generation | 在相同任务下比较PF-Net、PCN、PoinTr | 几何偏差、临床形态尺寸和设计时间；支持三种方法比较，不支持某个网络模块的因果贡献 |
| [18] Precise Tooth Design | DIT、牙形库TSL、平均牙模板ATT在不同缺损类型下比较；自然牙NST作为参照；另与经典补全网络比较 | 三维RMS及二维宽度、长度、比例、曲率、引导斜度等；属于模板策略和缺损条件比较。NST是参照，不能列作一个消融模型 |

## 四、跨论文可复用的消融设计

| 研究问题 | 可借鉴设置 | 直接参考 |
|---|---|---|
| 模块是否必要？ | 完整模型逐项删除，或用SAM/MLP等简单替代模块；固定其余条件 | [3][4][8][11][12] |
| 几何先验是否有效？ | 有／无颈缘、边界、牙位、对颌信息；模板替换 | [1][2][7][8][10][13] |
| 损失是否提供有效监督？ | 有／无重建损失；统一框架替换点云损失；分别启用邻牙与对颌约束 | [3][5][6][7] |
| 多个组件能否共同改善？ | 基线、基线+A、基线+B、基线+A+B；将共同前置模块固定 | [2] |
| 输出网格是否保留点云收益？ | 点云与最终网格分层评价；固定点云后替换重建器 | [1][6][8][14] |
| 增益是否来自更多数据或训练？ | 有／无扩增；同架构不同数据来源；延长基线训练作为预算对照 | [8][13] |
| 参数是否稳健？ | 扫描曲率／梯度权重、增强因子或输入点数，保留零权重基线 | [1][3][4][11][12] |

若用于后续牙冠网格论文，优先考虑“核心模块逐项删除＋关键损失独立启用＋最终网格验证”。牙科功能约束应另配颈缘、邻接或对颌评价，避免仅用整体CD证明局部功能改善。文献中的指标、单位、采样与归一化规则并不统一，本报告的不同文章数值不能直接横向排名。

## 五、本地原文索引

以下链接对应本次实际核对的18份PDF。

1. [MADCrowner: Margin Aware Dental Crown Design with Template Deformation and Refinement](</Users/jelly/Desktop/牙冠生成/MADCrowner_ Margin Aware Dental Crown Design with Template Deformation and Refinement.pdf>)

2. [VBCD: A Voxel-Based Framework for Personalized Dental Crown Design](</Users/jelly/Desktop/牙冠生成/VBCD_ A Voxel-Based Framework for Personalized Dental Crown Design.pdf>)

3. [DCrownFormer: Morphology-Aware Point-to-Mesh Generation Transformer for Dental Crown Prosthesis from 3D Scan Data of Antagonist and Preparation Teeth](</Users/jelly/Desktop/牙冠生成/DCrownFormer_ Morphology-Aware Point-to-Mesh Generation Transformer for Dental Crown Prosthesis from 3D Scan Data of Antagonist and Preparation Teeth.pdf>)

4. [DCrownFormer Morphology-aware mesh generation and refinement transformer for dental crown prosthesis from 3D scan data of preparation and antagonist teeth](</Users/jelly/Desktop/牙冠生成/DCrownFormer Morphology-aware mesh generation and refinement transformer for dental crown prosthesis from 3D scan data of preparation and antagonist teeth.pdf>)

5. [From Mesh Completion to AI Designed Crown](</Users/jelly/Desktop/牙冠生成/From Mesh Completion to AI Designed Crown.pdf>)

6. [Personalized dental crown design: A point-to-mesh completion network](</Users/jelly/Desktop/牙冠生成/Personalized dental crown design_ A point-to-mesh completion network.pdf>)

7. [3D Shape Generation Geometrical and Functional Methods for Dental Crown Design](</Users/jelly/Desktop/牙冠生成/3D Shape Generation Geometrical and Functional Methods for Dental Crown Design.pdf>)

8. [CrownGen Patient-customized Crown Generation via Point Diffusion Model](</Users/jelly/Desktop/牙冠生成/CrownGen Patient-customized Crown Generation via Point Diffusion Model.pdf>)

9. [DCPR-GAN: Dental Crown Prosthesis Restoration Using Two-Stage Generative Adversarial Networks](</Users/jelly/Desktop/牙冠生成/DCPR-GAN_ Dental Crown Prosthesis Restoration Using Two-Stage Generative Adversarial Networks.pdf>)

10. [From Synthetic Data to Real Restorations: Diffusion Model for Patient-Specific Dental Crown Completion](</Users/jelly/Desktop/牙冠生成/From Synthetic Data to Real Restorations_ Diffusion Model for Patient-Specific Dental Crown Completion.pdf>)

11. [Feasibility and accuracy of single maxillary molar designed by an implicit neural network (INN)‐based model: A comparative study](</Users/jelly/Desktop/牙冠生成/Feasibility and accuracy of single maxillary molar designed by an implicit neural network (INN)‐based model_ A comparative study.pdf>)

12. [A Dual Discriminator Adversarial Learning Approach for Dental Occlusal Surface Reconstruction](</Users/jelly/Desktop/牙冠生成/A Dual Discriminator Adversarial Learning Approach for Dental Occlusal Surface Reconstruction.pdf>)

13. [Tooth generative adversarial network: Anatomical optimisation using Wasserstein generative adversarial network for tooth generation hyphenated dental 3-dimensional precision printing](</Users/jelly/Desktop/牙冠生成/Tooth generative adversarial network_ Anatomical optimisation using Wasserstein generative adversarial network for tooth generation hyphenated dental 3-dimensional precision printing.pdf>)

14. [ToothCR: A Two-Stage Completion and Reconstruction Approach on 3D Dental Model](</Users/jelly/Desktop/牙冠生成/ToothCR_ A Two-Stage Completion and Reconstruction Approach on 3D Dental Model.pdf>)

15. [Tooth3dNet: A Preliminary Exploration for Automatic 3D Morphology Design of Dental Crowns with a Deep Generative Network](</Users/jelly/Desktop/牙冠生成/Tooth3dNet_ A Preliminary Exploration for Automatic 3D Morphology Design of Dental Crowns with a Deep Generative Network.pdf>)

16. [A latent variable deep generative model for 3D anterior tooth shape](</Users/jelly/Desktop/牙冠生成/A latent variable deep generative model for 3D anterior tooth shape.pdf>)

17. [AI-driven crown generation: A comparative analysis of point cloud completion models for mandibular first molar restoration](</Users/jelly/Desktop/牙冠生成/AI-driven crown generation_ A comparative analysis of point cloud completion models for mandibular first molar restoration.pdf>)

18. [Precise tooth design using deep learning-based templates](</Users/jelly/Desktop/牙冠生成/Precise tooth design using deep learning-based templates.pdf>)
