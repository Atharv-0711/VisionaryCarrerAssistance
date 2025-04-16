from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import sys

# Import analysis modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sentiment_analysis_rolemodels as rolemodels
import sentiment_analysis_background as background
import sentiment_analysis_behavoralimpact as behavioral
import sentiment_analysis_family_income as income
import survey_processor

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variable declaration
global data
data = None

# Load data once at startup
try:
    # Use a direct path without 'backend' prefix since we're already in the backend directory
    data = pd.read_excel('Childsurvey.xlsx', sheet_name=0)
    print(f"Data loaded successfully with {len(data)} records")
except Exception as e:
    print(f"Error loading data: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "data_loaded": data is not None})

@app.route('/api/analysis/background', methods=['GET'])
def get_background_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        # Get include_details parameter (default to True for backward compatibility)
        include_details = request.args.get('include_details', 'true').lower() == 'true'
        
        # Get full results
        results = background.get_background_sentiment(data)
        
        # Remove background_details if not needed
        if not include_details and 'background_details' in results:
            del results['background_details']
        
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/behavioral', methods=['GET'])
def get_behavioral_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        results = behavioral.analyze_behavioral_impact(data)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/rolemodel', methods=['GET'])
def get_rolemodel_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        results = rolemodels.analyze_role_model(data)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/income', methods=['GET'])
def get_income_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        results = income.get_income_sentiment(data)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/complete', methods=['GET'])
def get_complete_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        # Get include_details parameter (default to false to exclude background details)
        include_details = request.args.get('include_details', 'false').lower() == 'true'
        
        # Get full background results
        background_results = background.get_background_sentiment(data)
        
        # Remove background_details if not needed
        if not include_details and 'background_details' in background_results:
            del background_results['background_details']
        
        behavioral_results = behavioral.analyze_behavioral_impact(data)
        rolemodel_results = rolemodels.analyze_role_model(data)
        income_results = income.get_income_sentiment(data)
        
        return jsonify({
            "background": background_results,
            "behavioral": behavioral_results,
            "rolemodel": rolemodel_results,
            "income": income_results,
            "totalSurveys": len(data)
        })
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/complete-summary', methods=['GET'])
def get_complete_summary():
    """New endpoint that returns all analyses without detailed background data"""
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        # Get background results
        background_results = background.get_background_sentiment(data)
        
        # Always remove background_details
        if 'background_details' in background_results:
            del background_results['background_details']
        
        behavioral_results = behavioral.analyze_behavioral_impact(data)
        rolemodel_results = rolemodels.analyze_role_model(data)
        income_results = income.get_income_sentiment(data)
        
        return jsonify({
            "background": background_results,
            "behavioral": behavioral_results,
            "rolemodel": rolemodel_results,
            "income": income_results,
            "totalSurveys": len(data)
        })
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/submit-survey', methods=['POST'])
def submit_survey():
    global data
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        # Get the form data from the request
        survey_data = request.json
        
        # Process the survey data and get analysis results
        analysis_results = survey_processor.process_and_save_survey(survey_data)
        
        # Reload the data to include the new entry
        try:
            data = pd.read_excel('Childsurvey.xlsx')
            print(f"Data reloaded with {len(data)} records")
        except Exception as e:
            print(f"Error reloading data after submission: {e}")
        
        # Return the analysis results
        return jsonify({
            "message": "Survey submitted and analyzed successfully",
            "analysis": analysis_results
        })
    
    except Exception as e:
        print(f"Error in submit_survey: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze-survey', methods=['POST'])
def analyze_survey():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        # Get the form data from the request
        survey_data = request.json
        
        # Process the survey data without saving
        analysis_results = survey_processor.process_survey(survey_data)
        
        # Generate combined dashboard
        combined_dashboard = survey_processor.generate_combined_dashboard(analysis_results)
        analysis_results["combinedDashboard"] = combined_dashboard
        
        return jsonify({
            "message": "Survey analyzed successfully",
            "analysis": analysis_results
        })
    
    except Exception as e:
        print(f"Error in analyze_survey: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/trait-explanations', methods=['GET'])
def get_trait_explanations():
    """Return trait explanations from the text file"""
    try:
        if os.path.exists('trait_explanations.txt'):
            with open('trait_explanations.txt', 'r') as f:
                explanations = f.read()
            return jsonify({"explanations": explanations})
        else:
            return jsonify({"explanations": "Trait explanations not available"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-surveys', methods=['GET'])
def get_surveys():
    global data
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        # Reload data to ensure we have the latest
        data = pd.read_excel('Childsurvey.xlsx')
        
        # Replace NaN values with None (null in JSON) and convert to records
        data = data.replace({pd.NA: None})  # Replace pandas NA
        data = data.where(pd.notnull(data), None)  # Replace numpy NaN
        
        # Convert the data to a list of dictionaries and clean the data
        surveys = []
        for record in data.to_dict('records'):
            # Clean each record by replacing NaN, NA, and other invalid values with None
            cleaned_record = {}
            for key, value in record.items():
                if pd.isna(value) or value == 'NaN' or value == 'NA':
                    cleaned_record[key] = None
                elif isinstance(value, float) and value.is_integer():
                    # Convert float to int if it's a whole number
                    cleaned_record[key] = int(value)
                else:
                    cleaned_record[key] = value
            surveys.append(cleaned_record)
        
        # Return only the most recent entry (last row)
        if surveys:
            return jsonify([surveys[-1]])  # Return as a single-item list to maintain compatibility
        return jsonify([])  # Return empty list if no surveys
            
    except Exception as e:
        print(f"Error getting surveys: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
