import React from 'react';
import { formatPercent } from '../utils/formatters';

interface ProbabilityBarProps {
  classNameStr: string;
  probability: number;
  isPrimary?: boolean;
}

export const ProbabilityBar: React.FC<ProbabilityBarProps> = ({
  classNameStr,
  probability,
  isPrimary = false,
}) => {
  const percent = Math.min(100, Math.max(0, probability * 100));

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className={`font-medium ${isPrimary ? 'text-sky-950 font-bold' : 'text-slate-700'}`}>
          {classNameStr} {isPrimary && <span className="ml-1 text-[10px] text-sky-700 bg-sky-100 px-1.5 py-0.5 rounded-sm uppercase tracking-wide">Top Prediction</span>}
        </span>
        <span className={`font-mono ${isPrimary ? 'text-sky-900 font-bold' : 'text-slate-600'}`}>
          {formatPercent(probability)}
        </span>
      </div>
      <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200/60">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            isPrimary ? 'bg-sky-600' : 'bg-slate-400'
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
};
