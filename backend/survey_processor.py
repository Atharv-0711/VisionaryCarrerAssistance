# survey_processor.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
import os
from datetime import datetime

# Import sentiment analysis modules
import sentiment_analysis_rolemodels as rolemodels
import sentiment_analysis_background as background
import sentiment_analysis_behavoralimpact as behavioral
import sentiment_analysis_family_income as income

def process_survey(survey_data):
    """
    Process a single survey submission, perform sentiment analysis, and generate visualizations.
    
    Args:
        survey_data (dict): Dictionary containing survey form data
        
    Returns:
        dict: Analysis results with embedded visualizations
    """
    try:
        # Convert single survey to DataFrame format for compatibility with analysis modules
        df = pd.DataFrame([survey_data])
        
        # Perform sentiment analysis using each module
        try:
            role_model_results = rolemodels.analyze_role_model(df)
        except Exception as e:
            print(f"Error in role model analysis: {e}")
            role_model_results = {}
        
        try:
            background_results = background.get_background_sentiment(df)
        except Exception as e:
            print(f"Error in background analysis: {e}")
            background_results = {}
        
        try:
            behavioral_results = behavioral.analyze_behavioral_impact(df)
        except Exception as e:
            print(f"Error in behavioral analysis: {e}")
            behavioral_results = {}
        
        try:
            income_results = income.get_income_sentiment(df)
        except Exception as e:
            print(f"Error in income analysis: {e}")
            income_results = {}
        
        # Generate visualizations
        role_model_viz = generate_role_model_visualization(role_model_results)
        background_viz = generate_background_visualization(background_results)
        behavioral_viz = generate_behavioral_visualization(behavioral_results)
        income_viz = generate_income_visualization(income_results)
        
        # Combine all results
        combined_results = {
            "roleModel": {
                "analysis": role_model_results,
                "visualization": role_model_viz
            },
            "background": {
                "analysis": background_results,
                "visualization": background_viz
            },
            "behavioral": {
                "analysis": behavioral_results,
                "visualization": behavioral_viz
            },
            "income": {
                "analysis": income_results,
                "visualization": income_viz
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return combined_results
    
    except Exception as e:
        print(f"Error processing survey: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def generate_role_model_visualization(results):
    """Generate visualization for role model analysis results"""
    try:
        plt.figure(figsize=(10, 6))
        
        # Extract data
        top_traits = results.get("topTraits", {})
        traits = list(top_traits.keys())
        values = list(top_traits.values())
        
        # Create horizontal bar chart of top traits
        if traits and values:
            bars = plt.barh(traits, values, color='skyblue')
            
            # Add value labels on bars
            for bar in bars:
                width = bar.get_width()
                plt.text(width + 5, bar.get_y() + bar.get_height()/2, 
                        f'{width:.0f}', ha='left', va='center')
            
            plt.xlabel('Weighted Score')
            plt.title('Top Traits Based on Role Models')
            plt.tight_layout()
            
            # Convert plot to base64 encoded image
            img = get_image_base64()
            plt.close()
            return img
        else:
            plt.text(0.5, 0.5, 'No role model data available', 
                    horizontalalignment='center', verticalalignment='center')
            plt.title('Role Model Analysis')
            plt.axis('off')
            
            img = get_image_base64()
            plt.close()
            return img
    
    except Exception as e:
        print(f"Error generating role model visualization: {e}")
        return None

def generate_background_visualization(results):
    """Generate visualization for background sentiment analysis results"""
    try:
        plt.figure(figsize=(10, 6))
        
        # Extract data
        categories = ["Highly Positive", "Positive", "Neutral", "Negative", "Highly Negative"]
        values = [
            results.get("highly_positive", 0),
            results.get("positive", 0),
            results.get("neutral", 0),
            results.get("negative", 0),
            results.get("highly_negative", 0)
        ]
        
        # Check if we have any non-zero values
        if sum(values) > 0:
            # Create bar chart with custom colors
            colors = ['darkgreen', 'lightgreen', 'gold', 'orangered', 'darkred']
            bars = plt.bar(categories, values, color=colors)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, height + 0.1,
                        f'{height:.0f}', ha='center', va='bottom')
            
            plt.title('Background Sentiment Analysis')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
        else:
            plt.text(0.5, 0.5, 'No background sentiment data available', 
                    horizontalalignment='center', verticalalignment='center')
            plt.title('Background Sentiment Analysis')
            plt.axis('off')
        
        plt.tight_layout()
        
        # Convert plot to base64 encoded image
        img = get_image_base64()
        plt.close()
        return img
    
    except Exception as e:
        print(f"Error generating background visualization: {e}")
        return None

def generate_behavioral_visualization(results):
    """Generate visualization for behavioral impact analysis results"""
    try:
        plt.figure(figsize=(10, 6))
        
        # Extract data
        categories = ["Highly Positive", "Positive", "Neutral", "Negative", "Highly Negative"]
        values = [
            results.get("highly_positive_count", 0),
            results.get("positive_count", 0),
            results.get("neutral_count", 0),
            results.get("negative_count", 0),
            results.get("highly_negative_count", 0)
        ]
        
        # Check if we have any non-zero values
        if sum(values) > 0:
            # Create pie chart
            plt.pie(values, labels=categories, autopct='%1.1f%%', startangle=90,
                    colors=['darkgreen', 'lightgreen', 'gold', 'orangered', 'darkred'])
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        else:
            plt.text(0.5, 0.5, 'No behavioral impact data available', 
                    horizontalalignment='center', verticalalignment='center')
            plt.axis('off')
        
        plt.title('Behavioral Impact Sentiment Distribution')
        plt.tight_layout()
        
        # Convert plot to base64 encoded image
        img = get_image_base64()
        plt.close()
        return img
    
    except Exception as e:
        print(f"Error generating behavioral visualization: {e}")
        return None

def generate_income_visualization(results):
    """Generate visualization for income analysis results"""
    try:
        plt.figure(figsize=(10, 6))
        
        # Extract data
        categories = ["Below Poverty Line", "Low Income", "Below Average", "Average", "Above Average"]
        values = [
            results.get("below_poverty_line", 0),
            results.get("low_income", 0),
            results.get("below_average", 0),
            results.get("average", 0),
            results.get("above_average", 0)
        ]
        
        # Check if we have any non-zero values
        if sum(values) > 0:
            # Create bar chart with custom colors
            colors = ['darkred', 'orangered', 'gold', 'lightgreen', 'darkgreen']
            bars = plt.bar(categories, values, color=colors)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, height + 0.1,
                        f'{height:.0f}', ha='center', va='bottom')
            
            plt.title('Family Income Distribution')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
        else:
            plt.text(0.5, 0.5, 'No income data available', 
                    horizontalalignment='center', verticalalignment='center')
            plt.title('Family Income Distribution')
            plt.axis('off')
        
        plt.tight_layout()
        
        # Convert plot to base64 encoded image
        img = get_image_base64()
        plt.close()
        return img
    
    except Exception as e:
        print(f"Error generating income visualization: {e}")
        return None

def get_image_base64():
    """Convert the current matplotlib figure to a base64 encoded string"""
    try:
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        return image_base64
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None

def generate_combined_dashboard(results):
    """
    Generate a combined dashboard visualization of all sentiment analyses
    
    Args:
        results (dict): Dictionary containing all analysis results
        
    Returns:
        str: Base64 encoded image of the combined dashboard
    """
    try:
        fig, axs = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Psychological Insight Dashboard', fontsize=16)
        
        # Role Model Analysis (Top left)
        top_traits = results["roleModel"]["analysis"].get("topTraits", {})
        traits = list(top_traits.keys())
        values = list(top_traits.values())
        
        if traits and values:
            bars = axs[0, 0].barh(traits, values, color='skyblue')
            for bar in bars:
                width = bar.get_width()
                axs[0, 0].text(width + 5, bar.get_y() + bar.get_height()/2, 
                        f'{width:.0f}', ha='left', va='center')
            axs[0, 0].set_xlabel('Weighted Score')
        else:
            axs[0, 0].text(0.5, 0.5, 'No role model data available', 
                        horizontalalignment='center', verticalalignment='center')
            axs[0, 0].axis('off')
        
        axs[0, 0].set_title('Top Traits Based on Role Models')
        
        # Background Sentiment (Top right)
        background_data = results["background"]["analysis"]
        categories = ["Highly Positive", "Positive", "Neutral", "Negative", "Highly Negative"]
        values = [
            background_data.get("highly_positive", 0),
            background_data.get("positive", 0),
            background_data.get("neutral", 0),
            background_data.get("negative", 0),
            background_data.get("highly_negative", 0)
        ]
        
        if sum(values) > 0:
            colors = ['darkgreen', 'lightgreen', 'gold', 'orangered', 'darkred']
            bars = axs[0, 1].bar(categories, values, color=colors)
            for bar in bars:
                height = bar.get_height()
                axs[0, 1].text(bar.get_x() + bar.get_width()/2, height + 0.1,
                        f'{height:.0f}', ha='center', va='bottom')
            axs[0, 1].set_xticklabels(categories, rotation=45, ha='right')
        else:
            axs[0, 1].text(0.5, 0.5, 'No background sentiment data available', 
                        horizontalalignment='center', verticalalignment='center')
            axs[0, 1].axis('off')
        
        axs[0, 1].set_title('Background Sentiment Analysis')
        
        # Behavioral Impact (Bottom left)
        behavioral_data = results["behavioral"]["analysis"]
        categories = ["Highly Positive", "Positive", "Neutral", "Negative", "Highly Negative"]
        values = [
            behavioral_data.get("highly_positive_count", 0),
            behavioral_data.get("positive_count", 0),
            behavioral_data.get("neutral_count", 0),
            behavioral_data.get("negative_count", 0),
            behavioral_data.get("highly_negative_count", 0)
        ]
        
        if sum(values) > 0:
            axs[1, 0].pie(values, labels=categories, autopct='%1.1f%%', startangle=90,
                    colors=['darkgreen', 'lightgreen', 'gold', 'orangered', 'darkred'])
            axs[1, 0].axis('equal')
        else:
            axs[1, 0].text(0.5, 0.5, 'No behavioral impact data available', 
                        horizontalalignment='center', verticalalignment='center')
            axs[1, 0].axis('off')
        
        axs[1, 0].set_title('Behavioral Impact Sentiment')
        
        # Income Analysis (Bottom right)
        income_data = results["income"]["analysis"]
        categories = ["Below Poverty Line", "Low Income", "Below Average", "Average", "Above Average"]
        values = [
            income_data.get("below_poverty_line", 0),
            income_data.get("low_income", 0),
            income_data.get("below_average", 0),
            income_data.get("average", 0),
            income_data.get("above_average", 0)
        ]
        
        if sum(values) > 0:
            colors = ['darkred', 'orangered', 'gold', 'lightgreen', 'darkgreen']
            bars = axs[1, 1].bar(categories, values, color=colors)
            for bar in bars:
                height = bar.get_height()
                axs[1, 1].text(bar.get_x() + bar.get_width()/2, height + 0.1,
                        f'{height:.0f}', ha='center', va='bottom')
            axs[1, 1].set_xticklabels(categories, rotation=45, ha='right')
        else:
            axs[1, 1].text(0.5, 0.5, 'No income data available', 
                        horizontalalignment='center', verticalalignment='center')
            axs[1, 1].axis('off')
        
        axs[1, 1].set_title('Family Income Distribution')
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust layout to make room for suptitle
        
        # Convert plot to base64 encoded image
        img = get_image_base64()
        plt.close()
        return img
    
    except Exception as e:
        print(f"Error generating combined dashboard: {e}")
        return None

def process_and_save_survey(survey_data):
    """
    Process survey data, perform sentiment analysis, save to Excel, and return results
    
    Args:
        survey_data (dict): Dictionary containing survey form data
        
    Returns:
        dict: Analysis results with embedded visualizations
    """
    try:
        # Process the survey data
        analysis_results = process_survey(survey_data)
        
        # Load existing data
        excel_path = 'Childsurvey.xlsx'
        try:
            existing_data = pd.read_excel(excel_path)
        except Exception as e:
            print(f"Error loading existing data: {e}")
            existing_data = pd.DataFrame()
        
        # Ensure survey_data is properly formatted for Excel
        formatted_data = {}
        survey_columns = [
            "Name of Child ",
            "Age",
            "Class (बच्चे की कक्षा)",
            "Background of the Child ",
            "Problems in Home ",
            "Behavioral Impact",
            "Academic Performance ",
            "Family Income ",
            "Role models",
            "Reason for such role model "
        ]
        
        for col in survey_columns:
            if col in survey_data:
                formatted_data[col] = survey_data[col]
            else:
                formatted_data[col] = None
        
        # Convert to DataFrame
        new_row = pd.DataFrame([formatted_data])
        
        # Combine with existing data
        updated_data = pd.concat([existing_data, new_row], ignore_index=True)
        
        # Save to Excel
        try:
            updated_data.to_excel(excel_path, index=False)
            print(f"Survey data saved to {excel_path}")
        except Exception as e:
            print(f"Error saving survey data to Excel: {e}")
            raise e  # Re-raise the exception to be caught by the outer try-except
        
        # Generate combined dashboard
        combined_dashboard = generate_combined_dashboard(analysis_results)
        analysis_results["combinedDashboard"] = combined_dashboard
        
        return analysis_results
    
    except Exception as e:
        print(f"Error processing and saving survey: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# For testing purposes
if __name__ == "__main__":
    # Sample survey data for testing
    sample_survey = {
        "Name of Child ": "Test Child",
        "Age": 10.0,
        "Class (बच्चे की कक्षा)": 5.0,
        "Background of the Child ": "Middle Class",
        "Problems in Home ": "None",
        "Behavioral Impact": "Positive behavior and good academic interest",
        "Academic Performance ": 8.0,
        "Family Income ": 25000.0,
        "Role models": "Teacher",
        "Reason for such role model ": "Inspired by teaching style and knowledge"
    }
    
    # Process sample survey
    results = process_and_save_survey(sample_survey)
    print("Analysis completed successfully")
