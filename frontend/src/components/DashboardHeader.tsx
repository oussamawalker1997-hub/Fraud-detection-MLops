import { Activity, ShieldCheck } from 'lucide-react';

type DashboardHeaderProps = {
  ready: boolean;
  checking: boolean;
};

export function DashboardHeader({
  ready,
  checking,
}: DashboardHeaderProps) {
  const status = checking
    ? 'Checking model'
    : ready
      ? 'Model ready'
      : 'Model unavailable';

  const statusStyle = checking
    ? 'bg-sky-50 text-sky-700 ring-sky-200'
    : ready
      ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
      : 'bg-rose-50 text-rose-700 ring-rose-200';

  return (
    <header className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-5">
        <div className="flex items-center gap-4">
          <div className="flex size-12 items-center justify-center rounded-xl bg-slate-900 text-white">
            <ShieldCheck size={25} aria-hidden="true" />
          </div>

          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
              Fraud Intelligence
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Machine Learning Operations Dashboard
            </p>
          </div>
        </div>

        <div
          role="status"
          aria-live="polite"
          className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold ring-1 ${statusStyle}`}
        >
          <Activity size={16} aria-hidden="true" />
          {status}
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-2 border-t border-slate-100 pt-4">
        {['React', 'FastAPI', 'XGBoost', 'Google Cloud'].map((technology) => (
          <span
            key={technology}
            className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600"
          >
            {technology}
          </span>
        ))}
      </div>
    </header>
  );
}
