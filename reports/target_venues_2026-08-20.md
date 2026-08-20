# NeoRepro target-venue strategy

Assessment date: 2026-08-20

## Recommendation

NeoRepro should be submitted as a **benchmarking/resource contribution**, not as a new predictor or clinical-validation paper.

Recommended route:

1. Archive the public repository and frozen result release in Zenodo, then post the manuscript as a bioRxiv preprint.
2. Submit first to **PLOS Computational Biology as a Benchmarking article** if the authors accept a higher desk-rejection risk in exchange for the best scientific visibility.
3. If the priority is acceptance efficiency rather than maximum upside, submit first to **Bioinformatics Advances as an Original Article**.
4. Use **BMC Bioinformatics** as the sound fallback. Consider **GigaScience Technical Note** only after a presubmission enquiry about restricted upstream predictor licenses.

## 1. PLOS Computational Biology — Benchmarking article

**Fit: strongest scientific expression; stretch target.**

The journal explicitly publishes designated Benchmarking articles. Its current instructions require a comprehensive or judiciously selected set of publicly available tools, practical real-world metrics, transparent training conditions, and freely reusable benchmark input and expected-output datasets. This matches NeoRepro's leakage audit, executable predictor subset, patient-level metrics, common-support policy and frozen outputs unusually well.

Official requirements: <https://journals.plos.org/ploscompbiol/s/submission-guidelines#loc-benchmarkng-submissions>

Main gates before submission:

- explain predictor selection as a *judicious executable subset*, including exclusions;
- make author-generated code, benchmark inputs and expected outputs publicly accessible under a clear license;
- obtain a Zenodo DOI and replace repository placeholders;
- add the PLOS Author Summary and venue formatting;
- clarify what can be reproduced without redistributing academic-only BigMHC/PRIME artifacts;
- have a domain expert defend biological significance beyond software engineering.

Why it can maximize contribution: the article type treats benchmarking itself as the scientific product. The complete-overlap TESLA finding, the support-matched random controls and the reusable audit contract are central evidence rather than side material.

## 2. Bioinformatics Advances — Original Article

**Fit: best balance of scope, effort and acceptance realism.**

The journal covers bioinformatics algorithms, statistics, databases and software, plus biological studies in which computational methods are essential. Current Original Article limits are eight pages, a 200-word abstract, up to 50 references, and up to six figures and six tables. The current resource manuscript is close in scale but will need venue typesetting and abstract compression.

Official scope and article requirements: <https://academic.oup.com/bioinformaticsadvances/pages/author-guidelines>

Recommended article type: **Original Article**, not Application Note. The contribution is the validated benchmark and evidence chain, not merely a software interface.

Main gates before submission:

- compress the abstract to 200 words;
- foreground the resource contract and use cases within eight pages;
- provide a permanent public repository and archival DOI;
- keep pairwise model results subordinate to leakage, support and reproducibility findings.

## 3. GigaScience — Technical Note

**Fit: thematically excellent, licensing gate uncertain.**

GigaScience Technical Notes explicitly welcome open-source computational methods and adaptations, do not require outperforming existing methods, and emphasize documentation, tests, test data and exact reproducibility. These are major NeoRepro strengths. However, the current criteria expect reviewers and readers to be able to freely download, deploy, inspect and modify the software used to reproduce examples. PRIME and BigMHC retain academic or noncommercial upstream terms and are not redistributed, so editorial confirmation is needed before investing in reformatting.

Official criteria: <https://academic.oup.com/gigascience/pages/technical_note>

Recommended action: send a short presubmission enquiry describing the open NeoRepro harness and the two externally downloaded restricted dependencies. Proceed only if the editor confirms eligibility.

## 4. BMC Bioinformatics — Research Article

**Fit: credible fallback with a validity-focused editorial threshold.**

BMC Bioinformatics considers computational algorithms, software, models and tools for biological-data analysis. Its stated policy is not to decide on perceived interest or impact; research articles are assessed for a sound question, appropriate methods and analysis, and relevant community standards. This makes it a defensible fallback for a rigorous resource whose novelty is practical rather than algorithmic.

Official scope: <https://link.springer.com/journal/12859/aims-and-scope>

Main presentation requirement: show that NeoRepro is a reusable benchmark tool with a clearly defined user community, not a one-off replication script.

## Venues not recommended now

### NAR Genomics and Bioinformatics — Methods and Benchmark Surveys

The subject match is strong, but the current criteria say benchmarked components must meet its software requirements and that benchmark results on non-open-source software will not be published. PRIME's academic noncommercial terms and lack of redistribution permission create a direct eligibility risk. The journal also states that benchmark-survey authors generally need a publication track record in the field.

Official criteria: <https://academic.oup.com/nargab/pages/scope_and_criteria>

### Journal of Open Source Software

JOSS is a possible later companion route for the software, not the current results paper. Current requirements say the paper must not focus on new research results and privately developed projects need at least six months of public development history, with community-facing development evidence. NeoRepro should first be released, documented and used externally.

Official requirements: <https://joss.readthedocs.io/en/latest/submitting.html>

## Final choice

- **Maximum scientific upside:** PLOS Computational Biology Benchmarking article → Bioinformatics Advances transfer/resubmission if rejected.
- **Best time-to-publication tradeoff:** Bioinformatics Advances Original Article → BMC Bioinformatics fallback.
- **Best long-term asset strategy:** publish the research paper now, then consider a separate JOSS software paper only after sustained public use and development.
