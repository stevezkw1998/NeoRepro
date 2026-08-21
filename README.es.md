[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Français](README.fr.md)

# NeoRepro

> 🧪 **[Buscamos activamente revisores externos y autores de predictores.](https://github.com/stevezkw1998/NeoRepro/issues/2)**
>
> Agradecemos comprobaciones de coherencia de 15–30 minutos, intentos de reproducción, sugerencias de conjuntos de datos y críticas adversariales.

NeoRepro es un recurso de evaluación reproducible, sensible a la fuga de datos y a nivel de paciente para predictores públicos de neoantígenos péptido–HLA de MHC-I. Reúne artefactos de predictores fijados, procedencia por registro, auditorías de solapamiento con datos de entrenamiento, comparaciones sobre soporte común, incertidumbre a nivel de paciente, referencias aleatorias ajustadas al soporte y resultados generados automáticamente.

Es una contribución de referencia y recursos, no un predictor nuevo ni una afirmación de que exista un modelo universalmente ganador o de utilidad clínica.

## Por dónde empezar

- **Manuscrito actual:** [manuscrito orientado como recurso](paper/manuscript_resource.md).
- **Resumen de la evidencia en dos minutos:** [informe bilingüe para expertos](output/pdf/neorepro_expert_brief_bilingual.pdf) y [resumen de la extensión con cohorte independiente](reports/extension_summary.md).
- **Reproducir los resultados fijados:** usar el comando de la sección «Reproducción».
- **Añadir un conjunto de datos o predictor de terceros:** consultar el [plug-in contract](contracts/README.md).
- **Citar una versión fija:** [CITATION.cff](CITATION.cff) y [v0.1.0 release](https://github.com/stevezkw1998/NeoRepro/releases/tag/v0.1.0).

El contrato científico y el alcance están en [RESEARCH_SPEC.md](RESEARCH_SPEC.md).

## Estado

- Auditoría de la literatura actual: completa; decisión `RESCOPE, then GO`
- Predictores evaluados: MHCflurry 2.2.1, BigMHC v1.0, PRIME 2.0, DeepImmuno-CNN y DeepHLApan; otros siete instrumentos públicos conservan registros versionados de perfil, no comparabilidad o fallo de reproducción
- Piloto TESLA: completo; reclasificado como control positivo de solapamiento con entrenamiento
- Evaluación principal: IMPROVE, 17,475 registros tras filtrar fugas, 70 pacientes y 3 cohortes
- Inferencia principal de IMPROVE: completa; 52,425 predicciones de herramientas fijas sin registros ausentes
- Dominios externos: cohorte de vacunación Zhao y una cohorte RCC fijada por separado con 129 registros y 9 pacientes
- Interfaz de extensión reutilizable: Dataset Cards, Predictor Cards y contratos de artefactos de predicción validados por máquina
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

La extensión independiente con la cohorte de vacunación Zhao 2026 se reproduce con `make -j4 extension`. El resumen conciso de la evidencia está en [reports/extension_summary.md](reports/extension_summary.md), y el contrato congelado antes de la inferencia en [research/extension_protocol.json](research/extension_protocol.json). La extensión RCC fijada por separado está en [research/extension_protocol_rcc_v1.json](research/extension_protocol_rcc_v1.json), y las salidas exploratorias de estabilidad de tres dominios en `results/analysis/stability/`. Ambos criterios externos son posteriores a la vacunación y no deben interpretarse como presentación tumoral natural ni eficacia clínica.

## Licencia

El código y la documentación originales de NeoRepro utilizan la MIT License. Los predictores y conjuntos de datos de terceros conservan sus propias condiciones; su inclusión en el estudio no implica permiso de redistribución.
