import type { Preset, RunConfig, RunResult, TurnEvent } from '../types';

const BASE = '/api';

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`API error ${response.status}: ${body}`);
  }
  return response.json() as Promise<T>;
}

export async function getDisclaimer(): Promise<string> {
  const data = await fetchJson<{ disclaimer: string }>('/disclaimer');
  return data.disclaimer;
}

export async function getPresets(): Promise<Record<string, Preset>> {
  return fetchJson<Record<string, Preset>>('/presets');
}

export async function getTurnLevelAttacks(): Promise<string[]> {
  const data = await fetchJson<{ available: string[] }>('/attacks/turn-level');
  return data.available;
}

export async function getRunResult(runId: string): Promise<RunResult> {
  return fetchJson<RunResult>(`/runs/${runId}/result`);
}

export async function cancelRun(runId: string): Promise<void> {
  await fetchJson(`/runs/${runId}/cancel`, { method: 'POST' });
}

export async function pauseRun(runId: string): Promise<void> {
  await fetchJson(`/runs/${runId}/pause`, { method: 'POST' });
}

export async function resumeRun(runId: string): Promise<void> {
  await fetchJson(`/runs/${runId}/resume`, { method: 'POST' });
}

export async function exportRun(
  runId: string,
  exportConfig: {
    include_api_keys: boolean;
    redact_sensitive_content: boolean;
    include_judge_rationale: boolean;
    filename: string;
  },
): Promise<{ filename: string; data: string }> {
  return fetchJson(`/runs/${runId}/export`, {
    method: 'POST',
    body: JSON.stringify(exportConfig),
  });
}

export function createRunWebSocket(
  config: RunConfig,
  onEvent: (event: TurnEvent) => void,
  onError: (error: Event) => void,
  onClose: (event: CloseEvent) => void,
): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  // In dev mode, use the IPv4 loopback explicitly to avoid browsers resolving
  // `localhost` to IPv6 while the backend listens on 127.0.0.1.
  const isDev = import.meta.env.DEV;
  const host = isDev ? '127.0.0.1:8000' : window.location.host;
  const ws = new WebSocket(`${protocol}//${host}/api/ws/run`);

  ws.onopen = () => {
    ws.send(
      JSON.stringify({
        config,
        research_acknowledged: true,
      }),
    );
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data) as TurnEvent;
    onEvent(data);
  };

  ws.onerror = onError;
  ws.onclose = onClose;

  return ws;
}
