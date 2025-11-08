import React from 'react';
import { Users } from 'lucide-react';

interface RoleModelAnalysisProps {
  data?: {
    positiveImpact: number;
    neutralImpact: number;
    negativeImpact: number;
    influentialCount: number;
    totalTraits: number;
    topTraits: {
      [key: string]: number;
    };
  };
}

const RoleModelAnalysis: React.FC<RoleModelAnalysisProps> = ({ data }) => {
  console.log('RoleModelAnalysis received data:', data);

  if (!data) {
    console.log('No data provided to RoleModelAnalysis, showing loading state');
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  const totalImpact = data.positiveImpact + data.neutralImpact + data.negativeImpact;
  const positivePercentage = ((data.positiveImpact / totalImpact) * 100).toFixed(1);
  const neutralPercentage = ((data.neutralImpact / totalImpact) * 100).toFixed(1);
  const negativePercentage = ((data.negativeImpact / totalImpact) * 100).toFixed(1);

  console.log('Calculated percentages:', {
    positive: positivePercentage,
    neutral: neutralPercentage,
    negative: negativePercentage
  });

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5 sm:p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div className="flex items-center">
          <Users className="h-6 w-6 text-purple-600 mr-2" />
          <h2 className="text-lg sm:text-xl font-semibold text-gray-900">Role Model Analysis</h2>
        </div>
        <p className="text-xs text-gray-500 sm:hidden">Positive influences at a glance.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        <div className="space-y-4">
          <div className="bg-purple-50 rounded-xl p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-purple-800 mb-3">Impact Distribution</h3>
            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-xs sm:text-sm mb-1">
                  <span>Positive Impact</span>
                  <span>{positivePercentage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 rounded-full h-2"
                    style={{ width: `${positivePercentage}%` }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Neutral Impact</span>
                  <span>{neutralPercentage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-yellow-500 rounded-full h-2"
                    style={{ width: `${neutralPercentage}%` }}
                  ></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Negative Impact</span>
                  <span>{negativePercentage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-red-500 rounded-full h-2"
                    style={{ width: `${negativePercentage}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 rounded-xl p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-blue-800 mb-2">Key Metrics</h3>
            <div className="grid grid-cols-2 gap-3 sm:gap-4">
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Influential Count</p>
                <p className="text-xl sm:text-2xl font-semibold text-blue-600">{data.influentialCount}</p>
              </div>
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Total Traits</p>
                <p className="text-xl sm:text-2xl font-semibold text-blue-600">{data.totalTraits}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 rounded-xl p-4 sm:p-5">
          <h3 className="text-sm font-semibold text-gray-800 mb-3 sm:mb-4">Top Traits</h3>
          <div className="space-y-3 sm:space-y-4">
            {Object.entries(data.topTraits)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 5)
              .map(([trait, count], index) => (
                <div key={trait} className="flex items-center">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-600 font-medium">
                    {index + 1}
                  </div>
                  <div className="ml-3">
                    <p className="text-sm sm:text-base font-medium text-gray-900">{trait}</p>
                    <p className="text-xs sm:text-sm text-gray-500">{count} mentions</p>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoleModelAnalysis; 