import React, { useMemo } from 'react';
import { Home } from 'lucide-react';
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
} from 'recharts';

interface ThemeDistributionItem {
  theme: string;
  count: number;
}

interface HomeProblemsData {
  highly_positive_count: number;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  highly_negative_count: number;
  average_score: number;
  total_responses: number;
  matched_pairs_count?: number;
  academic_correlation?: number;
  theme_distribution?: ThemeDistributionItem[];
}

interface HomeProblemsAnalysisProps {
  data?: HomeProblemsData;
}

const HomeProblemsAnalysis: React.FC<HomeProblemsAnalysisProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  const sentimentBars = useMemo(
    () => [
      { label: 'Highly Positive', value: data.highly_positive_count, color: '#15803d' },
      { label: 'Positive', value: data.positive_count, color: '#4ade80' },
      { label: 'Neutral', value: data.neutral_count, color: '#9ca3af' },
      { label: 'Negative', value: data.negative_count, color: '#fb923c' },
      { label: 'Highly Negative', value: data.highly_negative_count, color: '#991b1b' },
    ],
    [
      data.highly_positive_count,
      data.positive_count,
      data.neutral_count,
      data.negative_count,
      data.highly_negative_count,
    ],
  );

  const topThemes = useMemo(
    () => (data.theme_distribution || []).slice(0, 8),
    [data.theme_distribution],
  );

  const correlation = data.academic_correlation ?? 0;
  const correlationPercent = correlation * 100;

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5 sm:p-6 space-y-5">
      <div className="flex items-center">
        <Home className="h-6 w-6 text-rose-600 mr-2" />
        <h2 className="text-lg sm:text-xl font-semibold text-gray-900">{INSIGHT_TITLES.homeProblems}</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        <div className="bg-rose-50 rounded-xl p-4 sm:p-5">
          <h3 className="text-sm font-semibold text-rose-800 mb-3">Sentiment Distribution</h3>
          <div className="h-56 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sentimentBars}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} interval={0} />
                <YAxis allowDecimals={false} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey="value">
                  {sentimentBars.map((entry, index) => (
                    <Cell key={`sentiment-cell-${entry.label}-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-gray-50 rounded-xl p-4 sm:p-5">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">Academic Correlation</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-600">Average Sentiment Score</p>
              <p className="text-2xl font-semibold text-rose-600">{formatInsightScore(data.average_score)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600">Total Responses</p>
              <p className="text-2xl font-semibold text-rose-600">{formatCount(data.total_responses)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600">Matched Pairs</p>
              <p className="text-xl font-semibold text-indigo-600">{formatCount(data.matched_pairs_count ?? 0)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600">Correlation</p>
              <p className="text-xl font-semibold text-indigo-600">
                {formatCorrelation(correlation)}
              </p>
            </div>
          </div>
          <p className="mt-3 text-xs text-gray-500">
            Positive value means better home sentiment links with stronger academic performance (scale: -1 to +1).
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4 sm:p-5">
        <h3 className="text-sm font-semibold text-gray-800 mb-3">Top Home Problem Themes</h3>
        {topThemes.length === 0 ? (
          <p className="text-sm text-gray-500">No theme data available.</p>
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topThemes} layout="vertical" margin={{ left: 10, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" allowDecimals={false} />
                <YAxis dataKey="theme" type="category" width={130} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#f43f5e" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomeProblemsAnalysis;

