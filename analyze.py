"""Reproducible analysis of the IBM Skills Network SpaceX capstone datasets.

This script uses only the bundled Python runtime (pandas and numpy). It keeps
training and test data separate and writes the statistics used in the report.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent


def confusion(y_true: np.ndarray, y_pred: np.ndarray) -> list[list[int]]:
    return [
        [int(np.sum((y_true == 0) & (y_pred == 0))), int(np.sum((y_true == 0) & (y_pred == 1)))],
        [int(np.sum((y_true == 1) & (y_pred == 0))), int(np.sum((y_true == 1) & (y_pred == 1)))],
    ]


def fit_logistic(x: np.ndarray, y: np.ndarray, c: float):
    w = np.zeros(x.shape[1])
    b = 0.0
    n = len(y)
    reg = 1.0 / c
    for _ in range(1800):
        z = np.clip(x @ w + b, -35, 35)
        p = 1.0 / (1.0 + np.exp(-z))
        w -= 0.13 * (x.T @ (p - y) / n + reg * w / n)
        b -= 0.13 * np.mean(p - y)
    return w, b


def predict_logistic(model, x: np.ndarray) -> np.ndarray:
    w, b = model
    return ((x @ w + b) >= 0).astype(int)


def fit_svm(x: np.ndarray, y: np.ndarray, c: float):
    labels = 2 * y - 1
    w = np.zeros(x.shape[1])
    b = 0.0
    n = len(y)
    for iteration in range(1800):
        margin = labels * (x @ w + b)
        active = margin < 1
        rate = 0.08 / (1 + iteration / 600)
        w -= rate * (w / n - c * (x[active].T @ labels[active]) / n)
        b += rate * c * np.sum(labels[active]) / n
    return w, b


def predict_svm(model, x: np.ndarray) -> np.ndarray:
    w, b = model
    return ((x @ w + b) >= 0).astype(int)


def fit_knn(x: np.ndarray, y: np.ndarray, k: int):
    return x, y, k


def predict_knn(model, x: np.ndarray) -> np.ndarray:
    train_x, train_y, k = model
    distance = ((x[:, None, :] - train_x[None, :, :]) ** 2).sum(axis=2)
    indices = np.argpartition(distance, k - 1, axis=1)[:, :k]
    return (train_y[indices].mean(axis=1) >= 0.5).astype(int)


def fit_tree(x: np.ndarray, y: np.ndarray, depth: int, min_leaf: int = 3):
    def build(rows: np.ndarray, remaining: int):
        probability = float(y[rows].mean())
        node = {"probability": probability}
        if remaining == 0 or len(rows) < 2 * min_leaf or probability in (0.0, 1.0):
            return node
        best_gain = 0.0
        best_split = None
        parent_gini = 2 * probability * (1 - probability)
        for col in range(x.shape[1]):
            values = np.unique(x[rows, col])
            if len(values) > 20:
                values = np.unique(np.quantile(values, np.linspace(0.05, 0.95, 10)))
            thresholds = (values[:-1] + values[1:]) / 2
            for threshold in thresholds:
                left = rows[x[rows, col] <= threshold]
                right = rows[x[rows, col] > threshold]
                if min(len(left), len(right)) < min_leaf:
                    continue
                p_left = y[left].mean()
                p_right = y[right].mean()
                gini = (len(left) * 2 * p_left * (1 - p_left) +
                        len(right) * 2 * p_right * (1 - p_right)) / len(rows)
                gain = parent_gini - gini
                if gain > best_gain:
                    best_gain = gain
                    best_split = (col, float(threshold), left, right)
        if best_split is not None:
            col, threshold, left, right = best_split
            node.update(feature=col, threshold=threshold,
                        left=build(left, remaining - 1),
                        right=build(right, remaining - 1))
        return node

    return build(np.arange(len(y)), depth)


def predict_tree(model, x: np.ndarray) -> np.ndarray:
    def classify(node, row):
        while "feature" in node:
            branch = "left" if row[node["feature"]] <= node["threshold"] else "right"
            node = node[branch]
        return int(node["probability"] >= 0.5)

    return np.array([classify(model, row) for row in x], dtype=int)


def split_stratified(y: np.ndarray, test_fraction: float, seed: int):
    rng = np.random.default_rng(seed)
    test = []
    train = []
    for cls in (0, 1):
        indices = rng.permutation(np.flatnonzero(y == cls))
        n_test = round(len(indices) * test_fraction)
        test.extend(indices[:n_test])
        train.extend(indices[n_test:])
    return np.array(sorted(train)), np.array(sorted(test))


def standardize(train_x: np.ndarray, other_x: np.ndarray):
    mean = train_x.mean(axis=0)
    scale = train_x.std(axis=0)
    scale[scale == 0] = 1
    return (train_x - mean) / scale, (other_x - mean) / scale


def model_comparison(features: pd.DataFrame, target: pd.Series):
    x = features.to_numpy(dtype=float)
    y = target.to_numpy(dtype=int)
    train_indices, test_indices = split_stratified(y, 0.2, 2)
    x_train_raw, y_train = x[train_indices], y[train_indices]
    x_test_raw, y_test = x[test_indices], y[test_indices]
    folds = np.array_split(np.random.default_rng(13).permutation(len(y_train)), 5)
    candidates = {
        "Logistic regression": [
            ({"C": c}, lambda a, b, c=c: fit_logistic(a, b, c), predict_logistic)
            for c in (0.1, 1.0, 10.0)
        ],
        "Linear SVM": [
            ({"C": c}, lambda a, b, c=c: fit_svm(a, b, c), predict_svm)
            for c in (0.1, 1.0, 10.0)
        ],
        "K nearest neighbors": [
            ({"k": k}, lambda a, b, k=k: fit_knn(a, b, k), predict_knn)
            for k in (3, 5, 7, 9)
        ],
        "Decision tree": [
            ({"max_depth": d}, lambda a, b, d=d: fit_tree(a, b, d), predict_tree)
            for d in (2, 3, 4)
        ],
    }
    scores = []
    for name, variants in candidates.items():
        best = None
        for params, fit, predict in variants:
            fold_scores = []
            for valid in folds:
                train = np.setdiff1d(np.arange(len(y_train)), valid)
                x_fit, x_valid = standardize(x_train_raw[train], x_train_raw[valid])
                model = fit(x_fit, y_train[train])
                fold_scores.append(float(np.mean(predict(model, x_valid) == y_train[valid])))
            cv_score = float(np.mean(fold_scores))
            if best is None or cv_score > best[0]:
                best = (cv_score, params, fit, predict)
        cv_score, params, fit, predict = best
        x_fit, x_test = standardize(x_train_raw, x_test_raw)
        predictions = predict(fit(x_fit, y_train), x_test)
        scores.append({
            "model": name,
            "parameters": params,
            "cross_validation_accuracy": round(cv_score, 3),
            "test_accuracy": round(float(np.mean(predictions == y_test)), 3),
            "confusion_matrix": confusion(y_test, predictions),
        })
    selected = max(scores, key=lambda item: item["cross_validation_accuracy"])
    return {
        "split": {"train": len(train_indices), "test": len(test_indices),
                  "test_positive": int(y_test.sum()), "seed": 2},
        "majority_class_test_accuracy": round(float(np.mean(y_test == 1)), 3),
        "models": scores,
        "selected_model": selected["model"],
    }


def sql_results(frame: pd.DataFrame):
    connection = sqlite3.connect(":memory:")
    frame.to_sql("SPACEXTBL", connection, index=False)
    queries = {
        "launch_sites": 'SELECT DISTINCT Launch_Site FROM SPACEXTBL ORDER BY Launch_Site',
        "five_cca_records": "SELECT Date, Launch_Site FROM SPACEXTBL WHERE Launch_Site LIKE 'CCA%' LIMIT 5",
        "nasa_payload_kg": "SELECT SUM(PAYLOAD_MASS__KG_) AS total_kg FROM SPACEXTBL WHERE Customer LIKE '%NASA%'",
        "f9_v11_average_kg": "SELECT AVG(PAYLOAD_MASS__KG_) AS average_kg FROM SPACEXTBL WHERE Booster_Version LIKE 'F9 v1.1%'",
        "first_ground_pad_success": "SELECT MIN(Date) AS first_date FROM SPACEXTBL WHERE Landing_Outcome = 'Success (ground pad)'",
        "drone_ship_4000_6000": "SELECT Booster_Version, PAYLOAD_MASS__KG_ FROM SPACEXTBL WHERE Landing_Outcome = 'Success (drone ship)' AND PAYLOAD_MASS__KG_ > 4000 AND PAYLOAD_MASS__KG_ < 6000",
        "mission_outcome_counts": "SELECT Mission_Outcome, COUNT(*) AS launches FROM SPACEXTBL GROUP BY Mission_Outcome ORDER BY launches DESC",
        "maximum_payload_booster": "SELECT Booster_Version, PAYLOAD_MASS__KG_ FROM SPACEXTBL WHERE PAYLOAD_MASS__KG_ = (SELECT MAX(PAYLOAD_MASS__KG_) FROM SPACEXTBL)",
        "failed_drone_ship_2015": "SELECT Date, Booster_Version, Launch_Site, Landing_Outcome FROM SPACEXTBL WHERE Date LIKE '2015%' AND Landing_Outcome LIKE 'Failure (drone ship)'",
        "outcome_rank_2010_2017": "SELECT Landing_Outcome, COUNT(*) AS launches FROM SPACEXTBL WHERE Date BETWEEN '2010-06-04' AND '2017-03-20' GROUP BY Landing_Outcome ORDER BY launches DESC",
    }
    result = {}
    for key, query in queries.items():
        data = pd.read_sql_query(query, connection)
        result[key] = {"query": query, "rows": data.where(pd.notna(data), None).to_dict("records")}
    connection.close()
    return result


def main():
    launches = pd.read_csv(ROOT / "dataset_part_2.csv")
    features = pd.read_csv(ROOT / "dataset_part_3.csv")
    dashboard = pd.read_csv(ROOT / "spacex_launch_dash.csv")
    sql_data = pd.read_csv(ROOT / "Spacex.csv")
    assert len(launches) == len(features) == 90
    assert (launches["FlightNumber"] == features["FlightNumber"]).all()
    launches["Year"] = pd.to_datetime(launches["Date"]).dt.year
    launches["PayloadQuartile"] = pd.qcut(launches["PayloadMass"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    groupings = {}
    for column in ("Year", "LaunchSite", "Orbit", "PayloadQuartile", "Reused", "GridFins", "Legs"):
        grouped = launches.groupby(column, observed=True)["Class"].agg(["count", "sum", "mean"]).reset_index()
        grouped[column] = grouped[column].astype(str)
        groupings[column] = grouped.round(4).to_dict("records")
    report = {
        "dataset": {"launches": len(launches), "successful_landings": int(launches["Class"].sum()),
                    "success_rate": round(float(launches["Class"].mean()), 4),
                    "year_min": int(launches["Year"].min()), "year_max": int(launches["Year"].max()),
                    "dashboard_rows": len(dashboard), "sql_rows": len(sql_data),
                    "missing_landing_pad": int(launches["LandingPad"].isna().sum())},
        "groups": groupings,
        "dashboard": dashboard.groupby("Launch Site")["class"].agg(["count", "sum", "mean"]).reset_index().round(4).to_dict("records"),
        "sql": sql_results(sql_data),
        "classification": model_comparison(features, launches["Class"]),
    }
    (ROOT / "analysis_results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"dataset": report["dataset"], "classification": report["classification"]}, indent=2))


if __name__ == "__main__":
    main()
