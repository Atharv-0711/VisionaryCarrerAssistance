import re
from collections import defaultdict

import numpy as np
import pandas as pd


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

THEME_PATTERNS = [
    ("financial_stress", r"\b(no money|money problem|financial|debt|loan|poverty|income issue|can't afford)\b", -1.1),
    ("domestic_conflict", r"\b(fight|conflict|quarrel|argument|separation|divorce|family stress|tension at home)\b", -1.2),
    (
        "violence_abuse",
        r"\b(violence|abuse|beating|harassment|unsafe|threat|aggression|aggressive|home aggression|violent attitude|bad attitude)\b",
        -1.8,
    ),
    ("health_issue", r"\b(illness|sick|disease|medical|hospital|disabled|health issue)\b", -1.0),
    ("addiction_issue", r"\b(alcohol|drinking|drug|addiction|substance)\b", -1.3),
    ("resource_constraints", r"\b(no electricity|power cut|no water|overcrowded|no room|poor housing|no light)\b", -1.3),
    ("caregiver_absence", r"\b(single parent|no parent|orphan|parents away|working all day|left alone)\b", -1.1),
    ("no_problem", r"\b(no problem|none|nothing|all good|no issue|stable home)\b", 0.7),
]

RELATION_PATTERNS = {
    "father": r"\b(father|dad|papa|stepfather)\b",
    "mother": r"\b(mother|mom|mummy|stepmother)\b",
    "brother": r"\b(brother|sibling brother)\b",
    "sister": r"\b(sister|sibling sister)\b",
    "grandfather": r"\b(grandfather|grandpa|dada|nana)\b",
    "grandmother": r"\b(grandmother|grandma|dadi|nani)\b",
    "uncle": r"\b(uncle|chacha|mama|tau)\b",
    "aunt": r"\b(aunt|aunty|bua|mausi)\b",
}

# Relative-specific impact when a relationship is mentioned with problem context.
RELATION_PROBLEM_WEIGHTS = {
    "father": -0.24,
    "mother": -0.22,
    "brother": -0.16,
    "sister": -0.16,
    "grandfather": -0.14,
    "grandmother": -0.14,
    "uncle": -0.14,
    "aunt": -0.14,
}

RELATION_PROBLEM_CONTEXT = re.compile(
    r"\b(fight|quarrel|conflict|abuse|violence|beating|threat|alcohol|drinking|drug|addiction|pressure|stress|harass|unsafe|fear|argument)\b"
)
RELATION_SUPPORT_CONTEXT = re.compile(r"\b(support|care|help|encourage|peaceful|understanding|guidance)\b")


def _resolve_column(df, primary_name):
    if primary_name in df.columns:
        return primary_name

    normalized_target = primary_name.strip().lower()
    for col in df.columns:
        if str(col).strip().lower() == normalized_target:
            return col
    return None


def _clamp(value, min_value=1.0, max_value=5.0):
    return max(min_value, min(max_value, float(value)))


def _to_academic_scale(value):
    if value is None or pd.isna(value):
        return None

    if isinstance(value, (int, float, np.number)):
        numeric = float(value)
        if numeric < 0:
            return None
        if numeric <= 5:
            return _clamp(numeric if numeric > 0 else 1.0)
        if numeric <= 10:
            return _clamp(numeric / 2.0)
        if numeric <= 100:
            return _clamp(numeric / 20.0)
        return _clamp(numeric)

    text = str(value).strip().lower()
    if not text:
        return None

    grade_map = {"a+": 5, "a": 4.8, "b+": 4.2, "b": 4, "c+": 3.2, "c": 3, "d": 2, "f": 1}
    if text in grade_map:
        return grade_map[text]

    for label, score in ACADEMIC_TEXT_TO_SCORE.items():
        if label in text:
            return score

    try:
        cleaned = text.replace("%", "").replace("/10", "").replace("/5", "")
        return _to_academic_scale(float(cleaned))
    except Exception:
        return None


def _sentiment_bucket(score):
    if score >= 4.5:
        return "Highly Positive"
    if score >= 3.5:
        return "Positive"
    if score >= 2.5:
        return "Neutral"
    if score >= 1.5:
        return "Negative"
    return "Highly Negative"


def _score_problem_text(text):
    cleaned = " ".join(str(text).strip().lower().split())
    if not cleaned:
        return 3.0, "other", [], 0.0

    score = 3.0
    matched_theme = "other"
    strongest_weight = 0.0

    for theme, pattern, weight in THEME_PATTERNS:
        if re.search(pattern, cleaned):
            score += weight
            if abs(weight) > abs(strongest_weight):
                strongest_weight = weight
                matched_theme = theme

    # Small lexical fallback so unknown texts still carry polarity signal.
    negative_tokens = ["stress", "problem", "difficult", "hard", "sad", "fear", "anxiety", "worry"]
    positive_tokens = ["support", "peace", "stable", "happy", "encourage", "care"]
    score -= sum(0.08 for token in negative_tokens if token in cleaned)
    score += sum(0.08 for token in positive_tokens if token in cleaned)

    matched_relations = [relation for relation, pattern in RELATION_PATTERNS.items() if re.search(pattern, cleaned)]
    relation_impact = 0.0
    if matched_relations:
        has_problem_context = RELATION_PROBLEM_CONTEXT.search(cleaned) is not None
        has_support_context = RELATION_SUPPORT_CONTEXT.search(cleaned) is not None
        if has_problem_context:
            relation_impact = sum(RELATION_PROBLEM_WEIGHTS.get(relation, -0.12) for relation in matched_relations)
            relation_impact = max(-0.9, relation_impact)
        elif has_support_context:
            relation_impact = min(0.35, 0.1 * len(matched_relations))
        score += relation_impact

    return _clamp(score), matched_theme, matched_relations, relation_impact


def _safe_correlation(x_values, y_values):
    if len(x_values) < 2 or len(y_values) < 2:
        return 0.0
    x_arr = np.array(x_values, dtype=float)
    y_arr = np.array(y_values, dtype=float)
    if np.std(x_arr) == 0 or np.std(y_arr) == 0:
        return 0.0
    return float(np.corrcoef(x_arr, y_arr)[0, 1])


def analyze_problems_in_home(data):
    default_result = {
        "highly_positive_count": 0,
        "positive_count": 0,
        "neutral_count": 0,
        "negative_count": 0,
        "highly_negative_count": 0,
        "average_score": 0,
        "total_responses": 0,
        "matched_pairs_count": 0,
        "academic_correlation": 0,
        "theme_distribution": [],
        "problems_details": [],
    }

    if data is None or data.empty:
        return default_result

    problems_column = _resolve_column(data, "Problems in Home ")
    academic_column = _resolve_column(data, "Academic Performance ")

    if not problems_column:
        payload = default_result.copy()
        payload["error"] = "Problems in Home column not found"
        return payload

    counts = {
        "Highly Positive": 0,
        "Positive": 0,
        "Neutral": 0,
        "Negative": 0,
        "Highly Negative": 0,
    }
    theme_counts = defaultdict(int)
    total_score = 0.0
    processed_count = 0
    sentiment_for_pairs = []
    academic_for_pairs = []
    details = []

    for _, row in data.iterrows():
        raw_problem = row.get(problems_column)
        if raw_problem is None or pd.isna(raw_problem):
            continue

        problem_text = str(raw_problem).strip()
        if not problem_text:
            continue

        sentiment_score, theme, matched_relations, relation_impact = _score_problem_text(problem_text)
        category = _sentiment_bucket(sentiment_score)
        academic_score = _to_academic_scale(row.get(academic_column)) if academic_column else None

        counts[category] += 1
        theme_counts[theme] += 1
        processed_count += 1
        total_score += sentiment_score

        if academic_score is not None:
            sentiment_for_pairs.append(sentiment_score)
            academic_for_pairs.append(academic_score)

        details.append(
            {
                "problem": problem_text,
                "theme": theme,
                "sentiment_score": round(sentiment_score, 3),
                "category": category,
                "matched_relations": matched_relations,
                "relation_impact": round(float(relation_impact), 3),
                "academic_score": None if academic_score is None else round(float(academic_score), 3),
            }
        )

    # Lightweight export for parity with other analyzers.
    try:
        if details:
            pd.DataFrame(details).to_excel("home_problems_sentiment_analysis.xlsx", index=False)
    except Exception as exc:
        print(f"Error saving home problems analysis: {exc}")

    academic_correlation = _safe_correlation(sentiment_for_pairs, academic_for_pairs)
    theme_distribution = [
        {"theme": theme, "count": count}
        for theme, count in sorted(theme_counts.items(), key=lambda item: item[1], reverse=True)
    ]

    return {
        "highly_positive_count": counts["Highly Positive"],
        "positive_count": counts["Positive"],
        "neutral_count": counts["Neutral"],
        "negative_count": counts["Negative"],
        "highly_negative_count": counts["Highly Negative"],
        "average_score": round(total_score / processed_count, 3) if processed_count else 0,
        "total_responses": processed_count,
        "matched_pairs_count": len(academic_for_pairs),
        "academic_correlation": round(academic_correlation, 3),
        "theme_distribution": theme_distribution,
        "problems_details": details,
    }

