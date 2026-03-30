import type { RunResult, TurnRecord } from '../types';
import { TurnCard } from './TurnCard';

interface ReviewPanelProps {
  result: RunResult | null;
  turns: TurnRecord[];
  onExport: () => void;
  onRerunWithChanges: () => void;
  onRetry: () => void;
}

export function ReviewPanel({
  result,
  turns,
  onExport,
  onRerunWithChanges,
  onRetry,
}: ReviewPanelProps) {
  if (!result) {
    return <div className="text-center text-dynamo-muted py-16">No results to display.</div>;
  }

  const outcomeLabel = result.outcome
    ? result.outcome.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    : 'Unknown';

  const outcomeStyle =
    result.outcome === 'success'
      ? 'bg-green-100 text-green-700 border-green-200'
      : result.outcome === 'failed'
        ? 'bg-red-100 text-red-700 border-red-200'
        : 'bg-amber-100 text-amber-700 border-amber-200';

  const duration =
    result.started_at && result.completed_at
      ? ((new Date(result.completed_at).getTime() - new Date(result.started_at).getTime()) / 1000).toFixed(1)
      : null;

  const successfulTurns = turns.filter(
    (t) => t.eval_decision && t.eval_decision.metadata >= (result.config.success_threshold ?? 100),
  );
  const backtracks = turns.filter((t) => t.is_backtrack).length;

  return (
    <div className="space-y-5">
      {/* Summary */}
      <div className="card">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-sm font-semibold text-dynamo-text">Run Summary</h2>
          <span className={`px-3 py-1 text-sm font-semibold rounded-full border ${outcomeStyle}`}>
            {outcomeLabel}
          </span>
        </div>
        <div className="grid grid-cols-5 gap-4">
          <Metric label="Total Rounds" value={String(result.total_rounds)} />
          <Metric label="Backtracks" value={String(backtracks)} />
          <Metric
            label="Final Eval"
            value={result.final_eval_score !== null ? `${result.final_eval_score}%` : '—'}
            accent={result.final_eval_score !== null && result.final_eval_score >= 80}
          />
          <Metric label="Successful Turns" value={String(successfulTurns.length)} />
          <Metric label="Duration" value={duration ? `${duration}s` : '—'} />
        </div>
      </div>

      {/* Escalation Path */}
      <div className="card">
        <div className="section-label">Escalation Path</div>
        <div className="flex items-end gap-1 overflow-x-auto pb-2 min-h-[52px]">
          {turns.map((turn, idx) => {
            const score = turn.eval_decision?.metadata ?? 0;
            const height = Math.max(8, Math.round((score / 100) * 36));
            const color = turn.is_backtrack
              ? '#f59e0b'
              : turn.enhancement_applied
                ? '#06b6d4'
                : score >= 80
                  ? '#16a34a'
                  : score >= 50
                    ? '#ca8a04'
                    : '#7C3AED';
            return (
              <div key={idx} className="flex flex-col items-center gap-1 flex-shrink-0" title={`Round ${turn.round_number} — ${score}%`}>
                <div
                  className="w-3 rounded-t-sm transition-all"
                  style={{ height: `${height}px`, backgroundColor: color }}
                />
                <span className="text-[9px] text-dynamo-muted">{turn.round_number}</span>
              </div>
            );
          })}
        </div>
        <div className="flex gap-4 mt-2 text-[10px] text-dynamo-muted">
          {[
            ['#16a34a', '≥80%'],
            ['#ca8a04', '≥50%'],
            ['#7C3AED', '<50%'],
            ['#f59e0b', 'Backtrack'],
            ['#06b6d4', 'Enhanced'],
          ].map(([color, label]) => (
            <span key={label} className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm inline-block" style={{ backgroundColor: color }} />
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* Transcript */}
      <div>
        <div className="section-label mb-3">Full Transcript ({turns.length} turns)</div>
        <div className="space-y-3 max-h-[56vh] overflow-y-auto pr-1">
          {turns.map((turn, idx) => (
            <TurnCard key={idx} turn={turn} maxRounds={result.config.max_rounds} />
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-2">
        <button onClick={onRerunWithChanges} className="btn-secondary">
          Rerun with Changes
        </button>
        <button onClick={onRetry} className="btn-secondary">
          Retry Same Config
        </button>
        <button onClick={onExport} className="btn-primary px-6">
          Export Results →
        </button>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="text-center">
      <p className={`text-2xl font-bold ${accent ? 'text-dynamo-purple' : 'text-dynamo-text'}`}>
        {value}
      </p>
      <p className="text-xs text-dynamo-muted mt-1">{label}</p>
    </div>
  );
}
