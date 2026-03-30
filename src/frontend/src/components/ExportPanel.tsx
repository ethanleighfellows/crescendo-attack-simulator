import { useState } from 'react';
import { exportRun } from '../api/client';
import type { RunResult } from '../types';

interface ExportPanelProps {
  runId: string | null;
  result: RunResult | null;
  onBack: () => void;
}

export function ExportPanel({ runId, result, onBack }: ExportPanelProps) {
  const [includeApiKeys, setIncludeApiKeys] = useState(false);
  const [redactContent, setRedactContent] = useState(false);
  const [includeJudgeRationale, setIncludeJudgeRationale] = useState(true);
  const [filename, setFilename] = useState(() => {
    const obj = result?.config.objective.slice(0, 30).replace(/\s+/g, '_') ?? 'run';
    const ts = new Date().toISOString().slice(0, 10);
    return `crescendo_${obj}_${ts}`;
  });
  const [downloading, setDownloading] = useState(false);

  const handleDownloadXlsx = async () => {
    if (!runId) return;
    setDownloading(true);
    try {
      const data = await exportRun(runId, {
        include_api_keys: includeApiKeys,
        redact_sensitive_content: redactContent,
        include_judge_rationale: includeJudgeRationale,
        filename,
      });
      const byteChars = atob(data.data);
      const byteArr = new Uint8Array(byteChars.length);
      for (let i = 0; i < byteChars.length; i++) byteArr[i] = byteChars.charCodeAt(i);
      const blob = new Blob([byteArr], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      _download(blob, data.filename);
    } catch (err) {
      alert(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setDownloading(false);
    }
  };

  const handleDownloadJson = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    _download(blob, `${filename}.json`);
  };

  const handleCopyTranscript = () => {
    if (!result) return;
    const text = result.turns
      .map((t) => `[Round ${t.round_number}] Attacker:\n${t.user_prompt}\n\n[Round ${t.round_number}] Target:\n${t.assistant_response}`)
      .join('\n\n---\n\n');
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-6 max-w-lg mx-auto">
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="text-sm text-dynamo-muted hover:text-dynamo-text">
          ← Back to Review
        </button>
        <h2 className="text-sm font-semibold text-dynamo-text">Export Results</h2>
      </div>

      <div className="card space-y-5">
        <div>
          <label className="block text-sm font-medium text-dynamo-text mb-1">Filename</label>
          <input
            type="text"
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            className="input-field"
          />
        </div>

        <div>
          <div className="section-label">Export Options</div>
          <div className="space-y-2">
            {[
              [includeApiKeys, setIncludeApiKeys, 'Include API keys in config sheet'] as const,
              [redactContent, setRedactContent, 'Redact sensitive content (keys, emails, phones)'] as const,
              [includeJudgeRationale, setIncludeJudgeRationale, 'Include judge rationale in outcomes sheet'] as const,
            ].map(([checked, setter, label]) => (
              <label key={label} className="flex items-center gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) => setter(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-dynamo-purple focus:ring-dynamo-purple/30"
                />
                <span className="text-sm text-dynamo-text">{label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleDownloadXlsx}
          disabled={!runId || downloading}
          className="btn-primary flex-1 py-3"
        >
          {downloading ? 'Generating…' : '⬇ Download XLSX'}
        </button>
        <button onClick={handleDownloadJson} disabled={!result} className="btn-secondary flex-1 py-3">
          ⬇ Download JSON
        </button>
        <button onClick={handleCopyTranscript} disabled={!result} className="btn-secondary px-4 py-3">
          ⎘ Copy
        </button>
      </div>
    </div>
  );
}

function _download(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
