import React, { useState, useEffect } from 'react';
import {
  History as HistoryIcon,
  Eye,
  Trash2,
  ChevronLeft,
  ChevronRight,
  AlertCircle
} from 'lucide-react';
import { diagnosisService } from '../services/diagnosis';
import { DiagnosisRecord, PaginatedHistory } from '../types';
import { formatDate, formatModality, formatPercent, getConfidenceBadgeClass } from '../utils/formatters';
import { ViewRecordModal } from '../components/ViewRecordModal';
import { DeleteModal } from '../components/DeleteModal';
import { EmptyState } from '../components/EmptyState';

export const History: React.FC = () => {
  const [data, setData] = useState<PaginatedHistory>({
    records: [],
    total: 0,
    page: 1,
    page_size: 10,
    total_pages: 0,
  });

  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [modalityFilter, setModalityFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Modals state
  const [viewingRecord, setViewingRecord] = useState<DiagnosisRecord | null>(null);
  const [deletingRecord, setDeletingRecord] = useState<DiagnosisRecord | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await diagnosisService.getHistory(page, pageSize, modalityFilter);
      setData(response);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve diagnosis audit history.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page, modalityFilter]);

  const handleDeleteConfirm = async () => {
    if (!deletingRecord) return;
    setIsDeleting(true);
    try {
      await diagnosisService.deleteRecord(deletingRecord.id);
      setDeletingRecord(null);
      // If we deleted the only item on the current page and page > 1, go back one page
      if (data.records.length === 1 && page > 1) {
        setPage(page - 1);
      } else {
        await fetchHistory();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete record.';
      setError(msg);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <HistoryIcon className="w-6 h-6 text-sky-700" />
            Clinical Diagnosis History & Audit
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 mt-1">
            Permanent audit trail of all medical scans, symptoms, predictions, and Grad-CAM explainability maps.
          </p>
        </div>

        {/* Modality Filter Pills */}
        <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1 text-xs font-medium text-slate-600 self-start sm:self-auto">
          <button
            type="button"
            onClick={() => {
              setModalityFilter('');
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              modalityFilter === ''
                ? 'bg-white text-sky-900 shadow-xs font-semibold'
                : 'hover:text-slate-900'
            }`}
          >
            All Modalities ({data.total})
          </button>
          <button
            type="button"
            onClick={() => {
              setModalityFilter('chest_xray');
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              modalityFilter === 'chest_xray'
                ? 'bg-white text-sky-900 shadow-xs font-semibold'
                : 'hover:text-slate-900'
            }`}
          >
            Chest X-Ray
          </button>
          <button
            type="button"
            onClick={() => {
              setModalityFilter('brain_mri');
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              modalityFilter === 'brain_mri'
                ? 'bg-white text-sky-900 shadow-xs font-semibold'
                : 'hover:text-slate-900'
            }`}
          >
            Brain MRI
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Table Container */}
      {loading ? (
        <div className="bg-white border border-slate-200 rounded-xl p-8 space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-slate-100 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : data.total === 0 ? (
        <EmptyState
          title="No diagnosis history available."
          description={
            modalityFilter
              ? `No diagnosis records found for ${formatModality(modalityFilter)}. Change filter or run a new scan.`
              : 'No diagnosis records exist in your account. Start your first analysis to build an audit history.'
          }
        />
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th scope="col" className="px-6 py-3.5">
                    Scan ID & Date
                  </th>
                  <th scope="col" className="px-6 py-3.5">
                    Modality
                  </th>
                  <th scope="col" className="px-6 py-3.5">
                    Model Prediction
                  </th>
                  <th scope="col" className="px-6 py-3.5">
                    Confidence
                  </th>
                  <th scope="col" className="px-6 py-3.5">
                    Version
                  </th>
                  <th scope="col" className="px-6 py-3.5 text-right">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {data.records.map((record) => (
                  <tr key={record.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-semibold text-slate-900 font-mono text-xs">
                        #{record.id}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        {formatDate(record.created_at)}
                      </div>
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-sm text-[11px] font-semibold bg-slate-100 text-slate-800">
                        {formatModality(record.modality)}
                      </span>
                      <span className="block text-[11px] text-slate-400 font-mono truncate max-w-[150px] mt-0.5">
                        {record.original_filename}
                      </span>
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-bold text-slate-900 text-sm">
                        {record.predicted_class}
                      </span>
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-sm font-mono text-xs font-bold border ${getConfidenceBadgeClass(
                          record.confidence
                        )}`}
                      >
                        {formatPercent(record.confidence)}
                      </span>
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap text-slate-500 font-mono text-[11px]">
                      {record.model_version}
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap text-right space-x-2">
                      <button
                        type="button"
                        onClick={() => setViewingRecord(record)}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium text-sky-700 bg-sky-50 hover:bg-sky-100 transition-colors"
                        title="View Full Diagnosis & Grad-CAM"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        View
                      </button>

                      <button
                        type="button"
                        onClick={() => setDeletingRecord(record)}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium text-rose-700 bg-rose-50 hover:bg-rose-100 transition-colors"
                        title="Delete Record"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {data.total_pages > 1 && (
            <div className="flex items-center justify-between px-6 py-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-600">
              <div>
                Showing page <span className="font-semibold text-slate-900">{data.page}</span> of{' '}
                <span className="font-semibold text-slate-900">{data.total_pages}</span> ({data.total} total records)
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={data.page <= 1}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-slate-300 bg-white font-medium hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                  disabled={data.page >= data.total_pages}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-slate-300 bg-white font-medium hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* View Detail Modal */}
      <ViewRecordModal
        record={viewingRecord}
        onClose={() => setViewingRecord(null)}
      />

      {/* Delete Confirmation Modal */}
      <DeleteModal
        isOpen={!!deletingRecord}
        onClose={() => setDeletingRecord(null)}
        onConfirm={handleDeleteConfirm}
        isDeleting={isDeleting}
        recordTitle={
          deletingRecord
            ? `Record #${deletingRecord.id} — ${formatModality(deletingRecord.modality)} (${deletingRecord.predicted_class})`
            : undefined
        }
      />
    </div>
  );
};
