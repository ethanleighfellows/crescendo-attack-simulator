interface DisclaimerBannerProps {
  onAcknowledge: () => void;
}

export function DisclaimerBanner({ onAcknowledge }: DisclaimerBannerProps) {
  return (
    <div className="bg-amber-50 border-b border-amber-200">
      <div className="max-w-7xl mx-auto px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-start justify-between gap-6">
          <div className="flex items-start gap-3">
            <span className="text-amber-500 text-lg mt-0.5 flex-shrink-0">&#9888;</span>
            <p className="text-sm text-amber-800">
              <span className="font-semibold">Research Use Only.</span>{' '}
              This tool is for authorized security research and red-teaming only. Use against
              systems without explicit authorization is prohibited. By continuing you accept
              full responsibility for your actions.
            </p>
          </div>
          <button
            onClick={onAcknowledge}
            className="flex-shrink-0 px-4 py-1.5 text-sm font-semibold text-white bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors whitespace-nowrap"
          >
            I Acknowledge
          </button>
        </div>
      </div>
    </div>
  );
}
