import React from 'react';
import { LucideIcon, FileText } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: LucideIcon;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = "No diagnosis records yet.",
  description = "Start your first diagnosis to see clinical statistics and records here.",
  icon: Icon = FileText,
  actionText,
  onAction,
}) => {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white/60 p-8 sm:p-12 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500 mb-4">
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="text-base font-semibold text-slate-800">
        {title}
      </h3>
      <p className="mt-1 text-sm text-slate-500 max-w-sm mx-auto">
        {description}
      </p>
      {actionText && onAction && (
        <div className="mt-6">
          <button
            type="button"
            onClick={onAction}
            className="inline-flex items-center gap-2 rounded-lg bg-sky-700 px-4 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-sky-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-600 transition-colors"
          >
            {actionText}
          </button>
        </div>
      )}
    </div>
  );
};
