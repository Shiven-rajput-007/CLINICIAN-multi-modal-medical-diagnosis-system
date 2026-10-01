import React from 'react';
import { X, Calendar, Stethoscope, Layers } from 'lucide-react';
import { DiagnosisRecord } from '../types';
import { formatDate, formatModality, formatPercent, getConfidenceBadgeClass } from '../utils/formatters';
import { ProbabilityBar } from './ProbabilityBar';

interface ViewRecordModalProps {
  record: DiagnosisRecord | null;
  onClose: () => void;
}

export const ViewRecordModal: React.FC<ViewRecordModalProps> = ({
  record,
  onClose,
}) => {
  if (!record) return null;

  const activeSymptoms = Object.entries(record.symptom_data || {}).filter(([_, val]) => !!val);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-xs overflow-y-auto">
      <div
        className="w-full max-w-4xl rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden my-8"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-900 text-white">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-sky-600 text-white">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold">
                Clinical Audit Record #{record.id}
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                {record.original_filename} • {record.model_version}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {/* Summary Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
            <div>
              <span className="text-slate-500 block uppercase tracking-wider text-[10px] font-semibold">
                Modality
              </span>
              <span className="font-semibold text-slate-900 text-sm mt-0.5 block">
                {formatModality(record.modality)}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block uppercase tracking-wider text-[10px] font-semibold">
                Prediction
              </span>
              <span className="font-semibold text-sky-900 text-sm mt-0.5 block">
                {record.predicted_class}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block uppercase tracking-wider text-[10px] font-semibold">
                Confidence
              </span>
              <span className={`inline-block px-2 py-0.5 rounded-sm font-mono font-bold mt-0.5 text-xs border ${getConfidenceBadgeClass(record.confidence)}`}>
                {formatPercent(record.confidence)}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block uppercase tracking-wider text-[10px] font-semibold">
                Date & Time
              </span>
              <span className="text-slate-700 font-medium mt-0.5 block flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                {formatDate(record.created_at)}
              </span>
            </div>
          </div>

          {/* Scans & Grad-CAM Display */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-3 flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-sky-600" />
              Imaging & Attention Map
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-950 p-4 rounded-xl">
              <div className="flex flex-col items-center">
                <span className="text-[11px] font-mono text-slate-400 mb-2 uppercase">
                  Original Scan
                </span>
                <div className="w-full aspect-square max-w-[260px] bg-black rounded-lg overflow-hidden border border-slate-800 flex items-center justify-center">
                  <img
                    src={record.image_url}
                    alt="Original scan"
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-[11px] font-mono text-sky-400 mb-2 uppercase">
                  Grad-CAM Attention Map
                </span>
                <div className="w-full aspect-square max-w-[260px] bg-black rounded-lg overflow-hidden border border-sky-800/60 flex items-center justify-center">
                  <img
                    src={record.gradcam_url}
                    alt="Grad-CAM overlay"
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Multimodal Breakdown & Symptoms */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Probability Breakdown */}
            <div className="border border-slate-200 rounded-xl p-4 bg-white space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
                Probability Distribution
              </h4>
              <div className="space-y-2.5">
                {Object.entries(record.class_probabilities || {})
                  .sort(([, a], [, b]) => b - a)
                  .map(([cls, prob]) => (
                    <ProbabilityBar
                      key={cls}
                      classNameStr={cls}
                      probability={prob}
                      isPrimary={cls === record.predicted_class}
                    />
                  ))}
              </div>
            </div>

            {/* Symptoms Checklist */}
            <div className="border border-slate-200 rounded-xl p-4 bg-white space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center justify-between">
                <span>Recorded Symptom Indicators</span>
                <span className="text-slate-400 font-mono text-[11px]">
                  {activeSymptoms.length} Reported
                </span>
              </h4>
              {activeSymptoms.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {activeSymptoms.map(([key]) => (
                    <div
                      key={key}
                      className="px-2.5 py-1.5 rounded-md bg-sky-50 border border-sky-200 text-xs text-sky-950 font-medium capitalize"
                    >
                      • {key.replace('_', ' ')}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic p-3 bg-slate-50 rounded-lg">
                  No positive symptoms were marked for this clinical scan.
                </p>
              )}

              {/* Multimodal comparison if available */}
              {(record.image_prediction || record.fusion_prediction) && (
                <div className="pt-3 border-t border-slate-100 text-xs space-y-1.5">
                  <span className="text-slate-500 block uppercase tracking-wider text-[10px] font-semibold">
                    Late-Fusion Refinement
                  </span>
                  <div className="flex items-center justify-between bg-slate-50 p-2 rounded-md border border-slate-200">
                    <span className="text-slate-600">Image Backbone:</span>
                    <span className="font-semibold text-slate-800">
                      {record.image_prediction || '—'} {record.image_confidence ? `(${formatPercent(record.image_confidence)})` : ''}
                    </span>
                  </div>
                  <div className="flex items-center justify-between bg-sky-50 p-2 rounded-md border border-sky-200">
                    <span className="text-sky-800">Multimodal Fusion:</span>
                    <span className="font-semibold text-sky-950">
                      {record.fusion_prediction || record.predicted_class} {record.fusion_confidence ? `(${formatPercent(record.fusion_confidence)})` : ''}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-100 transition-colors"
          >
            Close Audit View
          </button>
        </div>
      </div>
    </div>
  );
};
