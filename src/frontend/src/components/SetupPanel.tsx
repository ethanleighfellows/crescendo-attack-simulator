import { useState } from 'react';
import type { PresetName, RunConfig } from '../types';

interface SetupPanelProps {
  config: RunConfig;
  onConfigChange: (config: RunConfig) => void;
  onStart: (config: RunConfig) => void;
}

const PROVIDERS = ['openai', 'anthropic', 'azure', 'ollama', 'together'];
const TURN_LEVEL_ATTACKS = ['base64', 'leetspeak', 'rot13', 'roleplay', 'reverse'];

const PRESETS: Record<string, Partial<RunConfig>> = {
  conservative: {
    max_rounds: 5,
    max_backtracks: 3,
    enhancement_probability: 0.0,
    success_threshold: 100,
    turn_level_attacks: [],
  },
  balanced: {
    max_rounds: 10,
    max_backtracks: 10,
    enhancement_probability: 0.5,
    success_threshold: 100,
    turn_level_attacks: [],
  },
  aggressive: {
    max_rounds: 30,
    max_backtracks: 20,
    enhancement_probability: 0.8,
    success_threshold: 80,
    turn_level_attacks: ['base64', 'leetspeak', 'rot13', 'roleplay'],
  },
};

export function SetupPanel({ config, onConfigChange, onStart }: SetupPanelProps) {
  const [preset, setPreset] = useState<PresetName>('balanced');

  const update = (partial: Partial<RunConfig>) => {
    onConfigChange({ ...config, ...partial });
  };

  const applyPreset = (name: PresetName) => {
    setPreset(name);
    if (name !== 'custom') {
      update(PRESETS[name] ?? {});
    }
  };

  const toggleAttack = (name: string) => {
    const current = config.turn_level_attacks;
    const next = current.includes(name)
      ? current.filter((a) => a !== name)
      : [...current, name];
    update({ turn_level_attacks: next });
    setPreset('custom');
  };

  const isValid = config.objective.trim().length > 0;

  return (
    <div className="space-y-5">
      {/* Attack Configuration */}
      <section className="card">
        <h2 className="text-sm font-semibold text-dynamo-text mb-4 flex items-center gap-2">
          <span className="w-5 h-5 rounded-full bg-dynamo-light flex items-center justify-center text-dynamo-purple text-xs font-bold">1</span>
          Attack Configuration
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dynamo-text mb-1">
              Objective <span className="text-red-500">*</span>
            </label>
            <textarea
              value={config.objective}
              onChange={(e) => update({ objective: e.target.value })}
              placeholder="The target goal for the jailbreak (e.g., 'Explain how to pick a lock')"
              rows={3}
              className="input-field resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-dynamo-text mb-1">Vulnerability Category</label>
              <input
                type="text"
                value={config.vulnerability}
                onChange={(e) => update({ vulnerability: e.target.value })}
                placeholder="e.g., Content Policy Bypass"
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dynamo-text mb-1">Vulnerability Type</label>
              <input
                type="text"
                value={config.vulnerability_type}
                onChange={(e) => update({ vulnerability_type: e.target.value })}
                placeholder="e.g., Harmful Content Generation"
                className="input-field"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-dynamo-text mb-1">
              Initial Prompt{' '}
              <span className="text-dynamo-muted font-normal">(optional — auto-generated if blank)</span>
            </label>
            <textarea
              value={config.initial_prompt ?? ''}
              onChange={(e) => update({ initial_prompt: e.target.value || null })}
              rows={2}
              className="input-field resize-none"
            />
          </div>
        </div>
      </section>

      {/* Model Configuration */}
      <section className="card">
        <h2 className="text-sm font-semibold text-dynamo-text mb-4 flex items-center gap-2">
          <span className="w-5 h-5 rounded-full bg-dynamo-light flex items-center justify-center text-dynamo-purple text-xs font-bold">2</span>
          Model Configuration
        </h2>
        <div className="grid grid-cols-2 gap-6">
          {/* Target */}
          <div className="space-y-3">
            <div className="section-label">Target Model (being tested)</div>
            <div>
              <label className="block text-xs font-medium text-dynamo-muted mb-1">Provider</label>
              <select
                value={config.target_provider}
                onChange={(e) => update({ target_provider: e.target.value })}
                className="input-field"
              >
                {PROVIDERS.map((p) => (
                  <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-dynamo-muted mb-1">Model ID</label>
              <input type="text" value={config.target_model}
                onChange={(e) => update({ target_model: e.target.value })}
                className="input-field" />
            </div>
            <div>
              <label className="block text-xs font-medium text-dynamo-muted mb-1">API Key</label>
              <input type="password" value={config.target_api_key ?? ''}
                onChange={(e) => update({ target_api_key: e.target.value || null })}
                placeholder="Falls back to provider env var"
                className="input-field" />
            </div>
            <div>
              <label className="block text-xs font-medium text-dynamo-muted mb-1">Base URL <span className="text-gray-400">(optional)</span></label>
              <input type="text" value={config.target_base_url ?? ''}
                onChange={(e) => update({ target_base_url: e.target.value || null })}
                placeholder="For Azure / Ollama / Together custom endpoints"
                className="input-field" />
            </div>
          </div>
          {/* Simulator */}
          <div className="space-y-3">
            <div className="section-label">Simulator / Judge Model</div>
            <div>
              <label className="block text-xs font-medium text-dynamo-muted mb-1">Provider</label>
              <select
                value={config.simulator_provider}
                onChange={(e) => update({ simulator_provider: e.target.value })}
                className="input-field"
              >
                {PROVIDERS.map((p) => (
                  <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-dynamo-muted mb-1">Model ID</label>
              <input type="text" value={config.simulator_model}
                onChange={(e) => update({ simulator_model: e.target.value })}
                className="input-field" />
            </div>
            <div>
              <label className="block text-xs font-medium text-dynamo-muted mb-1">API Key</label>
              <input type="password" value={config.simulator_api_key ?? ''}
                onChange={(e) => update({ simulator_api_key: e.target.value || null })}
                placeholder="Falls back to provider env var"
                className="input-field" />
            </div>
            <div>
              <label className="block text-xs font-medium text-dynamo-muted mb-1">Base URL <span className="text-gray-400">(optional)</span></label>
              <input type="text" value={config.simulator_base_url ?? ''}
                onChange={(e) => update({ simulator_base_url: e.target.value || null })}
                className="input-field" />
            </div>
          </div>
        </div>
      </section>

      {/* Engine Settings */}
      <section className="card">
        <h2 className="text-sm font-semibold text-dynamo-text mb-4 flex items-center gap-2">
          <span className="w-5 h-5 rounded-full bg-dynamo-light flex items-center justify-center text-dynamo-purple text-xs font-bold">3</span>
          Engine Settings
        </h2>
        <div className="space-y-5">
          {/* Presets */}
          <div>
            <div className="section-label">Preset</div>
            <div className="flex gap-2">
              {(['conservative', 'balanced', 'aggressive', 'custom'] as PresetName[]).map((p) => (
                <button
                  key={p}
                  onClick={() => applyPreset(p)}
                  className={`px-4 py-2 text-sm font-medium rounded-lg border transition-all ${
                    preset === p
                      ? 'bg-dynamo-purple text-white border-dynamo-purple shadow-sm'
                      : 'bg-white text-dynamo-muted border-gray-200 hover:border-dynamo-purple hover:text-dynamo-purple'
                  }`}
                >
                  {p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Sliders */}
          <div className="grid grid-cols-2 gap-x-8 gap-y-4">
            <SliderField
              label="Max Rounds"
              value={config.max_rounds}
              min={1} max={50}
              onChange={(v) => { update({ max_rounds: v }); setPreset('custom'); }}
            />
            <SliderField
              label="Max Backtracks"
              value={config.max_backtracks}
              min={0} max={50}
              onChange={(v) => { update({ max_backtracks: v }); setPreset('custom'); }}
            />
            <SliderField
              label="Enhancement Probability"
              value={Math.round(config.enhancement_probability * 100)}
              min={0} max={100}
              suffix="%"
              onChange={(v) => { update({ enhancement_probability: v / 100 }); setPreset('custom'); }}
            />
            <SliderField
              label="Success Threshold"
              value={config.success_threshold}
              min={1} max={100}
              suffix="%"
              onChange={(v) => { update({ success_threshold: v }); setPreset('custom'); }}
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="stopOnSuccess"
              checked={config.stop_on_first_success}
              onChange={(e) => update({ stop_on_first_success: e.target.checked })}
              className="w-4 h-4 rounded border-gray-300 text-dynamo-purple focus:ring-dynamo-purple/30"
            />
            <label htmlFor="stopOnSuccess" className="text-sm text-dynamo-text">
              Stop on first success
            </label>
          </div>

          {/* Turn-level attacks */}
          <div>
            <div className="section-label">Turn-Level Attack Augmentation</div>
            <div className="flex flex-wrap gap-2">
              {TURN_LEVEL_ATTACKS.map((attack) => (
                <button
                  key={attack}
                  onClick={() => toggleAttack(attack)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all ${
                    config.turn_level_attacks.includes(attack)
                      ? 'bg-dynamo-light text-dynamo-purple border-dynamo-purple/30'
                      : 'bg-white text-dynamo-muted border-gray-200 hover:border-dynamo-purple/40'
                  }`}
                >
                  {attack}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <SliderField
              label="Temperature"
              value={Math.round(config.temperature * 10)}
              min={0} max={20}
              display={(v) => (v / 10).toFixed(1)}
              onChange={(v) => update({ temperature: v / 10 })}
            />
            <div>
              <label className="block text-sm font-medium text-dynamo-text mb-1">Max Retries</label>
              <input
                type="number" min={1} max={10} value={config.max_retries}
                onChange={(e) => update({ max_retries: Number(e.target.value) })}
                className="input-field"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Start */}
      <div className="flex justify-end pt-1">
        <button
          onClick={() => onStart(config)}
          disabled={!isValid}
          className="btn-primary px-8 py-3 text-base"
        >
          Start Crescendo Run →
        </button>
      </div>
    </div>
  );
}

function SliderField({
  label,
  value,
  min,
  max,
  suffix = '',
  display,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  suffix?: string;
  display?: (v: number) => string;
  onChange: (v: number) => void;
}) {
  const displayed = display ? display(value) : String(value);
  return (
    <div>
      <div className="flex justify-between mb-1">
        <label className="text-sm font-medium text-dynamo-text">{label}</label>
        <span className="text-sm font-semibold text-dynamo-purple">
          {displayed}{suffix}
        </span>
      </div>
      <input
        type="range" min={min} max={max} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 rounded-full accent-dynamo-purple cursor-pointer"
      />
    </div>
  );
}
