import type { FormEvent } from 'react';
import { ArrowRight, LoaderCircle, SlidersHorizontal, Wallet } from 'lucide-react';

type TransactionFormProps = {
  values: Record<string, number | ''>;
  onChange: (feature: string, value: number | '') => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  disabled: boolean;
  loading: boolean;
};

const ANONYMIZED_FEATURES = Array.from(
  { length: 28 },
  (_, index) => `V${index + 1}`,
);

export function TransactionForm({
  values,
  onChange,
  onSubmit,
  disabled,
  loading,
}: TransactionFormProps) {
  const renderField = (feature: string) => (
    <label
      key={feature}
      className="block min-w-0 text-xs font-medium text-slate-600"
    >
      <span className="mb-1.5 block">{feature}</span>
      <input
        type="number"
        inputMode="decimal"
        step="any"
        required
        disabled={disabled || loading}
        value={values[feature]}
        onChange={(event) =>
          onChange(
            feature,
            event.target.value === '' ? '' : Number(event.target.value),
          )
        }
        className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
      />
    </label>
  );

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      <section className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
        <div className="mb-4 flex items-center gap-2">
          <Wallet size={18} className="text-blue-700" aria-hidden="true" />
          <h3 className="font-semibold text-slate-900">
            Transaction details
          </h3>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {renderField('Time')}
          {renderField('Amount')}
        </div>

        <p className="mt-3 text-xs text-slate-500">
          Time is measured in seconds relative to the dataset reference.
          Amount is the transaction amount from the dataset.
        </p>
      </section>

      <section>
        <div className="mb-4 flex items-center gap-2">
          <SlidersHorizontal
            size={18}
            className="text-blue-700"
            aria-hidden="true"
          />
          <h3 className="font-semibold text-slate-900">
            Anonymized features
          </h3>
        </div>

        <p className="mb-4 text-xs leading-relaxed text-slate-500">
          V1–V28 are anonymized transformed features.
          They do not represent customer identity fields.
        </p>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
          {ANONYMIZED_FEATURES.map(renderField)}
        </div>
      </section>

      <button
        type="submit"
        disabled={disabled || loading}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white transition hover:bg-blue-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? (
          <>
            <LoaderCircle size={18} className="animate-spin" />
            Analyzing transaction…
          </>
        ) : (
          <>
            Analyze transaction
            <ArrowRight size={18} />
          </>
        )}
      </button>
    </form>
  );
}
