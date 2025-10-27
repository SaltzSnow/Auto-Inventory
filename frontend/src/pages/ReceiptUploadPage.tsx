import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileDropzone } from '../components/FileDropzone';
import { ProcessingStatus } from '../components/ProcessingStatus';
import { useReceiptUpload, useTaskStatus } from '../hooks/useReceiptUpload';
import type { TaskStatus } from '../hooks/useReceiptUpload';

export const ReceiptUploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [taskId, setTaskId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const { uploadReceipt } = useReceiptUpload();
  const { data: taskStatus, isLoading: isPolling } = useTaskStatus(taskId, !!taskId) as { data: TaskStatus | undefined; isLoading: boolean };

  // Handle file selection
  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    
    // Create preview URL
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  // Handle upload
  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      const response = await uploadReceipt.mutateAsync(selectedFile);
      setTaskId(response.task_id);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  // Handle reset
  const handleReset = () => {
    setTaskId(null);
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    uploadReceipt.reset();
  };

  // Auto-redirect when completed
  useEffect(() => {
    if (taskStatus?.status === 'completed' && taskStatus.result) {
      // Navigate to confirmation page with task_id
      setTimeout(() => {
        navigate(`/confirm/${taskId}`);
      }, 1500);
    }
  }, [taskStatus, taskId, navigate]);

  // Cleanup preview URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const isProcessing = !!taskId && taskStatus?.status !== 'failed';

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">อัปโหลดใบเสร็จ</h1>
        <p className="mt-2 text-gray-600">
          อัปโหลดรูปภาพใบเสร็จเพื่อให้ AI อ่านและอัปเดตสต็อกสินค้าอัตโนมัติ
        </p>
      </div>

      {!taskId ? (
        <div className="space-y-6">
          <FileDropzone
            onFileSelect={handleFileSelect}
            disabled={uploadReceipt.isPending}
          />

          {selectedFile && previewUrl && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">ตัวอย่างรูปภาพ</h3>
              <div className="flex items-start space-x-6">
                <img
                  src={previewUrl}
                  alt="Receipt preview"
                  className="w-64 h-auto rounded-lg border border-gray-200"
                />
                <div className="flex-1 space-y-4">
                  <div>
                    <p className="text-sm text-gray-600">ชื่อไฟล์</p>
                    <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">ขนาดไฟล์</p>
                    <p className="text-sm font-medium text-gray-900">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <div className="flex space-x-3">
                    <button
                      onClick={handleUpload}
                      disabled={uploadReceipt.isPending}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {uploadReceipt.isPending ? 'กำลังอัปโหลด...' : 'เริ่มประมวลผล'}
                    </button>
                    <button
                      onClick={handleReset}
                      disabled={uploadReceipt.isPending}
                      className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      ยกเลิก
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {uploadReceipt.isError && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <svg
                  className="h-5 w-5 text-red-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">ไม่สามารถอัปโหลดไฟล์ได้</h3>
                  <p className="mt-1 text-sm text-red-700">
                    กรุณาลองใหม่อีกครั้ง หรือติดต่อผู้ดูแลระบบ
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          <ProcessingStatus
            status={taskStatus?.status || 'pending'}
            progress={taskStatus?.progress || 0}
            currentStep={taskStatus?.current_step || ''}
            error={taskStatus?.error}
          />

          {taskStatus?.status === 'failed' && (
            <div className="flex justify-center">
              <button
                onClick={handleReset}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                อัปโหลดใหม่
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
