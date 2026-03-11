import React from 'react';
import { BarChart } from 'lucide-react';
import {
  formatCorrelation,
  formatCount,
  formatInsightScore,
  INSIGHT_TITLES,
} from '../../utils/insightPresentation';

interface IncomeAcademicProfile {
  category: string;
  households: number;
  avg_income: number | null;
  avg_academic_score: number | null;
  rl_expected_academic_score: number;
}

interface IncomeData {
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
  academic_correlation?: number;
  income_academic_correlation?: number;
  training_samples?: number;
  model_updated?: boolean;
  income_academic_profile?: IncomeAcademicProfile[];
}

interface IncomeDistributionProps {
  data?: IncomeData;
}

const IncomeDistribution: React.FC<IncomeDistributionProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  const totalHouseholds = data.total_households || 0;
  const calculatePercentage = (value: number) =>
    totalHouseholds > 0 ? ((value / totalHouseholds) * 100).toFixed(1) : '0.0';

  const getCorrelationTone = (value?: number) => {
    if (typeof value !== 'number') return 'text-gray-500';
    const abs = Math.abs(value);
    if (abs >= 0.7) return 'text-green-700';
    if (abs >= 0.4) return 'text-blue-700';
    if (abs >= 0.2) return 'text-amber-700';
    return 'text-gray-700';
  };

  const incomeData = [
    { label: 'Below Poverty Line', value: data.below_poverty_line, color: 'bg-red-500', percentage: calculatePercentage(data.below_poverty_line), threshold: data.current_thresholds.poverty_line },
    { label: 'Low Income', value: data.low_income, color: 'bg-orange-400', percentage: calculatePercentage(data.low_income), threshold: data.current_thresholds.low_income },
    { label: 'Below Average', value: data.below_average, color: 'bg-yellow-400', percentage: calculatePercentage(data.below_average), threshold: data.current_thresholds.below_average },
    { label: 'Average', value: data.average, color: 'bg-green-400', percentage: calculatePercentage(data.average), threshold: data.current_thresholds.average },
    { label: 'Above Average', value: data.above_average, color: 'bg-green-600', percentage: calculatePercentage(data.above_average), threshold: 'Above' },
  ];

  const profileRows = data.income_academic_profile || [];

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5 sm:p-6 space-y-5">
      <div className="flex items-center">
        <BarChart className="h-6 w-6 text-orange-600 mr-2" />
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900">{INSIGHT_TITLES.income}</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        <div className="space-y-4">
          <div className="bg-orange-50 rounded-xl p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-orange-800 mb-2">Distribution by Income Level</h3>
            <div className="space-y-3">
              {incomeData.map((item, index) => (
                <div key={index}>
                  <div className="flex justify-between text-xs sm:text-sm mb-1">
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
          <div className="bg-gray-50 rounded-xl p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">Key Metrics</h3>
            <div className="grid grid-cols-2 gap-3 sm:gap-4 mb-4">
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Average Income</p>
                <p className="text-xl sm:text-2xl font-semibold text-orange-600">
                  ₹{data.averageIncome.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Total Households</p>
                <p className="text-xl sm:text-2xl font-semibold text-orange-600">
                  {formatCount(data.total_households)}
                </p>
              </div>
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Income-Academic Correlation</p>
                <p className={`text-lg sm:text-xl font-semibold ${getCorrelationTone(data.income_academic_correlation)}`}>
                  {formatCorrelation(data.income_academic_correlation)}
                </p>
                <p className="text-xs text-gray-500">Scale: -1 to +1</p>
              </div>
            </div>

          </div>

          <div className="bg-orange-50 rounded-xl p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-orange-800 mb-3 sm:mb-4">Income Thresholds</h3>
            <div className="space-y-2">
              {Object.entries(data.current_thresholds).map(([key, value]) => (
                <div key={key} className="flex justify-between text-xs sm:text-sm">
                  <span className="text-gray-600">
                    {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                  </span>
                  <span className="font-medium text-gray-800">₹{value.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-slate-50 rounded-xl p-4 sm:p-5">
        <h3 className="text-sm font-semibold text-slate-800 mb-3">
          Income vs Academic Profile (RL)
        </h3>
        {profileRows.length === 0 ? (
          <p className="text-xs sm:text-sm text-slate-600">
            No category-level academic profile available yet.
          </p>
        ) : (
          <div className="space-y-3">
            {profileRows.map((row) => (
              <div key={row.category} className="rounded-lg border border-slate-200 bg-white p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-slate-800">
                    {row.category.replace(/_/g, ' ')}
                  </p>
                  <p className="text-xs text-slate-500">
                    Households: {row.households.toLocaleString()}
                  </p>
                </div>
                <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs sm:text-sm">
                  <p className="text-slate-600">
                    Avg Income:{' '}
                    <span className="font-medium text-slate-800">
                      {row.avg_income === null ? 'N/A' : `₹${row.avg_income.toLocaleString()}`}
                    </span>
                  </p>
                  <p className="text-slate-600">
                    Avg Academic:{' '}
                    <span className="font-medium text-slate-800">
                      {row.avg_academic_score === null ? 'N/A' : row.avg_academic_score.toFixed(2)}
                      
                    </span>
                  </p>
                  <p className="text-slate-600">
                    RL Expected:{' '}
                    <span className="font-medium text-slate-800">
                      {formatInsightScore(row.rl_expected_academic_score)}
                    </span>
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default IncomeDistribution; 