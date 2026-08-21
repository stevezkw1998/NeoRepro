[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Français](README.fr.md)

# NeoRepro

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22037063.svg)](https://doi.org/10.5281/zenodo.22037063)

NeoRepro est une ressource d’évaluation reproductible, tenant compte des fuites de données et menée au niveau du patient, pour les prédicteurs publics de néoantigènes peptide–HLA de MHC-I. Elle rassemble des artefacts de prédicteurs épinglés, la provenance de chaque enregistrement, des audits de chevauchement avec les données d’entraînement, des comparaisons sur un support commun, l’incertitude au niveau du patient, des références aléatoires adaptées au support et des résultats générés automatiquement.

Il s’agit d’une contribution de type ressource et benchmark, et non d’un nouveau prédicteur ni d’une affirmation concernant un modèle universellement gagnant ou une utilité clinique.

## Pour commencer

- **Manuscrit actuel :** [manuscrit positionné comme ressource](paper/manuscript_resource.md).
- **Synthèse des preuves en deux minutes :** [note bilingue pour experts](output/pdf/neorepro_expert_brief_bilingual.pdf) et [résumé de l’extension sur une cohorte indépendante](reports/extension_summary.md).
- **Reproduire les résultats figés :** utiliser la commande de la section « Reproduction » ci-dessous.
- **Citer une version figée :** [CITATION.cff](CITATION.cff), [v0.1.1 release](https://github.com/stevezkw1998/NeoRepro/releases/tag/v0.1.1) et [Zenodo DOI 10.5281/zenodo.22037064](https://doi.org/10.5281/zenodo.22037064).

Le contrat scientifique et le périmètre sont décrits dans [RESEARCH_SPEC.md](RESEARCH_SPEC.md).

## État

- Audit de la littérature actuelle : terminé ; décision `RESCOPE, then GO`
- Prédicteurs reproduits : MHCflurry 2.2.1, BigMHC v1.0, PRIME 2.0, DeepImmuno-CNN et DeepHLApan
- Pilote TESLA : terminé ; reclassé comme contrôle positif de chevauchement avec l’entraînement
- Benchmark principal : IMPROVE, 17,475 enregistrements après filtrage des fuites, 70 patients et 3 cohortes
- Inférence IMPROVE principale : terminée ; 52,425 prédictions d’outils fixes sans enregistrement manquant
- Manuscrit : [version positionnée comme ressource](paper/manuscript_resource.md), générée à partir des résultats figés ; revues statistique et biologique indépendantes terminées

## Résultat principal

Le supplément officiel de PRIME2 a montré que les 520 enregistrements du jeu TESLA initial correspondaient exactement aux données d’entraînement ; ils ne sont donc conservés que comme contrôle positif de fuite. Sur le benchmark commun IMPROVE, filtré pour exclure les chevauchements exacts et présélectionné selon la présentation, PRIME a obtenu une AUROC de 0.597 et un Recall@20 patient-pMHC moyen de 0.260 ; BigMHC a obtenu respectivement 0.546 et 0.146. Dans la cohorte vaccinale indépendante de Zhao, le NDCG@5 par patient de BigMHC était de 0.658, contre une référence aléatoire adaptée au support de 0.578. DeepHLApan obtenait 0.580 contre 0.578, et DeepImmuno-CNN 0.755 contre 0.759 avec une couverture de 43.8%. Ces résultats soutiennent un contrat d’évaluation auditable, explicite sur la tâche et le support, et non un classement universel.

## Reproduction

Installez [uv](https://docs.astral.sh/uv/), puis reconstruisez toutes les analyses, figures, tables et tous les artefacts du manuscrit avec CPython 3.11.15 épinglé par le projet et les fichiers de benchmark et de prédiction versionnés :

```bash
make -j4 reproduce-results
```

Make parallélise les analyses bootstrap indépendantes. Utilisez `make reproduce-results` sans `-j4` si les ressources CPU ou mémoire sont limitées. `make -j4 full-reproduce` télécharge également les données sources publiques épinglées, puis installe et exécute les prédicteurs tiers. Cette commande exige l’acceptation explicite des conditions d’utilisation académique de BigMHC et PRIME, plusieurs GB d’espace disque et une durée d’exécution nettement supérieure.

## Chaîne de preuves

- **Dossier scientifique principal :** [manuscrit actuel](paper/manuscript_resource.md), [rapport final](FINAL_REPORT.md) et [dossier de revue](paper/reviewer_response.md).
- **Sorties auditables :** [table finale des résultats](results/final_results.csv), [figures](results/figures/), [audit du chevauchement avec l’entraînement](research/training_overlap_summary_improve.json) et [manifeste SHA-256](results/manifest.json).
- **Planification de la soumission :** [stratégie des revues cibles](reports/target_venues_2026-08-20.md).

L’extension indépendante sur la cohorte vaccinale Zhao 2026 est reproduite avec `make -j4 extension`. La synthèse concise des preuves se trouve dans [reports/extension_summary.md](reports/extension_summary.md), et le contrat figé avant l’inférence dans [research/extension_protocol.json](research/extension_protocol.json). Le critère externe est un ELISPOT après vaccination et administration de cellules dendritiques chargées en peptides ; il ne doit pas être interprété comme une présentation tumorale naturelle ni comme une efficacité clinique.

## Licence

Le code et la documentation d’origine de NeoRepro utilisent la MIT License. Les prédicteurs et jeux de données tiers restent soumis à leurs propres conditions ; leur inclusion dans l’étude n’implique pas une autorisation de redistribution.
