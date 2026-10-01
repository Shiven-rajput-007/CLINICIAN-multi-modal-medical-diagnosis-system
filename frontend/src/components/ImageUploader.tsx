import React, { useState, useRef, ChangeEvent, DragEvent } from 'react';
import { UploadCloud, Image as ImageIcon, X, AlertCircle } from 'lucide-react';
import { formatBytes } from '../utils/formatters';

interface ImageUploaderProps {
  selectedFile: File | null;
  onFileSelect: (file: File | null) => void;
  maxSizeMB?: number;
}

const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg'];

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  selectedFile,
  onFileSelect,
  maxSizeMB = 15,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (file: File) => {
    setError(null);

    // Validate type
    if (!ALLOWED_TYPES.includes(file.type)) {
      setError('Unsupported file type. Please upload a PNG, JPG, or JPEG medical scan.');
      return;
    }

    // Validate size
    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`File size exceeds ${maxSizeMB}MB limit. Current size: ${formatBytes(file.size)}.`);
      return;
    }

    onFileSelect(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleRemove = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    onFileSelect(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-3">
      <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600">
        Clinical Imaging Scan (DICOM Export / PNG / JPG)
      </label>

      {error && (
        <div className="flex items-center gap-2 p-3 text-xs text-rose-800 bg-rose-50 border border-rose-200 rounded-md">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {!selectedFile ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${
            isDragging
              ? 'border-sky-500 bg-sky-50/60'
              : 'border-slate-300 hover:border-slate-400 bg-white'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".png,.jpg,.jpeg"
            className="hidden"
            onChange={handleFileInputChange}
          />
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500 mb-3">
            <UploadCloud className="w-6 h-6 text-slate-600" />
          </div>
          <p className="text-sm font-medium text-slate-700">
            Click to upload scan or drag and drop
          </p>
          <p className="mt-1 text-xs text-slate-500">
            PNG, JPG, or JPEG (Max: {maxSizeMB}MB)
          </p>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
          <div className="flex flex-col sm:flex-row items-center gap-4">
            {previewUrl && (
              <div className="relative w-28 h-28 bg-slate-900 rounded-lg overflow-hidden border border-slate-700 shrink-0 flex items-center justify-center">
                <img
                  src={previewUrl}
                  alt="Scan Preview"
                  className="w-full h-full object-contain"
                />
              </div>
            )}
            <div className="flex-1 min-w-0 text-center sm:text-left">
              <div className="flex items-center gap-2 justify-center sm:justify-start">
                <ImageIcon className="w-4 h-4 text-sky-600 shrink-0" />
                <h4 className="text-sm font-semibold text-slate-900 truncate">
                  {selectedFile.name}
                </h4>
              </div>
              <p className="text-xs text-slate-500 mt-1 font-mono">
                Size: {formatBytes(selectedFile.size)} • Type: {selectedFile.type || 'image/png'}
              </p>
              <div className="mt-3 flex items-center gap-2 justify-center sm:justify-start">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-xs font-medium text-sky-700 hover:text-sky-800 underline"
                >
                  Change scan
                </button>
                <span className="text-slate-300">•</span>
                <button
                  type="button"
                  onClick={handleRemove}
                  className="text-xs font-medium text-rose-600 hover:text-rose-700 flex items-center gap-1"
                >
                  <X className="w-3.5 h-3.5" /> Remove
                </button>
              </div>
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".png,.jpg,.jpeg"
            className="hidden"
            onChange={handleFileInputChange}
          />
        </div>
      )}
    </div>
  );
};
