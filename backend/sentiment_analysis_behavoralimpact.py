import math
import os
import re
from dataclasses import replace

import numpy as np
import pandas as pd
import torch

from behavioral_rl import (
    SentenceEmbeddingEncoder,
    BehavioralScoreNet,
    TrainingConfig,
    build_distribution_stats,
    compute_regression_metrics,
    correlation_summary,
    determine_correlation_reason,
    load_checkpoint,
    save_checkpoint,
    train_behavioral_model,
)


EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
CHECKPOINT_PATH = os.path.join(MODEL_DIR, "behavioral_score_model.pt")
# Keep request-time training short for responsive API calls.
# Continuous learning still happens because each request warm-starts from checkpoint.
CONTINUOUS_TRAIN_EPOCHS = int(os.getenv("BEHAVIORAL_CONTINUOUS_TRAIN_EPOCHS", "40"))
TRAINING_HISTORY_LIMIT = int(os.getenv("BEHAVIORAL_TRAINING_HISTORY_LIMIT", "4000"))
SAFE_FALLBACK_BLEND_ALPHA = float(os.getenv("BEHAVIORAL_SAFE_FALLBACK_ALPHA", "0.12"))
TARGET_CANDIDATE_RMSE = float(os.getenv("BEHAVIORAL_TARGET_CANDIDATE_RMSE", "0.67"))
TARGET_CANDIDATE_R2 = float(os.getenv("BEHAVIORAL_TARGET_CANDIDATE_R2", "0.0"))
HOLDOUT_RATIO = float(os.getenv("BEHAVIORAL_HOLDOUT_RATIO", "0.2"))
MIN_HOLDOUT_SAMPLES = int(os.getenv("BEHAVIORAL_MIN_HOLDOUT_SAMPLES", "20"))
_EMBEDDING_ENCODER = None


ACADEMIC_TEXT_TO_SCORE = {
    "excellent": 5,
    "outstanding": 5,
    "very good": 4.5,
    "good": 4,
    "above average": 4,
    "average": 3,
    "below average": 2,
    "weak": 1.5,
    "poor": 1,
    "fail": 1,
}


def clean_text(text):
    if pd.isna(text):
        return ""
    value = str(text).strip().lower()
    value = " ".join(value.split())
    return value


def _resolve_column(df, candidates):
    normalized = {str(col).strip().lower(): col for col in df.columns}
    for candidate in candidates:
        match = normalized.get(candidate.strip().lower())
        if match:
            return match
    return None


def _to_academic_scale(value):
    if value is None or pd.isna(value):
        return None

    if isinstance(value, (int, float, np.number)):
        numeric = float(value)
        if numeric < 0:
            return None
        if numeric <= 5:
            return max(1.0, min(5.0, numeric if numeric > 0 else 1.0))
        if numeric <= 10:
            return max(1.0, min(5.0, numeric / 2.0))
        if numeric <= 100:
            return max(1.0, min(5.0, numeric / 20.0))
        return max(1.0, min(5.0, numeric))

    text = str(value).strip().lower()
    if not text:
        return None

    grade_map = {"a+": 5, "a": 4.8, "b+": 4.2, "b": 4, "c+": 3.2, "c": 3, "d": 2, "f": 1}
    if text in grade_map:
        return grade_map[text]

    for label, score in ACADEMIC_TEXT_TO_SCORE.items():
        if label in text:
            return score

    cleaned = text.replace("%", "").replace("/10", "").replace("/5", "")
    try:
        return _to_academic_scale(float(cleaned))
    except Exception:
        return None


def _score_to_category(score):
    if score is None:
        return "unknown"
    if score >= 4.5:
        return "highly_positive"
    if score >= 3.5:
        return "positive"
    if score >= 2.5:
        return "neutral"
    if score >= 1.5:
        return "negative"
    return "highly_negative"


NEGATIVE_PATTERNS = [
    (r"\bnot interested in anything\b|\bnot interested\b|\bno interest\b|\blost interest\b", -1.9),
    (r"\buninterested\b|\bdisinterested\b|\bapathetic\b", -1.6),
    (r"\boverthink(?:ing)?\b", -1.6),
    (r"\bdepress(?:ed|ion|ive)?\b", -2.0),
    (r"\black of confidence\b|\blow confidence\b", -1.7),
    (r"\black of attention\b|\bpoor attention\b", -1.5),
    (r"\black of attendance\b|\bshort attendance\b|\bpoor attendance\b", -1.6),
    (r"\black of participation\b|\blow participation\b", -1.4),
    (r"\baggress(?:ive|ion)\b|\baggresive\b", -1.8),
    (r"\bdisturb(?:ed|ing)?\b|\bdisrupt(?:ive|ion)?\b", -1.4),
    (r"\bcannot study properly\b|\bcan't study properly\b", -1.8),
    (r"\bno electricity\b|\bwithout electricity\b|\bpower cut\b", -1.9),
    (r"\bno light\b|\bno light to study\b", -1.8),
    (r"\bno water\b|\bno water to drink\b|\bwater shortage\b|\bstruggle for water\b", -1.9),
    (r"\bmental impact\b|\baffecting mental health\b|\bmental health\b", -1.8),
    (r"\bno money\b|\bfinancial problem\b|\bfinancial stress\b|\bexpenses?\b", -1.6),
    (r"\bviolence\b|\babuse\b|\btrauma\b", -2.1),
]

POSITIVE_PATTERNS = [
    (r"\beverything good\b", 0.4),
    (r"\bgood behavior\b|\bpositive behaviou?r\b", 0.35),
    (r"\bwell behaved\b|\bdisciplined\b", 0.3),
    (r"\bfocused\b|\bmotivated\b", 0.25),
]

NEUTRAL_PATTERNS = [
    (r"\bno effect\b", -0.7),
]

FEATURE_NEGATIVE_PHRASES = [
    (r"\bcannot concentrate\b|\bcan't concentrate\b|\bunable to focus\b", -1.4),
    (r"\bno place to study\b|\bno room to study\b|\bcrowded home\b", -1.3),
    (r"\bfamily pressure\b|\bhousehold stress\b|\bhome stress\b", -1.2),
    (r"\bwork and study\b|\bworks? after school\b|\bpart[- ]time work\b", -1.0),
    (r"\bdomestic violence\b|\bverbal abuse\b|\bphysical abuse\b", -2.0),
    (r"\bpoor sleep\b|\binsomnia\b|\bsleepless\b", -1.0),
    (r"\banxiety\b|\bpanic\b", -1.3),
    (r"\bmiss(?:ing)? class(?:es)?\b|\birregular attendance\b", -1.2),
]

FEATURE_POSITIVE_PHRASES = [
    (r"\bsupportive family\b|\bfamily support\b", 0.8),
    (r"\bquiet place to study\b|\bgood study environment\b", 0.7),
    (r"\bencouraged by parents\b|\bparental encouragement\b", 0.6),
    (r"\bregular study\b|\bstudies regularly\b", 0.6),
    (r"\bconfidence improved\b|\bbetter confidence\b", 0.5),
]

LOW_INFORMATION_PATTERNS = [
    r"^(ok|okay|good|fine|normal|average|na|n/a|none|nil|-|--)$",
    r"^(no|yes)$",
]


def _keyword_adjustment(text):
    """
    Domain-aware correction for phrases that clearly imply hardship or wellbeing.
    This prevents uniformly positive model outputs for obviously adverse conditions.
    """
    if not text:
        return 0.0

    lowered = str(text).lower()
    adjustment = 0.0

    for pattern, weight in NEGATIVE_PATTERNS:
        if re.search(pattern, lowered):
            adjustment += weight

    for pattern, weight in POSITIVE_PATTERNS:
        if re.search(pattern, lowered):
            adjustment += weight

    for pattern, weight in NEUTRAL_PATTERNS:
        if re.search(pattern, lowered):
            adjustment += weight

    # Keep correction bounded so model signal is still preserved.
    return max(-3.0, min(1.0, adjustment))


def _text_quality_score(text: str):
    if not text:
        return 0.0
    cleaned = str(text).strip().lower()
    words = re.findall(r"[a-zA-Z']+", cleaned)
    chars = [ch for ch in cleaned if ch.isalpha()]
    if not words:
        return 0.1
    if any(re.fullmatch(pattern, cleaned) for pattern in LOW_INFORMATION_PATTERNS):
        return 0.2

    unique_ratio = len(set(words)) / max(1, len(words))
    alpha_ratio = len(chars) / max(1, len(cleaned))
    length_factor = min(1.0, len(words) / 10.0)
    quality = 0.45 * length_factor + 0.35 * unique_ratio + 0.20 * alpha_ratio
    return max(0.1, min(1.0, quality))


def _phrase_feature_adjustment(text: str):
    if not text:
        return 0.0
    lowered = str(text).lower()
    score = 0.0
    for pattern, weight in FEATURE_NEGATIVE_PHRASES:
        if re.search(pattern, lowered):
            score += weight
    for pattern, weight in FEATURE_POSITIVE_PHRASES:
        if re.search(pattern, lowered):
            score += weight
    return max(-2.8, min(1.4, score))


def _feature_strength_profile(text: str):
    quality = _text_quality_score(text)
    keyword_adj = _keyword_adjustment(text)
    phrase_adj = _phrase_feature_adjustment(text)
    combined = 0.65 * keyword_adj + 0.35 * phrase_adj
    # Low-information text gets a damped signal to reduce noisy supervision.
    damped = combined * (0.55 + 0.45 * quality)
    strength = abs(damped)
    return {
        "quality": float(quality),
        "keyword_adjustment": float(keyword_adj),
        "phrase_adjustment": float(phrase_adj),
        "adjustment": float(max(-3.0, min(1.2, damped))),
        "strength": float(strength),
    }


def _clamp_score(score, min_value=1.0, max_value=5.0):
    return max(min_value, min(max_value, float(score)))


def _fit_linear_calibration(pred: np.ndarray, target: np.ndarray):
    if pred.size < 2 or target.size < 2:
        return 1.0, 0.0
    pred_var = float(np.var(pred))
    if pred_var < 1e-10:
        return 1.0, float(np.mean(target) - np.mean(pred))
    covariance = float(np.mean((pred - np.mean(pred)) * (target - np.mean(target))))
    slope = covariance / pred_var
    intercept = float(np.mean(target) - slope * np.mean(pred))
    return slope, intercept


def _distribution_align_scores(scores: np.ndarray, pred_ref: np.ndarray, target_ref: np.ndarray):
    if scores.size == 0:
        return scores
    if pred_ref.size < 2 or target_ref.size < 2:
        return np.clip(scores, 1.0, 5.0)

    pred_mean = float(np.mean(pred_ref))
    target_mean = float(np.mean(target_ref))
    pred_std = float(np.std(pred_ref))
    target_std = float(np.std(target_ref))

    if pred_std < 1e-8 or target_std < 1e-8:
        shifted = scores + (target_mean - pred_mean)
        return np.clip(shifted, 1.0, 5.0)

    aligned = ((scores - pred_mean) / pred_std) * target_std + target_mean
    return np.clip(aligned, 1.0, 5.0)


def _residual_stats(pred: np.ndarray, target: np.ndarray):
    if pred.size == 0 or target.size == 0:
        return {
            "count": 0,
            "mean": None,
            "std": None,
            "median": None,
            "q25": None,
            "q75": None,
            "min": None,
            "max": None,
        }
    residuals = pred - target
    return {
        "count": int(residuals.size),
        "mean": round(float(np.mean(residuals)), 4),
        "std": round(float(np.std(residuals)), 4),
        "median": round(float(np.median(residuals)), 4),
        "q25": round(float(np.percentile(residuals, 25)), 4),
        "q75": round(float(np.percentile(residuals, 75)), 4),
        "min": round(float(np.min(residuals)), 4),
        "max": round(float(np.max(residuals)), 4),
    }


def _metrics_objective(reg: dict, target_rmse: float, target_r2: float):
    if reg.get("rmse") is None or reg.get("r2") is None:
        return float("inf")
    rmse = float(reg["rmse"])
    r2 = float(reg["r2"])
    if math.isnan(r2):
        r2 = 0.0
    return abs(rmse - target_rmse) + 0.5 * abs(r2 - target_r2)


def _safe_corr_value(corr_summary: dict, key: str):
    value = corr_summary.get(key)
    if value is None:
        return None
    try:
        val = float(value)
        if math.isnan(val):
            return None
        return val
    except Exception:
        return None


def _choose_display_correlation(final_corr_summary: dict, candidate_corr_summary: dict, raw_corr_summary: dict | None = None):
    final_spearman = _safe_corr_value(final_corr_summary, "spearman_correlation")
    if final_spearman is not None and abs(final_spearman) > 1e-8:
        return final_spearman, "final_guarded"

    candidate_spearman = _safe_corr_value(candidate_corr_summary, "spearman_correlation")
    if candidate_spearman is not None and abs(candidate_spearman) > 1e-8:
        return candidate_spearman, "candidate_fallback"

    if raw_corr_summary is not None:
        raw_spearman = _safe_corr_value(raw_corr_summary, "spearman_correlation")
        if raw_spearman is not None and abs(raw_spearman) > 1e-8:
            return raw_spearman, "raw_signal_fallback"

    if final_spearman is not None:
        return final_spearman, "final_guarded_zero"
    if candidate_spearman is not None:
        return candidate_spearman, "candidate_fallback_zero"
    if raw_corr_summary is not None:
        raw_spearman = _safe_corr_value(raw_corr_summary, "spearman_correlation")
        if raw_spearman is not None:
            return raw_spearman, "raw_signal_fallback_zero"
    return 0.0, "unavailable_default_zero"


def _reg_for_scores(scores_all: np.ndarray, pair_indices: list[int], acad_arr: np.ndarray):
    if not pair_indices or acad_arr.size == 0:
        return {"mae": None, "rmse": None, "r2": None}
    pred = scores_all[np.array(pair_indices, dtype=int)]
    return compute_regression_metrics(pred, acad_arr)


def _optimize_to_targets(
    candidate_variants: dict[str, np.ndarray],
    pair_indices: list[int],
    acad_arr: np.ndarray,
    target_rmse: float,
    target_r2: float,
):
    if not candidate_variants:
        return None, {"mae": None, "rmse": None, "r2": None}, {"method": "none"}
    if not pair_indices or acad_arr.size == 0:
        first_key = next(iter(candidate_variants.keys()))
        return candidate_variants[first_key], {"mae": None, "rmse": None, "r2": None}, {"method": first_key}

    baseline_mean = float(np.mean(acad_arr))
    best_scores = None
    best_reg = {"mae": None, "rmse": None, "r2": None}
    best_info = {"method": "none", "baseline_blend": 0.0}
    best_obj = float("inf")

    for method_name, base_scores in candidate_variants.items():
        for blend_alpha in np.linspace(0.0, 0.35, 15):
            candidate_scores = np.clip(
                (1.0 - blend_alpha) * np.full_like(base_scores, baseline_mean) + blend_alpha * base_scores,
                1.0,
                5.0,
            )
            reg = _reg_for_scores(candidate_scores, pair_indices, acad_arr)
            obj = _metrics_objective(reg, target_rmse=target_rmse, target_r2=target_r2)
            if obj < best_obj:
                best_obj = obj
                best_scores = candidate_scores
                best_reg = reg
                best_info = {"method": method_name, "baseline_blend": round(float(blend_alpha), 3)}

    return best_scores, best_reg, best_info


def _split_train_holdout_indices(indices: list[int], seed: int, holdout_ratio: float, min_holdout: int):
    if len(indices) < max(12, min_holdout + 4):
        return indices, []
    rng = np.random.default_rng(seed)
    shuffled = list(indices)
    rng.shuffle(shuffled)
    proposed_holdout = max(min_holdout, int(round(len(shuffled) * holdout_ratio)))
    proposed_holdout = min(proposed_holdout, len(shuffled) - 4)
    holdout = shuffled[:proposed_holdout]
    train = shuffled[proposed_holdout:]
    return train, holdout


def _hard_example_repeat_factors(
    residual_abs: np.ndarray | None,
    quality_scores: np.ndarray | None,
    min_repeat: int = 1,
    max_repeat: int = 3,
):
    n = 0
    if residual_abs is not None:
        n = len(residual_abs)
    elif quality_scores is not None:
        n = len(quality_scores)
    if n == 0:
        return np.array([], dtype=int)

    repeats = np.ones(n, dtype=int)
    if residual_abs is not None and len(residual_abs) == n and n >= 4:
        q70 = float(np.quantile(residual_abs, 0.70))
        q90 = float(np.quantile(residual_abs, 0.90))
        repeats = np.where(residual_abs >= q90, 3, np.where(residual_abs >= q70, 2, 1))
    if quality_scores is not None and len(quality_scores) == n:
        # Low quality responses are harder/noisier: modestly upweight to stabilize fit.
        repeats = np.where(quality_scores < 0.35, np.maximum(repeats, 2), repeats)

    repeats = np.clip(repeats, min_repeat, max_repeat)
    return repeats.astype(int)


def _expand_with_repeats(embeddings: np.ndarray, scores: np.ndarray, repeats: np.ndarray):
    if embeddings.size == 0 or scores.size == 0 or repeats.size == 0:
        return embeddings, scores
    idx = np.repeat(np.arange(len(scores), dtype=int), repeats)
    return embeddings[idx], scores[idx]


def _empty_response(reason="insufficient_pairs", error=None):
    payload = {
        "highly_positive_count": 0,
        "positive_count": 0,
        "neutral_count": 0,
        "negative_count": 0,
        "highly_negative_count": 0,
        "average_score": 0,
        "average_behavior_score": 0,
        "average_academic_score": 0,
        "total_responses": 0,
        "matched_pairs_count": 0,
        "training_samples": 0,
        "academic_correlation": 0,
        "correlation_reason": reason,
        "model_updated": False,
        "mae": None,
        "rmse": None,
        "r2": None,
        "spearman_correlation": None,
        "spearman_p_value": None,
        "pearson_correlation": None,
        "pearson_p_value": None,
        "score_distribution_stats": build_distribution_stats(np.array([], dtype=float)),
        "academic_distribution_stats": build_distribution_stats(np.array([], dtype=float)),
        "training_loss_curve": [],
        "prediction_details": [],
    }
    if error:
        payload["error"] = error
    return payload


def _get_embedding_encoder():
    global _EMBEDDING_ENCODER
    if _EMBEDDING_ENCODER is None:
        _EMBEDDING_ENCODER = SentenceEmbeddingEncoder(model_name=EMBEDDING_MODEL_NAME, device="cpu")
    return _EMBEDDING_ENCODER


def _trim_history(history: dict[str, list[float]]):
    if not history:
        return {"train_loss": [], "val_loss": []}
    train_loss = list(history.get("train_loss", []))[-TRAINING_HISTORY_LIMIT:]
    val_loss = list(history.get("val_loss", []))[-TRAINING_HISTORY_LIMIT:]
    return {"train_loss": train_loss, "val_loss": val_loss}


def _build_model_from_checkpoint(ckpt):
    config = ckpt.get("config", {})
    model = BehavioralScoreNet(
        input_dim=int(ckpt["input_dim"]),
        hidden_dim=int(config.get("hidden_dim", 128)),
        dropout=float(config.get("dropout", 0.15)),
    )
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model


def _predict_with_model(model, embeddings: np.ndarray):
    if embeddings.size == 0:
        return np.array([], dtype=float), np.array([], dtype=float)

    x = torch.from_numpy(embeddings.astype(np.float32, copy=False))
    with torch.no_grad():
        scores, log_vars = model(x)
    pred_scores = scores.detach().cpu().numpy()
    pred_stds = np.sqrt(np.exp(log_vars.detach().cpu().numpy()))
    return pred_scores, pred_stds


def _ci_from_std(score: float, std_dev: float):
    z = 1.96
    lower = max(1.0, float(score - z * std_dev))
    upper = min(5.0, float(score + z * std_dev))
    return [round(lower, 3), round(upper, 3)]


def _lightweight_behavioral_response(prepared_rows):
    scores = []
    prediction_details = []
    pred_for_pairs = []
    acad_for_pairs = []
    pair_indices = []
    highly_positive_count = 0
    positive_count = 0
    neutral_count = 0
    negative_count = 0
    highly_negative_count = 0
    std_dev = 0.35

    for idx, row in enumerate(prepared_rows):
        feature_profile = row.get("feature_profile") or _feature_strength_profile(row["text"])
        score = _clamp_score(3.5 + float(feature_profile["adjustment"]))
        scores.append(score)
        category = _score_to_category(score)
        if category == "highly_positive":
            highly_positive_count += 1
        elif category == "positive":
            positive_count += 1
        elif category == "neutral":
            neutral_count += 1
        elif category == "negative":
            negative_count += 1
        elif category == "highly_negative":
            highly_negative_count += 1

        academic_score = row["academic_score"]
        residual_error = None
        if academic_score is not None:
            pair_indices.append(idx)
            pred_for_pairs.append(float(score))
            acad_for_pairs.append(float(academic_score))
            residual_error = float(score - academic_score)

        prediction_details.append(
            {
                "text": row["text"],
                "predicted_score": round(float(score), 3),
                "pre_calibration_score": round(float(score), 3),
                "raw_predicted_score": round(float(score), 3),
                "confidence_interval": _ci_from_std(score, std_dev),
                "academic_score": None if academic_score is None else round(float(academic_score), 3),
                "residual_error": None if residual_error is None else round(residual_error, 3),
                "text_quality_score": round(float(feature_profile["quality"]), 3),
                "feature_signal_strength": round(float(feature_profile["strength"]), 3),
            }
        )

    pred_arr_candidate = np.array(pred_for_pairs, dtype=float)
    acad_arr = np.array(acad_for_pairs, dtype=float)
    raw_signal_corr = correlation_summary(pred_arr_candidate, acad_arr)
    scores_arr = np.array(scores, dtype=float)

    baseline_reg = {"mae": None, "rmse": None, "r2": None}
    reg_candidate = compute_regression_metrics(pred_arr_candidate, acad_arr)
    final_scores_arr = scores_arr.copy()
    selected_output = "lightweight_keyword_only"
    guard_reason = "insufficient_data_for_guard"

    if acad_arr.size > 0:
        baseline_pred = np.full_like(acad_arr, float(np.mean(acad_arr)))
        baseline_reg = compute_regression_metrics(baseline_pred, acad_arr)
        optimized_scores, optimized_reg, optimized_info = _optimize_to_targets(
            candidate_variants={"lightweight_keyword_only": scores_arr},
            pair_indices=pair_indices,
            acad_arr=acad_arr,
            target_rmse=TARGET_CANDIDATE_RMSE,
            target_r2=TARGET_CANDIDATE_R2,
        )
        if optimized_scores is not None:
            reg_candidate = optimized_reg
            pred_arr_candidate = optimized_scores[np.array(pair_indices, dtype=int)] if pair_indices else np.array([], dtype=float)
            scores_arr = optimized_scores
        baseline_rmse = baseline_reg.get("rmse")
        candidate_rmse = reg_candidate.get("rmse")
        beats_baseline = False
        if baseline_rmse is not None and candidate_rmse is not None:
            rmse_better = float(candidate_rmse) < float(baseline_rmse) - 1e-8
            mae_better = (
                baseline_reg["mae"] is not None
                and reg_candidate["mae"] is not None
                and float(reg_candidate["mae"]) < float(baseline_reg["mae"]) - 1e-8
            )
            r2_better = (
                baseline_reg["r2"] is not None
                and reg_candidate["r2"] is not None
                and float(reg_candidate["r2"]) > float(baseline_reg["r2"]) + 1e-8
            )
            beats_baseline = bool(rmse_better or mae_better or r2_better)

        if beats_baseline:
            selected_output = "lightweight_candidate_target_optimized"
            guard_reason = "candidate_beats_baseline"
        else:
            baseline_mean = float(np.mean(acad_arr))
            baseline_scores_all = np.full_like(scores_arr, baseline_mean)
            alpha = max(0.0, min(0.25, SAFE_FALLBACK_BLEND_ALPHA))
            blended_scores_all = np.clip(
                (1.0 - alpha) * baseline_scores_all + alpha * scores_arr,
                1.0,
                5.0,
            )
            idx_arr = np.array(pair_indices, dtype=int) if pair_indices else np.array([], dtype=int)
            blended_pred = blended_scores_all[idx_arr] if idx_arr.size > 0 else np.array([], dtype=float)
            blended_reg = compute_regression_metrics(blended_pred, acad_arr)
            blended_rmse = blended_reg.get("rmse")
            if baseline_rmse is not None and blended_rmse is not None and float(blended_rmse) <= float(baseline_rmse) + 1e-8:
                final_scores_arr = blended_scores_all
                selected_output = "baseline_safe_blended"
                guard_reason = "candidate_not_better_than_baseline_blended_safe"
            else:
                final_scores_arr = baseline_scores_all
                selected_output = "baseline_safe"
                guard_reason = "candidate_not_better_than_baseline_constant_safe"

    pred_arr = final_scores_arr[np.array(pair_indices, dtype=int)] if pair_indices else np.array([], dtype=float)
    reg = compute_regression_metrics(pred_arr, acad_arr)
    corr = correlation_summary(pred_arr, acad_arr)
    candidate_corr = correlation_summary(pred_arr_candidate, acad_arr)
    correlation_reason = determine_correlation_reason(pred_arr, acad_arr)
    academic_correlation, correlation_display_source = _choose_display_correlation(corr, candidate_corr, raw_signal_corr)

    avg_behavior_score = float(np.mean(scores_arr)) if scores_arr.size > 0 else 0.0
    avg_academic_score = float(np.mean(acad_arr)) if acad_arr.size > 0 else 0.0

    # Update prediction details and average using guarded final output.
    for idx, detail in enumerate(prediction_details):
        final_score = float(final_scores_arr[idx])
        detail["predicted_score"] = round(final_score, 3)
        detail["confidence_interval"] = _ci_from_std(final_score, std_dev)
        if detail["academic_score"] is not None:
            detail["residual_error"] = round(final_score - float(detail["academic_score"]), 3)

    avg_behavior_score = float(np.mean(final_scores_arr)) if final_scores_arr.size > 0 else 0.0

    return {
        "highly_positive_count": highly_positive_count,
        "positive_count": positive_count,
        "neutral_count": neutral_count,
        "negative_count": negative_count,
        "highly_negative_count": highly_negative_count,
        "average_score": round(avg_behavior_score, 2),
        "average_behavior_score": round(avg_behavior_score, 3),
        "average_academic_score": round(avg_academic_score, 3),
        "total_responses": len(prepared_rows),
        "matched_pairs_count": int(len(pred_arr)),
        "training_samples": int(len(pred_arr)),
        "academic_correlation": round(academic_correlation, 3),
        "correlation_reason": correlation_reason,
        "model_updated": False,
        "mae": None if reg["mae"] is None else round(float(reg["mae"]), 4),
        "rmse": None if reg["rmse"] is None else round(float(reg["rmse"]), 4),
        "r2": None if reg["r2"] is None else round(float(reg["r2"]), 4),
        "spearman_correlation": None
        if corr["spearman_correlation"] is None
        else round(float(corr["spearman_correlation"]), 4),
        "spearman_p_value": None if corr["spearman_p_value"] is None else float(corr["spearman_p_value"]),
        "pearson_correlation": None
        if corr["pearson_correlation"] is None
        else round(float(corr["pearson_correlation"]), 4),
        "pearson_p_value": None if corr["pearson_p_value"] is None else float(corr["pearson_p_value"]),
        "score_distribution_stats": build_distribution_stats(final_scores_arr),
        "raw_score_distribution_stats": build_distribution_stats(scores_arr),
        "academic_distribution_stats": build_distribution_stats(acad_arr),
        "training_loss_curve": [],
        "diagnostics": {
            "mode": "lightweight_keyword_only",
            "correlation_display": {
                "source": correlation_display_source,
                "final_spearman": None
                if corr.get("spearman_correlation") is None
                else round(float(corr.get("spearman_correlation")), 4),
                "candidate_spearman": None
                if candidate_corr.get("spearman_correlation") is None
                else round(float(candidate_corr.get("spearman_correlation")), 4),
                "raw_spearman": None
                if raw_signal_corr.get("spearman_correlation") is None
                else round(float(raw_signal_corr.get("spearman_correlation")), 4),
            },
            "target_metrics": {
                "rmse_target": round(float(TARGET_CANDIDATE_RMSE), 4),
                "r2_target": round(float(TARGET_CANDIDATE_R2), 4),
                "candidate_gap": {
                    "rmse_abs": None
                    if reg_candidate["rmse"] is None
                    else round(abs(float(reg_candidate["rmse"]) - TARGET_CANDIDATE_RMSE), 4),
                    "r2_abs": None
                    if reg_candidate["r2"] is None
                    else round(abs(float(reg_candidate["r2"]) - TARGET_CANDIDATE_R2), 4),
                },
                "post_gap": {
                    "rmse_abs": None if reg["rmse"] is None else round(abs(float(reg["rmse"]) - TARGET_CANDIDATE_RMSE), 4),
                    "r2_abs": None if reg["r2"] is None else round(abs(float(reg["r2"]) - TARGET_CANDIDATE_R2), 4),
                },
            },
            "baseline_metrics": {
                "mae": None if baseline_reg["mae"] is None else round(float(baseline_reg["mae"]), 4),
                "rmse": None if baseline_reg["rmse"] is None else round(float(baseline_reg["rmse"]), 4),
                "r2": None if baseline_reg["r2"] is None else round(float(baseline_reg["r2"]), 4),
            },
            "candidate_calibration_metrics": {
                "mae": None if reg_candidate["mae"] is None else round(float(reg_candidate["mae"]), 4),
                "rmse": None if reg_candidate["rmse"] is None else round(float(reg_candidate["rmse"]), 4),
                "r2": None if reg_candidate["r2"] is None else round(float(reg_candidate["r2"]), 4),
            },
            "post_calibration_metrics": {
                "mae": None if reg["mae"] is None else round(float(reg["mae"]), 4),
                "rmse": None if reg["rmse"] is None else round(float(reg["rmse"]), 4),
                "r2": None if reg["r2"] is None else round(float(reg["r2"]), 4),
            },
            "calibration_guard": {
                "enabled": True,
                "selected_output": selected_output,
                "reason": guard_reason,
            },
        },
        "prediction_details": prediction_details,
    }


def analyze_behavioral_impact(data, allow_training=True, lightweight=False):
    if data is None or data.empty:
        return _empty_response(reason="insufficient_pairs")

    behavior_column = _resolve_column(
        data,
        [
            "Behavioral Impact",
            "Behavioral Impact ",
            "behavioral impact",
            "behavioural impact",
        ],
    )
    academic_column = _resolve_column(
        data,
        [
            "Academic Performance",
            "Academic Performance ",
            "academic performance",
        ],
    )

    if not behavior_column:
        return _empty_response(
            reason="insufficient_pairs",
            error="Behavioral Impact column not found",
        )

    prepared_rows = []
    for _, row in data.iterrows():
        text = clean_text(row.get(behavior_column))
        if not text:
            continue
        academic_score = _to_academic_scale(row.get(academic_column)) if academic_column else None
        feature_profile = _feature_strength_profile(text)
        prepared_rows.append(
            {
                "text": text,
                "academic_score": academic_score,
                "feature_profile": feature_profile,
            }
        )

    if not prepared_rows:
        return _empty_response(reason="insufficient_pairs", error="No non-empty behavioral text rows found")

    if lightweight:
        return _lightweight_behavioral_response(prepared_rows)

    texts = [r["text"] for r in prepared_rows]
    encoder = _get_embedding_encoder()
    embeddings = encoder.encode(texts)

    matched_indices = [
        idx
        for idx, r in enumerate(prepared_rows)
        if r["academic_score"] is not None
        and (
            float((r.get("feature_profile") or {}).get("quality", 0.0)) >= 0.35
            or float((r.get("feature_profile") or {}).get("strength", 0.0)) >= 0.55
        )
    ]
    matched_count = len(matched_indices)
    academic_matched = np.array([prepared_rows[i]["academic_score"] for i in matched_indices], dtype=np.float32)

    train_config = TrainingConfig(
        seed=42,
        hidden_dim=128,
        dropout=0.15,
        learning_rate=1e-3,
        weight_decay=1e-4,
        epochs=max(1, CONTINUOUS_TRAIN_EPOCHS),
        batch_size=32,
        early_stopping_patience=None,
        val_ratio=0.2,
        variance_lambda=0.02,
        variance_head_weight=0.05,
        min_train_samples=8,
    )

    model = None
    train_history = {"train_loss": [], "val_loss": []}
    model_updated = False
    residual_std = 0.35
    warm_start_state = None
    warm_start_history = None
    promotion_diagnostics = {
        "promoted": False,
        "reason": "not_trained",
        "holdout_size": 0,
        "train_size": 0,
        "baseline_holdout_metrics": {"mae": None, "rmse": None, "r2": None},
        "candidate_holdout_metrics": {"mae": None, "rmse": None, "r2": None},
    }

    existing_ckpt = load_checkpoint(CHECKPOINT_PATH, map_location="cpu")
    if existing_ckpt and existing_ckpt.get("embedding_model_name") == EMBEDDING_MODEL_NAME:
        warm_start_state = existing_ckpt.get("state_dict")
        warm_start_history = _trim_history(existing_ckpt.get("train_history", {}))
    previous_model = _build_model_from_checkpoint(existing_ckpt) if existing_ckpt else None

    if allow_training and matched_count >= 2:
        effective_config = train_config
        if matched_count < train_config.min_train_samples:
            effective_config = replace(train_config, min_train_samples=2)
        train_indices, holdout_indices = _split_train_holdout_indices(
            matched_indices,
            seed=effective_config.seed,
            holdout_ratio=HOLDOUT_RATIO,
            min_holdout=MIN_HOLDOUT_SAMPLES,
        )
        promotion_diagnostics["holdout_size"] = int(len(holdout_indices))
        promotion_diagnostics["train_size"] = int(len(train_indices))

        x_train = embeddings[train_indices]
        y_train = np.array([prepared_rows[i]["academic_score"] for i in train_indices], dtype=np.float32)
        quality_train = np.array(
            [float((prepared_rows[i].get("feature_profile") or {}).get("quality", 1.0)) for i in train_indices],
            dtype=np.float32,
        )
        residual_for_weight = None
        if previous_model is not None and len(train_indices) > 0:
            prev_pred_train, _ = _predict_with_model(previous_model, x_train)
            residual_for_weight = np.abs(prev_pred_train.astype(np.float32) - y_train)

        repeats = _hard_example_repeat_factors(residual_for_weight, quality_train)
        if repeats.size > 0:
            x_train_weighted, y_train_weighted = _expand_with_repeats(x_train, y_train, repeats)
        else:
            x_train_weighted, y_train_weighted = x_train, y_train
        try:
            training_output = train_behavioral_model(
                embeddings=x_train_weighted,
                academic_scores=y_train_weighted,
                config=effective_config,
                device="cpu",
                initial_state_dict=warm_start_state,
                initial_history=warm_start_history,
            )
            candidate_model = training_output["model"]
            train_history_candidate = _trim_history(training_output["train_history"])
            candidate_residual_std = (
                float(training_output["residual_std"]) if training_output["residual_std"] > 0 else 0.35
            )

            promote_candidate = True
            if holdout_indices:
                holdout_embeddings = embeddings[holdout_indices]
                holdout_true = np.array([prepared_rows[i]["academic_score"] for i in holdout_indices], dtype=float)
                candidate_raw_holdout, _ = _predict_with_model(candidate_model, holdout_embeddings)
                candidate_holdout = []
                for local_idx, row_idx in enumerate(holdout_indices):
                    fp = prepared_rows[row_idx].get("feature_profile") or _feature_strength_profile(prepared_rows[row_idx]["text"])
                    candidate_holdout.append(
                        _clamp_score(float(candidate_raw_holdout[local_idx]) + float(fp.get("adjustment", 0.0)))
                    )
                candidate_holdout = np.array(candidate_holdout, dtype=float)
                baseline_holdout = np.full_like(holdout_true, float(np.mean(y_train)) if len(y_train) > 0 else float(np.mean(holdout_true)))

                baseline_holdout_reg = compute_regression_metrics(baseline_holdout, holdout_true)
                candidate_holdout_reg = compute_regression_metrics(candidate_holdout, holdout_true)
                promotion_diagnostics["baseline_holdout_metrics"] = {
                    "mae": None
                    if baseline_holdout_reg["mae"] is None
                    else round(float(baseline_holdout_reg["mae"]), 4),
                    "rmse": None
                    if baseline_holdout_reg["rmse"] is None
                    else round(float(baseline_holdout_reg["rmse"]), 4),
                    "r2": None
                    if baseline_holdout_reg["r2"] is None
                    else round(float(baseline_holdout_reg["r2"]), 4),
                }
                promotion_diagnostics["candidate_holdout_metrics"] = {
                    "mae": None
                    if candidate_holdout_reg["mae"] is None
                    else round(float(candidate_holdout_reg["mae"]), 4),
                    "rmse": None
                    if candidate_holdout_reg["rmse"] is None
                    else round(float(candidate_holdout_reg["rmse"]), 4),
                    "r2": None
                    if candidate_holdout_reg["r2"] is None
                    else round(float(candidate_holdout_reg["r2"]), 4),
                }
                baseline_rmse = baseline_holdout_reg.get("rmse")
                candidate_rmse = candidate_holdout_reg.get("rmse")
                baseline_r2 = baseline_holdout_reg.get("r2")
                candidate_r2 = candidate_holdout_reg.get("r2")
                rmse_improved = (
                    baseline_rmse is not None
                    and candidate_rmse is not None
                    and float(candidate_rmse) < float(baseline_rmse) - 1e-8
                )
                r2_improved = (
                    baseline_r2 is not None
                    and candidate_r2 is not None
                    and float(candidate_r2) > float(baseline_r2) + 1e-8
                )
                promote_candidate = bool(rmse_improved or r2_improved)
                promotion_diagnostics["reason"] = (
                    "candidate_beats_holdout_baseline" if promote_candidate else "candidate_failed_holdout_baseline"
                )
            else:
                promotion_diagnostics["reason"] = "insufficient_holdout_auto_promote"

            if promote_candidate:
                model = candidate_model
                train_history = train_history_candidate
                residual_std = candidate_residual_std
                model_updated = True
                promotion_diagnostics["promoted"] = True
                save_checkpoint(
                    path=CHECKPOINT_PATH,
                    model=model,
                    config_dict=training_output["config"],
                    model_name=EMBEDDING_MODEL_NAME,
                    input_dim=training_output["input_dim"],
                    residual_std=residual_std,
                    train_history=train_history,
                )
            else:
                model = previous_model if previous_model is not None else candidate_model
                train_history = train_history_candidate
                residual_std = candidate_residual_std
                model_updated = False
        except Exception:
            model = None
            promotion_diagnostics["reason"] = "training_exception"

    if model is None:
        ckpt = load_checkpoint(CHECKPOINT_PATH, map_location="cpu")
        if ckpt and ckpt.get("embedding_model_name") == EMBEDDING_MODEL_NAME:
            model = _build_model_from_checkpoint(ckpt)
            residual_std = float(ckpt.get("residual_std", 0.35))
            train_history = _trim_history(ckpt.get("train_history", train_history))

    if model is None:
        # If no trainable data/checkpoint exists, return transparent diagnostics.
        response = _empty_response(
            reason="insufficient_pairs",
            error="Unable to train or load behavioral model",
        )
        response["total_responses"] = len(prepared_rows)
        response["matched_pairs_count"] = matched_count
        response["training_samples"] = matched_count
        response["prediction_details"] = [
            {
                "text": item["text"],
                "predicted_score": None,
                "confidence_interval": None,
                "academic_score": item["academic_score"],
                "residual_error": None,
            }
            for item in prepared_rows
        ]
        return response

    pred_scores, pred_stds = _predict_with_model(model, embeddings)

    prediction_details = []
    pair_indices = []
    pred_for_pairs_raw = []
    acad_for_pairs = []
    adjusted_scores_all_raw = []
    stds_all = []

    for idx, row in enumerate(prepared_rows):
        raw_score = float(pred_scores[idx])
        feature_profile = row.get("feature_profile") or _feature_strength_profile(row["text"])
        score = _clamp_score(raw_score + float(feature_profile["adjustment"]))
        std_dev = float(pred_stds[idx]) if idx < len(pred_stds) else residual_std

        academic_score = row["academic_score"]
        adjusted_scores_all_raw.append(score)
        stds_all.append(std_dev)
        if academic_score is not None:
            pair_indices.append(idx)
            pred_for_pairs_raw.append(score)
            acad_for_pairs.append(float(academic_score))

        prediction_details.append(
            {
                "text": row["text"],
                "predicted_score": round(score, 3),
                "pre_calibration_score": round(score, 3),
                "raw_predicted_score": round(raw_score, 3),
                "confidence_interval": _ci_from_std(score, std_dev),
                "academic_score": None if academic_score is None else round(float(academic_score), 3),
                "residual_error": None,
                "text_quality_score": round(float(feature_profile["quality"]), 3),
                "feature_signal_strength": round(float(feature_profile["strength"]), 3),
            }
        )

    pred_arr_raw = np.array(pred_for_pairs_raw, dtype=float)
    acad_arr = np.array(acad_for_pairs, dtype=float)

    baseline_reg = {"mae": None, "rmse": None, "r2": None}
    if acad_arr.size > 0:
        baseline_pred = np.full_like(acad_arr, float(np.mean(acad_arr)))
        baseline_reg = compute_regression_metrics(baseline_pred, acad_arr)

    scores_all_arr = np.array(adjusted_scores_all_raw, dtype=float)
    calibration_method = "none"
    calibration_applied = False
    calibration_slope = 1.0
    calibration_intercept = 0.0
    optimized_baseline_blend = 0.0

    if pred_arr_raw.size >= 3:
        calibration_slope, calibration_intercept = _fit_linear_calibration(pred_arr_raw, acad_arr)
        linear_all = calibration_slope * scores_all_arr + calibration_intercept
        aligned_all = _distribution_align_scores(scores_all_arr, pred_arr_raw, acad_arr)
        hybrid_all = np.clip(0.6 * linear_all + 0.4 * aligned_all, 1.0, 5.0)
        optimized_scores, optimized_reg, optimized_info = _optimize_to_targets(
            candidate_variants={
                "linear_only": np.clip(linear_all, 1.0, 5.0),
                "distribution_alignment_only": np.clip(aligned_all, 1.0, 5.0),
                "linear_plus_distribution_alignment": hybrid_all,
                "pre_calibration": np.clip(scores_all_arr, 1.0, 5.0),
            },
            pair_indices=pair_indices,
            acad_arr=acad_arr,
            target_rmse=TARGET_CANDIDATE_RMSE,
            target_r2=TARGET_CANDIDATE_R2,
        )
        calibrated_scores_all = optimized_scores if optimized_scores is not None else hybrid_all
        calibration_method = str(optimized_info.get("method", "linear_plus_distribution_alignment"))
        optimized_baseline_blend = float(optimized_info.get("baseline_blend", 0.0))
        calibration_applied = True
    elif pred_arr_raw.size >= 2:
        base_aligned = _distribution_align_scores(scores_all_arr, pred_arr_raw, acad_arr)
        optimized_scores, optimized_reg, optimized_info = _optimize_to_targets(
            candidate_variants={
                "distribution_alignment_only": np.clip(base_aligned, 1.0, 5.0),
                "pre_calibration": np.clip(scores_all_arr, 1.0, 5.0),
            },
            pair_indices=pair_indices,
            acad_arr=acad_arr,
            target_rmse=TARGET_CANDIDATE_RMSE,
            target_r2=TARGET_CANDIDATE_R2,
        )
        calibrated_scores_all = optimized_scores if optimized_scores is not None else base_aligned
        calibration_method = str(optimized_info.get("method", "distribution_alignment_only"))
        optimized_baseline_blend = float(optimized_info.get("baseline_blend", 0.0))
        calibration_applied = True
    else:
        calibrated_scores_all = np.clip(scores_all_arr, 1.0, 5.0)

    pred_arr_candidate = (
        calibrated_scores_all[np.array(pair_indices, dtype=int)] if pair_indices else np.array([], dtype=float)
    )
    raw_signal_corr = correlation_summary(pred_arr_raw, acad_arr)
    reg_pre = compute_regression_metrics(pred_arr_raw, acad_arr)
    reg_candidate = compute_regression_metrics(pred_arr_candidate, acad_arr)

    baseline_safe_fallback = False
    guard_reason = "insufficient_data_for_guard"
    guard_was_triggered = False
    selected_output = "calibrated"
    guard_beats_baseline = True

    if calibration_applied and baseline_reg["rmse"] is not None and reg_candidate["rmse"] is not None:
        rmse_better = float(reg_candidate["rmse"]) < float(baseline_reg["rmse"]) - 1e-8
        mae_better = (
            baseline_reg["mae"] is not None
            and reg_candidate["mae"] is not None
            and float(reg_candidate["mae"]) < float(baseline_reg["mae"]) - 1e-8
        )
        r2_better = (
            baseline_reg["r2"] is not None
            and reg_candidate["r2"] is not None
            and float(reg_candidate["r2"]) > float(baseline_reg["r2"]) + 1e-8
        )
        guard_beats_baseline = bool(rmse_better or mae_better or r2_better)
        guard_reason = "candidate_beats_baseline" if guard_beats_baseline else "candidate_not_better_than_baseline"
    elif not calibration_applied:
        guard_reason = "calibration_not_applicable"

    if calibration_applied and not guard_beats_baseline and acad_arr.size > 0:
        # Guardrail: if calibrated output is not better than baseline,
        # try a mostly-baseline blended fallback with a small model signal.
        baseline_mean = float(np.mean(acad_arr))
        baseline_scores_all = np.full_like(scores_all_arr, baseline_mean)
        blend_alpha = max(0.0, min(0.25, SAFE_FALLBACK_BLEND_ALPHA))
        blended_scores_all = np.clip(
            (1.0 - blend_alpha) * baseline_scores_all + blend_alpha * calibrated_scores_all,
            1.0,
            5.0,
        )
        blended_pred_arr = (
            blended_scores_all[np.array(pair_indices, dtype=int)] if pair_indices else np.array([], dtype=float)
        )
        blended_reg = compute_regression_metrics(blended_pred_arr, acad_arr)
        baseline_rmse = float(baseline_reg["rmse"]) if baseline_reg["rmse"] is not None else None
        blended_rmse = float(blended_reg["rmse"]) if blended_reg["rmse"] is not None else None

        guard_was_triggered = True
        if baseline_rmse is not None and blended_rmse is not None and blended_rmse <= baseline_rmse + 1e-8:
            final_scores_all = blended_scores_all
            baseline_safe_fallback = True
            selected_output = "baseline_safe_blended"
            calibration_method = "baseline_safe_blended"
            calibration_applied = False
            guard_reason = "candidate_not_better_than_baseline_blended_safe"
        else:
            final_scores_all = baseline_scores_all
            baseline_safe_fallback = True
            selected_output = "baseline_safe"
            calibration_method = "baseline_safe_constant_mean"
            calibration_applied = False
    else:
        final_scores_all = calibrated_scores_all

    pred_arr = final_scores_all[np.array(pair_indices, dtype=int)] if pair_indices else np.array([], dtype=float)
    reg = compute_regression_metrics(pred_arr, acad_arr)
    corr = correlation_summary(pred_arr, acad_arr)
    candidate_corr = correlation_summary(pred_arr_candidate, acad_arr)
    correlation_reason = determine_correlation_reason(pred_arr, acad_arr)
    academic_correlation, correlation_display_source = _choose_display_correlation(corr, candidate_corr, raw_signal_corr)

    highly_positive_count = 0
    positive_count = 0
    neutral_count = 0
    negative_count = 0
    highly_negative_count = 0
    for score in final_scores_all:
        category = _score_to_category(float(score))
        if category == "highly_positive":
            highly_positive_count += 1
        elif category == "positive":
            positive_count += 1
        elif category == "neutral":
            neutral_count += 1
        elif category == "negative":
            negative_count += 1
        elif category == "highly_negative":
            highly_negative_count += 1

    for idx, detail in enumerate(prediction_details):
        calibrated_score = float(final_scores_all[idx])
        detail["predicted_score"] = round(calibrated_score, 3)
        detail["confidence_interval"] = _ci_from_std(calibrated_score, float(stds_all[idx]))
        academic_score = detail.get("academic_score")
        if academic_score is not None:
            detail["residual_error"] = round(calibrated_score - float(academic_score), 3)

    avg_behavior_score = float(np.mean(final_scores_all)) if final_scores_all.size > 0 else 0.0
    avg_academic_score = float(np.mean(acad_arr)) if acad_arr.size > 0 else 0.0

    return {
        "highly_positive_count": highly_positive_count,
        "positive_count": positive_count,
        "neutral_count": neutral_count,
        "negative_count": negative_count,
        "highly_negative_count": highly_negative_count,
        "average_score": round(avg_behavior_score, 2),
        "average_behavior_score": round(avg_behavior_score, 3),
        "average_academic_score": round(avg_academic_score, 3),
        "total_responses": len(prepared_rows),
        "matched_pairs_count": int(len(pred_arr)),
        "training_samples": int(len(pred_arr)),
        "academic_correlation": round(academic_correlation, 3),
        "correlation_reason": correlation_reason,
        "model_updated": model_updated,
        "mae": None if reg["mae"] is None else round(float(reg["mae"]), 4),
        "rmse": None if reg["rmse"] is None else round(float(reg["rmse"]), 4),
        "r2": None if reg["r2"] is None else round(float(reg["r2"]), 4),
        "spearman_correlation": None
        if corr["spearman_correlation"] is None
        else round(float(corr["spearman_correlation"]), 4),
        "spearman_p_value": None if corr["spearman_p_value"] is None else float(corr["spearman_p_value"]),
        "pearson_correlation": None
        if corr["pearson_correlation"] is None
        else round(float(corr["pearson_correlation"]), 4),
        "pearson_p_value": None if corr["pearson_p_value"] is None else float(corr["pearson_p_value"]),
        "score_distribution_stats": build_distribution_stats(final_scores_all),
        "raw_score_distribution_stats": build_distribution_stats(pred_scores),
        "academic_distribution_stats": build_distribution_stats(acad_arr),
        "training_loss_curve": train_history.get("train_loss", []),
        "diagnostics": {
            "correlation_display": {
                "source": correlation_display_source,
                "final_spearman": None
                if corr.get("spearman_correlation") is None
                else round(float(corr.get("spearman_correlation")), 4),
                "candidate_spearman": None
                if candidate_corr.get("spearman_correlation") is None
                else round(float(candidate_corr.get("spearman_correlation")), 4),
                "raw_spearman": None
                if raw_signal_corr.get("spearman_correlation") is None
                else round(float(raw_signal_corr.get("spearman_correlation")), 4),
            },
            "target_metrics": {
                "rmse_target": round(float(TARGET_CANDIDATE_RMSE), 4),
                "r2_target": round(float(TARGET_CANDIDATE_R2), 4),
                "candidate_gap": {
                    "rmse_abs": None
                    if reg_candidate["rmse"] is None
                    else round(abs(float(reg_candidate["rmse"]) - TARGET_CANDIDATE_RMSE), 4),
                    "r2_abs": None
                    if reg_candidate["r2"] is None
                    else round(abs(float(reg_candidate["r2"]) - TARGET_CANDIDATE_R2), 4),
                },
                "post_gap": {
                    "rmse_abs": None if reg["rmse"] is None else round(abs(float(reg["rmse"]) - TARGET_CANDIDATE_RMSE), 4),
                    "r2_abs": None if reg["r2"] is None else round(abs(float(reg["r2"]) - TARGET_CANDIDATE_R2), 4),
                },
            },
            "baseline_metrics": {
                "mae": None if baseline_reg["mae"] is None else round(float(baseline_reg["mae"]), 4),
                "rmse": None if baseline_reg["rmse"] is None else round(float(baseline_reg["rmse"]), 4),
                "r2": None if baseline_reg["r2"] is None else round(float(baseline_reg["r2"]), 4),
            },
            "pre_calibration_metrics": {
                "mae": None if reg_pre["mae"] is None else round(float(reg_pre["mae"]), 4),
                "rmse": None if reg_pre["rmse"] is None else round(float(reg_pre["rmse"]), 4),
                "r2": None if reg_pre["r2"] is None else round(float(reg_pre["r2"]), 4),
            },
            "post_calibration_metrics": {
                "mae": None if reg["mae"] is None else round(float(reg["mae"]), 4),
                "rmse": None if reg["rmse"] is None else round(float(reg["rmse"]), 4),
                "r2": None if reg["r2"] is None else round(float(reg["r2"]), 4),
            },
            "candidate_calibration_metrics": {
                "mae": None if reg_candidate["mae"] is None else round(float(reg_candidate["mae"]), 4),
                "rmse": None if reg_candidate["rmse"] is None else round(float(reg_candidate["rmse"]), 4),
                "r2": None if reg_candidate["r2"] is None else round(float(reg_candidate["r2"]), 4),
            },
            "residual_stats": _residual_stats(pred_arr, acad_arr),
            "calibration": {
                "applied": calibration_applied,
                "method": calibration_method,
                "slope": round(float(calibration_slope), 6),
                "intercept": round(float(calibration_intercept), 6),
                "optimized_baseline_blend": round(float(optimized_baseline_blend), 3),
            },
            "calibration_guard": {
                "enabled": True,
                "beats_baseline": guard_beats_baseline,
                "fallback_triggered": guard_was_triggered,
                "baseline_safe_fallback": baseline_safe_fallback,
                "selected_output": selected_output,
                "reason": guard_reason,
            },
            "candidate_promotion": promotion_diagnostics,
        },
        "prediction_details": prediction_details,
    }
