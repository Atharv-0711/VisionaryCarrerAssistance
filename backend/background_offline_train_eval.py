import argparse
import json
import os
from collections import Counter
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from sentiment_analysis_background import (
    BackgroundSentimentRL,
    NORMALIZED_BACKGROUND_PRIORS,
    _normalize_background_label,
    _resolve_column,
    _to_academic_scale,
)


def _clamp_score(value: float) -> float:
    return float(max(1.0, min(5.0, value)))


def _detect_group_column(df: pd.DataFrame):
    candidates = [
        "Name of Child ",
        "Name of Child",
        "studentName",
        "name",
        "Student Name",
    ]
    for col in candidates:
        resolved = _resolve_column(df, col)
        if resolved:
            return resolved
    return None


def _prepare_rows(df: pd.DataFrame):
    background_col = _resolve_column(df, "Background of the Child ")
    academic_col = _resolve_column(df, "Academic Performance ")
    group_col = _detect_group_column(df)

    if not background_col or not academic_col:
        raise ValueError("Required columns missing: Background of the Child / Academic Performance")

    rows = []
    for idx, row in df.iterrows():
        bg_raw = row.get(background_col)
        target = _to_academic_scale(row.get(academic_col))
        if bg_raw is None or pd.isna(bg_raw) or target is None:
            continue
        background = str(bg_raw).strip()
        if not background or background.lower() in {"none", "null", ""}:
            continue

        group_value = row.get(group_col) if group_col else None
        group_key = str(group_value).strip().lower() if group_value is not None and str(group_value).strip() else f"idx_{idx}"
        rows.append(
            {
                "job_key": _normalize_background_label(background),
                "target": float(target),
                "group": group_key,
            }
        )

    if not rows:
        raise ValueError("No valid rows after filtering")
    return rows


def _split_by_group(rows, seed=42, train_frac=0.7, val_frac=0.15):
    groups = sorted({r["group"] for r in rows})
    rng = np.random.default_rng(seed)
    rng.shuffle(groups)

    n = len(groups)
    if n < 3:
        # Fallback when groups are very few: still keep strict non-overlap.
        train_cut = max(1, int(round(n * 0.7)))
        val_cut = min(n - 1, train_cut + max(0, int(round(n * 0.15))))
    else:
        train_cut = max(1, int(round(n * train_frac)))
        val_cut = min(n - 1, train_cut + max(1, int(round(n * val_frac))))
        if val_cut <= train_cut:
            val_cut = min(n - 1, train_cut + 1)

    train_groups = set(groups[:train_cut])
    val_groups = set(groups[train_cut:val_cut])
    test_groups = set(groups[val_cut:])

    train_rows = [r for r in rows if r["group"] in train_groups]
    val_rows = [r for r in rows if r["group"] in val_groups]
    test_rows = [r for r in rows if r["group"] in test_groups]

    if not train_rows or not val_rows or not test_rows:
        raise ValueError("Split failed to produce non-empty train/val/test partitions")
    return train_rows, val_rows, test_rows


def _metrics(y_true, y_pred):
    y_t = np.array(y_true, dtype=float)
    y_p = np.array(y_pred, dtype=float)
    mse = float(np.mean((y_t - y_p) ** 2))
    rmse = float(np.sqrt(mse))
    mae = float(np.mean(np.abs(y_t - y_p)))
    ss_res = float(np.sum((y_t - y_p) ** 2))
    ss_tot = float(np.sum((y_t - np.mean(y_t)) ** 2))
    r2 = 0.0 if ss_tot == 0 else float(1.0 - (ss_res / ss_tot))
    return {"rmse": round(rmse, 4), "mae": round(mae, 4), "r2": round(r2, 4)}


def _targets(rows):
    return [r["target"] for r in rows]


def _predict_mean(rows, train_mean):
    return [_clamp_score(train_mean) for _ in rows]


def _predict_prior(rows):
    return [_clamp_score(NORMALIZED_BACKGROUND_PRIORS.get(r["job_key"], 3.0)) for r in rows]


def _fit_simple_linear(train_rows):
    x = np.array([NORMALIZED_BACKGROUND_PRIORS.get(r["job_key"], 3.0) for r in train_rows], dtype=float)
    y = np.array(_targets(train_rows), dtype=float)
    x_design = np.column_stack([x, np.ones_like(x)])
    a, b = np.linalg.lstsq(x_design, y, rcond=None)[0]
    return float(a), float(b)


def _predict_simple_linear(rows, a, b):
    return [_clamp_score((a * NORMALIZED_BACKGROUND_PRIORS.get(r["job_key"], 3.0)) + b) for r in rows]


def _train_rl(train_rows):
    rl = BackgroundSentimentRL(initial_scores=dict(NORMALIZED_BACKGROUND_PRIORS))
    # Prevent writes during experimental training/evaluation.
    rl.save_model = lambda filename="background_sentiment_model.json": None

    freq = Counter(r["job_key"] for r in train_rows)
    for r in train_rows:
        pred = rl.get_policy_score(r["job_key"])
        sample_weight = 1.0 / max(freq[r["job_key"]], 1)
        rl.add_experience(r["job_key"], pred, r["target"], sample_weight=sample_weight)
    rl.update_model()
    return rl


def _predict_rl(rows, rl):
    return [_clamp_score(rl.get_blended_policy_score(r["job_key"])) for r in rows]


def main():
    parser = argparse.ArgumentParser(description="Offline background model train/eval with baseline gating.")
    parser.add_argument("--input", default="Childsurvey.xlsx", help="Input survey Excel file path")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for splitting")
    args = parser.parse_args()

    input_path = args.input
    if not os.path.isabs(input_path):
        input_path = os.path.join(os.path.dirname(__file__), input_path)

    df = pd.read_excel(input_path)

    rows = _prepare_rows(df)
    train_rows, val_rows, test_rows = _split_by_group(rows, seed=args.seed)

    train_mean = float(np.mean(_targets(train_rows)))
    a, b = _fit_simple_linear(train_rows)
    rl = _train_rl(train_rows)

    models = {
        "mean_predictor": lambda x: _predict_mean(x, train_mean),
        "static_prior": _predict_prior,
        "simple_linear": lambda x: _predict_simple_linear(x, a, b),
        "rl_model": lambda x: _predict_rl(x, rl),
    }

    evaluation = {}
    for name, predictor in models.items():
        val_pred = predictor(val_rows)
        test_pred = predictor(test_rows)
        evaluation[name] = {
            "val": _metrics(_targets(val_rows), val_pred),
            "test": _metrics(_targets(test_rows), test_pred),
        }

    baseline_names = ["mean_predictor", "static_prior", "simple_linear"]
    best_baseline = min(baseline_names, key=lambda k: evaluation[k]["val"]["rmse"])

    rl_val = evaluation["rl_model"]["val"]
    base_val = evaluation[best_baseline]["val"]
    promote = (rl_val["rmse"] < base_val["rmse"]) and (rl_val["r2"] >= base_val["r2"]) and (rl_val["r2"] >= 0)

    backend_dir = os.path.dirname(__file__)
    models_dir = os.path.join(backend_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    versioned_model_path = os.path.join(models_dir, f"background_sentiment_model_{timestamp}.json")
    active_model_path = os.path.join(backend_dir, "background_sentiment_model.json")

    if promote:
        # Persist promoted model (versioned + active pointer file).
        original_save = BackgroundSentimentRL.save_model.__get__(rl, BackgroundSentimentRL)
        original_save(versioned_model_path)
        original_save(active_model_path)

    report = {
        "input_path": input_path,
        "seed": args.seed,
        "split": {
            "train_rows": len(train_rows),
            "val_rows": len(val_rows),
            "test_rows": len(test_rows),
            "train_groups": len({r["group"] for r in train_rows}),
            "val_groups": len({r["group"] for r in val_rows}),
            "test_groups": len({r["group"] for r in test_rows}),
        },
        "best_baseline_on_val": best_baseline,
        "promote_rl_model": promote,
        "models": evaluation,
        "artifacts": {
            "versioned_model_path": versioned_model_path if promote else None,
            "active_model_path": active_model_path if promote else None,
        },
    }

    linear_payload = {
        "slope": round(a, 8),
        "intercept": round(b, 8),
        "fit_source": "offline_train_eval",
        "seed": args.seed,
        "input_path": input_path,
        "created_at": timestamp,
    }
    linear_versioned_path = os.path.join(models_dir, f"background_simple_linear_model_{timestamp}.json")
    linear_active_path = os.path.join(models_dir, "background_simple_linear_model.json")
    with open(linear_versioned_path, "w", encoding="utf-8") as f:
        json.dump(linear_payload, f, indent=2)
    with open(linear_active_path, "w", encoding="utf-8") as f:
        json.dump(linear_payload, f, indent=2)
    report["artifacts"]["simple_linear_versioned_path"] = linear_versioned_path
    report["artifacts"]["simple_linear_active_path"] = linear_active_path

    report_path = os.path.join(models_dir, f"background_eval_report_{timestamp}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    print(f"\nSaved evaluation report to: {report_path}")
    if promote:
        print("RL model promoted (beats baseline on validation).")
    else:
        print("RL model NOT promoted (failed validation gate).")


if __name__ == "__main__":
    main()
