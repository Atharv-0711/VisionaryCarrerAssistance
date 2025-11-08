import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Clock, RefreshCcw, TrendingUp } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import PsychiatricInsights from './psychatric_insights';
import { apiRequest } from '../utils/api';

interface AssessmentListItem {
  id: number;
  created_at: string;
  headline?: string | null;
  backgroundAverageScore?: number | null;
  student_id?: number | null;
  student_name?: string | null;
}

interface AssessmentDetail {
  id: number;
  created_at: string;
  survey_data: Record<string, unknown>;
  scores: any;
  recommendations?: any;
  career_suggestions?: any;
  student?: {
    id: number;
    full_name: string;
    unique_code?: string | null;
  } | null;
}

interface MyAssessmentsProps {
  authToken: string;
  studentId?: number;
  studentName?: string;
}

const formatDateTime = (value: string) => {
  try {
    return new Date(value).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  } catch {
    return value;
  }
};

const MyAssessments: React.FC<MyAssessmentsProps> = ({
  authToken,
  studentId,
  studentName,
}) => {
  const location = useLocation();
  const searchParams = useMemo(
    () => new URLSearchParams(location.search),
    [location.search]
  );
  const studentIdFromQuery = searchParams.get('studentId');
  const studentNameFromQuery = searchParams.get('studentName');
  const resolvedStudentId = useMemo(() => {
    if (typeof studentId === 'number') {
      return studentId;
    }
    if (studentIdFromQuery) {
      const parsed = Number.parseInt(studentIdFromQuery, 10);
      return Number.isNaN(parsed) ? undefined : parsed;
    }
    return undefined;
  }, [studentId, studentIdFromQuery]);
  const resolvedStudentName =
    studentName ?? (studentNameFromQuery ? studentNameFromQuery : undefined);

  const [assessments, setAssessments] = useState<AssessmentListItem[]>([]);
  const [selectedAssessment, setSelectedAssessment] =
    useState<AssessmentDetail | null>(null);
  const [listLoading, setListLoading] = useState<boolean>(true);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [comparisonIds, setComparisonIds] = useState<number[]>([]);
  const [detailCache, setDetailCache] = useState<Record<number, AssessmentDetail>>({});

  const fetchAssessmentDetail = useCallback(
    async (id: number, options: { silent?: boolean } = {}) => {
      if (!options.silent) {
        setDetailLoading(true);
      }
      setError(null);
      try {
        const detail = await apiRequest<AssessmentDetail>(
          `/api/assessments/${id}`,
          { authToken }
        );
        setDetailCache((prev) => ({ ...prev, [id]: detail }));
        if (!options.silent) {
          setSelectedAssessment(detail);
        }
        return detail;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Failed to load assessment.';
        setError(message);
        return undefined;
      } finally {
        if (!options.silent) {
          setDetailLoading(false);
        }
      }
    },
    [authToken]
  );

  const fetchAssessments = useCallback(async () => {
    setListLoading(true);
    setError(null);
    try {
      const path =
        resolvedStudentId !== undefined
          ? `/api/assessments?student_id=${resolvedStudentId}`
          : '/api/assessments';
      const list = await apiRequest<AssessmentListItem[]>(path, { authToken });
      setAssessments(list);
      if (list.length > 0) {
        await fetchAssessmentDetail(list[0].id);
      } else {
        setSelectedAssessment(null);
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to load assessments.';
      setError(message);
      setAssessments([]);
      setSelectedAssessment(null);
    } finally {
      setListLoading(false);
    }
  }, [authToken, fetchAssessmentDetail, resolvedStudentId]);

  useEffect(() => {
    fetchAssessments();
  }, [fetchAssessments]);

  useEffect(() => {
    setComparisonIds((prev) =>
      prev.filter((id) => assessments.some((assessment) => assessment.id === id))
    );
  }, [assessments]);

  const enrichedSurveyData = useMemo(() => {
    if (!selectedAssessment) return undefined;
    return {
      ...selectedAssessment.survey_data,
      analysis: selectedAssessment.scores,
    };
  }, [selectedAssessment]);

  const comparisonAssessments = useMemo(
    () =>
      comparisonIds
        .map((id) => detailCache[id])
        .filter((item): item is AssessmentDetail => Boolean(item)),
    [comparisonIds, detailCache]
  );

  const toggleComparison = useCallback(
    async (id: number) => {
      if (comparisonIds.includes(id)) {
        setComparisonIds((prev) => prev.filter((value) => value !== id));
        return;
      }

      if (!detailCache[id]) {
        const detail = await fetchAssessmentDetail(id, { silent: true });
        if (!detail) {
          return;
        }
      }

      setComparisonIds((prev) => {
        const next = [...prev, id];
        if (next.length > 2) {
          next.shift();
        }
        return next;
      });
    },
    [comparisonIds, detailCache, fetchAssessmentDetail]
  );

  const extractKeyMetrics = useCallback((assessment: AssessmentDetail | null) => {
    if (!assessment?.scores) return null;
    const scores = assessment.scores;
    const background =
      scores?.background?.analysis?.average_score ??
      scores?.background?.analysis?.averageScore;
    const behavioral =
      scores?.behavioral?.analysis?.average_score ??
      scores?.behavioral?.analysis?.averageScore;
    const rolePositive =
      scores?.roleModel?.analysis?.positiveImpact ??
      scores?.roleModel?.analysis?.positive_impact;
    const influential =
      scores?.roleModel?.analysis?.influentialCount ??
      scores?.roleModel?.analysis?.influential_count;
    const incomeAverage =
      scores?.income?.analysis?.average ??
      scores?.income?.analysis?.averageIncome;

    return {
      background: background ?? null,
      behavioral: behavioral ?? null,
      rolePositive: rolePositive ?? null,
      influential: influential ?? null,
      incomeAverage: incomeAverage ?? null,
    };
  }, []);

  const formatMetric = (value: number | null, digits = 2) =>
    value === null || Number.isNaN(value)
      ? 'N/A'
      : Number(value).toFixed(digits);

  const renderComparison = () => {
    const pool =
      comparisonAssessments.length > 0
        ? comparisonAssessments
        : selectedAssessment
        ? [selectedAssessment]
        : [];

    if (pool.length === 0) {
      return (
        <div className="rounded-xl border border-dashed border-purple-200 bg-purple-50/40 p-4 text-xs sm:text-sm text-purple-600">
          Select up to two assessments from the list to compare their key
          metrics.
        </div>
      );
    }

    if (pool.length === 1) {
      const [single] = pool;
      const metrics = extractKeyMetrics(single);
      if (!metrics) return null;

      return (
        <div className="rounded-xl border border-purple-200 bg-white p-5 sm:p-6 space-y-4">
          <h3 className="text-sm font-semibold text-purple-800 flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Assessment Snapshot ({formatDateTime(single.created_at)})
          </h3>
          <div className="grid grid-cols-2 gap-3 text-xs sm:text-sm text-gray-600">
            <div>
              <p className="font-medium text-gray-800">Background average</p>
              <p>{formatMetric(metrics.background)}</p>
            </div>
            <div>
              <p className="font-medium text-gray-800">Behavioral average</p>
              <p>{formatMetric(metrics.behavioral)}</p>
            </div>
            <div>
              <p className="font-medium text-gray-800">Positive impact</p>
              <p>{formatMetric(metrics.rolePositive, 0)}</p>
            </div>
            <div>
              <p className="font-medium text-gray-800">Influential count</p>
              <p>{formatMetric(metrics.influential, 0)}</p>
            </div>
            <div>
              <p className="font-medium text-gray-800">Average income</p>
              <p>₹{formatMetric(metrics.incomeAverage, 0)}</p>
            </div>
          </div>
        </div>
      );
    }

    if (pool.length === 2) {
      const [first, second] = pool;
      const firstMetrics = extractKeyMetrics(first);
      const secondMetrics = extractKeyMetrics(second);

      const metricsToCompare: Array<{
        label: string;
        first: number | null;
        second: number | null;
        formatter?: (value: number | null) => string;
      }> = [
        { label: 'Background average', first: firstMetrics?.background ?? null, second: secondMetrics?.background ?? null },
        { label: 'Behavioral average', first: firstMetrics?.behavioral ?? null, second: secondMetrics?.behavioral ?? null },
        { label: 'Positive impact', first: firstMetrics?.rolePositive ?? null, second: secondMetrics?.rolePositive ?? null },
        { label: 'Influential count', first: firstMetrics?.influential ?? null, second: secondMetrics?.influential ?? null },
        {
          label: 'Average income',
          first: firstMetrics?.incomeAverage ?? null,
          second: secondMetrics?.incomeAverage ?? null,
          formatter: (value) =>
            value === null ? 'N/A' : `₹${Number(value).toFixed(0)}`,
        },
      ];

      const renderDelta = (firstValue: number | null, secondValue: number | null) => {
        if (
          firstValue === null ||
          Number.isNaN(firstValue) ||
          secondValue === null ||
          Number.isNaN(secondValue)
        ) {
          return 'N/A';
        }
        const delta = Number(secondValue) - Number(firstValue);
        if (delta === 0) return 'No change';
        return `${delta > 0 ? '+' : ''}${delta.toFixed(2)}`;
      };

      return (
        <div className="rounded-xl border border-purple-200 bg-white p-5 sm:p-6 space-y-4">
          <h3 className="text-sm font-semibold text-purple-800 flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Comparison Overview
          </h3>
          <div className="text-xs text-gray-500">
            Comparing assessments from{' '}
            <span className="font-medium">
              {formatDateTime(first.created_at)}
            </span>{' '}
            and{' '}
            <span className="font-medium">
              {formatDateTime(second.created_at)}
            </span>
          </div>
          <div className="grid grid-cols-1 gap-3 text-xs sm:text-sm text-gray-700">
            {metricsToCompare.map((metric) => (
              <div
                key={metric.label}
                className="grid grid-cols-1 sm:grid-cols-4 sm:items-center gap-2 p-3 rounded-lg border border-gray-100"
              >
                <p className="font-medium text-gray-900">{metric.label}</p>
                <p>
                  {metric.formatter
                    ? metric.formatter(metric.first)
                    : formatMetric(metric.first)}
                </p>
                <p>
                  {metric.formatter
                    ? metric.formatter(metric.second)
                    : formatMetric(metric.second)}
                </p>
                <p className="text-xs text-purple-600">
                  Δ {renderDelta(metric.first, metric.second)}
                </p>
              </div>
            ))}
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm p-5 sm:p-6">
      <div className="flex flex-col md:flex-row md:space-x-6 space-y-6 md:space-y-0">
        <div className="md:w-1/3 space-y-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900">
              {resolvedStudentName
                ? `${resolvedStudentName}'s Assessments`
                : 'My Assessments'}
            </h2>
            <button
              onClick={fetchAssessments}
              disabled={listLoading}
              className="inline-flex items-center justify-center space-x-1 rounded-md border border-purple-200 px-3 py-2 min-h-[44px] text-sm font-medium text-purple-600 hover:bg-purple-50 disabled:opacity-60"
            >
              <RefreshCcw className="h-4 w-4" />
              <span>Refresh</span>
            </button>
          </div>
          <p className="text-sm text-gray-500 leading-relaxed">
            All assessments are securely stored so you can revisit them and
            monitor progress over time.
          </p>
          <div className="max-h-[420px] overflow-y-auto rounded-xl border border-gray-100">
            {listLoading ? (
              <div className="flex items-center justify-center py-12 text-sm text-gray-500">
                Loading assessments...
              </div>
            ) : assessments.length === 0 ? (
              <div className="flex items-center justify-center py-12 text-sm text-gray-500">
                No assessments yet. Complete a survey to generate your first
                report.
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {assessments.map((assessment) => {
                  const isActive =
                    selectedAssessment?.id === assessment.id &&
                    !detailLoading;
                  const isCompared = comparisonIds.includes(assessment.id);
                  return (
                    <li key={assessment.id}>
                      <button
                        onClick={() => fetchAssessmentDetail(assessment.id)}
                        className={`w-full text-left px-3 sm:px-4 py-3 transition-colors ${
                          isActive
                            ? 'bg-purple-50 border-l-4 border-purple-400'
                            : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-semibold text-gray-900">
                            {assessment.headline ||
                              assessment.student_name ||
                              'Assessment'}
                          </span>
                          <span className="text-xs text-gray-400 flex items-center space-x-1">
                            <Clock className="h-3.5 w-3.5" />
                            <span>{formatDateTime(assessment.created_at)}</span>
                          </span>
                        </div>
                        <div className="mt-1 text-xs text-gray-500">
                          Avg Background Score:{' '}
                          {typeof assessment.backgroundAverageScore === 'number'
                            ? assessment.backgroundAverageScore.toFixed(2)
                            : 'N/A'}
                        </div>
                        {assessment.student_name && (
                          <div className="mt-1 text-xs text-gray-400">
                            Student: {assessment.student_name}
                          </div>
                        )}
                        <div className="mt-2 flex items-center justify-between text-xs text-purple-600">
                          <span>
                            {isCompared
                              ? 'Selected for comparison'
                              : 'Compare this assessment'}
                          </span>
                          <button
                            type="button"
                            onClick={(event) => {
                              event.stopPropagation();
                              toggleComparison(assessment.id);
                            }}
                            className={`rounded-md px-2 py-1 border text-xs font-medium transition-colors ${
                              isCompared
                                ? 'border-purple-400 bg-purple-100 text-purple-700'
                                : 'border-purple-200 text-purple-600 hover:bg-purple-50'
                            }`}
                          >
                            {isCompared ? 'Remove' : 'Compare'}
                          </button>
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>

        <div className="md:w-2/3 space-y-6">
          {error && (
            <div className="rounded-md border border-red-100 bg-red-50 p-4 text-sm text-red-600">
              {error}
            </div>
          )}

          {detailLoading && (
            <div className="rounded-md border border-blue-100 bg-blue-50 p-4 text-sm text-blue-600">
              Loading assessment details...
            </div>
          )}

          {!detailLoading && !selectedAssessment && assessments.length === 0 && (
            <div className="rounded-md border border-gray-100 bg-gray-50 p-6 text-sm text-gray-500">
              Complete a survey to generate your first assessment.
            </div>
          )}

          {!detailLoading && selectedAssessment && (
            <>
              <div className="rounded-xl border border-gray-100 bg-gradient-to-r from-purple-50 to-blue-50 p-5">
                <p className="text-sm text-gray-600">
                  Assessment generated on{' '}
                  <span className="font-medium text-gray-900">
                    {formatDateTime(selectedAssessment.created_at)}
                  </span>
                </p>
                {selectedAssessment.student && (
                  <p className="mt-1 text-xs text-gray-500">
                    Student:{' '}
                    <span className="font-medium">
                      {selectedAssessment.student.full_name}
                    </span>
                    {selectedAssessment.student.unique_code
                      ? ` · Code: ${selectedAssessment.student.unique_code}`
                      : ''}
                  </p>
                )}
              </div>

              {renderComparison()}

              <PsychiatricInsights surveyData={enrichedSurveyData} />

              {(selectedAssessment.recommendations ||
                selectedAssessment.career_suggestions) && (
                <div className="rounded-xl border border-purple-200 bg-white p-5 sm:p-6 space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Recommendations &amp; Career Suggestions
                  </h3>
                  {selectedAssessment.recommendations ? (
                    <pre className="whitespace-pre-wrap rounded-lg bg-purple-50 p-4 text-sm text-gray-700 leading-relaxed">
                      {JSON.stringify(
                        selectedAssessment.recommendations,
                        null,
                        2
                      )}
                    </pre>
                  ) : (
                    <p className="text-sm text-gray-500">
                      No specific recommendations were generated for this
                      assessment.
                    </p>
                  )}
                  {selectedAssessment.career_suggestions ? (
                    <pre className="whitespace-pre-wrap rounded-lg bg-blue-50 p-4 text-sm text-gray-700 leading-relaxed">
                      {JSON.stringify(
                        selectedAssessment.career_suggestions,
                        null,
                        2
                      )}
                    </pre>
                  ) : null}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default MyAssessments;


