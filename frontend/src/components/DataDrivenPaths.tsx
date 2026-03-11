import React from 'react';
import RoleModelAnalysis from './analysis/RoleModelAnalysis';
import BackgroundAnalysis from './analysis/BackgroundAnalysis';
import BehavioralImpact from './analysis/BehavioralImpact';
import IncomeDistribution from './analysis/IncomeDistribution';
import HomeProblemsAnalysis from './analysis/HomeProblemsAnalysis';
import { INSIGHT_TITLES } from '../utils/insightPresentation';

interface AnalysisData {
  rolemodel?: {
    positiveImpact: number;
    neutralImpact: number;
    negativeImpact: number;
    influentialCount: number;
    totalTraits: number;
    sentimentScore?: number;
    academicCorrelation?: number;
    topTraits: {
      [key: string]: number;
    };
  };
  background?: {
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
  behavioral?: {
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
  income?: {
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
    income_academic_profile?: Array<{
      category: string;
      households: number;
      avg_income: number | null;
      avg_academic_score: number | null;
      rl_expected_academic_score: number;
    }>;
    rl_expected_academic_by_category?: Record<string, number>;
  };
  home_problems?: {
    highly_positive_count?: number;
    positive_count?: number;
    neutral_count?: number;
    negative_count?: number;
    highly_negative_count?: number;
    average_score?: number;
    total_responses?: number;
    matched_pairs_count?: number;
    academic_correlation?: number;
    theme_distribution?: Array<{
      theme: string;
      count: number;
    }>;
  };
  analysis_errors?: Record<string, string>;
}

type DataDrivenPathsProps = {
  analysisData: AnalysisData | null;
  loading?: boolean;
  error?: string | null;
};

const hasNumber = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);

const hasRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null;

const AnalysisSectionFallback: React.FC<{ title: string; message?: string }> = ({
  title,
  message,
}) => (
  <div className="bg-white rounded-2xl shadow-sm p-5 sm:p-6 space-y-2">
    <h2 className="text-lg sm:text-xl font-semibold text-gray-900">{title}</h2>
    <p className="text-sm text-gray-600">
      {message || 'This analysis is temporarily unavailable.'}
    </p>
  </div>
);

const DataDrivenPaths: React.FC<DataDrivenPathsProps> = ({ analysisData, loading = false, error = null }) => {
  const roleModel = analysisData?.rolemodel;
  const background = analysisData?.background;
  const behavioral = analysisData?.behavioral;
  const income = analysisData?.income;
  const homeProblems = analysisData?.home_problems;
  const analysisErrors = analysisData?.analysis_errors || {};

  const hasRoleModelData =
    !!roleModel &&
    hasNumber(roleModel.positiveImpact) &&
    hasNumber(roleModel.neutralImpact) &&
    hasNumber(roleModel.negativeImpact) &&
    hasNumber(roleModel.influentialCount) &&
    hasNumber(roleModel.totalTraits) &&
    hasRecord(roleModel.topTraits);

  const hasBackgroundData =
    !!background &&
    hasNumber(background.positive_count) &&
    hasNumber(background.negative_count) &&
    hasNumber(background.neutral_count) &&
    hasNumber(background.average_score) &&
    hasNumber(background.highly_positive) &&
    hasNumber(background.positive) &&
    hasNumber(background.neutral) &&
    hasNumber(background.negative) &&
    hasNumber(background.highly_negative);

  const hasBehavioralData =
    !!behavioral &&
    hasNumber(behavioral.highly_positive_count) &&
    hasNumber(behavioral.positive_count) &&
    hasNumber(behavioral.neutral_count) &&
    hasNumber(behavioral.negative_count) &&
    hasNumber(behavioral.highly_negative_count) &&
    hasNumber(behavioral.average_score) &&
    hasNumber(behavioral.total_responses);

  const hasIncomeData =
    !!income &&
    hasNumber(income.below_poverty_line) &&
    hasNumber(income.low_income) &&
    hasNumber(income.below_average) &&
    hasNumber(income.average) &&
    hasNumber(income.above_average) &&
    hasNumber(income.averageIncome) &&
    hasNumber(income.total_households) &&
    hasRecord(income.current_thresholds);

  const hasDetailedHomeProblems =
    homeProblems &&
    hasNumber(homeProblems.highly_positive_count) &&
    hasNumber(homeProblems.positive_count) &&
    hasNumber(homeProblems.neutral_count) &&
    hasNumber(homeProblems.negative_count) &&
    hasNumber(homeProblems.highly_negative_count) &&
    hasNumber(homeProblems.average_score) &&
    hasNumber(homeProblems.total_responses);


  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div data-testid="loading-spinner" className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 sm:py-8">
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-3 sm:mb-4">Data-Driven Career Insights</h1>
        <p className="text-gray-600 text-sm sm:text-base leading-relaxed">
          Comprehensive analysis of student backgrounds, behaviors, and aspirations to provide personalized career guidance.
        </p>
      </div>

      {Object.keys(analysisErrors).length > 0 && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Some analytics sections could not be generated right now. Available sections are shown below.
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 sm:gap-8">
        {hasRoleModelData ? (
          <RoleModelAnalysis data={roleModel} />
        ) : (
          <AnalysisSectionFallback
            title={INSIGHT_TITLES.roleModel}
            message={analysisErrors.rolemodel}
          />
        )}
        {hasBackgroundData ? (
          <BackgroundAnalysis data={background} />
        ) : (
          <AnalysisSectionFallback
            title={INSIGHT_TITLES.background}
            message={analysisErrors.background}
          />
        )}
        {hasBehavioralData ? (
          <BehavioralImpact data={behavioral} />
        ) : (
          <AnalysisSectionFallback
            title={INSIGHT_TITLES.behavioral}
            message={analysisErrors.behavioral}
          />
        )}
        {hasIncomeData ? (
          <IncomeDistribution data={income} />
        ) : (
          <AnalysisSectionFallback
            title={INSIGHT_TITLES.income}
            message={analysisErrors.income}
          />
        )}
        {hasDetailedHomeProblems ? (
          <HomeProblemsAnalysis data={homeProblems as any} />
        ) : (
          <AnalysisSectionFallback
            title={INSIGHT_TITLES.homeProblems}
            message={analysisErrors.home_problems}
          />
        )}
      </div>
    </div>
  );
};

export default DataDrivenPaths; 