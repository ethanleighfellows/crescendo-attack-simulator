import type { AppPhase } from '../types';

interface HeaderProps {
  phase: AppPhase;
  onNavigate: (phase: AppPhase) => void;
}

const PHASES: { id: AppPhase; label: string }[] = [
  { id: 'setup', label: 'Setup' },
  { id: 'running', label: 'Run' },
  { id: 'review', label: 'Review' },
  { id: 'export', label: 'Export' },
];

const DYNAMO_LOGO =
  'https://media.licdn.com/dms/image/v2/D560BAQEA_R90IfwVQw/company-logo_200_200/B56ZVJSrZIGUAI-/0/1740691388344/dynamofl_logo?e=2147483647&v=beta&t=ymy9r23yayr3iexYq_ODWcA9e3s-2U7KorHPlQqMPyg';

export function Header({ phase, onNavigate }: HeaderProps) {
  return (
    <header className="bg-dynamo-navy border-b border-dynamo-mid shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo + title */}
          <div className="flex items-center gap-3">
            <img
              src={DYNAMO_LOGO}
              alt="Dynamo AI"
              className="w-8 h-8 rounded-lg object-cover bg-white p-0.5"
              onError={(e) => {
                // fallback to text logo if CDN fails
                (e.currentTarget as HTMLImageElement).style.display = 'none';
              }}
            />
            <div className="flex flex-col leading-none">
              <span className="text-white font-semibold text-sm tracking-tight">
                Crescendo Generator
              </span>
              <span className="text-dynamo-teal text-[10px] font-medium tracking-wide uppercase">
                Dynamo AI · Red Teaming
              </span>
            </div>
          </div>

          {/* Phase navigation */}
          <nav className="flex items-center gap-1">
            {PHASES.map((p, idx) => (
              <button
                key={p.id}
                onClick={() => onNavigate(p.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
                  phase === p.id
                    ? 'bg-dynamo-purple text-white shadow-sm'
                    : 'text-gray-400 hover:text-white hover:bg-white/10'
                }`}
              >
                <span
                  className={`w-4 h-4 flex items-center justify-center rounded-full text-[10px] font-bold ${
                    phase === p.id ? 'bg-white/20' : 'bg-white/10'
                  }`}
                >
                  {idx + 1}
                </span>
                {p.label}
              </button>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}
