import React, { useState, useEffect, useCallback } from 'react';
import RoleModelAnalysis from './analysis/RoleModelAnalysis';
import BackgroundAnalysis from './analysis/BackgroundAnalysis';
import BehavioralImpact from './analysis/BehavioralImpact';
import IncomeDistribution from './analysis/IncomeDistribution';
import { io, Socket } from 'socket.io-client';

interface AnalysisData {
  rolemodel?: {
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
    background_details?: {
      background: string;
      score: number;
      category: string;
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
  const [backendBase, setBackendBase] = useState<string | null>(null);

  const fetchData = useCallback(async (preferredBase?: string) => {
    const timeoutFetch = (input: RequestInfo | URL, init?: RequestInit, timeoutMs = 6000) => {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), timeoutMs);
      return fetch(input, { ...init, signal: controller.signal }).finally(() => clearTimeout(id));
    };

    try {
      try {
        console.log('Fetching analysis data...');

        const envBase = (import.meta as any).env?.VITE_API_URL as string | undefined;
        const likelyBases = [
          preferredBase,
          envBase,
          `${window.location.origin}`,
          'http://localhost:5000',
          'http://127.0.0.1:5000',
          `${window.location.protocol}//${window.location.hostname}:5000`,
        ].filter(Boolean) as string[];

        // Try to discover a healthy backend first
        const findHealthyBase = async (): Promise<string | null> => {
          for (const base of likelyBases) {
            try {
              const res = await timeoutFetch(`${base}/api/health`, { method: 'GET' }, 3000);
              if (!res.ok) continue;
              const json = await res.json();
              if (json?.status === 'healthy') return base;
            } catch (_) {
              // ignore and continue
            }
          }
          return null;
        };

        const healthyBase = await findHealthyBase();
        const basesToTry = healthyBase ? [healthyBase] : likelyBases;

        const endpoints = [
          (base: string) => `${base}/api/analysis/complete?include_details=true`,
          (base: string) => `${base}/api/analysis/complete-summary`,
        ];

        let lastError: unknown = null;
        for (const base of basesToTry) {
          for (const buildUrl of endpoints) {
            const url = buildUrl(base);
            try {
              const response = await timeoutFetch(url, { method: 'GET' });
              if (!response.ok) {
                lastError = new Error(`HTTP ${response.status}`);
                continue;
              }
              const data = await response.json();
              console.log('Received data from', url, data);
              setAnalysisData(data);
              setError(null);
              setBackendBase(base);
              return; // success
            } catch (err) {
              lastError = err;
              console.warn('Fetch attempt failed for', url, err);
            }
          }
        }

        throw lastError ?? new Error('All endpoints failed');
      } catch (error) {
        console.error('Error fetching analysis:', error);
        setAnalysisData(null);
        setError('Failed to load analysis data. Backend not reachable or no data loaded.');
      } finally {
        setLoading(false);
      }
    } catch (outerError) {
      console.error('Unexpected error fetching data:', outerError);
      setError('Failed to load analysis data.');
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!backendBase) return;

    const socket: Socket = io(backendBase, {
      transports: ['websocket', 'polling'],
    });

    const handleSurveyUpdate = () => {
      console.info('Real-time update received, refreshing analysis data');
      fetchData(backendBase);
    };

    socket.on('survey_submitted', handleSurveyUpdate);

    return () => {
      socket.off('survey_submitted', handleSurveyUpdate);
      socket.disconnect();
    };
  }, [backendBase, fetchData]);

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

      <div className="grid grid-cols-1 gap-6 sm:gap-8">
        <RoleModelAnalysis data={analysisData?.rolemodel} />
        <BackgroundAnalysis data={analysisData?.background} />
        <BehavioralImpact data={analysisData?.behavioral} />
        <IncomeDistribution data={analysisData?.income} />
      </div>
    </div>
  );
};

export default DataDrivenPaths; 