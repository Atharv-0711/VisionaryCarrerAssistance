import pandas as pd
import json
import random
import os
import numpy as np

# Original dictionary mapping backgrounds to sentiment scores
background_sentiment = {
    'Tailor': 3, 'Labour': 2, 'Driver': 3, 'Factory': 2, 'Farming': 3,
    'Furniture': 3, 'Maid': 2, 'Middle Class': 4, 'Nan': 1, 'No Effect': 3,
    'Painter': 3, 'Plumber': 4, 'Poor': 1, 'Priest': 4, 'Private Job': 4,
    'Ragpicker': 1, 'Shopkeeper': 3, 'Single Mother Parent': 3, 'Sweetseller': 3,
    'Tea Seller': 3, 'Vendor': 3, 'Welding': 3, 'Wood Cutter': 2, 'Security Guard': 2,
    'Housekeeper': 2, 'Daily Wage Worker': 1, 'Rickshaw Puller': 1, 'Street Vendor': 3,
    'Electrician': 4, 'Hawker': 2, 'Coolie': 1, 'Fisherman': 3, 'Mechanic': 4,
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
        
    def get_score(self, background):
        """Get sentiment score for a background with occasional exploration"""
        if background not in self.sentiment_scores:
            # If we encounter a new background, start with neutral score
            self.sentiment_scores[background] = 3
            
        # Occasionally explore by trying slightly different score (epsilon-greedy)
        if random.random() < self.exploration_rate:
            # Add small random adjustment but keep within valid range
            adjustment = random.uniform(-0.5, 0.5)
            return max(self.min_score, min(self.max_score, 
                                          self.sentiment_scores[background] + adjustment))
        
        # Most of the time, use our current best estimate
        return self.sentiment_scores[background]
        
    def add_experience(self, background, predicted_score, observed_outcome):
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
            'actual': observed_outcome
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
            
            # Q-learning update rule
            old_score = self.sentiment_scores[bg]
            new_score = old_score + self.learning_rate * error
            
            # Ensure score stays in valid range
            self.sentiment_scores[bg] = max(self.min_score, min(self.max_score, new_score))
            
            print(f"Updated {bg}: {old_score:.2f} -> {self.sentiment_scores[bg]:.2f}")
            
        # Clear buffer after updating
        self.experience_buffer = []
        
        # Save the updated model
        self.save_model()
        return True
        
    def save_model(self, filename="background_sentiment_model.json"):
        """Save the learned model to a JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.sentiment_scores, f, indent=2)
            print(f"Model saved to {filename}")
        except Exception as e:
            print(f"Error saving model: {e}")
            
    @classmethod
    def load_model(cls, filename="background_sentiment_model.json"):
        """Load a previously trained model from a JSON file"""
        try:
            with open(filename, 'r') as f:
                scores = json.load(f)
            print(f"Loaded model from {filename} with {len(scores)} backgrounds")
            return cls(initial_scores=scores)
        except FileNotFoundError:
            print(f"Model file {filename} not found, using default scores")
            return cls()  # Return new model with default scores if file not found
        except Exception as e:
            print(f"Error loading model: {e}")
            return cls()

# Initialize the RL agent
try:
    rl_agent = BackgroundSentimentRL.load_model()
except Exception as e:
    print(f"Error initializing RL agent: {e}")
    rl_agent = BackgroundSentimentRL()

def get_background_sentiment(data):
    """
    Analyze background sentiment from survey data
    
    Parameters:
    - data: DataFrame containing survey responses with 'Background of the Child ' column
    
    Returns:
    - Dictionary with sentiment analysis results
    """
    if data is None:
        return {}
    
    # Apply sentiment analysis
    category_counts = {"Highly Positive": 0, "Positive": 0, "Neutral": 0, "Negative": 0, "Highly Negative": 0}
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    total_score = 0
    processed_count = 0
    background_data = []  # List to store details for each background
    
    # Process each background
    for idx, row in data.iterrows():
        background = row.get('Background of the Child ', None)
        if pd.isna(background):
            continue
            
        background = str(background).strip()
        
        # Use RL agent to get the sentiment score
        score = rl_agent.get_score(background)
        total_score += score
        processed_count += 1
        
        # Map score to category
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
        
        # Add this background's data for detailed reporting
        background_data.append({
            "background": background,
            "score": round(score, 2),
            "category": category
        })
    
    # Calculate average score
    avg_score = total_score / processed_count if processed_count > 0 else 0
    
    # Create and save visualization
    try:
        # Create DataFrame from collected data
        result_df = pd.DataFrame(background_data)
        
        # Save the results to Excel for later analysis
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
        print("Bar graph created and saved as 'background_sentiment_graph.png'")
        
    except Exception as e:
        print(f"Error saving analysis results or creating visualization: {e}")
    
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
        "background_details": background_data  # Added for detailed reporting
    }

# For testing the module directly
if __name__ == "__main__":
    try:
        # Load test data if available
        test_data = pd.read_excel('Childsurvey.xlsx')
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
