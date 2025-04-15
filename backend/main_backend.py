import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from textblob import TextBlob
import re
import os

class VisionaryCareerAnalysis:
    def __init__(self):
        """Initialize the analysis system"""
        self.data = None
        self.load_data()
        plt.style.use('seaborn-v0_8')
        
    def load_data(self):
        """Load the main dataset"""
        try:
            self.data = pd.read_excel('Childsurvey.xlsx', sheet_name='Sheet1')
            print("Data loaded successfully!")
            print(f"Number of records: {len(self.data)}")
        except Exception as e:
            print(f"Error loading data: {str(e)}")
    
    def run_background_analysis(self):
        """Run background sentiment analysis"""
        try:
            print("\nRunning background analysis...")
            
            # Create visualization for background distribution
            plt.figure(figsize=(12, 6))
            background_counts = self.data['Background of the Child '].value_counts()
            sns.barplot(x=background_counts.values, y=background_counts.index)
            plt.title('Distribution of Children\'s Backgrounds')
            plt.xlabel('Count')
            plt.ylabel('Background Category')
            plt.tight_layout()
            plt.show()
            
            # Perform sentiment analysis on background descriptions
            self.data['Background_Sentiment'] = self.data['Background of the Child '].apply(
                lambda x: TextBlob(str(x)).sentiment.polarity
            )
            
            print("\nBackground Analysis Results:")
            print("-" * 50)
            print("\nBackground Distribution:")
            print(background_counts)
            print("\nAverage Sentiment Score:", self.data['Background_Sentiment'].mean())
            
            return self.data
        except Exception as e:
            print(f"Error in background analysis: {str(e)}")
            return self.data
    
    def run_behavioral_analysis(self):
        """Run behavioral impact analysis"""
        try:
            print("\nRunning behavioral analysis...")
            
            # Create visualization for behavioral impact
            plt.figure(figsize=(12, 6))
            behavior_counts = self.data['Behavioral Impact'].value_counts()
            sns.barplot(x=behavior_counts.values, y=behavior_counts.index)
            plt.title('Distribution of Behavioral Impact')
            plt.xlabel('Count')
            plt.ylabel('Impact Category')
            plt.tight_layout()
            plt.show()
            
            # Analyze behavioral impact patterns
            print("\nBehavioral Analysis Results:")
            print("-" * 50)
            print("\nBehavioral Impact Distribution:")
            print(behavior_counts)
            
            # Calculate percentage distribution
            behavior_percentages = (behavior_counts / len(self.data) * 100).round(2)
            print("\nPercentage Distribution:")
            print(behavior_percentages)
            
            return self.data
        except Exception as e:
            print(f"Error in behavioral analysis: {str(e)}")
            return self.data
    
    def run_role_model_analysis(self):
        """Run role model analysis"""
        try:
            print("\nRunning role model analysis...")
            
            # Create visualization for role models
            plt.figure(figsize=(12, 6))
            role_model_counts = self.data['Role models'].value_counts().head(10)
            sns.barplot(x=role_model_counts.values, y=role_model_counts.index)
            plt.title('Top 10 Role Models')
            plt.xlabel('Count')
            plt.ylabel('Role Model')
            plt.tight_layout()
            plt.show()
            
            # Analyze role model influence
            print("\nRole Model Analysis Results:")
            print("-" * 50)
            print("\nTop Role Models:")
            print(role_model_counts)
            
            return self.data
        except Exception as e:
            print(f"Error in role model analysis: {str(e)}")
            return self.data
    
    def run_income_analysis(self):
        """Run family income analysis"""
        try:
            print("\nRunning income analysis...")
            
            # Create visualization for income distribution
            plt.figure(figsize=(12, 6))
            sns.histplot(data=self.data, x='Family Income', bins=20)
            plt.title('Distribution of Family Income')
            plt.xlabel('Income')
            plt.ylabel('Count')
            plt.tight_layout()
            plt.show()
            
            # Calculate income statistics
            income_stats = self.data['Family Income'].describe()
            
            print("\nIncome Analysis Results:")
            print("-" * 50)
            print("\nIncome Statistics:")
            print(income_stats)
            
            # Calculate income quartiles
            quartiles = self.data['Family Income'].quantile([0.25, 0.5, 0.75])
            print("\nIncome Quartiles:")
            print(quartiles)
            
            return self.data
        except Exception as e:
            print(f"Error in income analysis: {str(e)}")
            return self.data
    
    def run_complete_analysis(self):
        """Run all analyses in sequence"""
        print("Starting complete analysis...\n")
        
        # Run all analyses
        background_results = self.run_background_analysis()
        behavioral_results = self.run_behavioral_analysis()
        role_model_results = self.run_role_model_analysis()
        income_results = self.run_income_analysis()
        
        # Create comprehensive report
        self.generate_report(
            background_results,
            behavioral_results,
            role_model_results,
            income_results
        )
        
        print("\nComplete analysis finished!")
    
    def generate_report(self, background, behavioral, role_model, income):
        """Generate a comprehensive analysis report"""
        print("\nGenerating comprehensive report...")
        
        # Create report directory if it doesn't exist
        if not os.path.exists('reports'):
            os.makedirs('reports')
        
        # Save comprehensive report
        report_path = 'reports/comprehensive_analysis.xlsx'
        
        try:
            with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
                # Ensure at least one sheet is written
                if background is not None:
                    background.to_excel(writer, sheet_name='Background_Analysis', index=False)
                else:
                    pd.DataFrame().to_excel(writer, sheet_name='Background_Analysis')
                
                if behavioral is not None:
                    behavioral.to_excel(writer, sheet_name='Behavioral_Analysis', index=False)
                
                if role_model is not None:
                    role_model.to_excel(writer, sheet_name='Role_Model_Analysis', index=False)
                
                if income is not None:
                    income.to_excel(writer, sheet_name='Income_Analysis', index=False)
            
            print(f"\nComprehensive report saved to: {report_path}")
        except Exception as e:
            print(f"Error generating report: {str(e)}")
            # Create a basic report with just the raw data
            try:
                self.data.to_excel(report_path, sheet_name='Raw_Data', index=False)
                print(f"\nBasic report saved to: {report_path}")
            except Exception as e2:
                print(f"Error saving basic report: {str(e2)}")
    
    def display_summary_statistics(self):
        """Display summary statistics for the dataset"""
        if self.data is not None:
            print("\nSummary Statistics:")
            print("-" * 50)
            print(f"Total number of children: {len(self.data)}")
            
            # Create overview visualization
            plt.figure(figsize=(15, 10))
            
            # Age distribution
            plt.subplot(2, 2, 1)
            sns.histplot(data=self.data, x='Age', bins=20)
            plt.title('Age Distribution')
            
            # Background distribution
            plt.subplot(2, 2, 2)
            background_counts = self.data['Background of the Child '].value_counts()
            sns.barplot(x=background_counts.values[:5], y=background_counts.index[:5])
            plt.title('Top 5 Backgrounds')
            
            # Behavioral Impact
            plt.subplot(2, 2, 3)
            behavior_counts = self.data['Behavioral Impact'].value_counts()
            sns.barplot(x=behavior_counts.values, y=behavior_counts.index)
            plt.title('Behavioral Impact Distribution')
            
            # Role Models
            plt.subplot(2, 2, 4)
            role_counts = self.data['Role models'].value_counts()
            sns.barplot(x=role_counts.values[:5], y=role_counts.index[:5])
            plt.title('Top 5 Role Models')
            
            plt.tight_layout()
            plt.show()
            
            print("\nDetailed Statistics:")
            print("-" * 50)
            print(f"\nAge Statistics:")
            print(self.data['Age'].describe())
            print(f"\nBackground Categories:")
            print(self.data['Background of the Child '].value_counts())
            print(f"\nBehavioral Impact Categories:")
            print(self.data['Behavioral Impact'].value_counts())
            print(f"\nRole Model Categories:")
            print(self.data['Role models'].value_counts().head())
        else:
            print("No data loaded. Please load data first.")

def main():
    """Main function to run the analysis"""
    # Create analysis instance
    analyzer = VisionaryCareerAnalysis()
    
    # Display menu
    while True:
        print("\nVisionary Career Analysis System")
        print("-" * 30)
        print("1. Run Complete Analysis")
        print("2. Run Background Analysis")
        print("3. Run Behavioral Analysis")
        print("4. Run Role Model Analysis")
        print("5. Run Income Analysis")
        print("6. Display Summary Statistics")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ")
        
        if choice == '1':
            analyzer.run_complete_analysis()
        elif choice == '2':
            analyzer.run_background_analysis()
        elif choice == '3':
            analyzer.run_behavioral_analysis()
        elif choice == '4':
            analyzer.run_role_model_analysis()
        elif choice == '5':
            analyzer.run_income_analysis()
        elif choice == '6':
            analyzer.display_summary_statistics()
        elif choice == '7':
            print("\nExiting...")
            break
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main() 