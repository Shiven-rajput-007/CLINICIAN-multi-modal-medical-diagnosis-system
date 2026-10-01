import React from 'react';
import { AlertCircle } from 'lucide-react';

interface MedicalDisclaimerProps {
  compact?: boolean;
}

export const MedicalDisclaimer: React.FC<MedicalDisclaimerProps> = ({ compact = false }) => {
  if (compact) {
    return (
      <div className="flex items-center gap-2 rounded-md bg-amber-50/80 px-3 py-2 text-xs text-amber-800 border border-amber-200">
        <AlertCircle className="w-4 h-4 shrink-0 text-amber-600" />
        <p>
          <span className="font-semibold">Research Demonstration:</span> Not approved as a diagnostic medical device. For qualified clinical research only.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-amber-200/90 bg-amber-50/70 p-4 shadow-xs">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-amber-700 mt-0.5 shrink-0" />
        <div className="space-y-1 text-xs sm:text-sm text-amber-900 leading-relaxed">
          <p className="font-semibold tracking-tight text-amber-950">
            Clinical Research & Educational Demonstration Notice
          </p>
          <p>
            This application is a research and educational demonstration of machine-learning inference using DenseNet-121 and multimodal late-fusion architectures. It is <strong>not a certified medical device</strong> and must not be used as a substitute for diagnosis, evaluation, or treatment by a licensed physician or healthcare professional.
          </p>
        </div>
      </div>
    </div>
  );
};
