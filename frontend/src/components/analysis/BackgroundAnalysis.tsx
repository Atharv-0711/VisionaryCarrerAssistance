import React, { useMemo } from 'react';
import { Brain } from 'lucide-react';
import {
  formatCorrelation,
  formatCount,
  formatInsightScore,
  INSIGHT_TITLES,
} from '../../utils/insightPresentation';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  LabelList,
} from 'recharts';

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
    academic_correlation?: number;
    training_samples?: number;
    model_updated?: boolean;
    background_details?: {
      background: string;
      score: number;
      category: string;
      academic_performance_score?: number | null;
    }[];
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
  
  const calculatePercentage = (value: number) => (total === 0 ? '0.0' : ((value / total) * 100).toFixed(1));

  const aggregatedBackgrounds = useMemo(() => {
    if (!data.background_details || data.background_details.length === 0) {
      return [];
    }

    const aggregatedMap = new Map<
      string,
      { background: string; totalScore: number; count: number }
    >();

    for (const detail of data.background_details) {
      const backgroundKey = detail.background.trim();
      if (!backgroundKey) continue;

      const existing = aggregatedMap.get(backgroundKey);
      if (existing) {
        existing.totalScore += detail.score;
        existing.count += 1;
      } else {
        aggregatedMap.set(backgroundKey, {
          background: backgroundKey,
          totalScore: detail.score,
          count: 1,
        });
      }
    }

    return Array.from(aggregatedMap.values()).map((item) => ({
      background: item.background,
      averageScore: item.totalScore / item.count,
      count: item.count,
    }));
  }, [data.background_details]);

  const topBackgrounds = useMemo(() => {
    if (aggregatedBackgrounds.length === 0) return [];
    const sorted = [...aggregatedBackgrounds].sort((a, b) => {
      if (b.averageScore === a.averageScore) {
        return b.count - a.count;
      }
      return b.averageScore - a.averageScore;
    });
    return sorted;
  }, [aggregatedBackgrounds]);

  const sentimentChartData = useMemo(
    () =>
      [
        { label: 'Highly Positive', value: data.highly_positive, color: '#15803d' },
        { label: 'Positive', value: data.positive, color: '#4ade80' },
        { label: 'Neutral', value: data.neutral, color: '#d1d5db' },
        { label: 'Negative', value: data.negative, color: '#f97316' },
        { label: 'Highly Negative', value: data.highly_negative, color: '#991b1b' },
      ].map((item) => ({
        ...item,
        percentage: parseFloat(calculatePercentage(item.value)),
      })),
    [
      data.highly_positive,
      data.positive,
      data.neutral,
      data.negative,
      data.highly_negative,
      total,
    ],
  );

  const sentimentData = [
    { label: 'Highly Positive', value: data.highly_positive, color: 'bg-green-500', percentage: calculatePercentage(data.highly_positive) },
    { label: 'Positive', value: data.positive, color: 'bg-green-300', percentage: calculatePercentage(data.positive) },
    { label: 'Neutral', value: data.neutral, color: 'bg-gray-300', percentage: calculatePercentage(data.neutral) },
    { label: 'Negative', value: data.negative, color: 'bg-red-300', percentage: calculatePercentage(data.negative) },
    { label: 'Highly Negative', value: data.highly_negative, color: 'bg-red-500', percentage: calculatePercentage(data.highly_negative) },
  ];

  const correlationValue = data.academic_correlation ?? 0;
  const correlationPercent = correlationValue * 100;
  const correlationLabel =
    correlationValue > 0
      ? 'Positive'
      : correlationValue < 0
      ? 'Negative'
      : 'No clear';

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5 sm:p-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div className="flex items-center">
          <Brain className="h-6 w-6 text-blue-600 mr-2" />
          <h2 className="text-lg sm:text-xl font-semibold text-gray-900">{INSIGHT_TITLES.background}</h2>
        </div>
        <p className="text-xs text-gray-500 sm:hidden">
          Sentiment distribution across student backgrounds.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        <div className="space-y-4">
          <div className="bg-blue-50 rounded-xl p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-blue-800 mb-3">Sentiment Distribution</h3>
            <div className="h-56 sm:h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sentimentChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} interval={0} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 10 }} />
                  <Tooltip
                    formatter={(value: number, _name, payload) => [`${value} backgrounds`, payload?.payload?.label]}
                    labelFormatter={(label) => `Category: ${label}`}
                  />
                  <Bar dataKey="value">
                    <LabelList
                      dataKey="percentage"
                      formatter={(value: number) => `${value.toFixed(1)}%`}
                      position="top"
                      className="text-xs"
                    />
                    {sentimentChartData.map((entry, index) => (
                      <Cell key={`cell-${entry.label}-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-gray-50 rounded-xl p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">Key Metrics</h3>
            <div className="grid grid-cols-2 gap-3 sm:gap-4">
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Average Score</p>
                <p className="text-xl sm:text-2xl font-semibold text-blue-600">
                  {formatInsightScore(data.average_score)}
                </p>
              </div>
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Total Responses</p>
                <p className="text-xl sm:text-2xl font-semibold text-blue-600">{formatCount(total)}</p>
              </div>
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Positive Responses</p>
                <p className="text-xl sm:text-2xl font-semibold text-green-600">
                  {formatCount(data.positive_count)}
                </p>
              </div>
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Negative Responses</p>
                <p className="text-xl sm:text-2xl font-semibold text-red-600">
                  {formatCount(data.negative_count)}
                </p>
              </div>
              <div>
                <p className="text-xs sm:text-sm text-gray-600">Academic Correlation</p>
                <p className="text-xl sm:text-2xl font-semibold text-indigo-600">
                  {formatCorrelation(correlationValue)}
                </p>
                <p className="text-xs text-gray-500">{correlationLabel} relation (scale: -1 to +1)</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-5">
            <h3 className="text-sm font-semibold text-gray-800 mb-3 sm:mb-4">All Background Sentiments</h3>
            {topBackgrounds.length === 0 ? (
              <p className="text-gray-500 text-sm">No background sentiment data available.</p>
            ) : (
              <div className="overflow-x-auto">
                <div
                  className="h-56 sm:h-64"
                  style={{ minWidth: `${Math.max(topBackgrounds.length * 90, 600)}px` }}
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={topBackgrounds}
                      margin={{ top: 10, right: 10, left: 0, bottom: 30 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="background" angle={-35} textAnchor="end" height={70} interval={0} />
                      <YAxis domain={[1, 5]} allowDecimals={false} />
                      <Tooltip
                        formatter={(value: number, _name, payload) => [
                          `${(value as number).toFixed(2)} (avg score)`,
                          `${payload?.payload?.count ?? 0} responses`,
                        ]}
                        labelFormatter={(label) => `Background: ${label}`}
                      />
                      <Bar dataKey="averageScore" fill="#6366f1" radius={[6, 6, 0, 0]}>
                        <LabelList dataKey="count" position="top" className="text-xs" />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>

          <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-800 mb-4">Category Breakdown</h3>
            <div className="flex flex-wrap gap-4">
              {sentimentData.map((item) => (
                <div key={item.label} className="flex items-center gap-3">
                  <span className={`inline-block h-3 w-3 rounded-full ${item.color}`} />
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">{item.label}</p>
                    <p className="text-sm font-semibold text-gray-800">
                      {item.value} ({item.percentage}%)
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BackgroundAnalysis; 