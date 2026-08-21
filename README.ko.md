[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Français](README.fr.md)

# NeoRepro

> 🧪 **[외부 검토자와 예측기 개발자를 적극적으로 찾고 있습니다.](https://github.com/stevezkw1998/NeoRepro/issues/2)**
>
> 15–30분의 타당성 점검, 재현 시도, 데이터셋 제안 및 비판적 검토를 환영합니다.

NeoRepro는 공개 MHC-I 펩타이드–HLA 신생항원 예측기를 위한 데이터 누출 인지형, 환자 수준, 재현 가능한 벤치마크 리소스입니다. 고정된 예측기 아티팩트, 레코드 수준 출처, 학습 데이터 중복 감사, 공통 평가 가능 집합 비교, 환자 수준 불확실성, 지원 범위를 맞춘 무작위 기준선 및 기계 생성 결과를 제공합니다.

이 프로젝트는 새로운 예측기가 아니라 벤치마크/리소스 기여이며, 보편적인 최우수 모델이나 임상적 유용성을 주장하지 않습니다.

## 시작하기

- **현재 원고:** [리소스 중심 원고](paper/manuscript_resource.md).
- **간단한 증거 요약:** [중영 이중언어 전문가 요약](output/pdf/neorepro_expert_brief_bilingual.pdf)과 [독립 코호트 확장 요약](reports/extension_summary.md).
- **고정 결과 재현:** 아래 재현 절의 명령을 사용하십시오.
- **제3자 데이터셋 또는 예측기 추가:** [plug-in contract](contracts/README.md)를 참조하십시오.
- **고정 버전 인용:** [CITATION.cff](CITATION.cff)와 [v0.1.0 release](https://github.com/stevezkw1998/NeoRepro/releases/tag/v0.1.0)를 참조하십시오.

과학적 연구 계약과 범위는 [RESEARCH_SPEC.md](RESEARCH_SPEC.md)를 참조하십시오.

## 상태

- 최신 문헌 감사: 완료, 결정은 `RESCOPE, then GO`
- 벤치마크 예측기: MHCflurry 2.2.1, BigMHC v1.0, PRIME 2.0, DeepImmuno-CNN, DeepHLApan. 추가로 일곱 공개 도구의 프로필 전용, 비교 불가 또는 재현 실패 기록을 버전 관리
- TESLA 파일럿: 완료, 학습 데이터 중복 양성 대조군으로 재분류
- 주요 벤치마크: IMPROVE, 누출 필터링 후 17,475개 레코드, 70명 환자, 세 개 코호트
- 주요 IMPROVE 추론: 완료, 고정 도구 예측 52,425개, 누락 레코드 없음
- 외부 도메인: Zhao 백신 코호트와 별도로 고정한 129개 레코드·9명 환자의 RCC 백신 코호트
- 재사용 가능한 확장 인터페이스: 기계 검증된 Dataset Card, Predictor Card 및 예측 아티팩트 계약
- 원고: [리소스 중심 버전](paper/manuscript_resource.md), 고정 결과 파일에서 생성, 독립 통계 및 생물학 검토 완료

## 주요 결과

PRIME2 공식 보충자료에서 초기 TESLA 픽스처의 520개 레코드 모두가 학습 데이터와 정확히 중복됨을 확인하여 누출 양성 대조군으로만 유지했습니다. 정확한 중복을 제거하고 제시 가능성으로 사전 선별한 IMPROVE 공통 벤치마크에서 PRIME은 AUROC 0.597과 평균 환자-pMHC Recall@20 0.260을, BigMHC는 각각 0.546과 0.146을 기록했습니다. 독립 Zhao 백신 코호트에서 BigMHC 환자 NDCG@5는 0.658, 지원 범위를 맞춘 무작위 참조는 0.578이었습니다. DeepHLApan은 0.580 대 0.578, DeepImmuno-CNN은 43.8% 범위에서 0.755 대 0.759였습니다. 이 결과는 보편적 순위표가 아니라 감사 가능하고 과제와 지원 범위를 명시하는 평가 계약을 지지합니다.

## 재현

[uv](https://docs.astral.sh/uv/)를 설치한 뒤 프로젝트에 고정된 CPython 3.11.15와 버전 관리된 벤치마크 및 예측 파일로 모든 분석, 그림, 표, 원고 아티팩트를 다시 생성합니다.

```bash
make -j4 reproduce-results
```

독립 bootstrap 분석은 Make가 병렬 처리합니다. CPU 또는 메모리가 제한되면 `-j4` 없이 `make reproduce-results`를 사용하십시오. `make -j4 full-reproduce`는 고정된 공개 원천 데이터를 내려받고 외부 예측기도 설치·실행합니다. BigMHC와 PRIME의 학술 전용 조건에 명시적으로 동의해야 하며, 수 GB의 디스크 공간과 훨씬 긴 실행 시간이 필요합니다.

## 증거 체계

- **주요 과학 기록:** [현재 원고](paper/manuscript_resource.md), [최종 보고서](FINAL_REPORT.md), [검토 기록](paper/reviewer_response.md).
- **감사 가능한 출력:** [최종 결과표](results/final_results.csv), [그림](results/figures/), [학습 데이터 중복 감사](research/training_overlap_summary_improve.json), [SHA-256 매니페스트](results/manifest.json).
- **투고 계획:** [대상 저널 전략](reports/target_venues_2026-08-20.md).

독립 Zhao 2026 백신 코호트 확장은 `make -j4 extension`으로 재현할 수 있습니다. 간결한 증거 요약은 [reports/extension_summary.md](reports/extension_summary.md), 추론 전에 고정한 연구 계약은 [research/extension_protocol.json](research/extension_protocol.json)에 있습니다. 별도로 고정한 RCC 확장은 [research/extension_protocol_rcc_v1.json](research/extension_protocol_rcc_v1.json), 세 도메인 탐색적 안정성 출력은 `results/analysis/stability/`에 있습니다. 두 외부 종말점 모두 백신 접종 후 측정이며 자연 종양 제시나 임상 효능으로 해석해서는 안 됩니다.

## 라이선스

NeoRepro의 원본 코드와 문서는 MIT License를 사용합니다. 외부 예측기와 데이터셋에는 각자의 조건이 그대로 적용되며, 연구에 포함되었다고 재배포가 허용되는 것은 아닙니다.
