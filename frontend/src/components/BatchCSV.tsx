import type { ChangeEvent } from 'react';
import { Download, FileSpreadsheet, LoaderCircle, Upload } from 'lucide-react';

export type BatchRow = {
  row: number;
  status: 'scored' | 'rejected';
  predicted_label?: number;
  model_score?: number;
  error?: string;
};

export type BatchResult = {
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

type BatchCSVProps = {
  batch: BatchResult | null;
  loading: boolean;
  error: string | null;
  disabled: boolean;
  apiUrl: string;
  onUpload: (event: ChangeEvent<HTMLInputElement>) => void;
};

export function BatchCSV({
  batch,
  loading,
  error,
  disabled,
  apiUrl,
  onUpload,
}: BatchCSVProps) {
  const stats = batch
    ? [
        { label: 'Received', value: batch.rows_received },
        { label: 'Processed', value: batch.rows_processed },
        { label: 'Rejected', value: batch.rows_rejected },
        { label: 'Flagged', value: batch.predicted_positive },
      ]
    : [];

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-blue-50 p-2.5 text-blue-700">
          <FileSpreadsheet size={22} aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            Batch Fraud Analysis
          </h2>
          <p className="text-xs text-slate-500">
            Analyze multiple transactions from a CSV file.
          </p>
        </div>
      </div>

      <p className="mt-4 text-sm leading-relaxed text-slate-600">
        Required columns: Time, V1–V28, Amount.
        Invalid rows are reported in the results.
      </p>

      <label className={`mt-4 flex min-h-32 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-300 p-5 text-center transition ${
        disabled || loading
          ? 'cursor-not-allowed opacity-60'
          : 'cursor-pointer hover:border-blue-400 hover:bg-blue-50/40'
      }`}>
        {loading ? (
          <LoaderCircle size={25} className="animate-spin text-blue-700" />
        ) : (
          <Upload size={25} className="text-blue-700" />
        )}
        <span className="text-sm font-semibold text-slate-800">
          {loading ? 'Processing CSV…' : 'Choose a CSV file'}
        </span>
        <span className="text-xs text-slate-500">CSV format</span>
        <input
          type="file"
          accept=".csv,text/csv"
          disabled={disabled || loading}
          onChange={onUpload}
          className="sr-only"
        />
      </label>

      {error && (
        <div role="alert" className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
          {error}
        </div>
      )}

      {batch && (
        <div className="mt-5 space-y-4" aria-live="polite">
          <div className="grid grid-cols-2 gap-3">
            {stats.map((stat) => (
              <div key={stat.label} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs text-slate-500">{stat.label}</p>
                <p className="mt-1 text-2xl font-bold text-slate-900">
                  {stat.value.toLocaleString()}
                </p>
              </div>
            ))}
          </div>

          <p className="text-xs leading-relaxed text-slate-500">
            Duration: {batch.duration_ms} ms · {batch.score_semantics}
          </p>

          <a
            href={`${apiUrl}${batch.download_url}`}
            className="flex items-center justify-center gap-2 rounded-lg bg-blue-700 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-800"
          >
            <Download size={17} aria-hidden="true" />
            Download enriched CSV
          </a>

          <div className="max-h-72 overflow-auto rounded-lg border border-slate-200">
            <table className="w-full min-w-72 text-left text-xs">
              <thead className="sticky top-0 bg-slate-100 text-slate-600">
                <tr>
                  <th scope="col" className="p-3">CSV row</th>
                  <th scope="col" className="p-3">Status</th>
                  <th scope="col" className="p-3">Result</th>
                </tr>
              </thead>
              <tbody>
                {batch.results.map((row) => (
                  <tr key={row.row} className="border-t border-slate-100">
                    <td className="p-3">{row.row}</td>
                    <td className="p-3">{row.status}</td>
                    <td className="p-3">
                      {row.status === 'scored'
                        ? `${row.predicted_label ? 'Flagged' : 'Not flagged'} · score ${row.model_score?.toFixed(5) ?? 'N/A'}`
                        : (
                          <span
                            title={row.error ?? 'Invalid row'}
                            className="block max-w-64 break-words text-rose-700"
                          >
                            {row.error?.includes('Amount') &&
                            row.error?.includes('float_parsing')
                              ? 'Invalid Amount: expected a numeric value'
                              : 'Invalid row — see exported CSV for details'}
                          </span>
                        )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
