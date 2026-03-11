from __future__ import annotations

from typing import Any, Dict, List, Sequence

import pandas as pd

REQUIRED_COLUMNS = [
    "family_income_stability",
    "behavioral_traits",
    "role_model_exposure",
    "career_confidence",
]


def _coerce_dataframe(records: Sequence[dict]) -> pd.DataFrame:
    df = pd.DataFrame.from_records(records or [])
    if df.empty:
        raise ValueError("No data provided.")

    df = df.rename(columns={c: c.strip().lower().replace(" ", "_") for c in df.columns})

    alias_map = {
        "family_income": "family_income_stability",
        "income_stability": "family_income_stability",
        "income": "family_income_stability",
        "behavior": "behavioral_traits",
        "behavioral": "behavioral_traits",
        "behavior_traits": "behavioral_traits",
        "role_model": "role_model_exposure",
        "role_models": "role_model_exposure",
        "role_model_support": "role_model_exposure",
        "career": "career_confidence",
        "confidence": "career_confidence",
    }
    for alias, target in alias_map.items():
        if alias in df.columns and target not in df.columns:
            df[target] = df[alias]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    df = df[REQUIRED_COLUMNS].apply(pd.to_numeric, errors="coerce")
    df = df.dropna()

    if len(df) < 5:
        raise ValueError("At least 5 complete observations are required for regression.")

    return df


def _load_statsmodels() -> Any:
    """
    Import statsmodels lazily so backend startup doesn't fail when optional
    scientific dependencies are temporarily mismatched.
    """
    try:
        import statsmodels.api as sm  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "statsmodels/scipy dependency mismatch. Reinstall backend requirements "
            "to run career confidence regression."
        ) from exc
    return sm


def _format_coefficients(model: Any) -> List[Dict]:
    coeffs = []
    for name, coef in model.params.items():
        label = "intercept" if name == "const" else name
        p_value = float(model.pvalues[name])
        coeffs.append(
            {
                "name": label,
                "coefficient": round(float(coef), 4),
                "p_value": round(p_value, 4),
                "significant": bool(p_value < 0.05),
            }
        )
    return coeffs


def run_career_confidence_models(records: Sequence[dict]) -> Dict:
    """
    Run hierarchical OLS models predicting career confidence.
    """
    sm = _load_statsmodels()
    df = _coerce_dataframe(records)
    y = df["career_confidence"]

    models_spec = [
        ("income_only", ["family_income_stability"]),
        ("income_plus_behavior", ["family_income_stability", "behavioral_traits"]),
        (
            "full_model",
            ["family_income_stability", "behavioral_traits", "role_model_exposure"],
        ),
    ]

    results = []
    prev_r2 = None

    for name, predictors in models_spec:
        X = sm.add_constant(df[predictors])
        model = sm.OLS(y, X).fit()
        r2 = float(model.rsquared)
        adj_r2 = float(model.rsquared_adj)

        model_entry = {
            "name": name,
            "predictors": predictors,
            "coefficients": _format_coefficients(model),
            "r_squared_adj": round(adj_r2, 4),
            "r_squared": round(r2, 4),
            "delta_r_squared": None if prev_r2 is None else round(r2 - prev_r2, 4),
        }
        results.append(model_entry)
        prev_r2 = r2

    full_model = results[-1]
    coeffs = [c for c in full_model["coefficients"] if c["name"] != "intercept"]
    strongest = max(coeffs, key=lambda c: abs(c["coefficient"])) if coeffs else None

    summary = ""
    if strongest:
        summary = (
            "Income stability, behavioral strengths, and role-model exposure together explain "
            f"{int(round(full_model['r_squared'] * 100))}% of career confidence variation. "
            f"{strongest['name'].replace('_', ' ').title()} shows the strongest link "
            f"({'+' if strongest['coefficient'] >= 0 else ''}{round(strongest['coefficient'], 2)}; "
            f"p={strongest['p_value']}). "
            "Students with steadier income contexts, supportive behaviors, and richer role-model exposure "
            "tend to report higher career confidence. Focus interventions on behavioral skill-building and "
            "connecting students to positive role models while sustaining income stability supports."
        )

    return {
        "models": results,
        "strongest_predictor": strongest,
        "summary": summary,
    }

