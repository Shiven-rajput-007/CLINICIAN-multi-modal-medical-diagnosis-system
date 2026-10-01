import { apiClient } from './api';
import {
  ModalityType,
  DiagnosisInferResponse,
  DiagnosisRecord,
  PaginatedHistory,
  DashboardStats,
  ClinicalMetadata,
} from '../types';

export const diagnosisService = {
  async getMetadata(): Promise<ClinicalMetadata> {
    return apiClient<ClinicalMetadata>('/diagnosis/metadata', {
      method: 'GET',
    });
  },

  async runDiagnosis(
    file: File,
    modality: ModalityType,
    symptoms: Record<string, boolean>
  ): Promise<DiagnosisInferResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('modality', modality);
    formData.append('symptoms', JSON.stringify(symptoms));

    return apiClient<DiagnosisInferResponse>('/diagnosis/infer', {
      method: 'POST',
      data: formData,
    });
  },

  async getHistory(
    page: number = 1,
    pageSize: number = 10,
    modality?: string
  ): Promise<PaginatedHistory> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (modality && modality.trim()) {
      params.append('modality', modality.trim());
    }

    return apiClient<PaginatedHistory>(`/diagnosis/history?${params.toString()}`, {
      method: 'GET',
    });
  },

  async getRecord(id: number): Promise<DiagnosisRecord> {
    return apiClient<DiagnosisRecord>(`/diagnosis/history/${id}`, {
      method: 'GET',
    });
  },

  async deleteRecord(id: number): Promise<void> {
    return apiClient<void>(`/diagnosis/history/${id}`, {
      method: 'DELETE',
    });
  },

  async getStats(): Promise<DashboardStats> {
    return apiClient<DashboardStats>('/diagnosis/stats', {
      method: 'GET',
    });
  },
};
