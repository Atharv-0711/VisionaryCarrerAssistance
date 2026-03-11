import React, { useEffect, useMemo, useState } from 'react';
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from 'recharts';
import { AlertTriangle, CheckCircle2, Database, Eye } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { apiRequest } from '../utils/api';

interface BatchSummary {
  batchId: string;
  schemaVersion: string;
  source: string;
  ingestedAt: string;
  totalRows: number;
  insertedRows: number;
  duplicateRows: number;
  outlierRows: number;
  completenessScore: number;
  alertCount: number;
}

interface MonitoringResponse {
  batches: BatchSummary[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
  thresholds: {
    completenessMin: number;
    duplicatesMax: number;
    outliersMax: number;
  };
}

interface FieldMetric {
  fieldName: string;
  totalCount: number;
  missingCount: number;
  completenessRatio: number;
  outlierCount: number;
}

interface BatchAlert {
  id: number;
  metricName: string;
  metricValue: number;
  thresholdValue: number;
  comparator: string;
  severity: string;
  message: string;
  createdAt: string;
}

interface BatchDetailResponse {
  batch: BatchSummary;
  fieldMetrics: FieldMetric[];
  alerts: BatchAlert[];
}

interface AlertConfigPayload {
  completenessMin: number;
  duplicatesMax: number;
  outliersMax: number;
  emailRecipients: string[];
  webhookUrls: string[];
  slackWebhookUrl: string;
  updatedAt?: string;
}

const MONITORING_PAGE_SIZE = 25;

const parsePositivePage = (rawValue: string | null): number => {
  const parsedValue = Number(rawValue);
  return Number.isInteger(parsedValue) && parsedValue > 0 ? parsedValue : 1;
};

const DataQualityMonitoring: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [currentPage, setCurrentPage] = useState<number>(() => parsePositivePage(searchParams.get('page')));
  const [monitoring, setMonitoring] = useState<MonitoringResponse | null>(null);
  const [selectedBatchId, setSelectedBatchId] = useState<string>(() => searchParams.get('batchId') || '');
  const [selectedBatch, setSelectedBatch] = useState<BatchDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [config, setConfig] = useState<AlertConfigPayload>({
    completenessMin: 0.9,
    duplicatesMax: 0,
    outliersMax: 5,
    emailRecipients: [],
    webhookUrls: [],
    slackWebhookUrl: '',
  });
  const [emailText, setEmailText] = useState('');
  const [webhookText, setWebhookText] = useState('');
  const [savingConfig, setSavingConfig] = useState(false);

  const loadMonitoring = async (page = currentPage) => {
    const response = await apiRequest<MonitoringResponse>(
      `/api/data-quality/monitoring?page=${page}&pageSize=${MONITORING_PAGE_SIZE}`
    );
    setMonitoring(response);
    setCurrentPage(response.pagination.page);
    setSelectedBatchId((currentBatchId) => currentBatchId || response.batches[0]?.batchId || '');
  };

  const loadAlertConfig = async () => {
    const response = await apiRequest<AlertConfigPayload>('/api/data-quality/alerts/config');
    setConfig(response);
    setEmailText((response.emailRecipients || []).join('\n'));
    setWebhookText((response.webhookUrls || []).join('\n'));
  };

  const loadBatchDetails = async (batchId: string) => {
    if (!batchId) return;
    const response = await apiRequest<BatchDetailResponse>(`/api/data-quality/batches/${encodeURIComponent(batchId)}`);
    setSelectedBatch(response);
  };

  useEffect(() => {
    setLoading(true);
    setError(null);
    loadMonitoring(currentPage)
      .catch((err) => {
        console.error(err);
        setError('Unable to load monitoring data right now.');
      })
      .finally(() => setLoading(false));
  }, [currentPage]);

  useEffect(() => {
    loadAlertConfig().catch((err) => {
      console.error(err);
      setError('Unable to load monitoring data right now.');
    });
  }, []);

  useEffect(() => {
    if (!selectedBatchId) return;
    loadBatchDetails(selectedBatchId).catch((err) => {
      console.error(err);
      setError('Unable to load the selected batch details.');
    });
  }, [selectedBatchId]);

  useEffect(() => {
    const pageFromUrl = parsePositivePage(searchParams.get('page'));
    const batchIdFromUrl = searchParams.get('batchId') || '';
    if (pageFromUrl !== currentPage) {
      setCurrentPage(pageFromUrl);
    }
    if (batchIdFromUrl && batchIdFromUrl !== selectedBatchId) {
      setSelectedBatchId(batchIdFromUrl);
    }
  }, [currentPage, searchParams, selectedBatchId]);

  useEffect(() => {
    const nextSearchParams = new URLSearchParams(searchParams);
    if (currentPage > 1) {
      nextSearchParams.set('page', String(currentPage));
    } else {
      nextSearchParams.delete('page');
    }
    if (selectedBatchId) {
      nextSearchParams.set('batchId', selectedBatchId);
    } else {
      nextSearchParams.delete('batchId');
    }

    if (nextSearchParams.toString() !== searchParams.toString()) {
      setSearchParams(nextSearchParams, { replace: true });
    }
  }, [currentPage, searchParams, selectedBatchId, setSearchParams]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      loadMonitoring(currentPage).catch((err) => {
        console.error('Monitoring refresh failed', err);
      });
    }, 30000);

    return () => window.clearInterval(timer);
  }, [currentPage]);

  const totalBatches = monitoring?.pagination.total || 0;
  const pageSize = monitoring?.pagination.pageSize || MONITORING_PAGE_SIZE;
  const totalPages = Math.max(monitoring?.pagination.totalPages || 1, 1);
  const pageStart = totalBatches === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const pageEnd = totalBatches === 0 ? 0 : Math.min((currentPage - 1) * pageSize + (monitoring?.batches.length || 0), totalBatches);

  const chartData = useMemo(() => {
    if (!monitoring?.batches?.length) return [];
    return [...monitoring.batches]
      .reverse()
      .map((item) => ({
        ...item,
        label: new Date(item.ingestedAt).toLocaleString(),
        completenessPercent: Number((item.completenessScore * 100).toFixed(2)),
      }));
  }, [monitoring]);

  const saveAlertConfig = async () => {
    setSavingConfig(true);
    setError(null);
    try {
      const payload = {
        completenessMin: config.completenessMin,
        duplicatesMax: config.duplicatesMax,
        outliersMax: config.outliersMax,
        emailRecipients: emailText.split('\n').map((v) => v.trim()).filter(Boolean),
        webhookUrls: webhookText.split('\n').map((v) => v.trim()).filter(Boolean),
        slackWebhookUrl: config.slackWebhookUrl.trim(),
      };

      const response = await apiRequest<{ config: AlertConfigPayload }>('/api/data-quality/alerts/config', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      setConfig(response.config);
    } catch (err) {
      console.error(err);
      setError('Unable to save alert configuration.');
    } finally {
      setSavingConfig(false);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-md border border-red-100 bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          icon={<Database className="h-5 w-5" />}
          label="Batches"
          value={totalBatches}
        />
        <MetricCard
          icon={<CheckCircle2 className="h-5 w-5" />}
          label="Avg Completeness"
          value={`${(
            ((monitoring?.batches || []).reduce((acc, row) => acc + row.completenessScore, 0) /
              Math.max((monitoring?.batches || []).length, 1)) *
            100
          ).toFixed(2)}%`}
        />
        <MetricCard
          icon={<AlertTriangle className="h-5 w-5" />}
          label="Total Alerts"
          value={(monitoring?.batches || []).reduce((acc, row) => acc + row.alertCount, 0)}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <section className="rounded-2xl border border-gray-100 bg-white p-4">
          <h3 className="font-semibold text-gray-900">Completeness Trend (%)</h3>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="completenessPercent" stroke="#7c3aed" name="Completeness %" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="rounded-2xl border border-gray-100 bg-white p-4">
          <h3 className="font-semibold text-gray-900">Duplicates and Outliers by Batch</h3>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="duplicateRows" fill="#f59e0b" name="Duplicate Rows" />
                <Bar dataKey="outlierRows" fill="#ef4444" name="Outlier Rows" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <section className="rounded-2xl border border-gray-100 bg-white p-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="font-semibold text-gray-900">Batch Drill-down</h3>
              <p className="mt-1 text-xs text-gray-500">Click a batch to inspect field-level completeness and outliers.</p>
            </div>
            <p className="text-xs text-gray-500">
              Showing {pageStart}-{pageEnd} of {totalBatches}
            </p>
          </div>
          <div className="mt-3 max-h-80 overflow-auto rounded-lg border border-gray-100">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="px-3 py-2">Batch</th>
                  <th className="px-3 py-2">Schema</th>
                  <th className="px-3 py-2">Completeness</th>
                  <th className="px-3 py-2">Alerts</th>
                  <th className="px-3 py-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {(monitoring?.batches || []).map((batch) => (
                  <tr key={batch.batchId} className={selectedBatchId === batch.batchId ? 'bg-purple-50' : 'hover:bg-gray-50'}>
                    <td className="px-3 py-2 font-mono text-xs">{batch.batchId}</td>
                    <td className="px-3 py-2">{batch.schemaVersion}</td>
                    <td className="px-3 py-2">{(batch.completenessScore * 100).toFixed(2)}%</td>
                    <td className="px-3 py-2">{batch.alertCount}</td>
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        onClick={() => setSelectedBatchId(batch.batchId)}
                        className="inline-flex items-center gap-1 rounded-md border border-purple-200 px-2 py-1 text-xs text-purple-700 hover:bg-purple-50"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        View
                      </button>
                    </td>
                  </tr>
                ))}
                {!loading && (!monitoring?.batches || monitoring.batches.length === 0) && (
                  <tr>
                    <td colSpan={5} className="px-3 py-4 text-center text-gray-500">No batch quality records found yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="mt-3 flex items-center justify-between gap-3">
            <p className="text-xs text-gray-500">
              Page {currentPage} of {totalPages}
            </p>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setCurrentPage((page) => Math.max(page - 1, 1))}
                disabled={loading || currentPage <= 1}
                className="rounded-md border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => setCurrentPage((page) => Math.min(page + 1, totalPages))}
                disabled={loading || currentPage >= totalPages}
                className="rounded-md border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-gray-100 bg-white p-4">
          <h3 className="font-semibold text-gray-900">Selected Batch Details</h3>
          {selectedBatch ? (
            <div className="space-y-4 mt-3">
              <div className="text-sm text-gray-700">
                <div><span className="font-medium">Batch:</span> <span className="font-mono">{selectedBatch.batch.batchId}</span></div>
                <div><span className="font-medium">Schema:</span> {selectedBatch.batch.schemaVersion}</div>
                <div><span className="font-medium">Source:</span> {selectedBatch.batch.source}</div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">Field Metrics</h4>
                <div className="max-h-48 overflow-auto rounded-lg border border-gray-100">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="px-2 py-2">Field</th>
                        <th className="px-2 py-2">Missing</th>
                        <th className="px-2 py-2">Completeness</th>
                        <th className="px-2 py-2">Outliers</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedBatch.fieldMetrics.map((item) => (
                        <tr key={item.fieldName} className="border-t">
                          <td className="px-2 py-1.5">{item.fieldName}</td>
                          <td className="px-2 py-1.5">{item.missingCount}/{item.totalCount}</td>
                          <td className="px-2 py-1.5">{(item.completenessRatio * 100).toFixed(2)}%</td>
                          <td className="px-2 py-1.5">{item.outlierCount}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">Triggered Alerts</h4>
                {selectedBatch.alerts.length > 0 ? (
                  <div className="space-y-2">
                    {selectedBatch.alerts.map((alert) => (
                      <div key={alert.id} className="rounded-md border border-amber-200 bg-amber-50 p-2 text-xs text-amber-900">
                        <p className="font-medium">{alert.message}</p>
                        <p className="mt-1">Metric: {alert.metricName} {alert.comparator} {alert.thresholdValue}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-500">No alerts triggered for this batch.</p>
                )}
              </div>
            </div>
          ) : (
            <p className="mt-3 text-sm text-gray-500">Select a batch to inspect details.</p>
          )}
        </section>
      </div>

      <section className="rounded-2xl border border-gray-100 bg-white p-4 space-y-4">
        <h3 className="font-semibold text-gray-900">Alert Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <label className="text-sm text-gray-700">
            Completeness Min (0-1)
            <input
              type="number"
              min={0}
              max={1}
              step={0.01}
              value={config.completenessMin}
              onChange={(e) => setConfig((prev) => ({ ...prev, completenessMin: Number(e.target.value) }))}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </label>
          <label className="text-sm text-gray-700">
            Duplicates Max
            <input
              type="number"
              min={0}
              value={config.duplicatesMax}
              onChange={(e) => setConfig((prev) => ({ ...prev, duplicatesMax: Number(e.target.value) }))}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </label>
          <label className="text-sm text-gray-700">
            Outliers Max
            <input
              type="number"
              min={0}
              value={config.outliersMax}
              onChange={(e) => setConfig((prev) => ({ ...prev, outliersMax: Number(e.target.value) }))}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </label>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
          <label className="text-sm text-gray-700">
            Email Recipients (one per line)
            <textarea
              value={emailText}
              onChange={(e) => setEmailText(e.target.value)}
              rows={5}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </label>
          <label className="text-sm text-gray-700">
            Webhook URLs (one per line)
            <textarea
              value={webhookText}
              onChange={(e) => setWebhookText(e.target.value)}
              rows={5}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </label>
          <label className="text-sm text-gray-700">
            Slack Webhook URL
            <textarea
              value={config.slackWebhookUrl}
              onChange={(e) => setConfig((prev) => ({ ...prev, slackWebhookUrl: e.target.value }))}
              rows={5}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </label>
        </div>

        <button
          type="button"
          onClick={saveAlertConfig}
          disabled={savingConfig}
          className="rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-60"
        >
          {savingConfig ? 'Saving...' : 'Save Alert Configuration'}
        </button>
      </section>
    </div>
  );
};

const MetricCard: React.FC<{ icon: React.ReactNode; label: string; value: string | number }> = ({ icon, label, value }) => (
  <div className="rounded-2xl border border-gray-100 bg-white p-4">
    <div className="flex items-center gap-2 text-purple-600">{icon}</div>
    <p className="mt-2 text-xs text-gray-500 uppercase tracking-wide">{label}</p>
    <p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
  </div>
);

export default DataQualityMonitoring;
