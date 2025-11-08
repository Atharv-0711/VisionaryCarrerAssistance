import React from 'react';
import { BarChart } from 'lucide-react';

interface IncomeDistributionProps {
  data?: {
    below_poverty_line: number;
    low_income: number;
    below_average: number;
    average: number;
    above_average: number;
    averageIncome: number;
    total_households: number;
    current_thresholds: {
      poverty_line: number;
      low_income: number;
      below_average: number;
      average: number;
    };
  };
}

const IncomeDistribution: React.FC<IncomeDistributionProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  const calculatePercentage = (value: number) => ((value / data.total_households) * 100).toFixed(1);

  const incomeData = [
    { label: 'Below Poverty Line', value: data.below_poverty_line, color: 'bg-red-500', percentage: calculatePercentage(data.below_poverty_line), threshold: data.current_thresholds.poverty_line },
    { label: 'Low Income', value: data.low_income, color: 'bg-orange-400', percentage: calculatePercentage(data.low_income), threshold: data.current_thresholds.low_income },
    { label: 'Below Average', value: data.below_average, color: 'bg-yellow-400', percentage: calculatePercentage(data.below_average), threshold: data.current_thresholds.below_average },
    { label: 'Average', value: data.average, color: 'bg-green-400', percentage: calculatePercentage(data.average), threshold: data.current_thresholds.average },
    { label: 'Above Average', value: data.above_average, color: 'bg-green-600', percentage: calculatePercentage(data.above_average), threshold: 'Above' },
  ];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center mb-6">
        <BarChart className="h-6 w-6 text-orange-600 mr-2" />
        <h2 className="text-xl font-semibold">Income Distribution</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div className="bg-orange-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-orange-800 mb-2">Distribution by Income Level</h3>
            <div className="space-y-3">
              {incomeData.map((item, index) => (
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
                <p className="text-sm text-gray-600">Average Income</p>
                <p className="text-2xl font-semibold text-orange-600">
                  ₹{data.averageIncome.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Households</p>
                <p className="text-2xl font-semibold text-orange-600">
                  {data.total_households.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-orange-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-orange-800 mb-4">Income Thresholds</h3>
            <div className="space-y-2">
              {Object.entries(data.current_thresholds).map(([key, value]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="text-gray-600">
                    {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                  </span>
                  <span className="font-medium">₹{value.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IncomeDistribution; 