# 基于定向有符号柔性双网格与多尺度条件流匹配的患者特异性三维牙冠生成

> 稿件状态：中文方法与实验协议初稿 v0.1，2026-08-15  
> 研究类型：回顾性单中心/多技工来源算法开发与单臂技师评价研究  
> 当前证据状态：方法链路和单病例推理已经跑通；正式基线、消融、1,203例测试集和技师评价结果尚待回填。文中不得将结果占位符改写为推测性数值。

## 摘要

### 目的

从预备体牙列、对颌牙列、三维颈缘线及目标牙FDI编号自动生成患者特异性的三维牙冠解剖外表面，减少传统数字CAD流程中对模板选择和人工雕刻的依赖。

### 方法

本研究构建了一种牙科条件三维生成框架。首先，将人工设计并沿颈缘线统一封底的牙冠网格表示为分辨率为1024³的柔性双网格（Flexible Dual Grid, FDG）。除双网格顶点偏移与相交状态外，在每个活动单元中编码到真值表面的截断有符号距离及定向表面法向，形成oriented signed-FDG。稀疏几何变分自编码器将该表示压缩为64³、32通道的稀疏latent。随后采用两阶段conditional flow matching：Structure Flow生成16³、8通道的稠密结构latent并恢复活动坐标，Feature Flow在预测坐标上生成决定牙尖、嵴、沟窝和颈缘细节的32维稀疏特征。预备体牙列、对颌牙列、颈缘线和FDI条件通过全局token、体素对齐特征及坐标邻域查询三个尺度注入生成网络。训练联合使用速度场回归、latent重建、局部梯度、Laplacian、SDF-normal线积分一致性及高法向变化区域加权监督。研究纳入24,049个病例，按病例划分为训练、验证和测试集20,441/2,405/1,203例。主要几何终点为排除人工底盖后的临床外表面Chamfer-L1；主要临床终点为3名技师对100例主要队列评价后，以至少2/3多数判定得到的“外冠无需修改率”。

### 结果

完整模型在1,203例测试集上的临床外表面Chamfer-L1为【待回填】mm，HD95为【待回填】mm，法向一致性为【待回填】。相较MADCrowner、【VBCD或DCrownFormer+】及FDI最近邻检索基线，主要终点的配对差异为【待回填】。100例主要临床队列的无需修改率为【待回填】%（95% CI【待回填】），3名技师的Fleiss κ为【待回填】。AI推理时间及从推理到外冠获准的完整处理时间分别为【待回填】s和【待回填】s。

### 结论

【待所有实验完成后撰写。当前只允许表述为：所提出框架旨在同时建模牙冠整体占位、颈缘约束、咬合关系和高频解剖细节，其有效性仍需由预设的外部基线、内部消融、完整测试集和技师评价共同验证。】

**关键词：** 三维牙冠生成；flow matching；柔性双网格；有符号距离场；多尺度条件；数字化修复

## 1 引言

牙冠修复的目标不仅是恢复缺损牙的外形，还需重建与邻牙和对颌牙协调的解剖轮廓、邻接关系及咬合功能。数字化CAD/CAM系统已将牙冠设计从手工蜡型转变为模板驱动的三维建模，但技师仍需围绕颈缘、牙尖沟窝、轴面突度、邻接点和咬合接触进行病例特异性调整。既有研究报告的人工设计时间因病例复杂度和计时边界差异较大，可从数分钟延长至一小时以上[1-3]。因此，能够直接输出可继续进行内冠、粘接间隙和车针补偿设计的外冠初稿，对提高数字修复流程的一致性和效率具有实际价值。

早期学习式牙冠设计多将任务简化为二维深度图或咬合面重建。双判别器GAN和两阶段DCPR-GAN能够学习局部沟窝与整体形态，但二维投影难以完整保留轴面和颈缘信息，对对颌与邻牙三维关系的利用也有限[4,5]。随后，ToothCR、DCrownFormer及point-to-mesh方法将缺失牙冠视为点云补全问题，并通过可微Poisson重建输出网格[6-9]。这些方法改善了三维形态表达，但固定点数、点云噪声、Poisson重建导致的底部过延伸以及高频细节平滑仍限制了其临床可用性。

近期方法开始显式引入牙科先验。VBCD在体素域采用粗到细生成，并加入FDI位置提示及曲率-颈缘惩罚[10]；MADCrowner通过模板变形、颈缘提取和后处理减少重建表面的过延伸[11]；DCrownFormer+进一步结合曲率与梯度监督，并以对颌、邻牙和预备体作为上下文[8]。这些研究表明，颈缘、牙位和对颌关系不是可选信息，而是决定牙冠临床几何约束的核心条件。然而，现有牙科网络通常在有限分辨率体素、固定点云或模板拓扑上进行预测，难以同时兼顾任意拓扑、高分辨率表面细节和生成式建模能力。

开放域三维生成近年来从稠密体素和隐式场转向稀疏结构latent、可学习网格表示及大规模flow/diffusion transformer。Flow Matching通过直接回归概率路径的速度场，为连续归一化流提供了无需数值模拟的训练目标[12]。TRELLIS采用稀疏结构与局部特征分离的structured latent，并以两阶段rectified flow分别生成结构和特征[13]；TRELLIS.2、SparseFlex、Direct3D-S2和TripoSG进一步提高了三维表示的分辨率、紧凑性和细节保持能力[14-17]。但这些通用模型主要以图像或文本为条件，其几何先验和评价指标并不直接对应牙冠设计中的颈缘、咬合和邻接约束。

本研究在通用高分辨率三维生成框架上进行牙科定向改造。需要明确的是，1024³ FDG、Structure/Feature两阶段生成和基础DiT采样机制来自Pixal3D/TRELLIS.2体系[13,14,18]；本文不将其宣称为原创。本文重点研究两个可证伪的技术问题：其一，oriented signed-FDG及解码表面联合几何监督能否提高牙尖、沟窝、颈缘和网格质量；其二，牙科条件的全局、体素和坐标邻域三级注入能否同时改善整体占位与局部关系。

本文的候选贡献如下：

1. 构建面向牙冠的oriented signed-FDG，在1024³稀疏活动单元上联合编码双网格几何、截断有符号距离和定向表面法向。
2. 提出牙科多尺度条件机制，将预备体牙列、对颌牙列、三维颈缘线和FDI通过全局token、体素对齐特征和坐标邻域查询注入Structure/Feature Flow。
3. 在Feature Flow训练中引入解码表面联合监督，以距离、法向、梯度、Laplacian、SDF-normal线积分一致性和细节加权约束高频表面。
4. 建立排除人工底盖的临床外表面评价协议，并联合报告几何误差、咬合穿透、拓扑质量、技师可接受性和实际工作流耗时。

## 2 相关工作

### 2.1 数据驱动的牙冠与牙齿形态生成

二维生成方法通常从咬合方向投影牙列，以图像到图像网络恢复缺损区域。Tian等提出的双判别器模型以全局和局部判别器约束咬合面，在1,000个样本上取得0.114 mm的RMS误差[4]；DCPR-GAN进一步将整体咬合结构和沟窝指纹分阶段学习[5]。此类方法能利用成熟的二维卷积网络，但遮挡与投影会丢失颈缘和轴面信息，输出仍需转换为完整三维网格。

点云补全将牙冠表示为无序点集。ToothCR采用补全与重建两阶段网络[6]；Hosseinimanesh等先后提出包含颈缘约束的点云补全和point-to-mesh框架，后者使用局部特征、Transformer、法向预测和可微Poisson重建，在388/98/71例训练、验证和测试病例上进行评估[7,9]。DCrownFormer及其扩展版本使用形态感知cross-attention、曲率惩罚Chamfer和梯度惩罚重建损失，输入包含预备体和对颌牙，在3,144个牙科模型上验证[8,19]。这些方法说明曲率、对颌和颈缘信息对细节生成有益，但从点云重建网格可能引入孔洞、过平滑和非临床底面。

体素、模板和隐式表示提供了不同权衡。VBCD在6,499例口扫上采用3D U-Net先生成粗体素牙冠，再以距离监督细化，并通过FDI提示和曲率-颈缘损失改善个体化[10]。MADCrowner从牙位模板出发进行由粗到细变形，同时提取颈缘并据此裁除Poisson重建的多余区域[11]。基于隐式网络和深度学习模板的临床研究则关注生成牙冠与CAD结果在形态、咬合、邻接和设计时间上的差异[2,3,20]。模板方法拓扑稳定、易于编辑，但可能受固定模板表达能力限制；体素和隐式方法拓扑灵活，却需要处理分辨率、内外方向和表面提取误差。

### 2.2 高分辨率三维几何生成

三维生成的核心矛盾是表示容量、拓扑灵活性和计算成本。直接网格自回归方法显式建模顶点与面连接，但序列长度随网格复杂度增长；MeshFlow等方法尝试以MeshVAE和rectified flow并行生成连续网格latent[21]。隐式SDF或occupancy表示支持任意拓扑，但在高分辨率均匀网格上成本较高。稀疏体素与结构latent只在表面附近保留活动单元，为高分辨率生成提供了可行路径。

TRELLIS将三维结构与局部特征分离：第一阶段生成稀疏占位结构，第二阶段仅在活动坐标上生成特征[13]。TRELLIS.2进一步提出紧凑的原生结构latent并支持1536³重建[14]。TripoSG采用大规模rectified flow和SDF、法向及Eikonal混合监督[17]；Direct3D-S2以空间稀疏注意力扩展到1024³[16]；SparseFlex和Pixal3D则探索柔性双网格、任意拓扑和像素对齐条件[15,18]。这些进展为牙冠的亚毫米局部几何提供了表示基础，但不能直接解决牙科条件语义和临床评价问题。

### 2.3 牙科几何条件与临床评价

颈缘约束直接决定外冠的颈部边界和后续内冠设计起点。既有工作通过颈缘损失、曲率-颈缘加权或后处理裁切降低边缘误差[7,10,11]。对颌条件决定咬合接触与穿透，邻牙条件则影响近远中接触和轴面突度。Cho等对深度学习设计的牙支持和种植支持后牙冠进行了形态、咬合、邻接与时间评价，提示纯几何距离不能替代临床工作流终点[2,3]。

现有研究常报告Chamfer distance、Hausdorff distance、F-score、法向一致性、曲率或穿透面积，但人工封底可能显著影响全表面距离。本研究将人工底盖保留为训练和水密拓扑的一部分，却通过颈缘线重新切分GT与预测网格，将底盖排除在主要临床外表面指标之外。由于当前全颌网格没有邻牙分割，客观邻接距离不作为终点，邻接关系由技师评价。

## 3 方法

### 3.1 任务定义

对病例 \(i\)，输入为目标牙所在牙列网格 \(J_i^t\)、对颌牙列网格 \(J_i^o\)、有序三维颈缘线 \(M_i\) 和FDI编号 \(f_i\)。模型学习条件分布

\[
p_\theta(S_i\mid J_i^t,J_i^o,M_i,f_i),
\]

其中 \(S_i\) 为人工CAD设计的牙冠解剖外表面及由预处理生成的封闭底面。部署时仅生成一个固定随机种子的预测 \(\hat S_i\)，不从多个候选中选择最优结果。输出定位为后牙单冠外形的CAD初稿，不包含内冠、粘接间隙、车针补偿或制造参数。

### 3.2 数据预处理与牙科局部坐标系

每个病例包含上颌网格、下颌网格、颈缘线和人工设计wax-up。颈缘线由技师在牙科软件中半自动标注；wax-up主要由Exocad设计，部分由3Shape设计，并在后续临床生产流程中继续用于内冠构建。为获得统一水密训练表征，使用有序颈缘线在原始牙冠上构建测地切割环，将闭合网格分成两侧；选择封闭后体积和面积较大的外侧曲面，并在颈缘开口处生成边界固定的调和最小曲面底盖。该步骤统一自动完成，不改变临床外表面。

局部坐标原点取颈缘点均值。对颈缘中心化坐标进行SVD，以最小奇异向量作为候选 \(z\) 轴，并根据对颌牙局部点云方向将其定向到对颌侧。\(y\) 轴由颈缘中心指向目标牙列外侧的向量在垂直于 \(z\) 轴的平面内投影得到，\(x=y\times z\)，最终重新正交化形成右手坐标系。该坐标系只使用输入条件，不使用目标牙冠，避免目标泄漏。

目标牙冠映射到边长24 mm的局部立方体，即半边长 \(h=12\) mm；上下颌分别在颈缘中心24 mm半径内裁剪并各采样4,096个带法向点，颈缘线重采样为1,024点。条件坐标按18 mm尺度归一化。病例在预处理阶段进行文件完整性、颈缘到目标距离、目标视野范围和有限数值检查。

### 3.3 1024³ oriented signed-FDG

标准FDG在与表面相交的活动单元 \(c_j\) 上保存双网格顶点在单元内的三维偏移 \(v_j\in[0,1]^3\)，以及沿三个轴的相交状态 \(b_j\in\{0,1\}^3\)。分辨率 \(R=1024\) 时，单个体素的物理边长约为 \(24/1024=0.0234\) mm。稀疏存储使模型只处理表面邻域，而不构造完整的1024³稠密体素。

为补充标准FDG缺少稳定内外方向的问题，在每个活动单元中心 \(x_j\) 查询真值三角网格上的最近点 \(p_j\) 及其三角面 \(T_j\)。通过重心插值得到单位表面法向 \(n_j\)。有符号距离定义为

\[
d_j=\operatorname{clip}\left(
\operatorname{sign}[(x_j-p_j)^\top n_{T_j}]
\frac{\lVert x_j-p_j\rVert_2}{\Delta},-\tau,\tau
\right),
\]

其中 \(\Delta=2h/R\) 为体素尺寸，\(\tau=3\) 个体素。由此，每个活动单元的输入由 \([v_j-0.5,b_j-0.5,d_j,n_j]\) 组成，共10维。对封闭且法向一致的目标，正值表示表面外部，负值表示内部；对存在方向问题的网格先统一法向并记录修复状态。

### 3.4 稀疏几何VAE

几何VAE采用五级稀疏编码器，通道数为48、96、192、384和512。通过octree式spatial-to-channel重排将1024³活动单元逐级压缩到64³稀疏网格，并输出每个活动latent的32维均值和对数方差。训练时使用重参数化采样，推理和latent缓存使用后验均值。解码器对称地预测逐级细分掩码，最终恢复双网格顶点偏移、三轴相交logit、quad插值权重、有符号距离及单位表面法向。

VAE损失写为

\[
\mathcal L_{\mathrm{VAE}}=
\lambda_v\mathcal L_v+
\lambda_b\mathcal L_b+
\lambda_s\mathcal L_{\mathrm{sub}}+
\lambda_q\mathcal L_{\mathrm{quad}}+
\lambda_{KL}\mathcal L_{KL}+
\lambda_d\mathcal L_d+
\lambda_n\mathcal L_n+
\mathcal L_{\mathrm{diff}}+
\lambda_{det}\mathcal L_{det}.
\]

其中 \(\mathcal L_v\) 为顶点偏移均方误差，\(\mathcal L_b\) 与 \(\mathcal L_{sub}\) 分别为相交和细分二元交叉熵，\(\mathcal L_d\) 为有符号距离Smooth-L1，\(\mathcal L_n=1-\hat n^\top n\)。\(\mathcal L_{diff}\) 对顶点、距离和法向分别匹配六邻域一阶差分与离散Laplacian。

代码配置中曾使用“Eikonal”命名的项并非标准的 \((\lVert\nabla d\rVert-1)^2\)。本研究将其准确表述为SDF-normal线积分一致性。对相邻活动单元 \((j,k)\)，定义

\[
r_{jk}=(d_j-d_k)-\frac{1}{2}(n_j+n_k)^\top(c_j-c_k),
\]

并以Smooth-L1匹配预测与真值残差。细节权重由真值法向的局部变化估计，在每个病例内归一化后提高牙尖、嵴和沟窝区域的监督权重。

### 3.5 牙科多尺度条件编码

目标牙列、对颌牙列和颈缘线分别通过来源特异的点MLP编码。牙列点输入位置与法向，颈缘点仅输入位置；三种来源增加可学习source embedding。

**全局条件。** 对每种来源的点特征分别进行均值池化和最大池化，拼接后投影为512维全局向量，并与FDI embedding相加。该向量描述目标牙位、整体间隙及牙列相对位置。

**体素级条件。** 将三种来源的点特征按局部坐标散射到64³网格，在同一体素内取平均，并通过3×3×3卷积细化。Structure Flow以4倍步长卷积下采样到16³；Feature Flow既保留64³逐坐标特征，又下采样到16³形成cross-attention token。

**邻域查询条件。** 对Feature Flow的每个64³活动坐标，分别在目标牙列、对颌牙列和颈缘点中查询4个最近邻。每个邻居以相对坐标、输入法向和归一化距离形成7维描述，共得到 \(3\times4\times7\) 维局部向量，经MLP投影后残差加入对应latent token。该路径使颈缘与咬合邻近区域无需依赖全局token间接传递几何关系。

训练以概率0.1将全部牙科条件替换为空条件，用于classifier-free guidance。消融实验分别保留全局、全局加体素和完整三级条件，以检验各尺度贡献。

### 3.6 Structure conditional flow matching

VAE latent的活动坐标转换为64³二值occupancy，并通过冻结的TRELLIS structure encoder压缩为16³、8通道的稠密latent \(x_0^S\)。Structure Flow采用1.3B参数DiT骨干，30个Transformer block、1,536隐藏维、12个注意力头和三维RoPE。以精确预训练权重初始化后，训练rank-32 LoRA，并解冻最后24个block；structure codec保持冻结。

给定高斯噪声 \(\epsilon\sim\mathcal N(0,I)\) 和 \(t\in[0,1]\)，概率路径为

\[
x_t=(1-t)x_0+[\sigma_{min}+(1-\sigma_{min})t]\epsilon,
\]

目标速度为

\[
u_t=(1-\sigma_{min})\epsilon-x_0.
\]

模型最小化 \(\mathcal L_S=\mathbb E\lVert v_\theta^S(x_t,t,C)-u_t\rVert_2^2\)。训练使用logit-normal时间采样；验证报告latent \(x_0\) MSE及解码occupancy的Dice和IoU，但后两项不参与反向传播。

### 3.7 Feature conditional flow matching

Feature Flow在Structure给出的64³活动坐标上生成32维稀疏latent特征。主训练阶段采用GT活动坐标，以降低结构错误对特征学习的干扰；端到端验证和正式推理使用Structure预测坐标。骨干为TRELLIS.2 1024 Shape SLat 1.3B DiT，包含30个block、1,536隐藏维、12头注意力、三维RoPE和变长FlashAttention。BF16主干冻结，训练rank-32 attention/MLP LoRA、输入输出投影及牙科条件adapter。

基础速度场损失与Structure阶段相同。由预测速度可估计

\[
\hat x_0=(1-\sigma_{min})x_t-[\sigma_{min}+(1-\sigma_{min})t]v_\theta^F(x_t,t,C).
\]

除速度MSE外，Feature阶段加入 \(x_0\) 重建损失、稀疏邻域latent梯度损失及高梯度token加权。每个训练step还将 \(\hat x_0\) 通过冻结VAE解码器映射到物理FDG输出，施加顶点、相交、细分、signed distance、sign、法向、一阶差分、Laplacian、SDF-normal线积分一致性和高频细节损失。由此，Feature Flow不是只在抽象latent空间拟合速度，而是直接受到牙冠表面位置与方向的约束。

### 3.8 推理与连续有符号距离重建

每例使用基础种子2026与case ID哈希得到固定病例种子，只生成一个结果。Structure Flow采用50步Heun求解和guidance 3.0；Feature Flow采用50步Euler求解、guidance 3.0及时间重标定3.0。预测Feature经VAE解码得到稀疏FDG顶点、距离和法向。

为生成水密网格，在1024³局部域内对稀疏预测建立连续有符号距离场。对查询点 \(x\)，选取 \(K=8\) 个邻近活动单元，以解码距离和法向构造一阶局部估计

\[
\tilde d_i(x)=d_i+(x-p_i)^\top n_i,
\]

再根据空间距离进行高斯加权融合。当前参数为带宽1.75体素、Gaussian sigma 3体素和支持半径12体素。提取零水平集后仅保留主连通域，不使用形态学closing或拓扑重试来掩盖局部缺陷。输出须通过连通性、流形性、面片比例、二面角和积分曲率门禁。

## 4 实验设计

### 4.1 数据集与划分

最终预处理发现24,051个目录，其中24,050个结构有效并完成处理；1例因目标超出视野排除，最终纳入24,049例。病例来自国内数据提供机构及多个技工厂，均已移除姓名、年龄、性别、机构和日期等身份信息。每例要求同时包含上下颌、清晰颈缘线、至少4颗牙及正确咬合关系。训练、验证和测试集按病例以85%/10%/5%固定划分，共20,441/2,405/1,203例。

当前划分不是患者级或口扫级独立划分。同一患者或同一上下颌扫描可能因多颗修复牙形成多个病例并跨越数据集；本研究不进行扫描指纹去重。因此论文只能称为“病例级随机划分”，并将潜在数据相关性列为限制，不能声称患者级独立。当前manifest仍包含5例前牙且均位于训练集；正式模型冻结前应【选择并记录：删除后重训，或如实说明仅测试与临床研究限定后牙】。测试集没有前牙；第三磨牙仅2例。

### 4.2 对比方法

1. FDI牙位最近邻检索与颈缘对齐基线。
2. MADCrowner公开实现[11]。
3. VBCD[10]或DCrownFormer+[8]中经复现审计后可稳定运行的一种方法。
4. 本文完整模型。

外部方法使用相同训练、验证和测试病例重新训练，不能直接引用其原论文数值。所有方法统一输出或裁切到临床外表面，并在相同采样、坐标和距离实现下评价。GT只作为参考真值，不作为算法基线。

### 4.3 内部消融

| 编号 | 表征与监督 | 条件注入 | Structure坐标 | 目的 |
|---|---|---|---|---|
| A0 | 标准FDG与基础重建损失 | 完整 | 预测 | 表征基线 |
| A1 | FDG + signed distance和oriented normal | 完整 | 预测 | 检验方向信息 |
| A2 | A1 + 梯度/Laplacian/线积分一致性/细节监督 | 完整 | 预测 | 完整几何监督 |
| C0 | 完整表征 | 仅全局 | 预测 | 全局条件基线 |
| C1 | 完整表征 | 全局 + 体素 | 预测 | 体素对齐贡献 |
| C2 | 完整表征 | 全局 + 体素 + 邻域查询 | 预测 | 完整模型 |
| P0 | 完整表征 | 完整 | GT | Feature生成上限 |
| P1 | 完整表征 | 完整 | 预测 | 端到端误差传播 |

补充输入消融分别去除颈缘、对颌或FDI。去除FDI的结论仅基于配对几何误差，不额外训练牙位分类器，也不增加技师消融评分，因此不声称模型能够客观分类牙位。

### 4.4 几何终点

使用同一条有序颈缘线对GT和预测闭合网格重新执行测地拓扑切割。面积较大且包含牙尖与咬合面的曲面定义为临床外表面，另一侧定义为人工底盖。主要几何指标仅在临床外表面之间计算；完整水密网格只用于拓扑和补充全表面指标。切割不对预测网格进行平滑、补洞或法向修复。无法按颈缘切分的预测记录为外表面提取失败，不静默排除。

每个外表面按三角形面积加权采样50,000点。正式测试前在20例验证病例上比较10k、50k和100k采样；若50k与100k的主要指标中位差异超过1%，正式评价使用100k。主要几何终点为对称Chamfer-L1：

\[
CD_{L1}=\frac{1}{2}\left[
\frac{1}{|P|}\sum_{p\in P}\min_{q\in Q}\lVert p-q\rVert_2+
\frac{1}{|Q|}\sum_{q\in Q}\min_{p\in P}\lVert q-p\rVert_2
\right].
\]

HD95定义为两个方向最近距离P95的较大值。次要指标包括两个方向P95、法向一致性、有符号法向一致性、平均及P95法向角，以及F-score@0.05/0.10/0.20 mm。颈缘指标为颈缘点到预测外表面的平均和P95距离，名称使用“颈缘线邻近误差”，不称为真实边界误差或内冠边缘适合性。

【待验证后冻结】咬合区拟由GT局部坐标中的冠方高度区域确定，高曲率区拟由咬合区内GT绝对曲率最高20%的点构成。窝沟的曲率符号必须先在验证集可视化确认，不能直接沿用当前“正曲率=窝沟”的假设。

### 4.5 咬合与拓扑终点

牙冠外表面到对颌牙三角网格的有符号距离 \(d_o\) 规定正值为间隙、负值为穿透。操作阈值如下：0至0.02 mm为接触，0.02至0.10 mm为近接触，0.10至0.20 mm为探索性间隙；-0.02至0 mm为轻微几何穿透，低于-0.02 mm为明显过早接触或重度穿透，低于-0.10 mm为严重穿透。报告接触和近接触面积比例、穿透面积比例、重度穿透比例、平均/HD95/最大穿透深度及严重穿透病例率，并在0.10和0.20 mm阈值下进行敏感性分析。

由于全颌PLY没有牙齿实例分割，本研究不计算自动近远中邻接距离。邻接接触仅由技师在Exocad中评价。拓扑指标包括水密率、winding consistency、边界边比例、非流形边比例、连通分量数、最大连通面比例、法向翻转、表面积比、二面角P95和积分绝对曲率。

### 4.6 技师评价

模型冻结后，从测试集一次性抽取100例主要队列。上下颌各50例并保持左右平衡：FDI 14/24各4例、15/25各6例、16/26各10例、17/27各5例、34/44各2例、35/45各4例、36/46各12例、37/47各7例。FDI 38和48各1例作为探索性第三磨牙，实际评价102例，但不进入主要临床终点。

3名具有3至5年经验的技师分别在统一Exocad环境中独立评价同一批病例，共306次病例评价。每名技师采用不同随机顺序，仅查看预备体牙列、对颌牙列、颈缘线、FDI和AI外冠，不查看GT、模型名称、检查点、自动指标或其他技师评分。由于技师知道对象均为AI结果，本研究称为单臂独立技师评价，不称为生成方法盲法比较。

颈缘外形、解剖形态、咬合关系、邻接关系和总体可接受性分别采用1至5分Likert量表：1为不可用且需完全重做，2为大幅修改，3为中等修改，4为轻微修改，5为该维度无需修改。总体评分5严格定义为：外冠无需任何雕刻、平滑、咬合、邻接、颈缘或刚体位置修正，即可进入内冠、粘接间隙和车针补偿流程。病例级主要临床终点为至少2/3名技师总体评分5；3/3一致判定作为敏感性分析。

未生成网格、无法导入Exocad或不构成完整牙冠定义为技术失败。失败病例进入100例主要终点分母并判定为需要修改，但不虚构Likert评分。成功导入但严重错误的病例仍正常评分。模型冻结后不得通过更换随机种子或候选选择挽救失败。

### 4.7 时间评价

AI组对约100例记录模型推理时间，以及从输入准备完成、推理、导入Exocad、检查和必要外冠修改直至外冠获准的总时间。计时不包括颈缘标注、内冠、粘接间隙、车针补偿、导出和制造。人工时间来自技工厂汇总经验：初级技师从病例与既有颈缘载入到外冠获准的典型时间约5 min。由于人工侧没有病例级原始计时，人工与AI之间只作描述性倍数比较，不计算p值，也不使用“统计学显著快于人工”的表述。

### 4.8 统计分析

连续指标先按病例汇总。模型间比较采用配对方法；正态性和差值分布经检查后，使用配对t检验或Wilcoxon符号秩检验，并报告配对差值、95% CI和效应量。多基线与多次要终点采用Holm校正。主要结果同时报告均值±标准差和中位数（四分位距），避免只提供p值。

病例级无需修改率报告双侧95%置信区间。100个主要病例使比例估计的最大95%置信区间半宽约为10个百分点；研究不预设70%为成功阈值。二分类技师一致性采用Fleiss κ；五维Likert评分采用双向随机效应、绝对一致性的ICC(2,1)和3名技师均值的ICC(2,3)，并补充两两二次加权κ。置信区间以病例为重采样单位进行bootstrap。300次主要队列评分不得视为300个独立病例。第三磨牙只作描述性探索，不进行亚组推断。

## 5 结果

### 5.1 数据与运行完整性

【待回填表1：纳入流程、牙位分布、训练/验证/测试分布、排除原因。】

【待回填：所有模型成功推理数、外表面切割成功数、失败原因、单例显存和时间。】

### 5.2 与外部基线比较

【待回填表2：FDI检索、MADCrowner、VBCD/DCrownFormer+和本文模型的CD-L1、HD95、normal consistency、F-score、颈缘、咬合、拓扑与时间。】

结果叙述必须以效应量和置信区间为主，例如：“完整模型相较最强基线的病例配对CD-L1差值为【】mm（95% CI【】；Holm校正p=【】）。”在数据产生前不得写“显著优于”。

### 5.3 表征与联合监督消融

【待回填表3：A0/A1/A2；重点对应normal consistency、高曲率CD、HD95、曲率误差和拓扑。】

### 5.4 多尺度条件与输入消融

【待回填表4：C0/C1/C2及无颈缘、无对颌、无FDI。】

颈缘消融重点报告颈缘线邻近误差；对颌消融重点报告接触、重度穿透和穿透深度；FDI消融按4/5/6/7号牙报告配对几何误差，不扩展为牙位分类结论。

### 5.5 Structure误差传播

【待回填表5：GT Structure坐标与预测Structure坐标的Feature结果，量化CD-L1、HD95及失败率差值。】

### 5.6 技师评价与效率

【待回填表6：五维Likert分布、2/3无需修改率、3/3一致率、各技师比例、Fleiss κ、ICC和加权κ。】

【待回填图：100例主要队列五维评分堆叠图；牙位/上下颌分层的无需修改率及95% CI；修改类型分布。】

【待回填表7：推理时间、导入检查时间、修改时间、完整AI工作流时间，以及相对技工厂约300 s经验基准的描述性倍数。】

## 6 讨论

### 6.1 主要发现

【待结果后撰写。按照H1至H4逐项回答，不按表格顺序重复数值。】

建议论证顺序：首先回答完整模型是否改善主要外表面CD-L1；其次区分oriented signed-FDG带来的方向/法向收益与联合监督带来的局部细节收益；再次说明全局条件负责整体占位，体素和邻域条件负责局部颈缘与咬合关系；最后讨论Structure预测与oracle坐标的差距是否为当前主要瓶颈。

### 6.2 与既有牙冠生成方法的关系

本研究与VBCD、MADCrowner和DCrownFormer+共同强调颈缘、牙位和局部形态约束[8,10,11]，但表示与生成机制不同：本文不将输出限制在固定模板或有限点集，而是在1024³稀疏双网格上生成带方向的连续表面字段。与TRELLIS/Pixal3D相比[13,18]，本文的贡献不在通用两阶段flow本身，而在牙科多尺度条件、oriented signed-FDG、物理解码监督及临床外表面评价。

### 6.3 临床意义

本系统的目标是提供外冠CAD初稿，而不是直接输出完整可加工修复体。即使外冠被技师判定为无需修改，仍需完成内冠、粘接间隙、车针补偿、材料和加工参数设置。人工约5 min来自技工厂经验汇总，证据层级低于病例级前瞻性计时；因此只能支持工作流潜力，不能形成严格人工优效性结论。

### 6.4 局限性

1. 数据没有伦理审批、知情同意豁免或书面数据使用协议；仅完成匿名化。这是投稿前必须处理的合规风险，不能通过措辞规避。
2. 数据按病例而非患者或原始口扫分组，同一扫描可能跨数据集，存在相关样本泄漏风险。
3. 数据缺乏机构、扫描仪和时间元数据，无法建立独立机构、设备或时间外部测试集，泛化性证据有限。
4. 原始纳入总数和各批次失败流程不可完全恢复，病例流程图只能依据现存manifest和audit报告。
5. GT来自多名技师的实际CAD设计，未进行独立复核；它代表可接受临床设计之一，而不是唯一解。
6. 训练使用人为封闭底面。虽然主要指标排除底盖，生成结果的颈缘仍需在后续CAD流程中结合内冠验证。
7. 缺少邻牙实例分割，不能客观计算近远中接触距离；该终点依赖技师评分。
8. 技师研究为单臂AI结果评价，不能证明质量优于人工设计或外部AI基线。
9. 人工设计时间是经验汇总而非病例级对照，不能进行人工与AI耗时的推断统计。
10. 第三磨牙测试病例仅2例；相关结果仅为探索性。前牙不属于主要验证范围。

## 7 结论

【待实验完成后回填。结论应限定为后牙单冠解剖外表面CAD初稿生成，不使用“无需人工”“直接加工”或“临床替代技师”等超出证据的措辞。】

## 数据与代码可用性

计划公开推理程序、模型权重和必要的环境配置。受数据来源与隐私限制，完整临床数据不公开；可根据合规条件提供脱敏子集或经审核的访问方式。【最终方案待确认。】

## 伦理声明

【阻断项】现阶段无法提供伦理委员会审批、知情同意或豁免证明。不得写“本研究经伦理委员会批准”“不涉及人类受试者”或其他未经文件支持的表述。投稿前需根据目标期刊政策决定研究是否具备投稿条件。

## 作者贡献、基金与利益冲突

【待作者、单位、CRediT角色、基金项目和利益冲突信息后回填。】

## 参考文献（v0.1已核验核心条目，后续扩展至约50篇）

1. Revilla-Leon M, et al. Artificial intelligence models for tooth-supported fixed and removable prosthodontics: a systematic review. J Prosthet Dent. 2023;129(2):276-292. doi:10.1016/j.prosdent.2021.06.001.
2. Cho JH, et al. Tooth morphology, internal fit, occlusion and proximal contacts of dental crowns designed by deep learning-based dental software: a comparative study. J Dent. 2024;141:104830. doi:10.1016/j.jdent.2023.104830.
3. Cho JH, et al. Deep learning-designed implant-supported posterior crowns: assessing time efficiency, tooth morphology, emergence profile, occlusion, and proximal contacts. J Dent. 2024;147:105142. doi:10.1016/j.jdent.2024.105142.
4. Tian S, Huang R, Li Z, et al. A dual discriminator adversarial learning approach for dental occlusal surface reconstruction. J Healthc Eng. 2022;2022:1933617. doi:10.1155/2022/1933617.
5. Tian S, Wang M, Dai N, et al. DCPR-GAN: dental crown prosthesis restoration using two-stage generative adversarial networks. IEEE J Biomed Health Inform. 2022;26(1):151-160. doi:10.1109/JBHI.2021.3119394.
6. Zhu H, Jia X, Zhang C, Liu T. ToothCR: a two-stage completion and reconstruction approach on 3D dental model. In: Advances in Knowledge Discovery and Data Mining. 2022. doi:10.1007/978-3-031-05981-0_13.
7. Hosseinimanesh G, et al. Personalized dental crown design: a point-to-mesh completion network. Med Image Anal. 2025;101:103439. doi:10.1016/j.media.2024.103439.
8. Yang S, et al. DCrownFormer+: morphology-aware mesh generation and refinement transformer for dental crown prosthesis from 3D scan data of preparation and antagonist teeth. Med Image Anal. 2025. doi:10.1016/j.media.2025.103717.
9. Yang S, et al. DCrownFormer: morphology-aware point-to-mesh generation transformer for dental crown prosthesis from 3D scan data of antagonist and preparation teeth. 2024. doi:10.1007/978-3-031-72089-5_11.
10. Wei L, Liu C, Zhang W, et al. VBCD: a voxel-based framework for personalized dental crown design. MICCAI. 2025. arXiv:2507.17205.
11. Wei L, Liu C, Zhang W, et al. MADCrowner: margin aware dental crown design with template deformation and refinement. 2026. arXiv:2603.04771.
12. Lipman Y, Chen RTQ, Ben-Hamu H, Nickel M, Le M. Flow matching for generative modeling. ICLR. 2023. arXiv:2210.02747.
13. Xiang J, Lv Z, Xu S, et al. Structured 3D latents for scalable and versatile 3D generation. Proc IEEE/CVF CVPR. 2025.
14. Xiang J, Chen X, Xu S, et al. Native and compact structured latents for 3D generation. 2025. arXiv:2512.14692.
15. TripoSF/SparseFlex authors. SparseFlex: high-resolution and arbitrary-topology 3D shape modeling. 2025. 【作者与正式出版信息待题录核验】.
16. Direct3D-S2 authors. Direct3D-S2: gigascale 3D generation made easy with spatial sparse attention. NeurIPS. 2025. 【作者待题录核验】.
17. Li Y, Zou ZX, Liu Z, et al. TripoSG: high-fidelity 3D shape synthesis using large-scale rectified flow models. 2025. arXiv:2502.06608.
18. Pixal3D authors. Pixal3D: pixel-aligned 3D generation from images. 2026. doi:10.1145/3799902.3811175. 【作者顺序待核验】.
19. Shu Z, Tian M, Wei H. AI-driven crown generation: a comparative analysis of point cloud completion models for mandibular first molar restoration. J Dent. 2026;168:106581. doi:10.1016/j.jdent.2026.106581.
20. Chanintonsongkhla C, Chouvatut V, Bunkhumpornpat C, Theerasopon P. A latent variable deep generative model for 3D anterior tooth shape. J Prosthodont. 2026;35(4):511-519. doi:10.1111/jopr.14092.
21. Broll S, et al. Generative deep learning approaches for the design of dental restorations: a narrative review. J Dent. 2024;145:104988. doi:10.1016/j.jdent.2024.104988.
22. Precise tooth design authors. Precise tooth design using deep learning-based templates. J Dent. 2024;145:104971. doi:10.1016/j.jdent.2024.104971. 【作者待核验】.
23. Tooth3dNet authors. Tooth3dNet: a preliminary exploration for automatic 3D morphology design of dental crowns with a deep generative network. J Dent. 2026:106696. doi:10.1016/j.jdent.2026.106696. 【卷期页码待核验】.
24. ToothGAN authors. Tooth generative adversarial network: anatomical optimisation using Wasserstein generative adversarial network for tooth generation and dental 3-dimensional precision printing. Eng Appl Artif Intell. 2026:114215. doi:10.1016/j.engappai.2026.114215. 【卷期待核验】.
25. Beck F, et al. Virtual occlusal analysis using interocclusal intersections. J Clin Med. 2023;12(3):996. doi:10.3390/jcm12030996.
26. He Q, et al. Evaluation of occlusal clearance in digital workflows. BMC Oral Health. 2023. doi:10.1186/s12903-023-02847-w. 【题名与卷页待最终核验】.
27. Wei H, et al. Digital evaluation of occlusal contact regions. Clin Oral Investig. 2024. doi:10.1007/s00784-024-05940-8. 【题名与卷页待最终核验】.
28. Kim, et al. Evaluation of proximal contact force. BMC Oral Health. 2025. doi:10.1186/s12903-025-05829-2. 【完整题录待核验】.
29. Kazhdan M, Hoppe H. Screened Poisson surface reconstruction. ACM Trans Graph. 2013;32(3):29. doi:10.1145/2487228.2487237. 【DOI待再次核验】.
30. Lorensen WE, Cline HE. Marching cubes: a high resolution 3D surface construction algorithm. ACM SIGGRAPH Comput Graph. 1987;21(4):163-169. doi:10.1145/37401.37422.

