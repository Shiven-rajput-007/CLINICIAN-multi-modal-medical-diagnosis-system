import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Stethoscope,
  FileCheck,
  Brain,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  FileText,
  Activity,
  Layers,
  ArrowRight
} from 'lucide-react';
import { ModalityType, DiagnosisInferResponse } from '../types';
import { diagnosisService } from '../services/diagnosis';
import { ImageUploader } from '../components/ImageUploader';
import { SymptomForm } from '../components/SymptomForm';
import { ProbabilityBar } from '../components/ProbabilityBar';
import { GradCamViewer } from '../components/GradCamViewer';
import { MedicalDisclaimer } from '../components/MedicalDisclaimer';
import { formatPercent, formatModality, getConfidenceBadgeClass } from '../utils/formatters';

export const Diagnose: React.FC = () => {
  const navigate = useNavigate();

  const [modality, setModality] = useState<ModalityType>('chest_xray');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [symptoms, setSymptoms] = useState<Record<string, boolean>>({});

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DiagnosisInferResponse | null>(null);

  const handleModalityChange = (newModality: ModalityType) => {
    if (newModality !== modality) {
      setModality(newModality);
      setSymptoms({});
      setResult(null);
      setError(null);
    }
  };

  const handleRunAnalysis = async () => {
    if (!selectedFile) {
      setError('Please upload a valid medical image scan before running diagnosis.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    try {
      setAnalysisStep('Preprocessing scan & running DenseNet-121 inference...');
      
      const inferResponse = await diagnosisService.runDiagnosis(
        selectedFile,
        modality,
        symptoms
      );

      setResult(inferResponse);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Diagnostic inference failed. Please verify scan format.';
      setError(msg);
    } finally {
      setIsAnalyzing(false);
      setAnalysisStep('');
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setSymptoms({});
    setResult(null);
    setError(null);
  };

  return (
    <div className="space-y-6">
      {/* Workspace Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <Stethoscope className="w-6 h-6 text-sky-700" />
            Multimodal Diagnostic Analysis
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 mt-1">
            Feed clinical scans and patient symptom profiles into transfer-learning DenseNet-121 and late-fusion neural networks.
          </p>
        </div>

        {result && (
          <button
            onClick={handleReset}
            className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors self-start sm:self-auto"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            New Analysis
          </button>
        )}
      </div>

      {error && (
        <div className="flex items-start gap-3 p-4 rounded-xl bg-rose-50 border border-rose-200 text-sm text-rose-800">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Diagnostic Pipeline Error:</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Input Workspace (Hidden when viewing completed result, or collapsible) */}
      {!result ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Modality & Image Upload */}
          <div className="lg:col-span-6 space-y-6">
            {/* 1. Modality Selector */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
                1. Select Diagnostic Modality
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => handleModalityChange('chest_xray')}
                  disabled={isAnalyzing}
                  className={`flex flex-col items-center p-4 rounded-xl border text-center transition-all ${
                    modality === 'chest_xray'
                      ? 'border-sky-600 bg-sky-50/80 shadow-xs'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  }`}
                >
                  <FileCheck className={`w-6 h-6 mb-2 ${modality === 'chest_xray' ? 'text-sky-700' : 'text-slate-400'}`} />
                  <span className="text-sm font-bold text-slate-900">Chest X-Ray</span>
                  <span className="text-[11px] text-slate-500 mt-0.5">
                    5 Pulmonary Pathologies
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => handleModalityChange('brain_mri')}
                  disabled={isAnalyzing}
                  className={`flex flex-col items-center p-4 rounded-xl border text-center transition-all ${
                    modality === 'brain_mri'
                      ? 'border-sky-600 bg-sky-50/80 shadow-xs'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  }`}
                >
                  <Brain className={`w-6 h-6 mb-2 ${modality === 'brain_mri' ? 'text-sky-700' : 'text-slate-400'}`} />
                  <span className="text-sm font-bold text-slate-900">Brain MRI</span>
                  <span className="text-[11px] text-slate-500 mt-0.5">
                    4 Tumor Categories
                  </span>
                </button>
              </div>
            </div>

            {/* 2. Image Upload */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <ImageUploader
                selectedFile={selectedFile}
                onFileSelect={(file) => {
                  setSelectedFile(file);
                  setError(null);
                }}
              />
            </div>
          </div>

          {/* Right Column: Symptom Checklist & Action */}
          <div className="lg:col-span-6 space-y-6">
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <SymptomForm
                modality={modality}
                symptoms={symptoms}
                onChange={setSymptoms}
              />
            </div>

            {/* Run Analysis CTA */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
              <button
                type="button"
                onClick={handleRunAnalysis}
                disabled={isAnalyzing || !selectedFile}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl shadow-xs text-sm font-bold text-white bg-sky-700 hover:bg-sky-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isAnalyzing ? (
                  <span className="flex items-center gap-2">
                    <Activity className="w-4 h-4 animate-spin" />
                    Executing Neural Diagnostic Pipeline...
                  </span>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>Run Multimodal Analysis</span>
                  </>
                )}
              </button>

              {isAnalyzing && (
                <div className="p-3 bg-sky-50 border border-sky-200 rounded-lg text-xs text-sky-900 space-y-1">
                  <p className="font-semibold">{analysisStep}</p>
                  <p className="text-[11px] text-sky-700">
                    Running DenseNet-121 feature extractor, symptom encoder MLP, and Grad-CAM backpropagation.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Result UI */
        <div className="space-y-6">
          {/* Top Result Banner */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div>
                  <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-500">
                    Diagnostic Inference Result • {formatModality(result.modality)}
                  </span>
                  <h2 className="text-2xl font-black text-slate-900 tracking-tight">
                    Model Prediction: <span className="text-sky-900">{result.predicted_class}</span>
                  </h2>
                </div>
              </div>

              <div className="flex items-center gap-3 self-start md:self-auto">
                <div className="text-right">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                    Prediction Confidence
                  </span>
                  <span className={`inline-block px-2.5 py-1 rounded-md font-mono text-base font-bold border mt-0.5 ${getConfidenceBadgeClass(result.confidence)}`}>
                    {formatPercent(result.confidence)}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Context & Meta */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200 font-mono">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Record ID</span>
                <span className="font-semibold text-slate-800">#{result.id}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Scan File</span>
                <span className="font-semibold text-slate-800 truncate block">{result.original_filename}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Architecture</span>
                <span className="font-semibold text-slate-800">{result.model_version}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Audit Persistence</span>
                <span className="text-emerald-700 font-semibold">Persisted in DB</span>
              </div>
            </div>
          </div>

          {/* Multimodal Fusion Comparison & Probability Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Probability Breakdown */}
            <div className="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-sky-600" />
                  Full Class Probability Distribution
                </h3>
                <span className="text-xs text-slate-500 font-mono">
                  {Object.keys(result.class_probabilities).length} Classes
                </span>
              </div>

              <div className="space-y-3">
                {Object.entries(result.class_probabilities)
                  .sort(([, a], [, b]) => b - a)
                  .map(([cls, prob]) => (
                    <ProbabilityBar
                      key={cls}
                      classNameStr={cls}
                      probability={prob}
                      isPrimary={cls === result.predicted_class}
                    />
                  ))}
              </div>
            </div>

            {/* Multimodal Late-Fusion Comparison Card */}
            <div className="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
              <div className="pb-3 border-b border-slate-100">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-sky-600" />
                  Multimodal Fusion Refinement
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Comparison between image-only classification and symptom-fused late decision head.
                </p>
              </div>

              <div className="space-y-3 text-xs">
                {/* Image Only */}
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                  <span className="text-slate-500 text-[10px] font-bold uppercase tracking-wider block">
                    Visual DenseNet-121 Alone
                  </span>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-800 text-sm">
                      {result.image_prediction.prediction_class}
                    </span>
                    <span className="font-mono text-slate-600 font-bold">
                      {formatPercent(result.image_prediction.confidence)}
                    </span>
                  </div>
                </div>

                {/* Multimodal Fusion */}
                <div className="p-3 rounded-lg bg-sky-50 border border-sky-200 space-y-1">
                  <span className="text-sky-800 text-[10px] font-bold uppercase tracking-wider block">
                    Multimodal Late-Fusion (Scan + Symptoms)
                  </span>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sky-950 text-sm">
                      {result.fusion_prediction.prediction_class}
                    </span>
                    <span className="font-mono text-sky-900 font-bold">
                      {formatPercent(result.fusion_prediction.confidence)}
                    </span>
                  </div>
                </div>

                {/* Symptoms Summary */}
                <div className="pt-2 text-slate-600">
                  <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                    Symptom Features Fed into Fusion MLP:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(result.symptom_data).filter(([_, v]) => !!v).length > 0 ? (
                      Object.entries(result.symptom_data)
                        .filter(([_, v]) => !!v)
                        .map(([k]) => (
                          <span key={k} className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded-sm font-medium text-[11px] capitalize">
                            {k.replace('_', ' ')}
                          </span>
                        ))
                    ) : (
                      <span className="text-slate-400 italic">No symptoms marked positive.</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Grad-CAM Heatmap Viewer */}
          <GradCamViewer
            originalImageUrl={result.image_url}
            gradcamImageUrl={result.gradcam_url}
            gradcamBase64={result.gradcam_base64}
            predictedClass={result.predicted_class}
          />

          {/* Actions & Disclaimer */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
            <button
              onClick={handleReset}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 text-xs font-semibold shadow-xs"
            >
              <RotateCcw className="w-4 h-4" />
              Analyze Another Scan
            </button>

            <button
              onClick={() => navigate('/history')}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-sky-700 text-white rounded-lg hover:bg-sky-800 text-xs font-semibold shadow-xs"
            >
              <FileText className="w-4 h-4" />
              View Clinical History & Audit Logs
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          <MedicalDisclaimer />
        </div>
      )}
    </div>
  );
};
