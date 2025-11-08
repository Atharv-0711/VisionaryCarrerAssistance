import React from 'react';
import { PieChart } from 'lucide-react';

interface BehavioralImpactProps {
  data?: {
    highly_positive_count: number;
    positive_count: number;
    neutral_count: number;
    negative_count: number;
    highly_negative_count: number;
    average_score: number;
    total_responses: number;
  };
}

const BehavioralImpact: React.FC<BehavioralImpactProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  const calculatePercentage = (value: number) => ((value / data.total_responses) * 100).toFixed(1);

  const behavioralData = [
    { label: 'Highly Positive', value: data.highly_positive_count, color: 'bg-green-500', percentage: calculatePercentage(data.highly_positive_count) },
    { label: 'Positive', value: data.positive_count, color: 'bg-green-300', percentage: calculatePercentage(data.positive_count) },
    { label: 'Neutral', value: data.neutral_count, color: 'bg-gray-300', percentage: calculatePercentage(data.neutral_count) },
    { label: 'Negative', value: data.negative_count, color: 'bg-red-300', percentage: calculatePercentage(data.negative_count) },
    { label: 'Highly Negative', value: data.highly_negative_count, color: 'bg-red-500', percentage: calculatePercentage(data.highly_negative_count) },
  ];

  const positivePercentage = ((data.highly_positive_count + data.positive_count) / data.total_responses * 100).toFixed(1);
  const negativePercentage = ((data.highly_negative_count + data.negative_count) / data.total_responses * 100).toFixed(1);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center mb-6">
        <PieChart className="h-6 w-6 text-green-600 mr-2" />
        <h2 className="text-xl font-semibold">Behavioral Impact</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="bg-green-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-green-800 mb-2">Impact Distribution</h3>
            <div className="space-y-3">
              {behavioralData.map((item, index) => (
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
            <h3 className="text-sm font-medium text-gray-800 mb-4">Summary Metrics</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Average Score</p>
                <p className="text-2xl font-semibold text-green-600">
                  {data.average_score.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Responses</p>
                <p className="text-2xl font-semibold text-green-600">
                  {data.total_responses}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-green-800 mb-4">Overall Impact</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Positive Impact</p>
                <p className="text-2xl font-semibold text-green-600">{positivePercentage}%</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Negative Impact</p>
                <p className="text-2xl font-semibold text-red-600">{negativePercentage}%</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BehavioralImpact; 