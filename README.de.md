[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Français](README.fr.md)

# NeoRepro

> 🧪 **[Wir suchen aktiv externe Gutachterinnen und Gutachter sowie Autorinnen und Autoren von Prädiktoren.](https://github.com/stevezkw1998/NeoRepro/issues/2)**
>
> Plausibilitätsprüfungen von 15–30 Minuten, Reproduktionsversuche, Datensatzvorschläge und kritische Gegenprüfungen sind willkommen.

NeoRepro ist eine reproduzierbare, patientenbezogene Benchmark-Ressource für öffentliche MHC-I-Peptid–HLA-Neoantigen-Prädiktoren unter Berücksichtigung von Datenlecks. Sie bündelt festgeschriebene Prädiktor-Artefakte, Provenienz auf Datensatzebene, Prüfungen auf Überschneidungen mit Trainingsdaten, Vergleiche auf einer gemeinsamen Auswertungsmenge, patientenbezogene Unsicherheit, an die Abdeckung angepasste Zufallsreferenzen und maschinell erzeugte Ergebnisse.

Der Beitrag ist eine Benchmark- und Forschungsressource, kein neuer Prädiktor und keine Behauptung eines universell besten Modells oder klinischen Nutzens.

## Einstieg

- **Aktuelles Manuskript:** [als Ressource positioniertes Manuskript](paper/manuscript_resource.md).
- **Evidenz in zwei Minuten:** [zweisprachige Expertenübersicht](output/pdf/neorepro_expert_brief_bilingual.pdf) und [Zusammenfassung der unabhängigen Kohortenerweiterung](reports/extension_summary.md).
- **Festgeschriebene Ergebnisse reproduzieren:** den Befehl im Abschnitt „Reproduktion“ verwenden.
- **Eigenen Prädiktor benchmarken:** `neorepro benchmark predictions.csv --output-dir neorepro-results` ausführen; siehe [Standardvertrag für eine einzelne Datei](contracts/README.md).
- **Drittanbieter-Datensatz oder -Prädiktor hinzufügen:** den [plug-in contract](contracts/README.md) verwenden.
- **Feste Version zitieren:** [CITATION.cff](CITATION.cff) und [v0.1.0 release](https://github.com/stevezkw1998/NeoRepro/releases/tag/v0.1.0).

Der wissenschaftliche Vertrag und Umfang stehen in [RESEARCH_SPEC.md](RESEARCH_SPEC.md).

## Status

- Aktuelle Literaturprüfung: abgeschlossen; Entscheidung `RESCOPE, then GO`
- Benchmark-Prädiktoren: MHCflurry 2.2.1, BigMHC v1.0, PRIME 2.0, DeepImmuno-CNN und DeepHLApan; für sieben weitere öffentliche Werkzeuge liegen versionierte Profil-, Nichtvergleichbarkeits- oder Fehlschlagsnachweise vor
- TESLA-Pilot: abgeschlossen; als Positivkontrolle für Trainingsdatenüberschneidung neu eingestuft
- Primärer Benchmark: IMPROVE, 17,475 nach Leakage-Filterung verbleibende Datensätze, 70 Patienten, 3 Kohorten
- Primäre IMPROVE-Inferenz: abgeschlossen; 52,425 Vorhersagen fester Werkzeuge ohne fehlende Datensätze
- Externe Domänen: Zhao-Impfkohorte sowie eine separat festgeschriebene RCC-Impfkohorte mit 129 Datensätzen und 9 Patienten
- Wiederverwendbare Erweiterungsschnittstelle: maschinell validierte Dataset Cards, Predictor Cards und Verträge für Vorhersageartefakte
- Manuskript: [Ressourcenfassung](paper/manuscript_resource.md), aus festgeschriebenen Ergebnisdateien erzeugt; unabhängige statistische und biologische Prüfung abgeschlossen

## Hauptergebnis

Die offizielle PRIME2-Ergänzung zeigte, dass alle 520 Datensätze der anfänglichen TESLA-Testmenge exakte Trainingsüberschneidungen waren; sie bleiben daher nur als Leakage-Positivkontrolle erhalten. Im auf exakte Überschneidungen gefilterten und nach Präsentation vorselektierten gemeinsamen IMPROVE-Benchmark erreichte PRIME eine AUROC von 0.597 und einen mittleren patientenbezogenen pMHC-Recall@20 von 0.260; BigMHC erreichte 0.546 beziehungsweise 0.146. In der unabhängigen Zhao-Impfkohorte betrug der patientenbezogene NDCG@5 für BigMHC 0.658 gegenüber einer an die Abdeckung angepassten Zufallsreferenz von 0.578. DeepHLApan erreichte 0.580 gegenüber 0.578, DeepImmuno-CNN bei 43.8% Abdeckung 0.755 gegenüber 0.759. Die Ergebnisse stützen einen prüfbaren, auf Aufgabe und Auswertungsmenge abgestimmten Bewertungsvertrag, keine universelle Rangliste.

## Reproduktion

[uv](https://docs.astral.sh/uv/) installieren und anschließend mit dem im Projekt festgeschriebenen CPython 3.11.15 alle Analysen, Abbildungen, Tabellen und Manuskriptartefakte aus den versionierten Benchmark- und Vorhersagedateien neu erzeugen:

```bash
make -j4 reproduce-results
```

Unabhängige bootstrap-Analysen werden von Make parallelisiert. Bei begrenzter CPU oder begrenztem Arbeitsspeicher `make reproduce-results` ohne `-j4` verwenden. `make -j4 full-reproduce` lädt zusätzlich die festgeschriebenen öffentlichen Quelldaten herunter und installiert bzw. startet die Prädiktoren Dritter. Dafür müssen die ausschließlich akademischen Bedingungen von BigMHC und PRIME ausdrücklich akzeptiert werden; außerdem sind mehrere GB Speicherplatz und eine deutlich längere Laufzeit erforderlich.

## Evidenzkette

- **Primärer wissenschaftlicher Nachweis:** [aktuelles Manuskript](paper/manuscript_resource.md), [Abschlussbericht](FINAL_REPORT.md) und [Prüfprotokoll](paper/reviewer_response.md).
- **Prüfbare Ausgaben:** [endgültige Ergebnistabelle](results/final_results.csv), [Abbildungen](results/figures/), [Prüfung auf Trainingsüberschneidungen](research/training_overlap_summary_improve.json) und [SHA-256-Manifest](results/manifest.json).
- **Publikationsplanung:** [Strategie für Zielzeitschriften](reports/target_venues_2026-08-20.md).

Die unabhängige Erweiterung um die Zhao 2026-Impfkohorte lässt sich mit `make -j4 extension` reproduzieren. Die kompakte Evidenzübersicht steht in [reports/extension_summary.md](reports/extension_summary.md), der vor der Inferenz festgeschriebene Studienvertrag in [research/extension_protocol.json](research/extension_protocol.json). Die separat festgeschriebene RCC-Erweiterung steht in [research/extension_protocol_rcc_v1.json](research/extension_protocol_rcc_v1.json), explorative Stabilitätsausgaben für drei Domänen unter `results/analysis/stability/`. Beide externen Endpunkte wurden nach der Impfung erhoben und dürfen nicht als natürliche Tumorpräsentation oder klinische Wirksamkeit interpretiert werden.

## Lizenz

Der ursprüngliche Code und die Dokumentation von NeoRepro stehen unter der MIT License. Für Prädiktoren und Datensätze Dritter gelten weiterhin deren eigene Bedingungen; die Aufnahme in die Studie bedeutet keine Erlaubnis zur Weiterverbreitung.
