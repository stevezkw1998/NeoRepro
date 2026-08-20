[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Français](README.fr.md)

# NeoRepro

> 🧪 **[我們正積極徵求外部審閱者與預測器作者。](https://github.com/stevezkw1998/NeoRepro/issues/2)**
>
> 歡迎進行 15–30 分鐘的合理性檢查、重現嘗試、資料集建議與對抗性批評。

NeoRepro 是一套針對公開 MHC-I 胜肽–HLA 新抗原預測器、考量資料洩漏、病人層級且可重現的基準資源。它整合固定版本的預測器產物、逐筆資料來源、訓練資料重疊稽核、共同可評估集合比較、病人層級不確定性、依支援範圍匹配的隨機基準，以及由機器產生的結果。

本專案的貢獻是基準與研究資源，不是新的預測器，也不主張存在普遍適用的最佳模型或臨床效益。

## 從這裡開始

- **目前論文稿：**[資源定位版論文](paper/manuscript_resource.md)。
- **兩分鐘證據摘要：**[中英雙語專家簡報](output/pdf/neorepro_expert_brief_bilingual.pdf)與[獨立隊列延伸摘要](reports/extension_summary.md)。
- **重現凍結結果：**使用下方「重現」章節中的指令。
- **引用固定版本：**請參閱 [CITATION.cff](CITATION.cff) 與 [v0.1.0 release](https://github.com/stevezkw1998/NeoRepro/releases/tag/v0.1.0)。

科學研究契約與範圍請見 [RESEARCH_SPEC.md](RESEARCH_SPEC.md)。

## 狀態

- 最新文獻稽核：已完成；決策為 `RESCOPE, then GO`
- 已重現的預測器：MHCflurry 2.2.1、BigMHC v1.0、PRIME 2.0、DeepImmuno-CNN 與 DeepHLApan
- TESLA 試驗：已完成；重新歸類為訓練資料重疊陽性對照
- 主要基準：IMPROVE，17,475 筆經資料洩漏過濾的記錄、70 位病人、3 個隊列
- 主要 IMPROVE 推論：已完成；52,425 筆固定工具預測，沒有缺漏記錄
- 論文稿：[資源定位版](paper/manuscript_resource.md)，由凍結結果檔案產生；獨立統計與生物學審查皆已完成

## 主要結果

PRIME2 官方補充資料顯示，初始 TESLA 資料集的全部 520 筆記錄皆與訓練資料完全重疊，因此僅保留為資料洩漏陽性對照。在排除完全重疊、且預先依呈遞能力篩選的 IMPROVE 共同支援基準中，PRIME 的 AUROC 為 0.597，病人-pMHC 平均 Recall@20 為 0.260；BigMHC 分別為 0.546 與 0.146。在獨立 Zhao 疫苗隊列中，BigMHC 的病人 NDCG@5 為 0.658，依支援範圍匹配的隨機參考值為 0.578；DeepHLApan 為 0.580，相對的隨機參考值為 0.578；DeepImmuno-CNN 在 43.8% 覆蓋率下為 0.755，相對的隨機參考值為 0.759。這些結果支持可稽核、區分任務並考量支援範圍的評估契約，而不是通用排行榜。

## 重現

安裝 [uv](https://docs.astral.sh/uv/)，再使用專案固定的 CPython 3.11.15，從已納入版本控制的基準與預測檔案重新產生所有分析、圖表、資料表與論文產物：

```bash
make -j4 reproduce-results
```

Make 會平行執行彼此獨立的 bootstrap 分析。CPU 或記憶體受限時，請使用不含 `-j4` 的 `make reproduce-results`。`make -j4 full-reproduce` 也會下載固定版本的公開來源資料，並安裝、執行第三方預測器；此指令要求明確接受 BigMHC 與 PRIME 僅供學術使用的條款，需要數 GB 磁碟空間，且執行時間明顯更長。

## 證據鏈

- **主要科學記錄：**[目前論文稿](paper/manuscript_resource.md)、[最終報告](FINAL_REPORT.md)與[審查記錄](paper/reviewer_response.md)。
- **可稽核輸出：**[最終結果表](results/final_results.csv)、[圖表](results/figures/)、[訓練資料重疊稽核](research/training_overlap_summary_improve.json)與 [SHA-256 清單](results/manifest.json)。
- **投稿規劃：**[目標期刊策略](reports/target_venues_2026-08-20.md)。

獨立 Zhao 2026 疫苗隊列延伸可用 `make -j4 extension` 重現。簡要證據摘要位於 [reports/extension_summary.md](reports/extension_summary.md)，推論前凍結的研究契約位於 [research/extension_protocol.json](research/extension_protocol.json)。外部終點是以胜肽脈衝樹突細胞施打後的疫苗接種後 ELISPOT，不應解讀為自然腫瘤呈遞或臨床療效。

## 授權條款

NeoRepro 原創程式碼與文件採用 MIT License。第三方預測器與資料集仍適用其各自條款；納入本研究不代表取得再散布許可。
