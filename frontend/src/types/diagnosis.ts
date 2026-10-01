export type ModalityType = 'chest_xray' | 'brain_mri';

export interface PredictionDetail {
  prediction_class: string;
  confidence: number;
  probabilities: Record<string, number>;
}

export interface DiagnosisInferResponse {
  id: number;
  user_id: number;
  modality: ModalityType;
  original_filename: string;
  predicted_class: string;
  confidence: number;
  class_probabilities: Record<string, number>;
  image_prediction: PredictionDetail;
  fusion_prediction: PredictionDetail;
  image_url: string;
  gradcam_url: string;
  gradcam_base64: string;
  symptom_data: Record<string, boolean>;
  model_version: string;
  created_at: string;
}

export interface DiagnosisRecord {
  id: number;
  user_id: number;
  modality: ModalityType;
  original_filename: string;
  predicted_class: string;
  confidence: number;
  class_probabilities: Record<string, number>;
  image_prediction?: string;
  image_confidence?: number;
  fusion_prediction?: string;
  fusion_confidence?: number;
  symptom_data: Record<string, boolean>;
  image_url: string;
  gradcam_url: string;
  model_version: string;
  created_at: string;
}

export interface PaginatedHistory {
  records: DiagnosisRecord[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RecentDiagnosisSummary {
  id: number;
  modality: ModalityType;
  predicted_class: string;
  confidence: number;
  created_at: string;
}

export interface ModelBenchmarkMetrics {
  image_model_test_accuracy: number;
  fusion_model_test_accuracy: number;
  evaluation_dataset: string;
}

export interface DashboardStats {
  total_diagnoses: number;
  chest_xray_count: number;
  brain_mri_count: number;
  average_confidence: number;
  most_recent_diagnosis: RecentDiagnosisSummary | null;
  class_distribution: Record<string, number>;
  modality_breakdown: Record<string, number>;
  model_evaluation_metrics: {
    chest_xray?: ModelBenchmarkMetrics;
    brain_mri?: ModelBenchmarkMetrics;
    note?: string;
  };
}

export interface ModalityMetadataItem {
  modality_name: string;
  num_classes: number;
  classes: string[];
  symptoms: string[];
  symptom_labels: Record<string, string>;
  image_size: [number, number];
  target_layer: string;
  evaluation_metrics: ModelBenchmarkMetrics;
}

export type ClinicalMetadata = Record<ModalityType, ModalityMetadataItem>;
