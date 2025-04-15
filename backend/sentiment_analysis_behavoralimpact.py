# sentiment_analysis_behavoralimpact.py

import pandas as pd
import re
from textblob import TextBlob

# Function to clean text
def clean_text(text):
    if pd.isna(text):
        return ""
    # Convert to string and lowercase
    text = str(text).lower()
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text.strip()

# Function to analyze behavioral impact sentiment
def analyze_behavioral_impact(data):
    if data is None:
        return {}

    highly_positive_count = 0
    positive_count = 0
    neutral_count = 0
    negative_count = 0
    highly_negative_count = 0
    total_score = 0
    processed_count = 0

    for idx, row in data.iterrows():
        text = row.get('Behavioral Impact', None)
        if pd.isna(text):
            continue

        text = clean_text(text)
        processed_count += 1

        # Keywords associated with different sentiment levels
        pos_keywords = ['excellent', 'outstanding', 'improved', 'better', 'positive', 'good', 'well', 'progress', 'no effect']
        pos_count = sum(1 for word in pos_keywords if word in text)

        neg_keywords = ['difficult', 'problem', 'issue', 'poor', 'bad', 'worse', 'negative', 'lack']
        neg_count = sum(1 for word in neg_keywords if word in text)

        h_neg_keywords = ['severe', 'serious', 'critical', 'extreme', 'very bad', 'very poor', 'worse']
        h_neg_count = sum(1 for word in h_neg_keywords if word in text)

        # Calculate sentiment score based on keyword matches
        if h_neg_count > 0:
            score = 1
            highly_negative_count += 1
        elif neg_count > 0:
            score = 2
            negative_count += 1
        elif pos_count > 0:
            # Check if there are multiple positive keywords for "highly positive"
            if pos_count >= 2:
                score = 5
                highly_positive_count += 1
            else:
                score = 4
                positive_count += 1
        else:
            # Use TextBlob for additional sentiment analysis
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            if polarity > 0.3:
                score = 4
                positive_count += 1
            elif polarity < -0.3:
                score = 2
                negative_count += 1
            else:
                score = 3
                neutral_count += 1

        total_score += score

    # Calculate average score
    avg_score = total_score / processed_count if processed_count > 0 else 0

    # Return structured data for the dashboard
    return {
        "highly_positive_count": highly_positive_count,
        "positive_count": positive_count,
        "neutral_count": neutral_count,
        "negative_count": negative_count,
        "highly_negative_count": highly_negative_count,
        "average_score": round(avg_score, 2),
        "total_responses": processed_count
    }
