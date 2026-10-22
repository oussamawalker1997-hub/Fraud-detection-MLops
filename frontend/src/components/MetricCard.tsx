import type { LucideIcon } from 'lucide-react';

type MetricCardProps = {
  label: string;
  value: number;
  icon: LucideIcon;
  description: string;
};

export function MetricCard({
  label,
  value,
  icon: Icon,
  description,
}: MetricCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow duration-200 hover:shadow-md">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <div className="flex size-10 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
          <Icon size={20} aria-hidden="true" />
        </div>
      </div>

      <p className="mt-4 text-3xl font-bold tracking-tight text-slate-900">
        {value.toFixed(3)}
      </p>

      <p className="mt-2 text-xs leading-relaxed text-slate-500">
        {description}
      </p>
    </article>
  );
}
