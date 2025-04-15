import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface SurveyData {
  "Name of Child ": string;
  "Age": number;
  "Class (बच्चे की कक्षा)": number;
  "Background of the Child ": string;
  "Problems in Home ": string;
  "Behavioral Impact": string;
  "Academic Performance ": number;
  "Family Income ": number;
  "Role models": string;
  "Reason for such role model ": string;
}

interface AnalysisResults {
  roleModel: {
    analysis: any;
    visualization: string;
  };
  background: {
    analysis: any;
    visualization: string;
  };
  behavioral: {
    analysis: any;
    visualization: string;
  };
  income: {
    analysis: any;
    visualization: string;
  };
  combinedDashboard: string;
}

const PsychologicalInsights: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [surveyData, setSurveyData] = useState<SurveyData | null>(null);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResults | null>(null);

  // Colors for charts
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];
  
  useEffect(() => {
    // Get data from navigation state or fetch it
    if (location.state?.surveyData) {
      setSurveyData(location.state.surveyData);
    }
    
    if (location.state?.analysisResults) {
      setAnalysisResults(location.state.analysisResults);
    } else {
      // If no analysis results in state, we can fetch aggregate data
      fetchAggregateData();
    }
  }, [location]);

  const fetchAggregateData = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/analysis/complete-summary');
      if (response.ok) {
        const data = await response.json();
        // Note: This is aggregate data, not for the specific survey
        setAnalysisResults({
          roleModel: { analysis: data.rolemodel, visualization: '' },
          background: { analysis: data.background, visualization: '' },
          behavioral: { analysis: data.behavioral, visualization: '' },
          income: { analysis: data.income, visualization: '' },
          combinedDashboard: ''
        });
      }
    } catch (error) {
      console.error('Error fetching analysis data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center">
          <div className="spinner-border animate-spin inline-block w-8 h-8 border-4 rounded-full text-purple-600" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-2 text-gray-600">Analyzing data...</p>
        </div>
      </div>
    );
  }

  if (!surveyData && !analysisResults) {
    return (
      <div className="max-w-3xl mx-auto p-8 mt-8 bg-white rounded-xl shadow-md">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">No Data Available</h2>
        <p className="text-gray-600 mb-4">No survey data or analysis results available.</p>
        <button
          onClick={() => navigate('/')}
          className="bg-purple-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-purple-700 transition-colors"
        >
          Take Survey
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 mt-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Psychological Insights</h2>
      
      {surveyData && (
        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Survey Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-gray-700"><span className="font-medium">Name:</span> {surveyData["Name of Child "]}</p>
              <p className="text-gray-700"><span className="font-medium">Age:</span> {surveyData["Age"]}</p>
              <p className="text-gray-700"><span className="font-medium">Class:</span> {surveyData["Class (बच्चे की कक्षा)"]}</p>
              <p className="text-gray-700"><span className="font-medium">Background:</span> {surveyData["Background of the Child "]}</p>
              <p className="text-gray-700"><span className="font-medium">Problems at Home:</span> {surveyData["Problems in Home "] || "None"}</p>
            </div>
            <div>
              <p className="text-gray-700"><span className="font-medium">Behavioral Impact:</span> {surveyData["Behavioral Impact"]}</p>
              <p className="text-gray-700"><span className="font-medium">Academic Performance:</span> {surveyData["Academic Performance "]} / 10</p>
              <p className="text-gray-700"><span className="font-medium">Family Income:</span> ₹{surveyData["Family Income "].toLocaleString()}</p>
              <p className="text-gray-700"><span className="font-medium">Role Model:</span> {surveyData["Role models"]}</p>
              <p className="text-gray-700"><span className="font-medium">Reason:</span> {surveyData["Reason for such role model "]}</p>
            </div>
          </div>
        </div>
      )}
      
      {analysisResults?.combinedDashboard && (
        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Combined Analysis Dashboard</h3>
          <img 
            src={`data:image/png;base64,${analysisResults.combinedDashboard}`}
            alt="Combined Analysis Dashboard"
            className="w-full h-auto rounded-lg"
          />
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Role Model Analysis */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Role Model Analysis</h3>
          {analysisResults?.roleModel?.visualization ? (
            <img 
              src={`data:image/png;base64,${analysisResults.roleModel.visualization}`}
              alt="Role Model Analysis"
              className="w-full h-auto rounded-lg"
            />
          ) : analysisResults?.roleModel?.analysis?.topTraits ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={Object.entries(analysisResults.roleModel.analysis.topTraits).map(([trait, value]) => ({
                    trait,
                    value
                  }))}
                  layout="vertical"
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="trait" type="category" />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#8884d8" name="Trait Score" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-gray-600">No role model analysis data available.</p>
          )}
        </div>
        
        {/* Background Sentiment Analysis */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Background Sentiment Analysis</h3>
          {analysisResults?.background?.visualization ? (
            <img 
              src={`data:image/png;base64,${analysisResults.background.visualization}`}
              alt="Background Sentiment Analysis"
              className="w-full h-auto rounded-lg"
            />
          ) : analysisResults?.background?.analysis ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={[
                    { name: 'Highly Positive', value: analysisResults.background.analysis.highly_positive || 0 },
                    { name: 'Positive', value: analysisResults.background.analysis.positive || 0 },
                    { name: 'Neutral', value: analysisResults.background.analysis.neutral || 0 },
                    { name: 'Negative', value: analysisResults.background.analysis.negative || 0 },
                    { name: 'Highly Negative', value: analysisResults.background.analysis.highly_negative || 0 }
                  ]}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#82ca9d" name="Count" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-gray-600">No background sentiment analysis data available.</p>
          )}
        </div>
        
        {/* Behavioral Impact Analysis */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Behavioral Impact Analysis</h3>
          {analysisResults?.behavioral?.visualization ? (
            <img 
              src={`data:image/png;base64,${analysisResults.behavioral.visualization}`}
              alt="Behavioral Impact Analysis"
              className="w-full h-auto rounded-lg"
            />
          ) : analysisResults?.behavioral?.analysis ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Highly Positive', value: analysisResults.behavioral.analysis.highly_positive_count || 0 },
                      { name: 'Positive', value: analysisResults.behavioral.analysis.positive_count || 0 },
                      { name: 'Neutral', value: analysisResults.behavioral.analysis.neutral_count || 0 },
                      { name: 'Negative', value: analysisResults.behavioral.analysis.negative_count || 0 },
                      { name: 'Highly Negative', value: analysisResults.behavioral.analysis.highly_negative_count || 0 }
                    ]}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label
                  >
                    {[
                      { name: 'Highly Positive', value: analysisResults.behavioral.analysis.highly_positive_count || 0 },
                      { name: 'Positive', value: analysisResults.behavioral.analysis.positive_count || 0 },
                      { name: 'Neutral', value: analysisResults.behavioral.analysis.neutral_count || 0 },
                      { name: 'Negative', value: analysisResults.behavioral.analysis.negative_count || 0 },
                      { name: 'Highly Negative', value: analysisResults.behavioral.analysis.highly_negative_count || 0 }
                    ].map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-gray-600">No behavioral impact analysis data available.</p>
          )}
        </div>
        
        {/* Income Analysis */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Family Income Analysis</h3>
          {analysisResults?.income?.visualization ? (
            <img 
              src={`data:image/png;base64,${analysisResults.income.visualization}`}
              alt="Family Income Analysis"
              className="w-full h-auto rounded-lg"
            />
          ) : analysisResults?.income?.analysis ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={[
                    { name: 'Below Poverty', value: analysisResults.income.analysis.below_poverty_line || 0 },
                    { name: 'Low Income', value: analysisResults.income.analysis.low_income || 0 },
                    { name: 'Below Average', value: analysisResults.income.analysis.below_average || 0 },
                    { name: 'Average', value: analysisResults.income.analysis.average || 0 },
                    { name: 'Above Average', value: analysisResults.income.analysis.above_average || 0 }
                  ]}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#ff7a45" name="Count" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-gray-600">No income analysis data available.</p>
          )}
        </div>
      </div>
      
      <div className="mt-8 text-center">
        <button
          onClick={() => navigate('/')}
          className="bg-purple-600 text-white py-2 px-6 rounded-lg font-medium hover:bg-purple-700 transition-colors"
        >
          Take Another Survey
        </button>
      </div>
    </div>
  );
};

export default PsychologicalInsights;
