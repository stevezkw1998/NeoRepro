你要从零自主完成 NeoRepro：

目标：
建立一个公开 neoantigen predictor 的
reproducibility + patient-level benchmark。

最终必须交付：
1. GitHub-ready repo
2. predictor registry
3. harmonized benchmark dataset
4. reproducible predictor adapters
5. experiments + statistics + figures
6. complete English research paper/preprint

核心研究问题：
- 公开 predictor 到底还能不能复现？
- 统一 benchmark 后排名是否改变？
- patient-held-out / study-held-out 下性能如何？
- AUROC 是否能反映患者 Top-K neoantigen prioritization？
- 是否存在 leakage / HLA / study bias？

原则：
- 不预设结论。
- novelty 不够时自行重新 scope。
- predictor 跑不起来也要记录，失败本身是结果。
- 优先公开数据和 CPU，额外成本尽量 <$50。
- 不允许虚构 citation、实验、数字或 biological conclusion。
- computational result 不得宣称改善临床疗效。
- 除登录、授权、付费等真正 blocker 外，不要询问我下一步。
- 遇到失败自行 debug 并继续。

你可以使用 OPENAI_API_KEY 和 ANTHROPIC_API_KEY，
但不得暴露、打印或 commit key。

首先：
1. 初始化 repo
2. 创建 RESEARCH_SPEC.md 和 AGENTS.md
3. 做最新 literature + novelty audit
4. 决定最终 scope
5. 做 cheap pilot
6. pilot 可行后完整执行
7. 最终完成 repo + data + paper

持续执行，不要只给计划。