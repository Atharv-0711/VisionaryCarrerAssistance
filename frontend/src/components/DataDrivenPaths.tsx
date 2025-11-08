import React, { useState, useEffect } from 'react';
import RoleModelAnalysis from './analysis/RoleModelAnalysis';
import BackgroundAnalysis from './analysis/BackgroundAnalysis';
import BehavioralImpact from './analysis/BehavioralImpact';
import IncomeDistribution from './analysis/IncomeDistribution';

interface AnalysisData {
  roleModel?: {
    positiveImpact: number;
    neutralImpact: number;
    negativeImpact: number;
    influentialCount: number;
    totalTraits: number;
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
  };
  behavioral?: {
    highly_positive_count: number;
    positive_count: number;
    neutral_count: number;
    negative_count: number;
    highly_negative_count: number;
    average_score: number;
    total_responses: number;
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
  };
}

const DataDrivenPaths: React.FC = () => {
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Fetching analysis data...');
        const response = await fetch('http://localhost:5000/api/analysis/complete');
        if (!response.ok) throw new Error('Failed to fetch analysis data');
        const data = await response.json();
        console.log('Received data:', data);
        console.log('Role Model data:', data.roleModel);
        setAnalysisData(data);
      } catch (error) {
        console.error('Error fetching analysis:', error);
        setError('Failed to load analysis data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
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
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Data-Driven Career Insights</h1>
        <p className="text-gray-600">
          Comprehensive analysis of student backgrounds, behaviors, and aspirations to provide personalized career guidance.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {console.log('Rendering with analysisData:', analysisData)}
        <RoleModelAnalysis data={analysisData?.roleModel} />
        <BackgroundAnalysis data={analysisData?.background} />
        <BehavioralImpact data={analysisData?.behavioral} />
        <IncomeDistribution data={analysisData?.income} />
      </div>
    </div>
  );
};

export default DataDrivenPaths; 