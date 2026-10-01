export function formatPercent(value: number, decimals: number = 1): string {
  if (value === undefined || value === null || isNaN(value)) return '0.0%';
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatDate(dateString: string): string {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(d);
  } catch {
    return dateString;
  }
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function formatModality(modality: string): string {
  if (modality === 'chest_xray') return 'Chest X-Ray';
  if (modality === 'brain_mri') return 'Brain MRI';
  return modality;
}

export function getConfidenceBadgeClass(confidence: number): string {
  if (confidence >= 0.80) {
    return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (confidence >= 0.50) {
    return 'bg-amber-50 text-amber-700 border-amber-200';
  } else {
    return 'bg-rose-50 text-rose-700 border-rose-200';
  }
}
