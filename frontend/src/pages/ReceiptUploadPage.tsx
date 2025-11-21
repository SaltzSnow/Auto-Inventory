import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileDropzone } from '../components/FileDropzone';
import { useReceiptUpload, useTaskStatus } from '../hooks/useReceiptUpload';
import type { TaskStatus } from '../hooks/useReceiptUpload';

type SelectedFile = {
  key: string;
  file: File;
  previewUrl: string;
};

type TaskRecord = {
  taskId: string;
  fileName: string;
};

const statusLabels: Record<string, string> = {
  pending: 'รอประมวลผล',
  processing: 'กำลังประมวลผล',
  completed: 'เสร็จสิ้น',
  failed: 'ล้มเหลว',
  unknown: 'ไม่ทราบสถานะ',
};

const TASK_STORAGE_KEY = 'receiptTaskRecords';

export const ReceiptUploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { uploadReceipt } = useReceiptUpload();
  const [selectedFiles, setSelectedFiles] = useState<SelectedFile[]>([]);
  const [taskRecords, setTaskRecords] = useState<TaskRecord[]>(() => {
    try {
      const stored = localStorage.getItem(TASK_STORAGE_KEY);
      if (!stored) return [];
      const parsed: TaskRecord[] = JSON.parse(stored);
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.warn('Failed to parse stored tasks', error);
      return [];
    }
  });
  const [batchError, setBatchError] = useState<string | null>(null);
  const [isUploadingBatch, setIsUploadingBatch] = useState(false);
  const selectedFilesRef = useRef<SelectedFile[]>([]);

  const handleFilesSelect = useCallback((files: File[]) => {
    setSelectedFiles((prev) => {
      const existingKeys = new Set(prev.map((item) => item.key));
      const additions: SelectedFile[] = [];

      files.forEach((file) => {
        const key = `${file.name}-${file.lastModified}-${file.size}`;
        if (existingKeys.has(key)) {
          return;
        }
        const previewUrl = URL.createObjectURL(file);
        additions.push({ key, file, previewUrl });
        existingKeys.add(key);
      });

      return [...prev, ...additions];
    });
  }, []);

  const handleRemoveFile = useCallback((key: string) => {
    setSelectedFiles((prev) => {
      const target = prev.find((item) => item.key === key);
      if (target) {
        URL.revokeObjectURL(target.previewUrl);
      }
      return prev.filter((item) => item.key !== key);
    });
  }, []);

  const handleClearSelected = () => {
    selectedFiles.forEach((item) => URL.revokeObjectURL(item.previewUrl));
    setSelectedFiles([]);
  };

  const handleUploadAll = async () => {
    if (!selectedFiles.length) return;

    setIsUploadingBatch(true);
    setBatchError(null);
    const queued = [...selectedFiles];

    for (const entry of queued) {
      try {
        const response = await uploadReceipt.mutateAsync(entry.file);
        setTaskRecords((prev) => {
          const exists = prev.some((r) => r.taskId === response.task_id);
          if (exists) return prev;
          return [
            ...prev,
            {
              taskId: response.task_id,
              fileName: entry.file.name,
            },
          ];
        });
      } catch (error: any) {
        console.error('Upload failed:', error);
        const message = error?.response?.data?.detail || 'เกิดข้อผิดพลาดในการอัปโหลด';
        setBatchError(`${entry.file.name}: ${message}`);
      }
    }

    handleClearSelected();
    setIsUploadingBatch(false);
  };

  useEffect(() => {
    selectedFilesRef.current = selectedFiles;
  }, [selectedFiles]);

  useEffect(() => {
    try {
      if (taskRecords.length === 0) {
        localStorage.removeItem(TASK_STORAGE_KEY);
      } else {
        localStorage.setItem(TASK_STORAGE_KEY, JSON.stringify(taskRecords));
      }
    } catch (error) {
      console.warn('Failed to persist tasks', error);
    }
  }, [taskRecords]);

  // Cleanup preview URLs on unmount
  useEffect(() => {
    return () => {
      selectedFilesRef.current.forEach((item) => {
        URL.revokeObjectURL(item.previewUrl);
      });
    };
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">อัปโหลดใบเสร็จ</h1>
        <p className="mt-2 text-gray-600">
          อัปโหลดรูปภาพใบเสร็จเพื่อให้ AI อ่านและอัปเดตสต็อกสินค้าอัตโนมัติ
        </p>
      </div>

      <div className="space-y-6">
        <FileDropzone
          onFilesSelect={handleFilesSelect}
          disabled={isUploadingBatch || uploadReceipt.isPending}
        />

        {selectedFiles.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">ไฟล์ที่เลือก ({selectedFiles.length})</h3>
              <button
                onClick={handleClearSelected}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                ล้างรายการ
              </button>
            </div>
            <div className="mt-4 space-y-3 max-h-80 overflow-y-auto">
              {selectedFiles.map((item) => (
                <div
                  key={item.key}
                  className="flex items-center justify-between border rounded-md p-3"
                >
                  <div className="flex items-center space-x-4">
                    <img
                      src={item.previewUrl}
                      alt={item.file.name}
                      className="w-16 h-16 object-cover rounded"
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{item.file.name}</p>
                      <p className="text-xs text-gray-500">{(item.file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemoveFile(item.key)}
                    className="text-sm text-red-500 hover:text-red-700"
                  >
                    ลบ
                  </button>
                </div>
              ))}
            </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={handleUploadAll}
                disabled={isUploadingBatch || uploadReceipt.isPending}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploadingBatch ? 'กำลังอัปโหลด...' : `อัปโหลด ${selectedFiles.length} ไฟล์`}
              </button>
            </div>
          </div>
        )}

        {batchError && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-700">{batchError}</p>
          </div>
        )}

        <TaskStatusBoard
          taskRecords={taskRecords}
          onViewResult={(taskId) => navigate(`/confirm/${taskId}`)}
          onClearAll={() => setTaskRecords([])}
        />
      </div>
    </div>
  );
};

const TaskStatusBoard: React.FC<{
  taskRecords: TaskRecord[];
  onViewResult: (taskId: string) => void;
  onClearAll: () => void;
}> = ({ taskRecords, onViewResult, onClearAll }) => {
  if (!taskRecords.length) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">สถานะการประมวลผล ({taskRecords.length})</h3>
        <button
          onClick={onClearAll}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ล้างรายการ
        </button>
      </div>
      <div className="space-y-4">
        {taskRecords.map((record) => (
          <TaskStatusCard
            key={record.taskId}
            record={record}
            onViewResult={() => onViewResult(record.taskId)}
          />
        ))}
      </div>
    </div>
  );
};

const TaskStatusCard: React.FC<{
  record: TaskRecord;
  onViewResult: () => void;
}> = ({ record, onViewResult }) => {
  const { data: taskStatus } = useTaskStatus(record.taskId, true) as { data: TaskStatus | undefined };
  const statusKey = taskStatus?.status || 'pending';
  const progress = taskStatus?.progress ?? 0;

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-sm font-medium text-gray-900">{record.fileName}</p>
          <p className="text-xs text-gray-500">Task ID: {record.taskId}</p>
        </div>
        <span className="text-sm text-gray-600">{statusLabels[statusKey] || statusLabels.unknown}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className={`h-2.5 rounded-full ${statusKey === 'failed' ? 'bg-red-500' : 'bg-blue-600'}`}
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>
      <div className="mt-3 flex justify-between items-center">
        <p className="text-xs text-gray-500">
          ขั้นตอน: {taskStatus?.current_step || '-'} | ความคืบหน้า: {progress}%
        </p>
        <button
          onClick={onViewResult}
          disabled={taskStatus?.status !== 'completed'}
          className="text-sm text-blue-600 hover:text-blue-800 disabled:text-gray-400 disabled:cursor-not-allowed"
        >
          ดูผลลัพธ์
        </button>
      </div>
      {taskStatus?.error && (
        <p className="mt-2 text-xs text-red-600">ข้อผิดพลาด: {taskStatus.error}</p>
      )}
    </div>
  );
};
