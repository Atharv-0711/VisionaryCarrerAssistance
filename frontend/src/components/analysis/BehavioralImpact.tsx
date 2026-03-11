import React from 'react';
import { PieChart } from 'lucide-react';
import {
  formatCorrelation,
  formatCount,
  formatInsightScore,
  formatPercent,
  INSIGHT_TITLES,
} from '../../utils/insightPresentation';

interface BehavioralImpactProps {
  data?: {
    highly_positive_count: number;
    positive_count: number;
    neutral_count: number;
    negative_count: number;
    highly_negative_count: number;
    average_score: number;
    total_responses: number;
    academic_correlation?: number;
    matched_pairs_count?: number;
    correlation_reason?: 'insufficient_pairs' | 'no_sentiment_variance' | 'no_academic_variance' | 'computed';
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

  const totalResponses = data.total_responses || 0;
  const calculatePercentage = (value: number) =>
    totalResponses > 0 ? ((value / totalResponses) * 100).toFixed(1) : '0.0';

  const getCorrelationTone = (value?: number) => {
    if (typeof value !== 'number') return 'text-gray-500';
    const abs = Math.abs(value);
    if (abs >= 0.7) return 'text-green-700';
    if (abs >= 0.4) return 'text-blue-700';
    if (abs >= 0.2) return 'text-amber-700';
    return 'text-gray-700';
  };

  const getCorrelationReasonLabel = (
    reason?: 'insufficient_pairs' | 'no_sentiment_variance' | 'no_academic_variance' | 'computed'
  ) => {
    switch (reason) {
      case 'computed':
        return 'Computed from matched sentiment-academic pairs.';
      case 'insufficient_pairs':
        return 'Not enough matched sentiment-academic pairs.';
      case 'no_sentiment_variance':
        return 'Sentiment scores do not vary across matched pairs.';
      case 'no_academic_variance':
        return 'Academic scores do not vary across matched pairs.';
      default:
        return 'Correlation reason unavailable.';
    }
  };

  const behavioralData = [
    { label: 'Highly Positive', value: data.highly_positive_count, color: 'bg-green-500', percentage: calculatePercentage(data.highly_positive_count) },
    { label: 'Positive', value: data.positive_count, color: 'bg-green-300', percentage: calculatePercentage(data.positive_count) },
    { label: 'Neutral', value: data.neutral_count, color: 'bg-gray-300', percentage: calculatePercentage(data.neutral_count) },
    { label: 'Negative', value: data.negative_count, color: 'bg-red-300', percentage: calculatePercentage(data.negative_count) },
    { label: 'Highly Negative', value: data.highly_negative_count, color: 'bg-red-500', percentage: calculatePercentage(data.highly_negative_count) },
  ];

  const positivePercentage =
    totalResponses > 0
      ? (((data.highly_positive_count + data.positive_count) / totalResponses) * 100).toFixed(1)
      : '0.0';
  const negativePercentage =
    totalResponses > 0
      ? (((data.highly_negative_count + data.negative_count) / totalResponses) * 100).toFixed(1)
      : '0.0';

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5 sm:p-6 space-y-5">
      <div className="flex items-center">
        <PieChart className="h-6 w-6 text-green-600 mr-2" />
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900">{INSIGHT_TITLES.behavioral}</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        <div className="space-y-4">
          <div className="bg-green-50 rounded-xl p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-green-800 mb-2">Impact Distribution</h3>
            <div className="space-y-3">
              {behavioralData.map((item, index) => (
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
            <h3 className="text-sm font-semibold text-gray-800 mb-3">Summary Metrics</h3>
            <div className="grid grid-cols-2 gap-3 sm:gap-4">
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Average Score</p>
                <p className="text-xl sm:text-2xl font-semibold text-green-600">
                  {formatInsightScore(data.average_score)}
                </p>
              </div>
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Total Responses</p>
                <p className="text-xl sm:text-2xl font-semibold text-green-600">
                  {formatCount(totalResponses)}
                </p>
              </div>
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Academic Correlation</p>
                <p className={`text-lg sm:text-xl font-semibold ${getCorrelationTone(data.academic_correlation)}`}>
                  {formatCorrelation(data.academic_correlation)}
                </p>
                <p className="text-xs text-gray-500">Scale: -1 to +1</p>
                <p className="text-xs text-gray-500">
                  {getCorrelationReasonLabel(data.correlation_reason)}
                </p>
              </div>
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Matched Pairs</p>
                <p className="text-lg sm:text-xl font-semibold text-indigo-600">
                  {formatCount(data.matched_pairs_count || 0)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 rounded-xl p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-green-800 mb-3">Overall Impact</h3>
            <div className="grid grid-cols-2 gap-3 sm:gap-4">
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Positive Impact</p>
                <p className="text-xl sm:text-2xl font-semibold text-green-600">{formatPercent(positivePercentage)}</p>
              </div>
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Negative Impact</p>
                <p className="text-xl sm:text-2xl font-semibold text-red-600">{formatPercent(negativePercentage)}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BehavioralImpact; 