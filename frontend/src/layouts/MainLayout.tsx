import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { MedicalDisclaimer } from '../components/MedicalDisclaimer';
import { ShieldCheck } from 'lucide-react';

export const MainLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <MedicalDisclaimer compact />
        <Outlet />
      </main>

      <footer className="bg-white border-t border-slate-200 py-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Multi-Modal Medical Diagnosis Assistant • Version 1.0.0</span>
          </div>
          <p className="text-center sm:text-right text-[11px] text-slate-400">
            PyTorch DenseNet-121 & Multimodal Late-Fusion with Grad-CAM Explainability. Academic & Research Deployment.
          </p>
        </div>
      </footer>
    </div>
  );
};
