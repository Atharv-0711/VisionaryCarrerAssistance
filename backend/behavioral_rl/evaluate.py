import math
from typing import Any

import numpy as np
from scipy.stats import pearsonr, spearmanr


def _safe_float(value: Any) -> float | None:
    try:
        cast = float(value)
    except Exception:
        return None
    if math.isnan(cast) or math.isinf(cast):
        return None
    return cast


def determine_correlation_reason(pred_scores: np.ndarray, academic_scores: np.ndarray) -> str:
    if pred_scores.size < 2 or academic_scores.size < 2:
        return "insufficient_pairs"
    if np.std(pred_scores) == 0:
        return "no_sentiment_variance"
    if np.std(academic_scores) == 0:
        return "no_academic_variance"
    return "computed"


def correlation_summary(pred_scores: np.ndarray, academic_scores: np.ndarray) -> dict[str, float | None]:
    reason = determine_correlation_reason(pred_scores, academic_scores)
    if reason != "computed":
        return {
            "correlation_reason": reason,
            "spearman_correlation": None,
            "spearman_p_value": None,
            "pearson_correlation": None,
            "pearson_p_value": None,
        }

    spearman_corr, spearman_p = spearmanr(pred_scores, academic_scores)
    pearson_corr, pearson_p = pearsonr(pred_scores, academic_scores)
    return {
        "correlation_reason": "computed",
        "spearman_correlation": _safe_float(spearman_corr),
        "spearman_p_value": _safe_float(spearman_p),
        "pearson_correlation": _safe_float(pearson_corr),
        "pearson_p_value": _safe_float(pearson_p),
    }


def compute_regression_metrics(pred_scores: np.ndarray, academic_scores: np.ndarray) -> dict[str, float | None]:
    if pred_scores.size == 0 or academic_scores.size == 0:
        return {
            "mae": None,
            "rmse": None,
            "r2": None,
        }

    residuals = pred_scores - academic_scores
    mae = float(np.mean(np.abs(residuals)))
    rmse = float(np.sqrt(np.mean(np.square(residuals))))
    y_mean = float(np.mean(academic_scores))
    sst = float(np.sum(np.square(academic_scores - y_mean)))
    sse = float(np.sum(np.square(residuals)))
    r2 = None if sst == 0 else float(1 - (sse / sst))

    return {"mae": mae, "rmse": rmse, "r2": r2}


def build_distribution_stats(values: np.ndarray) -> dict[str, float | None]:
    if values.size == 0:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "std": None,
            "q25": None,
            "q75": None,
        }

    return {
        "count": int(values.size),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "std": float(np.std(values)),
        "q25": float(np.percentile(values, 25)),
        "q75": float(np.percentile(values, 75)),
    }
