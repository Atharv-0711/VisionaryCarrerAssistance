import React, { useEffect, useMemo, useRef, useState } from 'react';
import { BarChart3, Users, Brain, School, Home, Sparkles } from 'lucide-react';
import { formatCorrelation, formatInsightScore, INSIGHT_TITLES } from '../utils/insightPresentation';

// Define TypeScript interfaces for our data structure
interface BackgroundDetail {
  background: string;
  score: number;
  category: string;
}

interface BackgroundData {
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
  background_details?: BackgroundDetail[];
}

interface BehavioralData {
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  [key: string]: any;
}

interface RoleModelData {
  influentialCount: number;
  [key: string]: any;
}

interface IncomeData {
  averageIncome: number;
  [key: string]: any;
}

interface AnalyticsData {
  totalSurveys: number;
  background: BackgroundData;
  behavioral: BehavioralData;
  rolemodel: RoleModelData;
  income: IncomeData;
  home_problems?: {
    highly_positive_count?: number;
    positive_count?: number;
    neutral_count?: number;
    negative_count?: number;
    highly_negative_count?: number;
    average_score?: number;
    total_responses?: number;
    academic_correlation?: number;
  };
}

interface StatCardProps {
  icon: React.ReactNode;
  title: string;
  value: number | string;
  label?: string;
  color: 'purple' | 'blue' | 'green' | 'orange' | 'rose';
  delayMs?: number;
}

interface AnalysisCardProps {
  title: string;
  data: any;
  color: 'purple' | 'blue' | 'green' | 'orange' | 'rose';
  delayMs?: number;
  shouldAnimateIn?: boolean;
}

const ANALYSIS_SECTIONS = [
  { key: 'all', label: 'All Insights' },
  { key: 'people', label: 'People & Behavior' },
  { key: 'context', label: 'Family & Context' },
] as const;

type AnalysisSectionKey = (typeof ANALYSIS_SECTIONS)[number]['key'];

const easeOutCubic = (x: number): number => 1 - Math.pow(1 - x, 3);

const AnalyticsDashboard: React.FC<{ data: AnalyticsData | null }> = ({ data }) => {
  const [selectedSection, setSelectedSection] = useState<AnalysisSectionKey>('all');
  const [cardsVisible, setCardsVisible] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setSelectedSection('all');
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const analysisCards = useMemo(
    () => [
      { id: 'background', title: INSIGHT_TITLES.background, data: data?.background, color: 'purple' as const, section: 'context' as const },
      { id: 'behavioral', title: INSIGHT_TITLES.behavioral, data: data?.behavioral, color: 'blue' as const, section: 'people' as const },
      { id: 'role-model', title: INSIGHT_TITLES.roleModel, data: data?.rolemodel, color: 'green' as const, section: 'people' as const },
      { id: 'income', title: INSIGHT_TITLES.income, data: data?.income, color: 'orange' as const, section: 'context' as const },
      { id: 'home-problems', title: INSIGHT_TITLES.homeProblems, data: data?.home_problems, color: 'rose' as const, section: 'context' as const },
    ],
    [data],
  );

  const visibleCards = analysisCards.filter(
    (card) => selectedSection === 'all' || card.section === selectedSection,
  );

  useEffect(() => {
    setCardsVisible(false);
    const timer = window.setTimeout(() => setCardsVisible(true), 24);
    return () => window.clearTimeout(timer);
  }, [selectedSection, data]);

  if (!data) {
    return (
      <div className="space-y-5 animate-pulse">
        <div className="h-20 bg-white rounded-2xl shadow-sm" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className="h-32 bg-white rounded-2xl shadow-sm" />
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-6">
          {Array.from({ length: 3 }).map((_, idx) => (
            <div key={idx} className="h-48 bg-white rounded-2xl shadow-sm" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 space-y-6 sm:space-y-8">
      <div className="bg-white rounded-2xl border border-purple-100 p-4 sm:p-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-purple-500 font-semibold">Live Dashboard</p>
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900">Student Insights Overview</h2>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full bg-purple-50 text-purple-700 px-3 py-1 text-xs sm:text-sm w-fit">
            <Sparkles size={14} />
            Updated as new surveys are submitted
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <StatCard 
          icon={<Users size={24} />}
          title="Total Surveys"
          value={data.totalSurveys}
          color="purple"
          delayMs={0}
        />
        <StatCard 
          icon={<Brain size={24} />}
          title="Behavioral Analysis"
          value={data.behavioral?.positive_count || 0}
          label="Positive Responses"
          color="blue"
          delayMs={50}
        />
        <StatCard 
          icon={<School size={24} />}
          title="Role Models"
          value={data.rolemodel?.influentialCount || 0}
          label="Influential Figures"
          color="green"
          delayMs={100}
        />
        <StatCard 
          icon={<BarChart3 size={24} />}
          title="Family Income"
          value={data.income?.averageIncome?.toFixed(2) || 0}
          label="Average Monthly"
          color="orange"
          delayMs={150}
        />
        <StatCard 
          icon={<Home size={24} />}
          title="Home Problems"
          value={data.home_problems?.negative_count || 0}
          label="Negative Responses"
          color="rose"
          delayMs={200}
        />
      </div>

      <div className="md:hidden overflow-x-auto pb-1">
        <div className="inline-flex gap-2">
          {ANALYSIS_SECTIONS.map((section) => (
            <button
              key={section.key}
              type="button"
              onClick={() => setSelectedSection(section.key)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium whitespace-nowrap transition-colors ${
                selectedSection === section.key
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200'
              }`}
            >
              {section.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-6">
        {visibleCards.map((card) => (
          <AnalysisCard
            key={card.id}
            title={card.title}
            data={card.data}
            color={card.color}
            delayMs={visibleCards.findIndex((visibleCard) => visibleCard.id === card.id) * 60}
            shouldAnimateIn={cardsVisible}
          />
        ))}
      </div>
    </div>
  );
};

const StatCard: React.FC<StatCardProps> = ({ icon, title, value, label, color, delayMs = 0 }) => {
  const colorClasses = {
    purple: 'bg-purple-50 text-purple-600',
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
    rose: 'bg-rose-50 text-rose-600',
  };
  const previousValueRef = useRef(0);
  const [displayValue, setDisplayValue] = useState<number | string>(value);

  useEffect(() => {
    const numericTarget = typeof value === 'number' ? value : Number(value);
    const isNumericTarget = Number.isFinite(numericTarget);

    if (!isNumericTarget) {
      setDisplayValue(value);
      return;
    }

    const startValue = previousValueRef.current;
    const endValue = numericTarget;
    const duration = 800;
    const startTime = performance.now();
    let frameId = 0;

    const animate = (time: number) => {
      const elapsed = time - startTime;
      const progress = Math.min(1, elapsed / duration);
      const easedProgress = easeOutCubic(progress);
      const nextValue = startValue + (endValue - startValue) * easedProgress;
      const hasDecimals = !Number.isInteger(endValue);
      setDisplayValue(hasDecimals ? nextValue.toFixed(2) : Math.round(nextValue));

      if (progress < 1) {
        frameId = window.requestAnimationFrame(animate);
      } else {
        setDisplayValue(hasDecimals ? endValue.toFixed(2) : Math.round(endValue));
        previousValueRef.current = endValue;
      }
    };

    frameId = window.requestAnimationFrame(animate);
    return () => window.cancelAnimationFrame(frameId);
  }, [value]);

  return (
    <div
      className="bg-white rounded-2xl shadow-sm p-5 sm:p-6 h-full transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md active:scale-[0.99]"
      style={{ transitionDelay: `${delayMs}ms` }}
    >
      <div className="flex flex-col">
        <div className={`p-2.5 sm:p-3 rounded-full inline-block ${colorClasses[color]}`}>
          {icon}
        </div>
        <div className="mt-3 sm:mt-4">
          <h3 className="text-gray-500 text-xs sm:text-sm font-medium">
            {title}
          </h3>
          <p className="text-xl sm:text-2xl font-bold leading-tight tabular-nums">
            {displayValue}
          </p>
          {label && <p className="text-gray-500 text-xs sm:text-sm">
            {label}
          </p>}
        </div>
      </div>
    </div>
  );
};

const AnalysisCard: React.FC<AnalysisCardProps> = ({ title, data, color, delayMs = 0, shouldAnimateIn = true }) => {
  const colorClasses = {
    purple: 'border-purple-200',
    blue: 'border-blue-200',
    green: 'border-green-200',
    orange: 'border-orange-200',
    rose: 'border-rose-200',
  };

  const formatKeyLabel = (key: string) =>
    key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());

  const formatPrimitiveValue = (value: any): string => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'number') return formatInsightScore(value);
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    return String(value);
  };

  const renderNestedValue = (value: any, depth = 0): React.ReactNode => {
    if (value === null || value === undefined) {
      return 'N/A';
    }

    if (Array.isArray(value)) {
      return value.length > 0 ? `${value.length} entries` : 'N/A';
    }

    if (typeof value === 'object') {
      return (
        <div className={`${depth > 0 ? 'pl-3 border-l border-gray-200 ml-1' : ''} mt-2 space-y-1`}>
          {Object.entries(value).map(([nestedKey, nestedValue]) => (
            <div key={`${nestedKey}-${depth}`} className="py-1">
              <div className="grid grid-cols-1 sm:grid-cols-[minmax(110px,1fr)_auto] gap-1 sm:gap-3 items-start">
                <span className="font-medium text-gray-600 text-sm break-words">{formatKeyLabel(nestedKey)}</span>
                {typeof nestedValue !== 'object' || nestedValue === null ? (
                  <span className="text-left sm:text-right text-sm text-gray-800 whitespace-normal break-words max-w-[220px]">
                    {formatPrimitiveValue(nestedValue)}
                  </span>
                ) : (
                  <span />
                )}
              </div>
              {typeof nestedValue === 'object' && nestedValue !== null && (
                <div className="mt-1">
                  {renderNestedValue(nestedValue, depth + 1)}
                </div>
              )}
            </div>
          ))}
        </div>
      );
    }

    return formatPrimitiveValue(value);
  };

  // Function to handle rendering of values that might be objects
  const renderValue = (key: string, value: any) => {
    if (value === null || value === undefined) {
      return 'N/A';
    }
    
    // Skip verbose detail arrays in summary cards.
    if (key === 'background_details' || key === 'income_details') {
      return null;
    }

    if (key === 'diagnostics' && typeof value === 'object' && !Array.isArray(value)) {
      const candidateMetrics = value.candidate_calibration_metrics ?? {};
      const mode = value.mode ?? 'N/A';

      return (
        <div className="mt-2 space-y-2">
          <div className="grid grid-cols-1 sm:grid-cols-[minmax(140px,1fr)_auto] gap-1 sm:gap-3 items-start">
            <span className="font-medium text-gray-600 text-sm">Candidate Calibration Metrics</span>
            <span />
          </div>
          <div className="pl-3 border-l border-gray-200 ml-1">
            {renderNestedValue({
              mae: candidateMetrics.mae,
              r2: candidateMetrics.r2,
              rmse: candidateMetrics.rmse,
            }, 1)}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-[minmax(140px,1fr)_auto] gap-1 sm:gap-3 items-start pt-1">
            <span className="font-medium text-gray-600 text-sm">Mode</span>
            <span className="text-left sm:text-right text-sm text-gray-800 whitespace-normal break-words max-w-[220px]">
              {formatPrimitiveValue(mode)}
            </span>
          </div>
        </div>
      );
    }

    if (key.includes('correlation')) {
      return formatCorrelation(value);
    }

    if (typeof value === 'object') {
      return renderNestedValue(value);
    }
    
    return formatPrimitiveValue(value);
  };

  const hiddenKeys = new Set([
    'background_details',
    'income_details',
    'pearson_correlation',
    'pearson_p_value',
    'spearman_correlation',
    'spearman_p_value',
    'total_responses',
    'training_loss_curve',
    'training_samples',
    'matched_pairs_count',
    'model_updated',
  ]);

  const visibleEntries = data
    ? Object.entries(data).filter(([key]) => !hiddenKeys.has(key))
    : [];

  return (
    <div
      className={`bg-white rounded-2xl shadow-sm p-5 sm:p-6 border-l-4 transition-all duration-400 ${colorClasses[color]} ${
        shouldAnimateIn ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
      }`}
      style={{ transitionDelay: `${delayMs}ms` }}
    >
      <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">{title}</h3>
      <div className="divide-y">
        {visibleEntries.length > 0 ? (
          visibleEntries.map(([key, value]) => (
            <div key={key} className="py-2">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-2">
                <span className="font-medium text-sm sm:text-base">
                  {formatKeyLabel(key)}
                </span>
                {typeof value !== 'object' && <span className="text-xs sm:text-sm text-gray-600">{renderValue(key, value)}</span>}
              </div>
              {typeof value === 'object' && value !== null && renderValue(key, value)}
            </div>
          ))
        ) : (
          <p className="py-2 text-sm text-gray-500">No analysis data available yet.</p>
        )}
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
