import { useState } from 'react';
import { ExportPanel } from './components/ExportPanel';
import { Header } from './components/Header';
import { LiveRunPanel } from './components/LiveRunPanel';
import { ReviewPanel } from './components/ReviewPanel';
import { SetupPanel } from './components/SetupPanel';
import { useCrescendoRun } from './hooks/useCrescendoRun';
import type { AppPhase, RunConfig } from './types';
import { DEFAULT_CONFIG } from './types';

export default function App() {
  const [phase, setPhase] = useState<AppPhase>('setup');
  const [config, setConfig] = useState<RunConfig>(DEFAULT_CONFIG);
  const run = useCrescendoRun();

  const handleStartRun = (cfg: RunConfig) => {
    setConfig(cfg);
    run.startRun(cfg);
    setPhase('running');
  };

  const handleRunComplete = () => {
    setPhase('review');
  };

  const handleGoToExport = () => {
    setPhase('export');
  };

  const handleRerunWithChanges = () => {
    run.reset();
    setPhase('setup');
  };

  const handleRetry = () => {
    run.reset();
    run.startRun(config);
    setPhase('running');
  };

  if (run.status === 'completed' && phase === 'running') {
    handleRunComplete();
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header phase={phase} onNavigate={setPhase} />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6 sm:px-6 lg:px-8">
        {phase === 'setup' && (
          <SetupPanel
            config={config}
            onConfigChange={setConfig}
            onStart={handleStartRun}
          />
        )}

        {phase === 'running' && (
          <LiveRunPanel
            turns={run.turns}
            status={run.status}
            error={run.error}
            config={config}
            onPause={run.pause}
            onResume={run.resume}
            onCancel={run.cancel}
          />
        )}

        {phase === 'review' && (
          <ReviewPanel
            result={run.result}
            turns={run.turns}
            onExport={handleGoToExport}
            onRerunWithChanges={handleRerunWithChanges}
            onRetry={handleRetry}
          />
        )}

        {phase === 'export' && (
          <ExportPanel
            runId={run.runId}
            result={run.result}
            onBack={() => setPhase('review')}
          />
        )}
      </main>
    </div>
  );
}
