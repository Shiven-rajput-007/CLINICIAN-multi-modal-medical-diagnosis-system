import React, { useState } from 'react';
import { Layers, Info } from 'lucide-react';

interface GradCamViewerProps {
  originalImageUrl: string;
  gradcamImageUrl?: string;
  gradcamBase64?: string;
  predictedClass: string;
}

export const GradCamViewer: React.FC<GradCamViewerProps> = ({
  originalImageUrl,
  gradcamImageUrl,
  gradcamBase64,
  predictedClass,
}) => {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'overlay-only' | 'original-only'>('side-by-side');

  const activeGradcamSource = gradcamBase64 || gradcamImageUrl;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-sky-600" />
            Model Attention / Grad-CAM Explainability
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Target Layer: DenseNet-121 Feature Block 4 (Conv 2)
          </p>
        </div>

        {/* View Toggle */}
        <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1 text-xs font-medium text-slate-600 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setViewMode('side-by-side')}
            className={`px-2.5 py-1 rounded-md transition-colors ${
              viewMode === 'side-by-side'
                ? 'bg-white text-sky-800 shadow-xs font-semibold'
                : 'hover:text-slate-900'
            }`}
          >
            Side-by-Side
          </button>
          <button
            type="button"
            onClick={() => setViewMode('overlay-only')}
            className={`px-2.5 py-1 rounded-md transition-colors ${
              viewMode === 'overlay-only'
                ? 'bg-white text-sky-800 shadow-xs font-semibold'
                : 'hover:text-slate-900'
            }`}
          >
            Grad-CAM
          </button>
          <button
            type="button"
            onClick={() => setViewMode('original-only')}
            className={`px-2.5 py-1 rounded-md transition-colors ${
              viewMode === 'original-only'
                ? 'bg-white text-sky-800 shadow-xs font-semibold'
                : 'hover:text-slate-900'
            }`}
          >
            Original Scan
          </button>
        </div>
      </div>

      {/* Visual Displays */}
      <div className="bg-slate-950 rounded-xl p-4 flex items-center justify-center min-h-[300px]">
        {viewMode === 'side-by-side' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
            <div className="flex flex-col items-center">
              <span className="text-[11px] font-mono text-slate-400 mb-2 uppercase tracking-wider">
                Original Input Scan
              </span>
              <div className="w-full max-w-[280px] aspect-square rounded-lg overflow-hidden border border-slate-800 bg-black flex items-center justify-center">
                <img
                  src={originalImageUrl}
                  alt="Original Clinical Scan"
                  className="w-full h-full object-contain"
                />
              </div>
            </div>

            <div className="flex flex-col items-center">
              <span className="text-[11px] font-mono text-sky-400 mb-2 uppercase tracking-wider flex items-center gap-1">
                Grad-CAM Heatmap Overlay ({predictedClass})
              </span>
              <div className="w-full max-w-[280px] aspect-square rounded-lg overflow-hidden border border-sky-800/60 bg-black flex items-center justify-center">
                {activeGradcamSource ? (
                  <img
                    src={activeGradcamSource}
                    alt="Grad-CAM Heatmap Overlay"
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <span className="text-xs text-slate-500">Grad-CAM unavailable</span>
                )}
              </div>
            </div>
          </div>
        )}

        {viewMode === 'overlay-only' && (
          <div className="flex flex-col items-center w-full">
            <span className="text-xs font-mono text-sky-400 mb-2 uppercase tracking-wider">
              Grad-CAM Class Activation Map ({predictedClass})
            </span>
            <div className="w-full max-w-sm aspect-square rounded-lg overflow-hidden border border-slate-800 bg-black flex items-center justify-center">
              {activeGradcamSource ? (
                <img
                  src={activeGradcamSource}
                  alt="Grad-CAM Heatmap"
                  className="w-full h-full object-contain"
                />
              ) : (
                <span className="text-xs text-slate-500">Grad-CAM unavailable</span>
              )}
            </div>
          </div>
        )}

        {viewMode === 'original-only' && (
          <div className="flex flex-col items-center w-full">
            <span className="text-xs font-mono text-slate-400 mb-2 uppercase tracking-wider">
              Original Medical Scan
            </span>
            <div className="w-full max-w-sm aspect-square rounded-lg overflow-hidden border border-slate-800 bg-black flex items-center justify-center">
              <img
                src={originalImageUrl}
                alt="Original Medical Scan"
                className="w-full h-full object-contain"
              />
            </div>
          </div>
        )}
      </div>

      {/* Explanatory note */}
      <div className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600">
        <Info className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
        <p>
          <span className="font-semibold text-slate-900">Interpretation Note:</span> Grad-CAM visualization highlights image regions that contributed most strongly to the convolutional neural network&apos;s feature classification for <em>{predictedClass}</em>. Warm colors (red/yellow) indicate salient focal regions. This is an explainability guide and does not constitute a certified radiologist delineation.
        </p>
      </div>
    </div>
  );
};
