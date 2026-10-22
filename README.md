# SpaceX Falcon 9 landing analysis

This repository contains a reproducible analysis and presentation for the IBM Applied Data Science Capstone. The question is whether information available before a Falcon 9 launch can help predict if its first stage will land successfully.

## Results

- The released 90-launch dataset contains 60 successful first-stage landings (66.7%).
- Site success rates in this snapshot are 33/55 at CCAFS SLC 40, 17/22 at KSC LC 39A, and 10/13 at VAFB SLC 4E.
- Four classification methods were compared with stratified five-fold cross-validation and a held-out 18-launch test set. The highest cross-validation accuracy was 83.4% for the shallow decision tree. Its test accuracy was 77.8%, compared with a 66.7% majority-class baseline. On the test set it missed four successful landings and produced no false positives.
- These are descriptive results for a small historical course dataset, not a current operational launch forecast.

## Files

| File | Purpose |
| --- | --- |
| `Data Science Capstone Project Report.pdf` | 38-slide report with the methods, charts, SQL findings, dashboard results, model comparison, and conclusions. |
| `capstone_analysis.ipynb` | Notebook to inspect the released datasets, reproduce summary statistics, SQL examples, and model results. |
| `analyze.py` | Reproducible analysis and model comparison. Writes `analysis_results.json`. |
| `visuals.py` | Builds the Folium map and Plotly Dash-style standalone dashboard. |
| `build_report.py` | Builds the PDF report from the saved analysis. |
| `dataset_part_2.csv`, `dataset_part_3.csv`, `spacex_launch_dash.csv`, `Spacex.csv` | IBM Skills Network course dataset snapshots. |
| `launch_sites_map.html`, `launch_dashboard.html` | Interactive views. Open locally in a browser. |
| `dashboard_*.png` | Dashboard screenshots used in the report. |

## Reproduce

With Python 3.10+ and the packages in `requirements.txt`:

```bash
python -m pip install -r requirements.txt
python analyze.py
python visuals.py
python build_report.py
```

The notebook can be opened in Jupyter after installing the same requirements. The analysis scripts read the CSV snapshots in this repository. The SpaceX API request did not complete in the authoring environment, so this project does **not** claim a fresh live API extraction or a fresh Wikipedia scrape. The report describes those course collection methods and performs the quantitative analysis on the published IBM snapshots.

## Data provenance

The CSVs are from the public IBM Skills Network Applied Data Science Capstone course materials. The official course project asks learners to use SpaceX API data, web scraping, SQL, Folium, Plotly Dash, and classification models. This repository retains the source data beside the code so the reported figures can be reproduced exactly.
