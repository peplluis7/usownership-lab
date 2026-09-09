# Data and provenance

`processed/anchors.json` contains manually transcribed official Eurostat quantities, including the annual 2025 first EDP notification published on 22 April 2026. EU27 GDP is EUR18,826,635 million; general government expenditure, revenue and debt are 49.5%, 46.4% and 81.7% of GDP. The rounded EU resident population of 452 million is the 1 January 2026 count reported in July 2026. The two reference periods are intentionally disclosed. These are scale anchors, not an estimated behavioural calibration.

The source URLs and retrieval date are stored alongside the numbers. A separate EA20 GDP value is retained to expose denominator differences. It is not labelled as the current euro-area membership. No euro-area M3/EU27 GDP ratio is constructed.

The household microdistributions, scores, automation paths, money-demand elasticity, public-service block, income floor, investment response and other behavioural coefficients are **scenario assumptions**. Generated household data do not identify real individuals. Outputs in `results/tables` are simulated, not observations.

The original eleven input files were read and hashed, but are private and are not redistributed. Workbook cell formula/value extracts and the derived audit are included. Full article PDFs were not copied into the repository.

`python scripts/download_data.py` optionally downloads a current official Eurostat JSON-stat GDP series to `data/raw`. Network/API availability is not required for numerical reproduction. It never silently overwrites the frozen calibration anchor. New values can differ from the April 2026 vintage. Failed retrieval exits explicitly rather than inventing replacement data.
