import { useEffect, useState } from 'react';
import { DashboardHeader } from './components/DashboardHeader';
import { MetricCard } from './components/MetricCard';
import { TransactionForm } from './components/TransactionForm';
import { BatchCSV, type BatchResult } from './components/BatchCSV';
import { Activity, Crosshair, ScanSearch, ShieldCheck, Target } from 'lucide-react';

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8080').replace(/\/$/, '');
const FEATURES = ['Time', ...Array.from({ length: 28 }, (_, i) => `V${i + 1}`), 'Amount'];

type Prediction = {
  predicted_label: number;
  model_score: number;
  score_semantics: string;
  threshold: number;
  model_version: string;
};

type MetricSummary = {
  selected_model: string;
  threshold_selection: { threshold: number; method: string };
  test: {
    precision: number;
    recall: number;
    f1: number;
    average_precision: number;
    roc_auc: number;
    false_positives: number;
    false_negatives: number;
    rows: number;
  };
};

async function responseError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    const detail = body.detail;
    if (typeof detail === 'string') return detail;
    if (detail?.message) return detail.message;
    if (detail?.code === 'schema_mismatch') {
      return `CSV schema mismatch. Missing: ${detail.missing_columns?.join(', ') || 'none'}; extra: ${detail.extra_columns?.join(', ') || 'none'}.`;
    }
    return JSON.stringify(detail ?? body);
  } catch {
    return `Request failed with HTTP ${response.status}.`;
  }
}

export default function App() {
  const [values, setValues] = useState<Record<string, number | ''>>(() =>
    Object.fromEntries(FEATURES.map((feature) => [feature, 0])),
  );
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [history, setHistory] = useState<Array<{ amount: number; time: string; prediction: Prediction }>>([]);
  const [metrics, setMetrics] = useState<MetricSummary | null>(null);
  const [ready, setReady] = useState(false);
  const [checking, setChecking] = useState(true);
  const [metricsError, setMetricsError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [batch, setBatch] = useState<BatchResult | null>(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchError, setBatchError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/ready`)
      .then((response) => {
        if (!response.ok) throw new Error('Model artifact is not ready. Run the training pipeline first.');
        setReady(true);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setChecking(false));

    fetch(`${API_URL}/metrics`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Metrics unavailable (HTTP ${response.status}).`);
        }
        return response.json() as Promise<MetricSummary>;
      })
      .then((data) => setMetrics(data))
      .catch((reason: unknown) => {
        setMetricsError(
          reason instanceof Error
            ? reason.message
            : 'Failed to load metrics.',
        );
      });
  }, []);


  const handlePredict = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setPrediction(null);

    if (FEATURES.some((feature) => values[feature] === '' || !Number.isFinite(values[feature]))) {
      setError('All 30 input features must contain valid finite numbers.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      if (!response.ok) throw new Error(await responseError(response));
      const result: Prediction = await response.json();
      setPrediction(result);
      setHistory((previous) => [{ amount: Number(values.Amount), time: new Date().toLocaleTimeString(), prediction: result }, ...previous].slice(0, 8));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Prediction request failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleBatch = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setBatch(null);
    setBatchError(null);
    setBatchLoading(true);
    const form = new FormData();
    form.append('file', file);
    try {
      const response = await fetch(`${API_URL}/predict/batch`, { method: 'POST', body: form });
      if (!response.ok) throw new Error(await responseError(response));
      setBatch(await response.json());
    } catch (reason) {
      setBatchError(reason instanceof Error ? reason.message : 'CSV processing failed.');
    } finally {
      setBatchLoading(false);
      event.target.value = '';
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 p-5 text-slate-900 md:p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <DashboardHeader ready={ready} checking={checking} />

        {error && <div role="alert" className="rounded-lg border border-rose-300 bg-rose-50 p-4 text-rose-800">{error}</div>}

        {metricsError && (
          <div role="alert" className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
            {metricsError}
          </div>
        )}

        {metrics && (
          <section className="rounded-xl border bg-white p-5 shadow-sm">
            <h2 className="text-lg font-bold">Independent test-set evaluation</h2>
            <p className="mt-1 text-sm text-slate-600">{metrics.selected_model}. These metrics use the saved test labels; batch predictions have no known outcomes.</p>
            <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              <MetricCard label="Average Precision" value={metrics.test.average_precision} icon={Target} description="Precision-recall performance" />
              <MetricCard label="ROC-AUC" value={metrics.test.roc_auc} icon={Activity} description="Ranking discrimination" />
              <MetricCard label="Precision" value={metrics.test.precision} icon={ShieldCheck} description="Correctness of fraud alerts" />
              <MetricCard label="Recall" value={metrics.test.recall} icon={ScanSearch} description="Fraud cases detected" />
              <MetricCard label="F1 Score" value={metrics.test.f1} icon={Crosshair} description="Precision-recall balance" />
            </div>
            <p className="mt-3 text-xs text-slate-500">Test rows: {metrics.test.rows.toLocaleString()} · false positives: {metrics.test.false_positives} · false negatives: {metrics.test.false_negatives} · validation F1 threshold: {metrics.threshold_selection.threshold.toFixed(4)}</p>
          </section>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="rounded-xl border bg-white p-5 shadow-sm lg:col-span-2">
            <h2 className="text-lg font-bold">Score one transaction</h2>
            <p className="mb-4 mt-1 text-sm text-slate-600">Enter the dataset features. V1–V28 are anonymized transformed features; no customer or IP fields are available.</p>
            <TransactionForm
              values={values}
              onChange={(feature, value) =>
                setValues((previous) => ({
                  ...previous,
                  [feature]: value,
                }))
              }
              onSubmit={handlePredict}
              disabled={!ready}
              loading={loading}
            />

            {prediction && (
              <div className="mt-5 rounded-lg border bg-slate-50 p-4" aria-live="polite">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm text-slate-500">Model score (uncalibrated)</div>
                    <div className="text-3xl font-bold">{prediction.model_score.toFixed(6)}</div>
                  </div>
                  <div className={`rounded-full px-4 py-2 font-bold ${prediction.predicted_label ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'}`}>
                    {prediction.predicted_label ? 'Flagged by model' : 'Not flagged'}
                  </div>
                </div>
                <p className="mt-3 text-sm text-slate-600">Decision threshold: {prediction.threshold.toFixed(6)} · {prediction.score_semantics}</p>
                <p className="mt-1 text-xs text-slate-500">A flagged prediction is not confirmation of fraud. Model: {prediction.model_version}</p>
              </div>
            )}
          </section>

          <div className="space-y-6">
            <BatchCSV
              batch={batch}
              loading={batchLoading}
              error={batchError}
              disabled={!ready}
              apiUrl={API_URL}
              onUpload={handleBatch}
            />

            <section className="rounded-xl border bg-white p-5 shadow-sm">
              <h2 className="text-lg font-bold">This session’s prediction history</h2>
              <p className="mb-3 mt-1 text-xs text-slate-500">Local browser history; no external transaction feed.</p>
              {history.length ? history.map((item, index) => (
                <div className="flex justify-between border-t py-2 text-sm" key={`${item.time}-${index}`}>
                  <span>{item.amount} · {item.time}</span>
                  <span className={item.prediction.predicted_label ? 'font-semibold text-rose-700' : 'text-emerald-700'}>{item.prediction.predicted_label ? 'Flagged' : 'Not flagged'}</span>
                </div>
              )) : <p className="py-5 text-center text-sm text-slate-400">No predictions yet.</p>}
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
