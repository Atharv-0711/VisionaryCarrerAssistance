import React, { useState, useEffect } from 'react';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import PsychatricInsights from './psychatric_insights';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface DataProps {
  behavioral?: {
    positive_count?: number;
    neutral_count?: number;
    negative_count?: number;
    highly_positive_count?: number;
    highly_negative_count?: number;
  };
  income?: {
    below_poverty_line?: number;
    below_average?: number;
    average?: number;
    above_average?: number;
    high_income?: number;
  };
}

interface SurveyData {
  "Name of Child "?: string;
  "Background of the Child "?: string;
  "Problems in Home "?: string;
  "Behavioral Impact"?: string;
  "Reason for such role model "?: string;
}

const DataChartComponent: React.FC<{ data: DataProps }> = ({ data }) => {
  const [surveyData, setSurveyData] = useState<SurveyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('http://localhost:5000/api/get-surveys');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      // Get the most recent entry (should be the only one in the array)
      setSurveyData(Array.isArray(result) && result.length > 0 ? result[0] : null);
    } catch (err) {
      console.error('Fetch error:', err);
      setError(err instanceof Error ? err.message : 'Failed to load data');
      setSurveyData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Add a refresh function that can be called after survey submission
  const refreshData = () => {
    fetchData();
  };

  // Make refreshData available to parent components
  if (typeof window !== 'undefined') {
    (window as any).refreshDashboard = refreshData;
  }

  return (
    <div className="space-y-8 p-4">
      {/* Charts Section unchanged */}

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-semibold mb-4">Latest Survey Insights</h3>
        
        {loading && <div>Loading...</div>}

        {error && (
          <div className="text-red-500 p-4 bg-red-50 rounded-lg mb-4">
            <strong>Note:</strong> {error}
          </div>
        )}

        {!loading && surveyData && (
          <PsychatricInsights surveyData={surveyData} />
        )}

        {!loading && !surveyData && (
          <div className="text-center p-4 text-gray-500">
            No survey data available
          </div>
        )}
      </div>
    </div>
  );
};

export default DataChartComponent;