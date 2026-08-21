[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Français](README.fr.md)

# NeoRepro

> 🧪 **[外部レビュアーおよび予測器の作者を積極的に募集しています。](https://github.com/stevezkw1998/NeoRepro/issues/2)**
>
> 15–30 分の妥当性確認、再現の試行、データセットの提案、批判的な検証を歓迎します。

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22037063.svg)](https://doi.org/10.5281/zenodo.22037063)

NeoRepro は、公開されている MHC-I ペプチド–HLA ネオアンチゲン予測器を対象とした、リーケージを考慮した患者単位の再現可能なベンチマークリソースです。固定された予測器アーティファクト、レコード単位の来歴、学習データ重複監査、共通評価可能集合での比較、患者単位の不確実性、評価可能範囲を一致させたランダムベースライン、および機械生成結果をまとめています。

本プロジェクトはベンチマーク／リソースとしての貢献であり、新しい予測器ではありません。また、普遍的に最良のモデルや臨床的有用性を主張するものでもありません。

## はじめに

- **現行原稿：**[リソースとして位置付けた原稿](paper/manuscript_resource.md)。
- **短時間で読めるエビデンス概要：**[中英併記の専門家向け概要](output/pdf/neorepro_expert_brief_bilingual.pdf)および[独立コホート拡張の概要](reports/extension_summary.md)。
- **凍結済み結果の再現：**下記「再現」節のコマンドを使用してください。
- **独自予測器のベンチマーク：**`neorepro benchmark predictions.csv --output-dir neorepro-results` を実行し、[標準単一ファイル契約](contracts/README.md)を参照してください。
- **第三者データセットまたは予測器の追加：**[plug-in contract](contracts/README.md) を参照してください。
- **固定版の引用：**[CITATION.cff](CITATION.cff)、[v0.1.1 release](https://github.com/stevezkw1998/NeoRepro/releases/tag/v0.1.1)、および [Zenodo DOI 10.5281/zenodo.22037064](https://doi.org/10.5281/zenodo.22037064)を参照してください。

科学的な研究契約と範囲については [RESEARCH_SPEC.md](RESEARCH_SPEC.md) を参照してください。

## 状況

- 最新文献監査：完了、判断は `RESCOPE, then GO`
- ベンチマーク対象予測器：MHCflurry 2.2.1、BigMHC v1.0、PRIME 2.0、DeepImmuno-CNN、DeepHLApan。さらに七つの公開ツールについて、プロファイル限定、比較不能、または再現失敗の記録をバージョン管理
- TESLA パイロット：完了、学習データ重複の陽性対照として再分類
- 主要ベンチマーク：IMPROVE、リーケージ除外後 17,475 レコード、70 患者、3 コホート
- 主要 IMPROVE 推論：完了、固定ツールによる 52,425 予測、欠損レコードなし
- 外部ドメイン：Zhao ワクチンコホートと、別途凍結した 129 レコード・9 患者の RCC ワクチンコホート
- 再利用可能な拡張インターフェース：機械検証済み Dataset Card、Predictor Card、予測アーティファクト契約
- 原稿：[リソース位置付け版](paper/manuscript_resource.md)、凍結結果ファイルから生成、独立した統計学・生物学レビュー済み

## 主な結果

PRIME2 の公式補足資料から、初期 TESLA フィクスチャの全 520 レコードが学習データと完全に重複していることが判明したため、リーケージ陽性対照としてのみ保持しました。完全重複を除外し、提示能で事前選択された IMPROVE の共通評価ベンチマークでは、PRIME の AUROC は 0.597、患者-pMHC 平均 Recall@20 は 0.260 であり、BigMHC はそれぞれ 0.546 と 0.146 でした。独立した Zhao ワクチンコホートでは、BigMHC の患者 NDCG@5 は 0.658、評価可能範囲を一致させたランダム参照は 0.578 でした。DeepHLApan は 0.580 対 0.578、DeepImmuno-CNN は 43.8% のカバレッジで 0.755 対 0.759 でした。これらの結果は、普遍的なランキングではなく、監査可能でタスクと評価可能範囲を明示する評価契約を支持します。

## 再現

[uv](https://docs.astral.sh/uv/) をインストールし、プロジェクトで固定した CPython 3.11.15 とバージョン管理済みのベンチマーク／予測ファイルを使って、すべての解析、図、表、原稿アーティファクトを再構築します。

```bash
make -j4 reproduce-results
```

独立した bootstrap 解析は Make により並列化されます。CPU またはメモリが限られる場合は、`-j4` を付けずに `make reproduce-results` を使用してください。`make -j4 full-reproduce` は、固定された公開元データのダウンロードと第三者予測器のインストール／実行も行います。BigMHC と PRIME の学術利用限定条件への明示的な同意、数 GB のディスク容量、および大幅に長い実行時間が必要です。

## エビデンスチェーン

- **主要な科学記録：**[現行原稿](paper/manuscript_resource.md)、[最終報告](FINAL_REPORT.md)、[レビュー記録](paper/reviewer_response.md)。
- **監査可能な出力：**[最終結果表](results/final_results.csv)、[図](results/figures/)、[学習データ重複監査](research/training_overlap_summary_improve.json)、[SHA-256 マニフェスト](results/manifest.json)。
- **投稿計画：**[投稿先戦略](reports/target_venues_2026-08-20.md)。

独立した Zhao 2026 ワクチンコホート拡張は `make -j4 extension` で再現できます。簡潔なエビデンス概要は [reports/extension_summary.md](reports/extension_summary.md)、推論前に凍結した研究契約は [research/extension_protocol.json](research/extension_protocol.json) にあります。別途凍結した RCC 拡張は [research/extension_protocol_rcc_v1.json](research/extension_protocol_rcc_v1.json)、三ドメインの探索的安定性出力は `results/analysis/stability/` にあります。両外部エンドポイントはワクチン接種後の測定であり、自然な腫瘍提示や臨床効果を示すものではありません。

## ライセンス

NeoRepro の独自コードと文書には MIT License が適用されます。第三者の予測器とデータセットにはそれぞれの条件が引き続き適用され、本研究への収載は再配布許可を意味しません。
