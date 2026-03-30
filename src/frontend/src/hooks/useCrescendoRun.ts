import { useCallback, useRef, useState } from 'react';
import { createRunWebSocket } from '../api/client';
import type { RunConfig, RunResult, TurnEvent, TurnRecord } from '../types';

interface CrescendoRunState {
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  runId: string | null;
  turns: TurnRecord[];
  result: RunResult | null;
  error: string | null;
}

export function useCrescendoRun() {
  const [state, setState] = useState<CrescendoRunState>({
    status: 'idle',
    runId: null,
    turns: [],
    result: null,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);

  const startRun = useCallback((config: RunConfig) => {
    setState({
      status: 'running',
      runId: null,
      turns: [],
      result: null,
      error: null,
    });

    const ws = createRunWebSocket(
      config,
      (event: TurnEvent) => {
        console.debug('[Crescendo WS event]', event.event_type, event.data);
        if (event.event_type === 'run_started') {
          setState((prev) => ({
            ...prev,
            runId: event.run_id,
            status: 'running',
          }));
        } else if (event.event_type === 'turn_completed') {
          const turn = event.data.turn as unknown as TurnRecord;
          setState((prev) => ({
            ...prev,
            turns: [...prev.turns, turn],
          }));
        } else if (event.event_type === 'run_paused') {
          setState((prev) => ({ ...prev, status: 'paused' }));
        } else if (event.event_type === 'run_completed') {
          const result = event.data.result as unknown as RunResult;
          setState((prev) => ({
            ...prev,
            status: result.status === 'failed' ? 'failed' : 'completed',
            result,
            error: result.error || null,
          }));
        } else if (event.event_type === 'error') {
          setState((prev) => ({
            ...prev,
            status: 'failed',
            error: (event.data.message as string) || 'Unknown error',
          }));
        }
      },
      (errorEvent: Event) => {
        console.error('[Crescendo WS error]', errorEvent);
        setState((prev) => ({
          ...prev,
          status: 'failed',
          error: prev.error || 'WebSocket connection error',
        }));
      },
      (closeEvent: CloseEvent) => {
        console.warn(
          '[Crescendo WS closed]',
          closeEvent.code,
          closeEvent.reason || '(no reason)',
        );
        setState((prev) => {
          if (prev.status === 'completed' || prev.status === 'failed' || prev.status === 'cancelled') {
            return prev;
          }
          const reason = closeEvent.reason?.trim();
          return {
            ...prev,
            status: 'failed',
            error:
              prev.error ||
              (reason
                ? `Run stopped: ${reason}`
                : `Run stopped unexpectedly (WebSocket closed: ${closeEvent.code})`),
          };
        });
      },
    );

    wsRef.current = ws;
  }, []);

  const sendCommand = useCallback((command: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command }));
    }
  }, []);

  const pause = useCallback(() => sendCommand('pause'), [sendCommand]);
  const resume = useCallback(() => sendCommand('resume'), [sendCommand]);
  const cancel = useCallback(() => {
    sendCommand('cancel');
    setState((prev) => ({ ...prev, status: 'cancelled' }));
  }, [sendCommand]);

  const reset = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setState({
      status: 'idle',
      runId: null,
      turns: [],
      result: null,
      error: null,
    });
  }, []);

  return {
    ...state,
    startRun,
    pause,
    resume,
    cancel,
    reset,
  };
}
