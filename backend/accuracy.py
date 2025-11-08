# accuracy.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

# Import the sentiment analysis models
from sentiment_analysis_behavoralimpact import analyze_behavioral_impact
from sentiment_analysis_family_income import get_income_sentiment, income_rl_agent
from sentiment_analysis_background import get_background_sentiment
from sentiment_analysis_rolemodels import analyze_role_model

def calculate_metrics(y_true, y_pred):
    """Calculate and return various performance metrics"""
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, average='weighted', zero_division=0),
        "recall": recall_score(y_true, y_pred, average='weighted', zero_division=0),
        "f1_score": f1_score(y_true, y_pred, average='weighted', zero_division=0)
    }
    
    # Create and save confusion matrix visualization
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png')
    plt.close()
    
    return metrics

def evaluate_behavioral_impact_model(test_data, ground_truth):
    """Evaluate the behavioral impact sentiment analysis model"""
    print("Evaluating Behavioral Impact Model...")
    
    # Get predictions
    results = analyze_behavioral_impact(test_data)
    
    # Extract true and predicted labels
    y_true = []
    y_pred = []
    
    for idx, row in test_data.iterrows():
        text = row.get('Behavioral Impact', None)
        if pd.isna(text):
            continue
        
        # Get ground truth from the provided data
        true_label = ground_truth.loc[idx, 'true_sentiment'] if idx in ground_truth.index else None
        if true_label is None:
            continue
        
        # Find the prediction
        # This assumes results contains score per entry
        score = 3  # Default neutral
        for keyword in results['pos_keywords']:
            if keyword in text.lower():
                score = 4  # Positive
                break
        for keyword in results['neg_keywords']:
            if keyword in text.lower():
                score = 2  # Negative
                break
        
        # Map scores to categories
        if score >= 4:
            pred_label = 'positive'
        elif score <= 2:
            pred_label = 'negative'
        else:
            pred_label = 'neutral'
            
        y_true.append(true_label)
        y_pred.append(pred_label)
    
    # Calculate metrics
    if y_true and y_pred:
        metrics = calculate_metrics(y_true, y_pred)
        print(f"Metrics: {metrics}")
        return metrics
    else:
        print("No data available for evaluation")
        return None

def evaluate_income_model(test_data, ground_truth):
    """Evaluate the family income categorization model"""
    print("Evaluating Income Categorization Model...")
    
    # Get predictions
    results = get_income_sentiment(test_data)
    
    # Extract true and predicted labels
    y_true = []
    y_pred = []
    
    for idx, row in test_data.iterrows():
        income = row.get('Family Income ', None)
        if pd.isna(income):
            continue
            
        # Get ground truth
        true_label = ground_truth.loc[idx, 'true_income_category'] if idx in ground_truth.index else None
        if true_label is None:
            continue
            
        # Get prediction using the model's categorization function
        try:
            income_val = float(income)
            pred_label = income_rl_agent.categorize_income(income_val)
            
            y_true.append(true_label)
            y_pred.append(pred_label)
        except:
            continue
    
    # Calculate metrics
    if y_true and y_pred:
        metrics = calculate_metrics(y_true, y_pred)
        print(f"Metrics: {metrics}")
        return metrics
    else:
        print("No data available for evaluation")
        return None

def evaluate_background_model(test_data, ground_truth):
    """Evaluate the background sentiment analysis model"""
    print("Evaluating Background Model...")
    
    # Get predictions
    results = get_background_sentiment(test_data)
    
    # Extract true and predicted labels
    y_true = []
    y_pred = []
    
    # Process background data based on the model output
    for idx, row in test_data.iterrows():
        background = row.get('Background of the Child ', None)
        if pd.isna(background):
            continue
            
        # Get ground truth
        true_label = ground_truth.loc[idx, 'true_background_category'] if idx in ground_truth.index else None
        if true_label is None:
            continue
            
        # Find the prediction for this background
        pred_label = None
        for entry in results.get('background_details', []):
            if entry['background'] == background:
                pred_label = entry['category']
                break
                
        if pred_label:
            y_true.append(true_label)
            y_pred.append(pred_label)
    
    # Calculate metrics
    if y_true and y_pred:
        metrics = calculate_metrics(y_true, y_pred)
        print(f"Metrics: {metrics}")
        return metrics
    else:
        print("No data available for evaluation")
        return None

def evaluate_role_model_analysis(test_data, ground_truth):
    """Evaluate the role model analysis model"""
    print("Evaluating Role Model Analysis...")
    
    # Get predictions
    results = analyze_role_model(test_data)
    
    # For role model analysis, we might evaluate trait identification accuracy
    # or impact categorization if ground truth is available
    
    # This is a simplified example
    if 'impact_categories' in ground_truth.columns:
        y_true = ground_truth['impact_categories'].tolist()
        
        # Create predictions based on model output
        # This will depend on the structure of your ground truth data
        y_pred = []
        
        # Calculate metrics if possible
        if y_true and y_pred:
            metrics = calculate_metrics(y_true, y_pred)
            print(f"Metrics: {metrics}")
            return metrics
        
    print("Role model analysis uses a different evaluation approach")
    return None

def visualize_results(all_metrics):
    """Create a comparison visualization for all models"""
    if not all_metrics:
        return
        
    models = list(all_metrics.keys())
    metrics = ['accuracy', 'precision', 'recall', 'f1_score']
    
    plt.figure(figsize=(12, 8))
    
    for i, metric in enumerate(metrics):
        plt.subplot(2, 2, i+1)
        values = [all_metrics[model].get(metric, 0) for model in models]
        bars = plt.bar(models, values, color='skyblue')
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{height:.2f}', ha='center', va='bottom')
                    
        plt.title(metric.replace('_', ' ').title())
        plt.ylabel('Score')
        plt.ylim(0, 1.1)
        plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('model_comparison.png')
    plt.close()
    print("Model comparison visualization saved as 'model_comparison.png'")

def main():
    """Main function to run all evaluations"""
    try:
        # Load test data and ground truth
        # You'll need to adjust these paths to your actual data
        test_data = pd.read_excel('test_data.xlsx')
        ground_truth = pd.read_excel('ground_truth.xlsx', index_col=0)
        
        print(f"Loaded test data with {len(test_data)} entries")
        print(f"Loaded ground truth with {len(ground_truth)} entries")
        
        # Evaluate each model
        all_metrics = {}
        
        # Behavioral impact model
        behavioral_metrics = evaluate_behavioral_impact_model(test_data, ground_truth)
        if behavioral_metrics:
            all_metrics['Behavioral Impact'] = behavioral_metrics
        
        # Income model
        income_metrics = evaluate_income_model(test_data, ground_truth)
        if income_metrics:
            all_metrics['Income'] = income_metrics
        
        # Background model
        background_metrics = evaluate_background_model(test_data, ground_truth)
        if background_metrics:
            all_metrics['Background'] = background_metrics
        
        # Role model analysis
        role_model_metrics = evaluate_role_model_analysis(test_data, ground_truth)
        if role_model_metrics:
            all_metrics['Role Model'] = role_model_metrics
        
        # Visualize the results
        visualize_results(all_metrics)
        
        # Save all metrics to a file
        import json
        with open('model_evaluation_results.json', 'w') as f:
            json.dump(all_metrics, f, indent=2)
            
        print("Evaluation complete. Results saved to 'model_evaluation_results.json'")
        
    except Exception as e:
        print(f"Error in evaluation: {e}")

if __name__ == "__main__":
    main()
