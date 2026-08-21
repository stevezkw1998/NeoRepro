[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Français](README.fr.md)

# NeoRepro

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22037063.svg)](https://doi.org/10.5281/zenodo.22037063)

NeoRepro es un recurso de evaluación reproducible, sensible a la fuga de datos y a nivel de paciente para predictores públicos de neoantígenos péptido–HLA de MHC-I. Reúne artefactos de predictores fijados, procedencia por registro, auditorías de solapamiento con datos de entrenamiento, comparaciones sobre soporte común, incertidumbre a nivel de paciente, referencias aleatorias ajustadas al soporte y resultados generados automáticamente.

Es una contribución de referencia y recursos, no un predictor nuevo ni una afirmación de que exista un modelo universalmente ganador o de utilidad clínica.

## Por dónde empezar

- **Manuscrito actual:** [manuscrito orientado como recurso](paper/manuscript_resource.md).
- **Resumen de la evidencia en dos minutos:** [informe bilingüe para expertos](output/pdf/neorepro_expert_brief_bilingual.pdf) y [resumen de la extensión con cohorte independiente](reports/extension_summary.md).
- **Reproducir los resultados fijados:** usar el comando de la sección «Reproducción».
- **Citar una versión fija:** [CITATION.cff](CITATION.cff), [v0.1.1 release](https://github.com/stevezkw1998/NeoRepro/releases/tag/v0.1.1) y [Zenodo DOI 10.5281/zenodo.22037064](https://doi.org/10.5281/zenodo.22037064).

El contrato científico y el alcance están en [RESEARCH_SPEC.md](RESEARCH_SPEC.md).

## Estado

- Auditoría de la literatura actual: completa; decisión `RESCOPE, then GO`
- Predictores reproducidos: MHCflurry 2.2.1, BigMHC v1.0, PRIME 2.0, DeepImmuno-CNN y DeepHLApan
- Piloto TESLA: completo; reclasificado como control positivo de solapamiento con entrenamiento
- Evaluación principal: IMPROVE, 17,475 registros tras filtrar fugas, 70 pacientes y 3 cohortes
- Inferencia principal de IMPROVE: completa; 52,425 predicciones de herramientas fijas sin registros ausentes
- Manuscrito: [versión orientada como recurso](paper/manuscript_resource.md), generada a partir de resultados fijados; revisión estadística y biológica independiente completada

## Resultado principal

El suplemento oficial de PRIME2 mostró que los 520 registros del conjunto TESLA inicial eran solapamientos exactos con el entrenamiento, por lo que se conservan únicamente como control positivo de fuga. En la evaluación IMPROVE de soporte común, filtrada por solapamiento exacto y preseleccionada por presentación, PRIME obtuvo una AUROC de 0.597 y un Recall@20 medio paciente-pMHC de 0.260; BigMHC obtuvo 0.546 y 0.146. En la cohorte independiente de vacunación de Zhao, el NDCG@5 por paciente de BigMHC fue 0.658 frente a una referencia aleatoria ajustada al soporte de 0.578. DeepHLApan obtuvo 0.580 frente a 0.578, y DeepImmuno-CNN 0.755 frente a 0.759 con una cobertura del 43.8%. Estos resultados respaldan un contrato de evaluación auditable y consciente de la tarea y del soporte, no una clasificación universal.

## Reproducción

Instale [uv](https://docs.astral.sh/uv/) y reconstruya todos los análisis, figuras, tablas y artefactos del manuscrito con CPython 3.11.15 fijado por el proyecto y los archivos versionados de evaluación y predicción:

```bash
make -j4 reproduce-results
```

Make paraleliza los análisis bootstrap independientes. Use `make reproduce-results` sin `-j4` si la CPU o la memoria son limitadas. `make -j4 full-reproduce` también descarga los datos públicos fijados e instala y ejecuta predictores de terceros. Requiere aceptar expresamente las condiciones de uso exclusivamente académico de BigMHC y PRIME, varios GB de espacio en disco y un tiempo de ejecución considerablemente mayor.

## Cadena de evidencia

- **Registro científico principal:** [manuscrito actual](paper/manuscript_resource.md), [informe final](FINAL_REPORT.md) y [registro de revisión](paper/reviewer_response.md).
- **Resultados auditables:** [tabla final de resultados](results/final_results.csv), [figuras](results/figures/), [auditoría de solapamiento con entrenamiento](research/training_overlap_summary_improve.json) y [manifiesto SHA-256](results/manifest.json).
- **Planificación del envío:** [estrategia de revistas objetivo](reports/target_venues_2026-08-20.md).

La extensión independiente con la cohorte de vacunación Zhao 2026 se reproduce con `make -j4 extension`. El resumen conciso de la evidencia está en [reports/extension_summary.md](reports/extension_summary.md), y el contrato congelado antes de la inferencia en [research/extension_protocol.json](research/extension_protocol.json). El criterio externo es ELISPOT posterior a la vacunación tras administrar células dendríticas pulsadas con péptidos; no debe interpretarse como presentación tumoral natural ni eficacia clínica.

## Licencia

El código y la documentación originales de NeoRepro utilizan la MIT License. Los predictores y conjuntos de datos de terceros conservan sus propias condiciones; su inclusión en el estudio no implica permiso de redistribución.
