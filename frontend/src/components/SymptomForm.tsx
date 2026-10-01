import React from 'react';
import { ModalityType } from '../types';

interface SymptomFormProps {
  modality: ModalityType;
  symptoms: Record<string, boolean>;
  onChange: (symptoms: Record<string, boolean>) => void;
}

export const CHEST_SYMPTOMS_LIST = [
  { key: 'cough', label: 'Persistent Cough', desc: 'Productive or dry cough > 2 weeks' },
  { key: 'fever', label: 'Fever / Chills', desc: 'Core body temperature > 38.0°C or rigor' },
  { key: 'dyspnea', label: 'Shortness of Breath', desc: 'Exertional or resting respiratory distress' },
  { key: 'chest_pain', label: 'Pleuritic Chest Pain', desc: 'Sharp pain aggravated by deep inspiration' },
  { key: 'fatigue', label: 'Severe Fatigue / Malaise', desc: 'Generalized lethargy impairing daily activity' },
  { key: 'hemoptysis', label: 'Hemoptysis', desc: 'Coughing up blood or blood-tinged sputum' },
  { key: 'wheezing', label: 'Wheezing / Stridor', desc: 'High-pitched expiratory or inspiratory airway sounds' },
  { key: 'tachypnea', label: 'Rapid Breathing', desc: 'Respiratory rate > 20 breaths per minute' },
];

export const BRAIN_SYMPTOMS_LIST = [
  { key: 'headache', label: 'Morning Headache', desc: 'Persistent headache worse upon waking or recumbency' },
  { key: 'seizures', label: 'Seizures / Convulsions', desc: 'New-onset focal or generalized epileptic events' },
  { key: 'vision_changes', label: 'Vision Loss / Diplopia', desc: 'Blurred vision, double vision, or visual field deficits' },
  { key: 'nausea_vomiting', label: 'Nausea / Projectile Vomiting', desc: 'Unexplained gastrointestinal symptoms without fever' },
  { key: 'cognitive_decline', label: 'Memory / Cognitive Decline', desc: 'Executive dysfunction, personality change, disorientation' },
  { key: 'balance_issues', label: 'Ataxia / Loss of Balance', desc: 'Gait instability, vertigo, unsteadiness' },
  { key: 'motor_weakness', label: 'Focal Motor Weakness', desc: 'Unilateral limb weakness or facial droop' },
  { key: 'speech_difficulty', label: 'Aphasia / Dysarthria', desc: 'Impaired word-finding or slurred speech articulation' },
];

export const SymptomForm: React.FC<SymptomFormProps> = ({
  modality,
  symptoms,
  onChange,
}) => {
  const currentList = modality === 'chest_xray' ? CHEST_SYMPTOMS_LIST : BRAIN_SYMPTOMS_LIST;

  const handleToggle = (key: string) => {
    onChange({
      ...symptoms,
      [key]: !symptoms[key],
    });
  };

  const handleClearAll = () => {
    const cleared: Record<string, boolean> = {};
    currentList.forEach((s) => {
      cleared[s.key] = false;
    });
    onChange(cleared);
  };

  const activeCount = Object.values(symptoms).filter(Boolean).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
            Clinical Symptom Checklist ({modality === 'chest_xray' ? 'Pulmonary' : 'Neurological'})
          </label>
          <p className="text-xs text-slate-500 mt-0.5">
            Structured indicators fed into the late-fusion neural network embedding MLP.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-sm">
            {activeCount}/{currentList.length} Positive
          </span>
          {activeCount > 0 && (
            <button
              type="button"
              onClick={handleClearAll}
              className="text-xs text-sky-700 hover:text-sky-800 font-medium underline"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {currentList.map(({ key, label, desc }) => {
          const isChecked = !!symptoms[key];
          return (
            <div
              key={key}
              onClick={() => handleToggle(key)}
              className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer select-none transition-all ${
                isChecked
                  ? 'border-sky-500 bg-sky-50/60 shadow-xs'
                  : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'
              }`}
            >
              <input
                type="checkbox"
                checked={isChecked}
                onChange={() => {}} // Handled by container onClick
                className="mt-0.5 h-4 w-4 rounded-sm border-slate-300 text-sky-600 focus:ring-sky-500"
              />
              <div className="text-xs leading-normal">
                <span className={`font-semibold block ${isChecked ? 'text-sky-950' : 'text-slate-800'}`}>
                  {label}
                </span>
                <span className="text-slate-500 block mt-0.5 text-[11px] leading-tight">
                  {desc}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
