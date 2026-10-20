import { useEffect, useMemo, useState } from 'react';

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8080').replace(/\/$/, '');
const FEATURES = ['Time', ...Array.from({ length: 28 }, (_, i) => `V${i + 1}`), 'Amount'];

type Prediction = {
  predicted_label: number;
  model_score: number;
  score_semantics: string;
  threshold: number;
  model_version: string;
};

type BatchRow = {
  row: number;
  status: 'scored' | 'rejected';
  predicted_label?: number;
  model_score?: number;
  error?: string;
};

type BatchResult = {
  result_id: string;
  rows_received: number;
  rows_processed: number;
  rows_rejected: number;
  predicted_positive: number;
  duration_ms: number;
  score_semantics: string;
  model_version: string;
  results: BatchRow[];
  download_url: string;
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
  const [values, setValues] = useState<Record<string, number>>(() =>
    Object.fromEntries(FEATURES.map((feature) => [feature, 0])),
  );
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [history, setHistory] = useState<Array<{ amount: number; time: string; prediction: Prediction }>>([]);
  const [metrics, setMetrics] = useState<MetricSummary | null>(null);
  const [ready, setReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [batch, setBatch] = useState<BatchResult | null>(null);
  const [batchLoading, setBatchLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/ready`)
      .then((response) => {
        if (!response.ok) throw new Error('Model artifact is not ready. Run the training pipeline first.');
        setReady(true);
      })
      .catch((reason: Error) => setError(reason.message));
    fetch(`${API_URL}/metrics`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data: MetricSummary | null) => setMetrics(data));
  }, []);

  const editFields = useMemo(() => ['Time', ...Array.from({ length: 28 }, (_, i) => `V${i + 1}`), 'Amount'], []);

  const handlePredict = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      if (!response.ok) throw new Error(await responseError(response));
      const result: Prediction = await response.json();
      setPrediction(result);
      setHistory((previous) => [{ amount: values.Amount, time: new Date().toLocaleTimeString(), prediction: result }, ...previous].slice(0, 8));
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
    setError(null);
    setBatchLoading(true);
    const form = new FormData();
    form.append('file', file);
    try {
      const response = await fetch(`${API_URL}/predict/batch`, { method: 'POST', body: form });
      if (!response.ok) throw new Error(await responseError(response));
      setBatch(await response.json());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'CSV processing failed.');
    } finally {
      setBatchLoading(false);
      event.target.value = '';
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 p-5 text-slate-900 md:p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold">Fraud Detection</h1>
            <p className="mt-1 text-slate-600">Local model scoring and batch analysis</p>
          </div>
          <div className={`rounded-full px-4 py-2 text-sm font-semibold ${ready ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-900'}`}>
            {ready ? 'Model ready' : 'Model unavailable'}
          </div>
        </header>

        {error && <div role="alert" className="rounded-lg border border-rose-300 bg-rose-50 p-4 text-rose-800">{error}</div>}

        {metrics && (
          <section className="rounded-xl border bg-white p-5 shadow-sm">
            <h2 className="text-lg font-bold">Independent test-set evaluation</h2>
            <p className="mt-1 text-sm text-slate-600">{metrics.selected_model}. These metrics use the saved test labels; batch predictions have no known outcomes.</p>
            <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-5">
              {[
                ['Average precision', metrics.test.average_precision],
                ['ROC-AUC', metrics.test.roc_auc],
                ['Precision', metrics.test.precision],
                ['Recall', metrics.test.recall],
                ['F1', metrics.test.f1],
              ].map(([label, value]) => (
                <div className="rounded-lg bg-slate-50 p-3" key={label}>
                  <div className="text-xs text-slate-500">{label}</div>
                  <div className="mt-1 text-xl font-bold">{Number(value).toFixed(3)}</div>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-slate-500">Test rows: {metrics.test.rows.toLocaleString()} · false positives: {metrics.test.false_positives} · false negatives: {metrics.test.false_negatives} · validation F1 threshold: {metrics.threshold_selection.threshold.toFixed(4)}</p>
          </section>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="rounded-xl border bg-white p-5 shadow-sm lg:col-span-2">
            <h2 className="text-lg font-bold">Score one transaction</h2>
            <p className="mb-4 mt-1 text-sm text-slate-600">Enter the dataset features. V1–V28 are anonymized transformed features; no customer or IP fields are available.</p>
            <form onSubmit={handlePredict}>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
                {editFields.map((feature) => (
                  <label className="text-xs font-medium text-slate-600" key={feature}>
                    {feature}
                    <input
                      className="mt-1 w-full rounded-md border bg-slate-50 px-2 py-2 text-sm text-slate-900"
                      type="number"
                      step="any"
                      required
                      value={values[feature]}
                      onChange={(event) => setValues((previous) => ({ ...previous, [feature]: Number(event.target.value) }))}
                    />
                  </label>
                ))}
              </div>
              <button className="mt-4 w-full rounded-lg bg-blue-700 px-4 py-3 font-semibold text-white disabled:opacity-50" disabled={!ready || loading}>
                {loading ? 'Scoring…' : 'Score transaction'}
              </button>
            </form>

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
            <section className="rounded-xl border bg-white p-5 shadow-sm">
              <h2 className="text-lg font-bold">Batch CSV</h2>
              <p className="mb-4 mt-1 text-sm text-slate-600">Upload a CSV with exactly Time, V1–V28, and Amount. Invalid rows are reported and included in the export.</p>
              <label className="block cursor-pointer rounded-lg border-2 border-dashed p-6 text-center text-sm font-semibold text-slate-700 hover:bg-slate-50">
                {batchLoading ? 'Processing CSV…' : 'Choose a CSV file'}
                <input className="sr-only" type="file" accept=".csv,text/csv" disabled={!ready || batchLoading} onChange={handleBatch} />
              </label>
              {batch && (
                <div className="mt-4 space-y-2 text-sm" aria-live="polite">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded bg-slate-50 p-2">Received: <b>{batch.rows_received}</b></div>
                    <div className="rounded bg-slate-50 p-2">Processed: <b>{batch.rows_processed}</b></div>
                    <div className="rounded bg-slate-50 p-2">Rejected: <b>{batch.rows_rejected}</b></div>
                    <div className="rounded bg-slate-50 p-2">Flagged: <b>{batch.predicted_positive}</b></div>
                  </div>
                  <p className="text-xs text-slate-500">{batch.duration_ms} ms · {batch.score_semantics}</p>
                  <a className="inline-block rounded bg-blue-700 px-4 py-2 font-semibold text-white" href={`${API_URL}${batch.download_url}`}>Download enriched CSV</a>
                  <div className="max-h-72 overflow-auto rounded border">
                    <table className="w-full text-left text-xs">
                      <thead className="sticky top-0 bg-slate-100"><tr><th className="p-2">CSV row</th><th>Status</th><th>Prediction / issue</th></tr></thead>
                      <tbody>
                        {batch.results.map((row) => (
                          <tr className="border-t" key={row.row}>
                            <td className="p-2">{row.row}</td>
                            <td>{row.status}</td>
                            <td>{row.status === 'scored' ? `${row.predicted_label ? 'Flagged' : 'Not flagged'} · score ${row.model_score?.toFixed(5)}` : row.error}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </section>

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
