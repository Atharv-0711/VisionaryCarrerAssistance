import json
import os
from datetime import datetime

import numpy as np
import pandas as pd

CATEGORY_ORDER = [
    "below_poverty_line",
    "low_income",
    "below_average",
    "average",
    "above_average",
]
CATEGORY_TO_SCORE = {
    "below_poverty_line": 1.0,
    "low_income": 2.0,
    "below_average": 3.0,
    "average": 4.0,
    "above_average": 5.0,
}
BOUNDARY_KEYS = ["poverty_line", "low_income", "below_average", "average"]
INCOME_RL_TRAIN_ON_ANALYSIS = os.getenv("INCOME_RL_TRAIN_ON_ANALYSIS", "0").lower() in {"1", "true", "yes"}

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


def _resolve_column(df, primary_name):
    """Resolve exact or trimmed column names (handles trailing spaces)."""
    if primary_name in df.columns:
        return primary_name

    normalized_target = primary_name.strip().lower()
    for col in df.columns:
        if str(col).strip().lower() == normalized_target:
            return col
    return None


def _clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def _to_academic_scale(value):
    """
    Convert raw academic performance values to a 1-5 scale.
    Supports numeric values (1-5, 0-10, 0-100) and common text labels.
    """
    if value is None or pd.isna(value):
        return None

    if isinstance(value, (int, float, np.number)):
        numeric = float(value)
        if numeric < 0:
            return None
        if numeric <= 5:
            return _clamp(numeric if numeric > 0 else 1, 1, 5)
        if numeric <= 10:
            return _clamp(numeric / 2.0, 1, 5)
        if numeric <= 100:
            return _clamp(numeric / 20.0, 1, 5)
        return _clamp(numeric, 1, 5)

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


class IncomeCategoryRL:
    """RL agent for optimizing income category thresholds."""

    def __init__(self, initial_thresholds=None, learning_rate=0.08):
        self.default_thresholds = {
            "poverty_line": 2250,
            "low_income": 10000,
            "below_average": 25000,
            "average": 45000,
        }
        os.makedirs("models", exist_ok=True)

        loaded_thresholds = initial_thresholds
        if loaded_thresholds is None:
            try:
                with open("models/income_threshold_model.json", "r") as f:
                    loaded_thresholds = json.load(f)
                print("Loaded income threshold model from file")
            except (FileNotFoundError, json.JSONDecodeError):
                print("Using default income thresholds")
                loaded_thresholds = self.default_thresholds.copy()

        self.thresholds = self._sanitize_thresholds(loaded_thresholds)
        self.learning_rate = learning_rate
        self.experience_buffer = []
        self.log_file = "models/income_rl_learning_log.txt"

        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("Timestamp,Threshold,OldValue,NewValue,Feedback\n")

    def _sanitize_thresholds(self, raw_thresholds):
        merged = self.default_thresholds.copy()
        if isinstance(raw_thresholds, dict):
            for key in BOUNDARY_KEYS:
                if key in raw_thresholds:
                    try:
                        merged[key] = float(raw_thresholds[key])
                    except Exception:
                        pass
        ordered = self._ensure_ordered_thresholds(merged)
        return {k: int(round(v)) for k, v in ordered.items()}

    def _ensure_ordered_thresholds(self, thresholds):
        sanitized = thresholds.copy()
        sanitized["poverty_line"] = max(500, sanitized["poverty_line"])
        sanitized["low_income"] = max(sanitized["poverty_line"] + 100, sanitized["low_income"])
        sanitized["below_average"] = max(sanitized["low_income"] + 100, sanitized["below_average"])
        sanitized["average"] = max(sanitized["below_average"] + 100, sanitized["average"])
        return sanitized

    def categorize_income(self, income):
        income = float(income)
        if income < self.thresholds["poverty_line"]:
            return "below_poverty_line"
        if income < self.thresholds["low_income"]:
            return "low_income"
        if income < self.thresholds["below_average"]:
            return "below_average"
        if income < self.thresholds["average"]:
            return "average"
        return "above_average"

    def get_income_score(self, income):
        category = self.categorize_income(income)
        return CATEGORY_TO_SCORE.get(category, 3.0)

    def add_feedback(self, income, predicted_category, correct_category):
        """Record manual feedback for threshold updates."""
        self.experience_buffer.append(
            {
                "income": float(income),
                "predicted": str(predicted_category),
                "actual": str(correct_category),
                "timestamp": datetime.now().isoformat(),
            }
        )
        print(
            f"Added feedback: income={income}, predicted={predicted_category}, actual={correct_category}"
        )
        return len(self.experience_buffer)

    def update_thresholds(self):
        """
        Apply RL-style updates by moving the relevant boundaries toward the
        feedback point while preserving valid threshold order.
        """
        if not self.experience_buffer:
            print("No feedback to learn from")
            return False

        updates_made = 0
        for feedback in self.experience_buffer:
            income = feedback["income"]
            predicted = feedback["predicted"]
            actual = feedback["actual"]
            if predicted == actual:
                continue
            if predicted not in CATEGORY_ORDER or actual not in CATEGORY_ORDER:
                continue

            predicted_idx = CATEGORY_ORDER.index(predicted)
            actual_idx = CATEGORY_ORDER.index(actual)
            lower = min(predicted_idx, actual_idx)
            upper = max(predicted_idx, actual_idx)

            for boundary_idx in range(lower, upper):
                threshold_key = BOUNDARY_KEYS[boundary_idx]
                old_value = float(self.thresholds[threshold_key])
                target = float(income - 100 if actual_idx > predicted_idx else income + 100)
                new_value = old_value + self.learning_rate * (target - old_value)

                # Avoid getting stuck when rounded values collapse to old threshold.
                if int(round(new_value)) == int(round(old_value)) and old_value != target:
                    step = 1 if target > old_value else -1
                    new_value = old_value + step

                self.thresholds[threshold_key] = new_value
                self.thresholds = self._sanitize_thresholds(self.thresholds)
                self._log_update(
                    threshold_key,
                    old_value,
                    self.thresholds[threshold_key],
                    f"income={income}, predicted={predicted}, actual={actual}",
                )
                updates_made += 1

        self.experience_buffer = []
        if updates_made > 0:
            self.save_thresholds()
        return updates_made > 0

    def save_thresholds(self, filename="models/income_threshold_model.json"):
        try:
            with open(filename, "w") as f:
                json.dump(self.thresholds, f, indent=2)
            print(f"Saved income thresholds to {filename}")
            return True
        except Exception as e:
            print(f"Error saving thresholds: {e}")
            return False

    def _log_update(self, threshold_name, old_value, new_value, feedback):
        try:
            with open(self.log_file, "a") as f:
                f.write(
                    f"{datetime.now().isoformat()},{threshold_name},{old_value},{new_value},{feedback}\n"
                )
        except Exception as e:
            print(f"Error logging update: {e}")

    @classmethod
    def load_model(cls, filename="models/income_threshold_model.json"):
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    thresholds = json.load(f)
                print(f"Loaded thresholds from {filename}")
                return cls(initial_thresholds=thresholds)
            print(f"Model file {filename} not found, using default thresholds")
            return cls()
        except Exception as e:
            print(f"Error loading thresholds: {e}")
            return cls()


class IncomeAcademicRL:
    """RL model that learns expected academic performance per income category."""

    def __init__(self, initial_scores=None, learning_rate=0.06):
        self.default_scores = {
            "below_poverty_line": 1.8,
            "low_income": 2.4,
            "below_average": 3.1,
            "average": 3.9,
            "above_average": 4.5,
        }
        self.learning_rate = learning_rate
        self.experience_buffer = []
        self.model_file = "models/income_academic_rl_model.json"
        os.makedirs("models", exist_ok=True)

        scores = initial_scores
        if scores is None:
            try:
                with open(self.model_file, "r") as f:
                    scores = json.load(f)
                print("Loaded income-academic RL model from file")
            except (FileNotFoundError, json.JSONDecodeError):
                scores = self.default_scores.copy()
                print("Using default income-academic RL priors")

        self.category_scores = self._sanitize_scores(scores)

    def _sanitize_scores(self, raw_scores):
        merged = self.default_scores.copy()
        if isinstance(raw_scores, dict):
            for category in CATEGORY_ORDER:
                if category in raw_scores:
                    try:
                        merged[category] = float(raw_scores[category])
                    except Exception:
                        pass
        return {k: float(_clamp(v, 1, 5)) for k, v in merged.items()}

    def get_expected_score(self, category):
        return float(self.category_scores.get(category, 3.0))

    def add_experience(self, category, observed_academic_score, sample_weight=1.0):
        if category not in CATEGORY_ORDER or observed_academic_score is None:
            return
        self.experience_buffer.append(
            {
                "category": category,
                "observed": float(observed_academic_score),
                "weight": float(sample_weight) if sample_weight is not None else 1.0,
            }
        )

    def update_model(self):
        if not self.experience_buffer:
            print("No income-academic experiences to learn from")
            return False

        for exp in self.experience_buffer:
            category = exp["category"]
            observed = exp["observed"]
            weight = exp["weight"]
            old_score = self.category_scores[category]
            error = observed - old_score
            new_score = old_score + self.learning_rate * error * weight
            self.category_scores[category] = float(_clamp(new_score, 1, 5))

        self.experience_buffer = []
        self.save_model()
        return True

    def save_model(self, filename=None):
        target = filename or self.model_file
        try:
            with open(target, "w") as f:
                json.dump(self.category_scores, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving income-academic RL model: {e}")
            return False

    @classmethod
    def load_model(cls, filename="models/income_academic_rl_model.json"):
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    scores = json.load(f)
                return cls(initial_scores=scores)
            return cls()
        except Exception as e:
            print(f"Error loading income-academic RL model: {e}")
            return cls()


try:
    income_rl_agent = IncomeCategoryRL.load_model()
except Exception as e:
    print(f"Error initializing income RL agent: {e}")
    income_rl_agent = IncomeCategoryRL()

try:
    income_academic_rl_agent = IncomeAcademicRL.load_model()
except Exception as e:
    print(f"Error initializing income-academic RL agent: {e}")
    income_academic_rl_agent = IncomeAcademicRL()


def _safe_correlation(x_values, y_values):
    if len(x_values) < 2 or len(y_values) < 2:
        return 0.0
    x_arr = np.array(x_values, dtype=float)
    y_arr = np.array(y_values, dtype=float)
    if np.std(x_arr) == 0 or np.std(y_arr) == 0:
        return 0.0
    return float(np.corrcoef(x_arr, y_arr)[0, 1])


def get_income_sentiment(data):
    """Analyze family income and estimate its RL-based relation with academics."""
    default_result = {
        "below_poverty_line": 0,
        "low_income": 0,
        "below_average": 0,
        "average": 0,
        "above_average": 0,
        "averageIncome": 0,
        "total_households": 0,
        "current_thresholds": income_rl_agent.thresholds,
        "academic_correlation": 0,
        "income_academic_correlation": 0,
        "training_samples": 0,
        "model_updated": False,
        "income_details": [],
        "rl_expected_academic_by_category": {
            k: round(v, 3) for k, v in income_academic_rl_agent.category_scores.items()
        },
    }

    if data is None or data.empty:
        return default_result

    income_column = _resolve_column(data, "Family Income ")
    if not income_column:
        print("Warning: Family Income column not found in DataFrame.")
        return default_result

    academic_column = _resolve_column(data, "Academic Performance ")
    if not academic_column:
        print("Warning: Academic Performance column not found. Correlation metrics will be limited.")

    counts = {category: 0 for category in CATEGORY_ORDER}
    total_income = 0.0
    processed_count = 0
    income_details = []
    category_stats = {
        category: {"count": 0, "income_values": [], "academic_values": []}
        for category in CATEGORY_ORDER
    }
    records_with_academic = []

    for _, row in data.iterrows():
        raw_income = row.get(income_column)
        if raw_income is None or pd.isna(raw_income):
            continue

        try:
            income_value = float(raw_income)
            category = income_rl_agent.categorize_income(income_value)
            academic_score = (
                _to_academic_scale(row.get(academic_column)) if academic_column else None
            )

            counts[category] += 1
            total_income += income_value
            processed_count += 1

            category_stats[category]["count"] += 1
            category_stats[category]["income_values"].append(income_value)
            if academic_score is not None:
                category_stats[category]["academic_values"].append(academic_score)
                records_with_academic.append(
                    {
                        "category": category,
                        "income": income_value,
                        "academic": academic_score,
                    }
                )

            income_details.append(
                {
                    "income": income_value,
                    "category": category,
                    "income_score": CATEGORY_TO_SCORE.get(category, 3.0),
                    "academic_performance_score": round(academic_score, 2)
                    if academic_score is not None
                    else None,
                }
            )
        except Exception as e:
            print(f"Error processing income value '{raw_income}': {e}")

    training_samples = 0
    model_updated = False
    if INCOME_RL_TRAIN_ON_ANALYSIS:
        for record in records_with_academic:
            category = record["category"]
            count_for_category = max(category_stats[category]["count"], 1)
            sample_weight = 1.0 / count_for_category
            income_academic_rl_agent.add_experience(
                category, record["academic"], sample_weight=sample_weight
            )
            training_samples += 1
        model_updated = income_academic_rl_agent.update_model() if training_samples > 0 else False

    rl_predicted_scores = []
    observed_scores = []
    numeric_incomes = []
    for record in records_with_academic:
        rl_predicted_scores.append(
            income_academic_rl_agent.get_expected_score(record["category"])
        )
        observed_scores.append(record["academic"])
        numeric_incomes.append(record["income"])

    academic_correlation = _safe_correlation(rl_predicted_scores, observed_scores)
    income_academic_correlation = _safe_correlation(numeric_incomes, observed_scores)

    average_income = round(total_income / processed_count, 2) if processed_count > 0 else 0

    # Visualization remains lightweight so dashboard behavior stays unchanged.
    try:
        import matplotlib.pyplot as plt

        categories = [
            "Below Poverty Line",
            "Low Income",
            "Below Average",
            "Average",
            "Above Average",
        ]
        values = [
            counts["below_poverty_line"],
            counts["low_income"],
            counts["below_average"],
            counts["average"],
            counts["above_average"],
        ]
        colors = ["darkred", "orangered", "gold", "lightgreen", "darkgreen"]

        plt.figure(figsize=(10, 6))
        bars = plt.bar(categories, values, color=colors)
        plt.title("Family Income Distribution")
        plt.xlabel("Income Category")
        plt.ylabel("Number of Households")
        plt.xticks(rotation=45)

        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.1,
                f"{int(height)}",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()
        plt.savefig("income_distribution.png")
        plt.close()
    except Exception as e:
        print(f"Error creating visualization: {e}")

    income_academic_profile = []
    for category in CATEGORY_ORDER:
        stat = category_stats[category]
        if stat["count"] == 0:
            continue
        avg_income = float(np.mean(stat["income_values"])) if stat["income_values"] else None
        avg_academic = float(np.mean(stat["academic_values"])) if stat["academic_values"] else None
        income_academic_profile.append(
            {
                "category": category,
                "households": stat["count"],
                "avg_income": round(avg_income, 2) if avg_income is not None else None,
                "avg_academic_score": round(avg_academic, 3)
                if avg_academic is not None
                else None,
                "rl_expected_academic_score": round(
                    income_academic_rl_agent.get_expected_score(category), 3
                ),
            }
        )

    return {
        "below_poverty_line": counts["below_poverty_line"],
        "low_income": counts["low_income"],
        "below_average": counts["below_average"],
        "average": counts["average"],
        "above_average": counts["above_average"],
        "averageIncome": average_income,
        "total_households": processed_count,
        "current_thresholds": income_rl_agent.thresholds,
        "income_details": income_details,
        "academic_correlation": round(academic_correlation, 3),
        "income_academic_correlation": round(income_academic_correlation, 3),
        "training_samples": training_samples,
        "model_updated": model_updated,
        "income_academic_profile": income_academic_profile,
        "rl_expected_academic_by_category": {
            k: round(v, 3) for k, v in income_academic_rl_agent.category_scores.items()
        },
    }


def add_income_feedback(income, predicted_category, correct_category):
    """
    Add feedback to improve income category threshold policy.
    """
    try:
        buffer_size = income_rl_agent.add_feedback(income, predicted_category, correct_category)
        if buffer_size >= 5:
            income_rl_agent.update_thresholds()
        return True
    except Exception as e:
        print(f"Error adding income feedback: {e}")
        return False


def add_income_academic_feedback(income_value, academic_performance):
    """
    Add supervised RL feedback linking one income value to academic performance.
    """
    try:
        academic_score = _to_academic_scale(academic_performance)
        if academic_score is None:
            return False
        category = income_rl_agent.categorize_income(float(income_value))
        income_academic_rl_agent.add_experience(category, academic_score, sample_weight=1.0)
        return True
    except Exception as e:
        print(f"Error adding income-academic feedback: {e}")
        return False


def train_income_model(train_academic_model=True):
    """Train income RL models using buffered feedback."""
    try:
        threshold_updated = income_rl_agent.update_thresholds()
        academic_updated = (
            income_academic_rl_agent.update_model() if train_academic_model else False
        )
        return threshold_updated or academic_updated
    except Exception as e:
        print(f"Error training income model: {e}")
        return False


if __name__ == "__main__":
    try:
        sample_data = pd.DataFrame(
            {
                "Family Income ": [1500, 5000, 15000, 30000, 60000],
                "Academic Performance ": [1.8, 2.5, 3.2, 4.0, 4.6],
            }
        )

        results = get_income_sentiment(sample_data)
        print(f"Analysis results: {results}")

        add_income_feedback(12000, "low_income", "below_average")
        add_income_feedback(40000, "below_average", "average")
        add_income_academic_feedback(18000, 3.1)

        train_income_model()
    except Exception as e:
        print(f"Test run error: {e}")
