import pandas as pd
import json
import random
import os
import numpy as np
from collections import defaultdict

# Original dictionary mapping backgrounds to sentiment scores
background_sentiment = {
    'Tailor': 3, 'Labour': 2, 'Driver': 3, 'Factory': 2, 'Farming': 3,
    'Furniture': 3, 'Maid': 2, 'Middle Class': 4, 'Nan': 1, 'No Effect': 3,
    'Painter': 3, 'Plumber': 4, 'Poor': 1, 'Priest': 4, 'Private Job': 4,
    'Ragpicker': 1, 'Shopkeeper': 3, 'Single Mother Parent': 3, 'Sweetseller': 3,
    'Tea Seller': 3, 'Vendor': 3, 'Welding': 3, 'Wood Cutter': 2, 'Security Guard': 2,
    'Housekeeper': 2, 'Daily Wage Worker': 1, 'Rickshaw Puller': 1, 'Street Vendor': 3,
    'Electrician': 3, 'Hawker': 2, 'Coolie': 1, 'Fisherman': 3, 'Mechanic': 2,
    'Construction Worker': 2, 'Cobbler': 2, 'Barber': 3, 'Milkman': 3, 'Blacksmith': 3,
    'Goldsmith': 4, 'Potter': 3, 'Weaver': 3, 'Shepherd': 3, 'Priestess': 4,
    'Beggar': 1, 'Fruit Seller': 3, 'Florist': 3, 'Brick Kiln Worker': 2, 'Cook': 4,
    'Watchman': 2, 'Sweeper': 2, 'Garbage Collector': 1, 'Gardener': 3,
    'Newspaper Vendor': 3, 'Call Center Employee': 3, 'Delivery Person': 3,
    'Small-scale Business Owner': 4, 'Government Clerk': 4, 'Army Personnel': 5,
    'Police Constable': 4, 'NGO Worker': 4, 'Taxi Driver': 3, 'Truck Driver': 2,
    'Factory Supervisor': 3, 'Small Farmer': 2, 'Landless Labourer': 1,
    'Carpenter Helper': 2, 'Tailoring Assistant': 3, 'Street Performer': 4,
    'Singer': 4, 'Actor': 5, 'Dancer': 4, 'Wedding Planner': 4, 'Laboratory Technician': 4,
    'Storekeeper': 3, 'Beautician': 4, 'Housewife': 2, 'Retired Pensioner': 4,
    'College Professor': 5, 'Shop Assistant': 3, 'Digital Marketer': 4,
    'Graphic Designer': 4, 'Web Developer': 4, 'Software Engineer': 5,
    'Photographer': 4, 'Social Worker': 4, 'Caregiver': 4, 'Architect': 5,
    'Fashion Designer': 5, 'Interior Designer': 5, 'Public Relations Executive': 4,
    'Marketing Executive': 4, 'Researcher': 5, 'Taxi Owner': 3, 'Dry Cleaner': 3,
    'Food Delivery Executive': 3, 'Street Food Vendor': 3, 'Shoe Polisher': 2,
    'Travel Agent': 4, 'Importer': 5, 'Exporter': 5, 'Corporate Manager': 5,
    'Teacher': 4, 'Journalist': 4, 'Accountant': 4, 'Bank Clerk': 4, 'Receptionist': 3,
    'Hotel Manager': 4, 'Real Estate Agent': 4, 'Entrepreneur': 5, 'Consultant': 5,
    'Self-employed Artisan': 4, 'Caretaker': 4, 'Security Supervisor': 3,
    'Veterinary Doctor': 4, 'Government Official': 4, 'Real Estate Developer': 5,
    'Telephone Operator': 3, 'Travel Guide': 4, 'Tailoring Entrepreneur': 4,
    'Rideshare Driver': 3, 'Mushroom Cultivator': 3, 'Organic Farmer': 4,
    'Biotech Worker': 5, 'Supply Chain Manager': 5, 'Product Designer': 5,
    'Public Health Worker': 4, 'Small-Scale Industrialist': 4, 'Organic Product Seller': 4,
    'Community Organizer': 4, 'Data Entry Operator': 3, 'Tiffin Service Provider': 3,
    'Computer Technician': 4
}

# Normalize common free-text variants to a consistent occupation key.
BACKGROUND_LABEL_ALIASES = {
    "labor": "labour",
    "labourer": "labour",
    "daily labour": "daily wage worker",
    "daily labor": "daily wage worker",
    "daily labourer": "daily wage worker",
    "daily laborer": "daily wage worker",
    "mechanic worker": "mechanic",
    "electrical worker": "electrician",
    "electric work": "electrician",
    "auto driver": "driver",
    "tempo driver": "driver",
    "e-rickshaw driver": "rickshaw puller",
    "e rickshaw driver": "rickshaw puller",
    "vegetable vendor": "street vendor",
    "fruit vendor": "fruit seller",
    "shop helper": "shop assistant",
    "office helper": "shop assistant",
    "helper": "daily wage worker",
}

# Consistent policy table for occupations that are often overestimated by RL drift.
# prior: default base score, cap: hard upper bound after model prediction.
OCCUPATION_SENTIMENT_POLICY = {
    "labour": {"prior": 2.0, "cap": 2.3},
    "daily wage worker": {"prior": 1.0, "cap": 2.0},
    "landless labourer": {"prior": 1.0, "cap": 2.0},
    "construction worker": {"prior": 2.0, "cap": 2.4},
    "mechanic": {"prior": 2.0, "cap": 2.6},
    "electrician": {"prior": 3.0, "cap": 3.0},
    "driver": {"prior": 2.7, "cap": 3.1},
    "taxi driver": {"prior": 2.8, "cap": 3.1},
    "truck driver": {"prior": 2.0, "cap": 2.8},
    "rideshare driver": {"prior": 2.8, "cap": 3.2},
    "rickshaw puller": {"prior": 1.0, "cap": 2.0},
    "vendor": {"prior": 2.7, "cap": 3.0},
    "street vendor": {"prior": 2.7, "cap": 3.0},
    "newspaper vendor": {"prior": 2.8, "cap": 3.0},
    "fruit seller": {"prior": 2.8, "cap": 3.1},
    "food delivery executive": {"prior": 2.8, "cap": 3.1},
    "carpenter helper": {"prior": 2.0, "cap": 2.5},
    "shop assistant": {"prior": 2.8, "cap": 3.2},
    "tailoring assistant": {"prior": 2.8, "cap": 3.2},
}

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
    "fail": 1
}


def _clamp_score(value, min_score=1, max_score=5):
    return max(min_score, min(max_score, value))


def _to_academic_scale(value):
    """
    Convert raw academic performance values to a 1-5 scale.
    Supports numeric values (1-5, 0-10, 0-100) and common text labels.
    """
    if value is None or pd.isna(value):
        return None

    # Numeric conversions
    if isinstance(value, (int, float, np.number)):
        numeric = float(value)
        if numeric < 0:
            return None
        if numeric <= 5:
            # Keep within sentiment range; treat 0 as lowest bound.
            return _clamp_score(numeric if numeric > 0 else 1)
        if numeric <= 10:
            return _clamp_score(numeric / 2.0)
        if numeric <= 100:
            return _clamp_score(numeric / 20.0)
        return _clamp_score(numeric)

    # Text conversions
    text = str(value).strip().lower()
    if not text:
        return None

    grade_map = {"a+": 5, "a": 4.8, "b+": 4.2, "b": 4, "c+": 3.2, "c": 3, "d": 2, "f": 1}
    if text in grade_map:
        return grade_map[text]

    for label, score in ACADEMIC_TEXT_TO_SCORE.items():
        if label in text:
            return score

    # Attempt numeric extraction from strings like "8/10" or "78%"
    try:
        cleaned = text.replace("%", "").replace("/10", "").replace("/5", "")
        numeric = float(cleaned)
        return _to_academic_scale(numeric)
    except Exception:
        return None


def _resolve_column(df, primary_name):
    """Resolve exact or trimmed column names (handles accidental trailing spaces)."""
    if primary_name in df.columns:
        return primary_name

    normalized_target = primary_name.strip().lower()
    for col in df.columns:
        if str(col).strip().lower() == normalized_target:
            return col
    return None


def _normalize_background_label(value):
    """Normalize raw background labels so scoring is learned per job type."""
    normalized = " ".join(str(value).strip().split())
    lowered = normalized.lower()
    return BACKGROUND_LABEL_ALIASES.get(lowered, lowered)


NORMALIZED_BACKGROUND_PRIORS = {
    _normalize_background_label(name): float(score)
    for name, score in background_sentiment.items()
}
for occupation, policy in OCCUPATION_SENTIMENT_POLICY.items():
    NORMALIZED_BACKGROUND_PRIORS[_normalize_background_label(occupation)] = float(policy["prior"])

# Guardrails so lower-income manual occupations don't drift to unrealistically
# high sentiment due online updates on sparse/noisy samples.
LOW_INCOME_SENTIMENT_CAP = {
    _normalize_background_label(occupation): float(policy["cap"])
    for occupation, policy in OCCUPATION_SENTIMENT_POLICY.items()
    if policy.get("cap") is not None
}

# Always-on learning mode: the model updates continuously during analysis.
BACKGROUND_RL_TRAIN_ON_ANALYSIS = False
BACKGROUND_SCORER = os.getenv("BACKGROUND_SCORER", "rl").strip().lower() or "rl"
if BACKGROUND_SCORER not in {"rl", "simple_linear"}:
    print(f"Unsupported BACKGROUND_SCORER '{BACKGROUND_SCORER}', defaulting to 'rl'")
    BACKGROUND_SCORER = "rl"
BACKGROUND_MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
BACKGROUND_RL_MODEL_PATH = os.path.join(
    BACKGROUND_MODELS_DIR,
    "background_sentiment_model.json",
)
BACKGROUND_LEGACY_MODEL_PATHS = [
    os.path.join(os.path.dirname(__file__), "background_sentiment_model.json"),
    "background_sentiment_model.json",
]
BACKGROUND_SIMPLE_LINEAR_MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "models",
    "background_simple_linear_model.json",
)
BACKGROUND_SIMPLE_LINEAR_LR = float(os.getenv("BACKGROUND_SIMPLE_LINEAR_LR", "0.002"))


def _load_simple_linear_params():
    default = {"slope": 1.0, "intercept": 0.0}
    try:
        with open(BACKGROUND_SIMPLE_LINEAR_MODEL_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)
        slope = float(payload.get("slope", 1.0))
        intercept = float(payload.get("intercept", 0.0))
        print(f"Loaded simple linear background model from {BACKGROUND_SIMPLE_LINEAR_MODEL_PATH}")
        return {"slope": slope, "intercept": intercept}
    except FileNotFoundError:
        print(f"Simple linear background model not found at {BACKGROUND_SIMPLE_LINEAR_MODEL_PATH}; using identity fallback.")
        return default
    except Exception as exc:
        print(f"Error loading simple linear background model: {exc}; using identity fallback.")
        return default


SIMPLE_LINEAR_PARAMS = _load_simple_linear_params()


def _save_simple_linear_params(params):
    payload = {
        "slope": float(params.get("slope", 1.0)),
        "intercept": float(params.get("intercept", 0.0)),
        "fit_source": "online_learning",
    }
    try:
        os.makedirs(os.path.dirname(BACKGROUND_SIMPLE_LINEAR_MODEL_PATH), exist_ok=True)
        with open(BACKGROUND_SIMPLE_LINEAR_MODEL_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as exc:
        print(f"Error saving simple linear background model: {exc}")


def _online_update_simple_linear(prior_score, observed_score, learning_rate=BACKGROUND_SIMPLE_LINEAR_LR):
    slope = float(SIMPLE_LINEAR_PARAMS.get("slope", 1.0))
    intercept = float(SIMPLE_LINEAR_PARAMS.get("intercept", 0.0))
    pred = (slope * float(prior_score)) + intercept
    error = pred - float(observed_score)

    # SGD step for squared error loss.
    slope -= learning_rate * 2.0 * error * float(prior_score)
    intercept -= learning_rate * 2.0 * error

    # Keep parameters in stable, interpretable bounds.
    slope = max(-2.0, min(2.0, slope))
    intercept = max(0.0, min(5.0, intercept))
    SIMPLE_LINEAR_PARAMS["slope"] = slope
    SIMPLE_LINEAR_PARAMS["intercept"] = intercept


def _predict_background_score(job_key, rl_fallback_agent=None):
    prior = NORMALIZED_BACKGROUND_PRIORS.get(job_key, 3.0)
    sentiment_cap = LOW_INCOME_SENTIMENT_CAP.get(job_key)
    if BACKGROUND_SCORER == "simple_linear":
        slope = SIMPLE_LINEAR_PARAMS.get("slope", 1.0)
        intercept = SIMPLE_LINEAR_PARAMS.get("intercept", 0.0)
        predicted = _clamp_score((slope * prior) + intercept)
        return min(predicted, sentiment_cap) if sentiment_cap is not None else predicted
    if rl_fallback_agent is not None:
        predicted = rl_fallback_agent.get_blended_policy_score(job_key)
        return min(predicted, sentiment_cap) if sentiment_cap is not None else predicted
    predicted = _clamp_score(prior)
    return min(predicted, sentiment_cap) if sentiment_cap is not None else predicted


class BackgroundSentimentRL:
    """
    Reinforcement Learning agent for background sentiment analysis
    Enhances static sentiment scores by adapting based on feedback
    """
    def __init__(self, initial_scores=None):
        # Load initial sentiment dictionary or use provided one
        if initial_scores:
            self.sentiment_scores = initial_scores
        else:
            # Use existing background_sentiment dictionary
            self.sentiment_scores = background_sentiment.copy()
            
        self.learning_rate = 0.05  # How quickly the model adapts to new information
        self.exploration_rate = 0.1  # Probability of trying new values (exploration)
        self.experience_buffer = []  # Store feedback for batch learning
        self.min_score = 1  # Minimum possible score
        self.max_score = 5  # Maximum possible score

    def _get_prior_score(self, background):
        return NORMALIZED_BACKGROUND_PRIORS.get(
            _normalize_background_label(background),
            3.0,
        )

    def _ensure_background(self, background):
        if background not in self.sentiment_scores:
            # Use known job prior instead of always defaulting to neutral.
            self.sentiment_scores[background] = self._get_prior_score(background)

    def get_blended_policy_score(self, background, learned_weight=0.35):
        """
        Keep predictions anchored to job priors so repeated training doesn't push
        all backgrounds into positive ranges.
        """
        self._ensure_background(background)
        prior = self._get_prior_score(background)
        learned = self.sentiment_scores[background]
        blended = prior + learned_weight * (learned - prior)
        return max(self.min_score, min(self.max_score, blended))
        
    def get_score(self, background):
        """Get sentiment score for a background with occasional exploration"""
        self._ensure_background(background)
            
        # Occasionally explore by trying slightly different score (epsilon-greedy)
        if random.random() < self.exploration_rate:
            # Add small random adjustment but keep within valid range
            adjustment = random.uniform(-0.5, 0.5)
            return max(self.min_score, min(self.max_score, 
                                          self.sentiment_scores[background] + adjustment))
        
        # Most of the time, use our current best estimate
        return self.sentiment_scores[background]

    def get_policy_score(self, background):
        """Get deterministic learned score (no exploration) for reporting."""
        self._ensure_background(background)
        return self.sentiment_scores[background]
        
    def add_experience(self, background, predicted_score, observed_outcome, sample_weight=1.0):
        """
        Record experience for batch learning
        
        Parameters:
        - background: The occupation/background being evaluated
        - predicted_score: The score our model predicted
        - observed_outcome: The actual outcome/feedback received
        """
        self.experience_buffer.append({
            'background': background,
            'predicted': predicted_score,
            'actual': observed_outcome,
            'weight': float(sample_weight) if sample_weight is not None else 1.0,
        })
        print(f"Added experience for {background}: predicted={predicted_score}, actual={observed_outcome}")
        
    def update_model(self):
        """Apply reinforcement learning update based on collected experiences"""
        if not self.experience_buffer:
            print("No experiences to learn from")
            return False
            
        print(f"Updating model with {len(self.experience_buffer)} experiences")
        
        for exp in self.experience_buffer:
            bg = exp['background']
            error = exp['actual'] - exp['predicted']
            weight = exp.get('weight', 1.0)
            
            # Q-learning update rule
            old_score = self.sentiment_scores[bg]
            new_score = old_score + self.learning_rate * error * weight
            
            # Ensure score stays in valid range
            self.sentiment_scores[bg] = max(self.min_score, min(self.max_score, new_score))
            
            print(f"Updated {bg}: {old_score:.2f} -> {self.sentiment_scores[bg]:.2f}")
            
        # Clear buffer after updating
        self.experience_buffer = []
        
        # Save the updated model
        self.save_model()
        return True
        
    def save_model(self, filename=None):
        """Save the learned model to a JSON file"""
        target_path = filename or BACKGROUND_RL_MODEL_PATH
        try:
            parent_dir = os.path.dirname(target_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(self.sentiment_scores, f, indent=2)
            print(f"Model saved to {target_path}")
        except Exception as e:
            print(f"Error saving model: {e}")
            
    @classmethod
    def load_model(cls, filename=None):
        """Load a previously trained model from a JSON file"""
        candidate_paths = [filename] if filename else [BACKGROUND_RL_MODEL_PATH, *BACKGROUND_LEGACY_MODEL_PATHS]
        last_error = None

        for candidate in candidate_paths:
            if not candidate:
                continue
            try:
                with open(candidate, 'r', encoding='utf-8') as f:
                    scores = json.load(f)
                # Normalize keys so legacy title-case and new normalized keys are unified.
                normalized_scores = {}
                for name, score in scores.items():
                    try:
                        normalized_scores[_normalize_background_label(name)] = float(score)
                    except Exception:
                        continue
                print(f"Loaded RL background model from {candidate} with {len(scores)} backgrounds")
                model = cls(initial_scores=normalized_scores)
                if not filename and os.path.abspath(candidate) != os.path.abspath(BACKGROUND_RL_MODEL_PATH):
                    # Normalize the active model location so deployments consistently
                    # pick up the RL model from backend/models/.
                    model.save_model(BACKGROUND_RL_MODEL_PATH)
                return model
            except FileNotFoundError:
                continue
            except Exception as e:
                last_error = e
                print(f"Error loading RL background model from {candidate}: {e}")

        if last_error is not None:
            print("Falling back to default RL background scores after model load error.")
        else:
            print(f"RL background model not found at {BACKGROUND_RL_MODEL_PATH}; using default scores")
        return cls()

# Initialize the RL agent
try:
    rl_agent = BackgroundSentimentRL.load_model()
except Exception as e:
    print(f"Error initializing RL agent: {e}")
    rl_agent = BackgroundSentimentRL()

def get_background_sentiment(data, persist_artifacts=True):
    """
    Analyze background sentiment from survey data
    
    Parameters:
    - data: DataFrame containing survey responses with 'Background of the Child ' column
    
    Returns:
    - Dictionary with sentiment analysis results
    """
    # Initialize default return structure
    default_result = {
        "positive_count": 0,
        "negative_count": 0,
        "neutral_count": 0,
        "average_score": 0,
        "highly_positive": 0,
        "positive": 0,
        "neutral": 0,
        "negative": 0,
        "highly_negative": 0,
        "background_details": [],
        "academic_correlation": 0,
        "training_samples": 0,
        "model_updated": False,
        "scoring_model": BACKGROUND_SCORER,
    }
    
    if data is None or data.empty:
        print("Warning: No data provided or DataFrame is empty")
        return default_result
    
    # Check if the required column exists
    background_column = _resolve_column(data, 'Background of the Child ')
    if background_column not in data.columns:
        print(f"Warning: Column '{background_column}' not found in DataFrame. Available columns: {list(data.columns)}")
        return default_result

    academic_column = _resolve_column(data, 'Academic Performance ')
    if not academic_column:
        print("Warning: Academic Performance column not found. RL updates will be skipped for this batch.")
    
    # Apply sentiment analysis
    category_counts = {"Highly Positive": 0, "Positive": 0, "Neutral": 0, "Negative": 0, "Highly Negative": 0}
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    total_score = 0
    processed_count = 0
    background_data = []
    prepared_rows = []
    raw_label_counts = defaultdict(lambda: defaultdict(int))
    job_stats = {}
    academic_scores = []
    training_samples = 0

    # First pass: gather job-level stats from responses.
    for idx, row in data.iterrows():
        # Access column using proper pandas Series indexing
        background = row[background_column] if background_column in row.index else None
        
        # Check if background is None, NaN, or empty string
        if background is None or pd.isna(background):
            continue
        
        background = str(background).strip()
        
        # Skip empty strings
        if not background or background.lower() in ['none', 'null', '']:
            continue
        
        # Convert observed academic performance to model feedback signal
        observed_academic = _to_academic_scale(row.get(academic_column)) if academic_column else None

        try:
            job_key = _normalize_background_label(background)
            raw_label_counts[job_key][background] += 1

            if job_key not in job_stats:
                job_stats[job_key] = {"response_count": 0, "academic_scores": []}

            job_stats[job_key]["response_count"] += 1
            if observed_academic is not None:
                job_stats[job_key]["academic_scores"].append(observed_academic)

            prepared_rows.append(
                {
                    "background": background,
                    "job_key": job_key,
                    "academic_score": observed_academic,
                }
            )
        except Exception as e:
            print(f"Error processing background '{background}': {e}")
            continue

    if BACKGROUND_SCORER == "simple_linear":
        if BACKGROUND_RL_TRAIN_ON_ANALYSIS:
            for row_data in prepared_rows:
                observed = row_data["academic_score"]
                if observed is None:
                    continue
                prior_score = NORMALIZED_BACKGROUND_PRIORS.get(row_data["job_key"], 3.0)
                _online_update_simple_linear(prior_score, observed)
                training_samples += 1
            model_updated = training_samples > 0
            if model_updated:
                _save_simple_linear_params(SIMPLE_LINEAR_PARAMS)
        else:
            model_updated = False
    else:
        # RL fallback path remains available and is also always-on.
        if BACKGROUND_RL_TRAIN_ON_ANALYSIS:
            for row_data in prepared_rows:
                observed = row_data["academic_score"]
                if observed is None:
                    continue
                job_key = row_data["job_key"]
                count_for_job = job_stats.get(job_key, {}).get("response_count", 1)
                sample_weight = 1.0 / max(count_for_job, 1)
                predicted_score = rl_agent.get_policy_score(job_key)
                rl_agent.add_experience(job_key, predicted_score, observed, sample_weight=sample_weight)
                training_samples += 1
            model_updated = rl_agent.update_model() if training_samples > 0 else False
        else:
            model_updated = False

    # Cache deterministic score per unique job so repeated rows don't alter job score.
    job_scores = {job_key: _predict_background_score(job_key, rl_fallback_agent=rl_agent) for job_key in job_stats}

    # Second pass: render response rows using job-level score (frequency doesn't change score).
    for row_data in prepared_rows:
        background = row_data["background"]
        job_key = row_data["job_key"]
        observed_academic = row_data["academic_score"]
        score = job_scores.get(job_key, rl_agent.get_policy_score(job_key))
        total_score += score
        processed_count += 1

        if score >= 4.5:
            category = "Highly Positive"
            positive_count += 1
        elif score >= 3.5:
            category = "Positive"
            positive_count += 1
        elif score >= 2.5:
            category = "Neutral"
            neutral_count += 1
        elif score >= 1.5:
            category = "Negative"
            negative_count += 1
        else:
            category = "Highly Negative"
            negative_count += 1

        category_counts[category] += 1

        background_data.append({
            "background": background,
            "score": round(score, 2),
            "category": category,
            "academic_performance_score": round(observed_academic, 2) if observed_academic is not None else None
        })

    # Calculate average score
    avg_score = total_score / processed_count if processed_count > 0 else 0

    # Correlation between learned sentiment score and academic performance
    academic_correlation = 0
    model_scores = []
    academic_scores = []
    for job_key, stats in job_stats.items():
        if not stats["academic_scores"]:
            continue
        model_scores.append(job_scores.get(job_key, _predict_background_score(job_key, rl_fallback_agent=rl_agent)))
        academic_scores.append(float(np.mean(stats["academic_scores"])))

    if len(academic_scores) >= 2 and len(model_scores) >= 2:
        paired_scores = [(m, a) for m, a in zip(model_scores, academic_scores) if a is not None]
        if len(paired_scores) >= 2:
            model_vals = np.array([m for m, _ in paired_scores], dtype=float)
            academic_vals = np.array([a for _, a in paired_scores], dtype=float)
            if np.std(model_vals) > 0 and np.std(academic_vals) > 0:
                academic_correlation = float(np.corrcoef(model_vals, academic_vals)[0, 1])
    
    # Persist Excel/chart artifacts only for offline workflows.
    if persist_artifacts and processed_count > 0:
        try:
            # Create DataFrame from collected data
            result_df = pd.DataFrame(background_data)
            
            # Save the results to Excel for later analysis
            if not result_df.empty:
                result_df.to_excel('background_sentiment_analysis.xlsx', index=False)
            
            # Create a bar chart of the sentiment distribution
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 6))
            categories = ["Highly Positive", "Positive", "Neutral", "Negative", "Highly Negative"]
            values = [category_counts[cat] for cat in categories]
            colors = ['darkgreen', 'lightgreen', 'gold', 'orangered', 'darkred']
            
            bars = plt.bar(categories, values, color=colors)
            plt.title('Background Sentiment Analysis Results')
            plt.xlabel('Sentiment Category')
            plt.ylabel('Number of Backgrounds')
            plt.xticks(rotation=45)
            
            # Add value labels on top of each bar
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{height}', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig('background_sentiment_graph.png')
            plt.close()  # Close the figure to free memory
            print("Bar graph created and saved as 'background_sentiment_graph.png'")
            
        except Exception as e:
            print(f"Error saving analysis results or creating visualization: {e}")
    elif processed_count == 0:
        print("Warning: No valid background data found to process")
    
    # Return structured data for the dashboard
    return {
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "average_score": round(avg_score, 2),
        "highly_positive": category_counts["Highly Positive"],
        "positive": category_counts["Positive"],
        "neutral": category_counts["Neutral"],
        "negative": category_counts["Negative"],
        "highly_negative": category_counts["Highly Negative"],
        "background_details": background_data,  # Added for detailed reporting
        "academic_correlation": round(academic_correlation, 3),
        "training_samples": training_samples,
        "model_updated": model_updated,
        "scoring_model": BACKGROUND_SCORER,
    }

# For testing the module directly
if __name__ == "__main__":
    try:
        # Load test data if available
        test_data = pd.read_excel('backend/Childsurvey.xlsx')
        results = get_background_sentiment(test_data)
        print(f"Analysis results: {results}")
        
        # Optional: Create a more detailed visualization
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Load the results that were saved to Excel
        detailed_data = pd.read_excel('background_sentiment_analysis.xlsx')
        
        # Create a count plot of categories
        plt.figure(figsize=(12, 8))
        sns.set_style("whitegrid")
        ax = sns.countplot(x='category', data=detailed_data, 
                          order=["Highly Positive", "Positive", "Neutral", "Negative", "Highly Negative"],
                          palette="RdYlGn_r")
        
        plt.title('Distribution of Background Sentiment Categories', fontsize=16)
        plt.xlabel('Sentiment Category', fontsize=14)
        plt.ylabel('Count', fontsize=14)
        
        # Add count labels on bars
        for p in ax.patches:
            ax.annotate(f'{p.get_height()}', 
                        (p.get_x() + p.get_width()/2., p.get_height()),
                        ha='center', va='bottom', fontsize=12)
        
        plt.tight_layout()
        plt.savefig('background_sentiment_distribution.png', dpi=300)
        print("Enhanced visualization saved as 'background_sentiment_distribution.png'")
        
    except Exception as e:
        print(f"Test run error: {e}")
