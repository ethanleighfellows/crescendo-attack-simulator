import { useEffect, useRef } from 'react';
import type { RunConfig, TurnRecord } from '../types';
import { TurnCard } from './TurnCard';

interface LiveRunPanelProps {
  turns: TurnRecord[];
  status: string;
  error: string | null;
  config: RunConfig;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
}

export function LiveRunPanel({
  turns,
  status,
  error,
  config,
  onPause,
  onResume,
  onCancel,
}: LiveRunPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [turns.length]);

  const currentRound = turns.length > 0 ? turns[turns.length - 1].round_number : 0;
  const currentBacktracks = turns.filter((t) => t.is_backtrack).length;
  const latestEvalScore =
    turns
      .filter((t) => t.eval_decision)
      .map((t) => t.eval_decision!.metadata)
      .pop() ?? null;

  const isActive = status === 'running' || status === 'paused';

  return (
    <div className="flex gap-6 h-[calc(100vh-11rem)]">
      {/* Transcript */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-dynamo-text">Live Transcript</h2>
          <StatusPill status={status} />
        </div>
        {error && (
          <div className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2">
            <p className="text-xs text-red-700">
              <span className="font-semibold">Run failed:</span> {error}
            </p>
          </div>
        )}
        <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-3 pr-1">
          {turns.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-dynamo-muted">
              <div className="w-12 h-12 rounded-full border-2 border-dynamo-purple/30 border-t-dynamo-purple animate-spin mb-3" />
              <p className="text-sm">Initializing Crescendo attack&hellip;</p>
            </div>
          )}
          {turns.map((turn, idx) => (
            <TurnCard key={idx} turn={turn} maxRounds={config.max_rounds} />
          ))}
        </div>
      </div>

      {/* Sidebar */}
      <div className="w-64 flex-shrink-0 space-y-4">
        {/* Status card */}
        <div className="card space-y-3">
          <div className="section-label">Run Status</div>
          <StatusRow label="Round" value={`${currentRound} / ${config.max_rounds}`} />
          <StatusRow label="Backtracks" value={`${currentBacktracks} / ${config.max_backtracks}`} />
          {latestEvalScore !== null && (
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-xs text-dynamo-muted">Eval Score</span>
                <span className="text-xs font-semibold text-dynamo-purple">{latestEvalScore}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div
                  className="h-2 rounded-full transition-all duration-700"
                  style={{
                    width: `${latestEvalScore}%`,
                    backgroundColor:
                      latestEvalScore >= 80 ? '#16a34a' : latestEvalScore >= 50 ? '#ca8a04' : '#7C3AED',
                  }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="card space-y-2">
          <div className="section-label">Controls</div>
          {status === 'running' && (
            <button onClick={onPause}
              className="w-full px-3 py-2 text-sm font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-lg hover:bg-amber-100 transition-colors">
              ⏸ Pause
            </button>
          )}
          {status === 'paused' && (
            <button onClick={onResume}
              className="w-full px-3 py-2 text-sm font-medium text-green-700 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors">
              ▶ Resume
            </button>
          )}
          <button
            onClick={onCancel}
            disabled={!isActive}
            className="w-full px-3 py-2 text-sm font-medium text-red-600 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
            ✕ Cancel Run
          </button>
        </div>

        {/* Objective */}
        <div className="bg-dynamo-light/50 border border-dynamo-purple/20 rounded-xl p-4">
          <div className="section-label text-dynamo-purple">Objective</div>
          <p className="text-xs text-dynamo-text line-clamp-4">{config.objective}</p>
        </div>
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const styles: Record<string, string> = {
    running: 'bg-green-100 text-green-700',
    paused: 'bg-amber-100 text-amber-700',
    completed: 'bg-dynamo-light text-dynamo-purple',
    failed: 'bg-red-100 text-red-700',
    cancelled: 'bg-gray-100 text-gray-500',
  };
  return (
    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${styles[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-xs text-dynamo-muted">{label}</span>
      <span className="text-sm font-semibold text-dynamo-text">{value}</span>
    </div>
  );
}
