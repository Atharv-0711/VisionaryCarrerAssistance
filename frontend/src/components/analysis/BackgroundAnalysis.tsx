import React from 'react';
import { Brain } from 'lucide-react';

interface BackgroundAnalysisProps {
  data?: {
    positive_count: number;
    negative_count: number;
    neutral_count: number;
    average_score: number;
    highly_positive: number;
    positive: number;
    neutral: number;
    negative: number;
    highly_negative: number;
  };
}

const BackgroundAnalysis: React.FC<BackgroundAnalysisProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  const total = data.highly_positive + data.positive + data.neutral + data.negative + data.highly_negative;
  
  const calculatePercentage = (value: number) => ((value / total) * 100).toFixed(1);

  const sentimentData = [
    { label: 'Highly Positive', value: data.highly_positive, color: 'bg-green-500', percentage: calculatePercentage(data.highly_positive) },
    { label: 'Positive', value: data.positive, color: 'bg-green-300', percentage: calculatePercentage(data.positive) },
    { label: 'Neutral', value: data.neutral, color: 'bg-gray-300', percentage: calculatePercentage(data.neutral) },
    { label: 'Negative', value: data.negative, color: 'bg-red-300', percentage: calculatePercentage(data.negative) },
    { label: 'Highly Negative', value: data.highly_negative, color: 'bg-red-500', percentage: calculatePercentage(data.highly_negative) },
  ];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center mb-6">
        <Brain className="h-6 w-6 text-blue-600 mr-2" />
        <h2 className="text-xl font-semibold">Background Analysis</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-800 mb-2">Sentiment Distribution</h3>
            <div className="space-y-3">
              {sentimentData.map((item, index) => (
                <div key={index}>
                  <div className="flex justify-between text-sm mb-1">
                    <span>{item.label}</span>
                    <span>{item.percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`${item.color} rounded-full h-2`}
                      style={{ width: `${item.percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-800 mb-4">Key Metrics</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Average Score</p>
                <p className="text-2xl font-semibold text-blue-600">
                  {data.average_score.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Responses</p>
                <p className="text-2xl font-semibold text-blue-600">{total}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Positive Responses</p>
                <p className="text-2xl font-semibold text-green-600">
                  {data.positive_count}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Negative Responses</p>
                <p className="text-2xl font-semibold text-red-600">
                  {data.negative_count}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BackgroundAnalysis; 