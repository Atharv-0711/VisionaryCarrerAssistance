import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

class IncomeCategoryRL:
    """Reinforcement Learning agent for optimizing income category thresholds"""
    
    def __init__(self, initial_thresholds=None, learning_rate=0.05):
        # Default thresholds in rupees (if none provided)
        self.default_thresholds = {
            "poverty_line": 2250,
            "low_income": 10000,
            "below_average": 25000,
            "average": 45000
        }
        
        # Load initial thresholds or use defaults
        if initial_thresholds:
            self.thresholds = initial_thresholds
        else:
            # Try to load from saved model file
            try:
                with open('models/income_threshold_model.json', 'r') as f:
                    self.thresholds = json.load(f)
                print(f"Loaded income threshold model from file")
            except (FileNotFoundError, json.JSONDecodeError):
                # If no file exists, use default thresholds
                self.thresholds = self.default_thresholds
                print(f"Using default income thresholds")
        
        # Create models directory if it doesn't exist
        os.makedirs('models', exist_ok=True)
        
        # RL parameters
        self.learning_rate = learning_rate
        self.experience_buffer = []
        self.log_file = 'models/income_rl_learning_log.txt'
        
        # Ensure log file exists
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write("Timestamp,Threshold,OldValue,NewValue,Feedback\n")
    
    def categorize_income(self, income):
        """Categorize income using current thresholds"""
        if income < self.thresholds["poverty_line"]:
            return "below_poverty_line"
        elif income < self.thresholds["low_income"]:
            return "low_income"
        elif income < self.thresholds["below_average"]:
            return "below_average"
        elif income < self.thresholds["average"]:
            return "average"
        else:
            return "above_average"
    
    def add_feedback(self, income, predicted_category, correct_category):
        """Record feedback for updating thresholds"""
        self.experience_buffer.append({
            'income': income,
            'predicted': predicted_category,
            'actual': correct_category,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"Added feedback: income={income}, predicted={predicted_category}, actual={correct_category}")
        return len(self.experience_buffer)
    
    def update_thresholds(self):
        """Apply reinforcement learning update based on feedback"""
        if not self.experience_buffer:
            print("No feedback to learn from")
            return False
        
        updates_made = 0
        for feedback in self.experience_buffer:
            income = feedback['income']
            predicted = feedback['predicted']
            actual = feedback['actual']
            
            # Skip if prediction was correct
            if predicted == actual:
                continue
            
            # Determine which threshold to adjust
            if actual == "below_poverty_line":
                if predicted != "below_poverty_line":
                    # Need to increase poverty line threshold if income was higher than current
                    if income >= self.thresholds["poverty_line"]:
                        old_threshold = self.thresholds["poverty_line"]
                        # Move threshold up, but not beyond the next category
                        self.thresholds["poverty_line"] = min(
                            income + 100,  # Add buffer
                            self.thresholds["low_income"] - 100  # Don't overlap with next threshold
                        )
                        self._log_update("poverty_line", old_threshold, self.thresholds["poverty_line"], 
                                        f"Adjusted for income {income}")
                        updates_made += 1
            
            elif actual == "low_income":
                if predicted == "below_poverty_line":
                    # Need to decrease poverty line threshold
                    old_threshold = self.thresholds["poverty_line"]
                    self.thresholds["poverty_line"] = max(500, income - 100)  # Don't go below reasonable minimum
                    self._log_update("poverty_line", old_threshold, self.thresholds["poverty_line"], 
                                    f"Adjusted for income {income}")
                    updates_made += 1
                elif predicted in ["below_average", "average", "above_average"]:
                    # Need to increase low_income threshold
                    old_threshold = self.thresholds["low_income"]
                    self.thresholds["low_income"] = min(
                        income + 100,
                        self.thresholds["below_average"] - 100
                    )
                    self._log_update("low_income", old_threshold, self.thresholds["low_income"], 
                                    f"Adjusted for income {income}")
                    updates_made += 1
            
            # Similar adjustment logic for other categories
            elif actual == "below_average":
                if predicted in ["below_poverty_line", "low_income"]:
                    # Need to decrease low_income threshold
                    old_threshold = self.thresholds["low_income"]
                    self.thresholds["low_income"] = max(
                        self.thresholds["poverty_line"] + 100,
                        income - 100
                    )
                    self._log_update("low_income", old_threshold, self.thresholds["low_income"], 
                                    f"Adjusted for income {income}")
                    updates_made += 1
                elif predicted in ["average", "above_average"]:
                    # Need to increase below_average threshold
                    old_threshold = self.thresholds["below_average"]
                    self.thresholds["below_average"] = min(
                        income + 100,
                        self.thresholds["average"] - 100
                    )
                    self._log_update("below_average", old_threshold, self.thresholds["below_average"], 
                                    f"Adjusted for income {income}")
                    updates_made += 1
            
            elif actual == "average":
                if predicted in ["below_poverty_line", "low_income", "below_average"]:
                    # Need to decrease below_average threshold
                    old_threshold = self.thresholds["below_average"]
                    self.thresholds["below_average"] = max(
                        self.thresholds["low_income"] + 100,
                        income - 100
                    )
                    self._log_update("below_average", old_threshold, self.thresholds["below_average"], 
                                    f"Adjusted for income {income}")
                    updates_made += 1
                elif predicted == "above_average":
                    # Need to increase average threshold
                    old_threshold = self.thresholds["average"]
                    self.thresholds["average"] = income + 100
                    self._log_update("average", old_threshold, self.thresholds["average"], 
                                    f"Adjusted for income {income}")
                    updates_made += 1
            
            elif actual == "above_average":
                if predicted in ["below_poverty_line", "low_income", "below_average", "average"]:
                    # Need to decrease average threshold
                    old_threshold = self.thresholds["average"]
                    self.thresholds["average"] = max(
                        self.thresholds["below_average"] + 100,
                        income - 100
                    )
                    self._log_update("average", old_threshold, self.thresholds["average"], 
                                    f"Adjusted for income {income}")
                    updates_made += 1
        
        # Clear processed feedback
        self.experience_buffer = []
        
        # Save updated thresholds
        if updates_made > 0:
            self.save_thresholds()
        
        return updates_made > 0
    
    def save_thresholds(self, filename="models/income_threshold_model.json"):
        """Save learned thresholds to a file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.thresholds, f, indent=2)
            print(f"Saved income thresholds to {filename}")
            return True
        except Exception as e:
            print(f"Error saving thresholds: {e}")
            return False
    
    def _log_update(self, threshold_name, old_value, new_value, feedback):
        """Log threshold updates for analysis"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()},{threshold_name},{old_value},{new_value},{feedback}\n")
        except Exception as e:
            print(f"Error logging update: {e}")
    
    @classmethod
    def load_model(cls, filename="models/income_threshold_model.json"):
        """Load a previously trained model"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    thresholds = json.load(f)
                print(f"Loaded thresholds from {filename}")
                return cls(initial_thresholds=thresholds)
            else:
                print(f"Model file {filename} not found, using default thresholds")
                return cls()  # Return new model with default thresholds
        except Exception as e:
            print(f"Error loading thresholds: {e}")
            return cls()  # Return new model with default thresholds

# Initialize RL agent with default or saved thresholds
try:
    income_rl_agent = IncomeCategoryRL.load_model()
except Exception as e:
    print(f"Error initializing income RL agent: {e}")
    income_rl_agent = IncomeCategoryRL()

# Function to categorize income sentiment based on Indian context with RL
def get_income_sentiment(data):
    if data is None:
        return {}

    below_poverty = 0
    low_income = 0
    below_average = 0
    average = 0
    above_average = 0
    total_income = 0
    count = 0
    
    # Store detailed income data for analysis
    income_details = []

    for idx, row in data.iterrows():
        income = row.get('Family Income ', None)
        if pd.isna(income):
            continue

        try:
            income = float(income)
            total_income += income
            count += 1

            # Use RL agent to categorize income
            category = income_rl_agent.categorize_income(income)
            
            # Update counts based on categorization
            if category == "below_poverty_line":
                below_poverty += 1
            elif category == "low_income":
                low_income += 1
            elif category == "below_average":
                below_average += 1
            elif category == "average":
                average += 1
            else:  # above_average
                above_average += 1
                
            # Store details for later analysis
            income_details.append({
                "income": income,
                "category": category
            })
            
        except Exception as e:
            print(f"Error processing income {income}: {e}")
            continue

    # Calculate average income
    average_income = round(total_income / count if count > 0 else 0, 2)

    # Create a visualization of income distribution
    try:
        import matplotlib.pyplot as plt
        
        # Create bar chart
        categories = ["Below Poverty Line", "Low Income", "Below Average", "Average", "Above Average"]
        values = [below_poverty, low_income, below_average, average, above_average]
        colors = ['darkred', 'orangered', 'gold', 'lightgreen', 'darkgreen']
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(categories, values, color=colors)
        plt.title('Family Income Distribution')
        plt.xlabel('Income Category')
        plt.ylabel('Number of Households')
        plt.xticks(rotation=45)
        
        # Add value labels on top of each bar
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('income_distribution.png')
        print("Income distribution graph created and saved as 'income_distribution.png'")
        
    except Exception as e:
        print(f"Error creating visualization: {e}")

    # Return structured data for the dashboard
    return {
        "below_poverty_line": below_poverty,
        "low_income": low_income,
        "below_average": below_average,
        "average": average,
        "above_average": above_average,
        "averageIncome": average_income,
        "total_households": count,
        "current_thresholds": income_rl_agent.thresholds
    }

# Function to add feedback for reinforcement learning
def add_income_feedback(income, predicted_category, correct_category):
    """
    Add feedback to improve income categorization
    
    Parameters:
    - income: The income value
    - predicted_category: The category assigned by the system
    - correct_category: The correct category according to expert or user
    
    Returns:
    - Success status
    """
    try:
        buffer_size = income_rl_agent.add_feedback(income, predicted_category, correct_category)
        
        # Auto-update thresholds if buffer reaches certain size
        if buffer_size >= 5:  # Update after every 5 feedbacks
            income_rl_agent.update_thresholds()
        
        return True
    except Exception as e:
        print(f"Error adding income feedback: {e}")
        return False

# Function to force training of the model
def train_income_model():
    """Train the income categorization model with current feedback"""
    try:
        success = income_rl_agent.update_thresholds()
        return success
    except Exception as e:
        print(f"Error training income model: {e}")
        return False

# For testing
if __name__ == "__main__":
    try:
        # Test with sample data
        sample_data = pd.DataFrame({
            'Family Income ': [1500, 5000, 15000, 30000, 60000]
        })
        
        results = get_income_sentiment(sample_data)
        print(f"Analysis results: {results}")
        
        # Test feedback mechanism
        add_income_feedback(12000, "low_income", "below_average")
        add_income_feedback(40000, "below_average", "average")
        
        # Force training
        train_income_model()
        
    except Exception as e:
        print(f"Test run error: {e}")
