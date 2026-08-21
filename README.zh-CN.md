[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Français](README.fr.md)

# NeoRepro

> 🧪 **[我们正在积极寻找外部审阅者和预测器作者。](https://github.com/stevezkw1998/NeoRepro/issues/2)**
>
> 欢迎进行 15–30 分钟的合理性检查、复现尝试、数据集建议和对抗性批评。

NeoRepro 是面向公开 MHC-I 肽–HLA 新抗原预测器的泄漏感知、患者级、可复现基准资源。它整合了固定版本的预测器工件、逐记录来源、训练数据重叠审计、共同支持集比较、患者级不确定性、支持集匹配的随机基线以及机器生成的结果。

本项目贡献的是基准与研究资源，而不是新的预测器，也不宣称存在普适的最佳模型或临床效用。

## 从这里开始

- **当前论文稿：**[资源定位版论文](paper/manuscript_resource.md)。
- **两分钟证据摘要：**[中英双语专家简报](output/pdf/neorepro_expert_brief_bilingual.pdf)和[独立队列扩展摘要](reports/extension_summary.md)。
- **复现冻结结果：**使用下方“复现”部分中的命令。
- **接入第三方数据集或预测器：**请参阅 [plug-in contract](contracts/README.md)。
- **引用固定版本：**参见 [CITATION.cff](CITATION.cff) 和 [v0.1.0 release](https://github.com/stevezkw1998/NeoRepro/releases/tag/v0.1.0)。

科学研究契约与范围见 [RESEARCH_SPEC.md](RESEARCH_SPEC.md)。

## 状态

- 最新文献审计：已完成；结论为 `RESCOPE, then GO`
- 已纳入基准的预测器：MHCflurry 2.2.1、BigMHC v1.0、PRIME 2.0、DeepImmuno-CNN 和 DeepHLApan；另有七个公开工具保留了仅档案、不可比较或复现失败的版本化记录
- TESLA 试点：已完成；重新归类为训练数据重叠阳性对照
- 主要基准：IMPROVE，17,475 条经过泄漏过滤的记录、70 名患者、3 个队列
- 主要 IMPROVE 推理：已完成；52,425 条固定工具预测，无缺失记录
- 外部领域：Zhao 疫苗队列，以及单独冻结的 RCC 疫苗队列（129 条记录、9 名患者）
- 可复用扩展接口：经机器验证的 Dataset Card、Predictor Card 和预测工件契约
- 论文稿：[资源定位版](paper/manuscript_resource.md)，由冻结结果文件生成；独立统计学与生物学审查均已完成

## 主要结果

PRIME2 官方补充材料显示，初始 TESLA 数据集的全部 520 条记录都与训练数据完全重叠，因此仅保留为泄漏阳性对照。在经过完全重叠过滤、且预先按呈递能力筛选的 IMPROVE 共同支持基准上，PRIME 的 AUROC 为 0.597，患者-pMHC 平均 Recall@20 为 0.260；BigMHC 分别为 0.546 和 0.146。在独立 Zhao 疫苗队列中，BigMHC 的患者 NDCG@5 为 0.658，而支持集匹配的随机参照为 0.578；DeepHLApan 为 0.580，对应随机参照为 0.578；DeepImmuno-CNN 在 43.8% 覆盖率下为 0.755，对应随机参照为 0.759。这些结果支持一种可审计、区分任务并关注支持集的评估契约，而不是通用排行榜。

## 复现

安装 [uv](https://docs.astral.sh/uv/)，然后使用项目固定的 CPython 3.11.15，从已版本化的基准与预测文件重新生成全部分析、图表、结果表和论文工件：

```bash
make -j4 reproduce-results
```

Make 会并行执行相互独立的 bootstrap 分析。在 CPU 或内存受限时，请使用不带 `-j4` 的 `make reproduce-results`。`make -j4 full-reproduce` 还会下载固定版本的公开源数据，并安装、运行第三方预测器；该命令要求明确接受 BigMHC 和 PRIME 仅限学术使用的条款，需要数 GB 磁盘空间，并且运行时间明显更长。

## 证据链

- **主要科学记录：**[当前论文稿](paper/manuscript_resource.md)、[最终报告](FINAL_REPORT.md)和[审查记录](paper/reviewer_response.md)。
- **可审计输出：**[最终结果表](results/final_results.csv)、[图表](results/figures/)、[训练数据重叠审计](research/training_overlap_summary_improve.json)和 [SHA-256 清单](results/manifest.json)。
- **投稿规划：**[目标期刊策略](reports/target_venues_2026-08-20.md)。

独立 Zhao 2026 疫苗队列扩展可通过 `make -j4 extension` 复现。简要证据摘要见 [reports/extension_summary.md](reports/extension_summary.md)，推理前冻结的研究契约见 [research/extension_protocol.json](research/extension_protocol.json)。单独冻结的 RCC 扩展记录在 [research/extension_protocol_rcc_v1.json](research/extension_protocol_rcc_v1.json)，三领域探索性稳定性输出位于 `results/analysis/stability/`。两个外部终点均为疫苗接种后检测，不应解读为自然肿瘤呈递或临床疗效。

## 许可证

NeoRepro 原创代码和文档采用 MIT License。第三方预测器和数据集仍受其各自条款约束；纳入本研究不代表获得再分发许可。
