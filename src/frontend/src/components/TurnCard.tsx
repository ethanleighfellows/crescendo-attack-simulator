import { useState } from 'react';
import type { TurnRecord } from '../types';

interface TurnCardProps {
  turn: TurnRecord;
  maxRounds: number;
}

export function TurnCard({ turn, maxRounds }: TurnCardProps) {
  const [expanded, setExpanded] = useState(false);

  const evalScore = turn.eval_decision?.metadata;
  const isRefusal = turn.refusal_decision?.value === true;
  const isSuccess = evalScore !== undefined && evalScore >= 80;

  const borderClass = turn.is_backtrack
    ? 'border-amber-200 bg-amber-50/60'
    : isSuccess
      ? 'border-green-200 bg-green-50/40'
      : isRefusal
        ? 'border-red-200 bg-red-50/40'
        : 'border-gray-100 bg-white';

  return (
    <div className={`rounded-xl border p-4 shadow-card transition-all ${borderClass}`}>
      {/* Header row */}
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs font-semibold text-dynamo-muted">
            Round {turn.round_number}/{maxRounds}
          </span>
          {turn.is_backtrack && (
            <Badge color="amber">↩ Backtrack #{turn.backtrack_count}</Badge>
          )}
          {turn.enhancement_applied && turn.turn_level_attack && (
            <Badge color="purple">{turn.turn_level_attack}</Badge>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          {isRefusal && <Badge color="red">Refused</Badge>}
          {evalScore !== undefined && (
            <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${
              evalScore >= 80 ? 'bg-green-100 text-green-700' :
              evalScore >= 50 ? 'bg-amber-100 text-amber-700' :
              'bg-dynamo-light text-dynamo-purple'
            }`}>
              {evalScore}%
            </span>
          )}
        </div>
      </div>

      {/* Attacker prompt */}
      <div className="mb-2">
        <span className="text-[10px] font-semibold text-dynamo-purple uppercase tracking-wider">Attacker</span>
        <p className="text-sm text-dynamo-text mt-0.5 whitespace-pre-wrap">{turn.user_prompt}</p>
      </div>

      {/* Target response */}
      <div>
        <span className="text-[10px] font-semibold text-dynamo-muted uppercase tracking-wider">Target</span>
        <p className="text-sm text-dynamo-text mt-0.5 whitespace-pre-wrap">
          {expanded
            ? turn.assistant_response
            : turn.assistant_response.slice(0, 280) +
              (turn.assistant_response.length > 280 ? '…' : '')}
        </p>
        {turn.assistant_response.length > 280 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-dynamo-purple hover:text-dynamo-violet mt-1 font-medium"
          >
            {expanded ? 'Show less ↑' : 'Show more ↓'}
          </button>
        )}
      </div>

      {/* Judge rationale (expanded only) */}
      {expanded && (turn.refusal_decision || turn.eval_decision) && (
        <div className="mt-3 pt-3 border-t border-gray-100 grid grid-cols-2 gap-3">
          {turn.refusal_decision && (
            <div>
              <span className="text-[10px] font-semibold text-dynamo-muted uppercase">Refusal Judge</span>
              <p className="text-xs text-dynamo-muted mt-0.5">{turn.refusal_decision.rationale}</p>
            </div>
          )}
          {turn.eval_decision && (
            <div>
              <span className="text-[10px] font-semibold text-dynamo-muted uppercase">Eval Judge</span>
              <p className="text-xs text-dynamo-muted mt-0.5">{turn.eval_decision.rationale}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Badge({
  color,
  children,
}: {
  color: 'amber' | 'purple' | 'red' | 'green';
  children: React.ReactNode;
}) {
  const styles = {
    amber: 'bg-amber-100 text-amber-700',
    purple: 'bg-dynamo-light text-dynamo-purple',
    red: 'bg-red-100 text-red-700',
    green: 'bg-green-100 text-green-700',
  };
  return (
    <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full ${styles[color]}`}>
      {children}
    </span>
  );
}
