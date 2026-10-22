"""Build a short, executable companion notebook for the capstone analysis."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def cell(kind: str, body: str) -> dict:
    output = {"cell_type": kind, "metadata": {}, "source": body.splitlines(keepends=True)}
    if kind == "code":
        output.update(execution_count=None, outputs=[])
    return output


cells = [
    cell("markdown", "# SpaceX Falcon 9 landing analysis\n\nA reproducible companion to the final project report. The analysis uses the IBM Skills Network course snapshots in this repository; it does not present them as a fresh live API pull."),
    cell("code", "from pathlib import Path\nimport json\nimport sqlite3\nimport pandas as pd\nimport numpy as np\nROOT = Path.cwd()\nlaunches = pd.read_csv(ROOT / 'dataset_part_2.csv')\nfeatures = pd.read_csv(ROOT / 'dataset_part_3.csv')\ndashboard = pd.read_csv(ROOT / 'spacex_launch_dash.csv')\nsql_data = pd.read_csv(ROOT / 'Spacex.csv')\nprint({name: frame.shape for name, frame in [('launches', launches), ('features', features), ('dashboard', dashboard), ('sql', sql_data)]})"),
    cell("markdown", "## Clean and inspect the released launch data\n\nCheck duplicate flight numbers, missing values, and the binary landing outcome before interpreting rates."),
    cell("code", "print('Duplicate flight numbers:', launches['FlightNumber'].duplicated().sum())\nprint('Landing outcome counts:')\nprint(launches['Class'].value_counts(dropna=False))\nprint('Most missing fields:')\nprint(launches.isna().sum().sort_values(ascending=False).head(10))"),
    cell("markdown", "## Exploratory data analysis\n\nThe grouped statistics below produce the launch-site and year comparisons in the presentation."),
    cell("code", "launches['Year'] = pd.to_datetime(launches['Date']).dt.year\nsite_stats = launches.groupby('LaunchSite')['Class'].agg(['count', 'sum', 'mean'])\nyear_stats = launches.groupby('Year')['Class'].agg(['count', 'sum', 'mean'])\ndisplay(site_stats, year_stats)"),
    cell("code", "ax = year_stats['mean'].plot(kind='bar', figsize=(10, 4), color='#287e9b', ylim=(0, 1), title='Landing success rate by year')\nax.set_ylabel('Success rate')"),
    cell("markdown", "## SQL checks\n\nThe course SQL snapshot is loaded into in-memory SQLite. These are examples from the ten SQL questions summarized in the report."),
    cell("code", "connection = sqlite3.connect(':memory:')\nsql_data.to_sql('SPACEXTBL', connection, index=False)\nprint(pd.read_sql_query('SELECT COUNT(*) AS Launches FROM SPACEXTBL', connection))\nprint(pd.read_sql_query(\"SELECT Launch_Site, COUNT(*) AS Launches FROM SPACEXTBL GROUP BY Launch_Site ORDER BY Launches DESC\", connection))"),
    cell("markdown", "## Predictive modeling\n\nThe full source in `analyze.py` compares logistic regression, a linear margin classifier, k-nearest neighbors, and a shallow decision tree. It uses a stratified 80/20 train/test split and five-fold cross-validation for model selection."),
    cell("code", "import runpy\nrunpy.run_path(str(ROOT / 'analyze.py'), run_name='__main__')\nresults = json.loads((ROOT / 'analysis_results.json').read_text(encoding='utf-8'))\nprint('Dataset summary:', results['dataset'])\nprint('Model results:', results.get('models', results.get('classification', 'See analysis_results.json')))"),
    cell("markdown", "## Interactive outputs\n\nRun `visuals.py` to regenerate `launch_sites_map.html` and `launch_dashboard.html`. Open those files in a browser to inspect site-level Folium markers and the Plotly dashboard. The final PDF summarizes their results and the model limitations."),
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
(ROOT / "capstone_analysis.ipynb").write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
