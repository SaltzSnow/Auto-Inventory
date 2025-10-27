import React from 'react';

interface ProcessingStatusProps {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  currentStep: string;
  error?: string;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  status,
  progress,
  currentStep,
  error,
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'processing':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'pending':
        return 'รอการประมวลผล';
      case 'processing':
        return 'กำลังประมวลผล';
      case 'completed':
        return 'ประมวลผลสำเร็จ';
      case 'failed':
        return 'เกิดข้อผิดพลาด';
      default:
        return 'ไม่ทราบสถานะ';
    }
  };

  const getStepText = (step: string) => {
    switch (step) {
      case 'vision_extraction':
        return 'กำลังอ่านข้อมูลจากใบเสร็จ';
      case 'matching':
        return 'กำลังจับคู่สินค้า';
      case 'validation':
        return 'กำลังตรวจสอบและแปลงหน่วย';
      case 'done':
        return 'เสร็จสิ้น';
      default:
        return step;
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto bg-white rounded-lg shadow-md p-6">
      <div className="space-y-4">
        {/* Status Header */}
        <div className="flex items-center justify-between">
          <h3 className={`text-lg font-semibold ${getStatusColor()}`}>
            {getStatusText()}
          </h3>
          <span className="text-sm text-gray-500">{progress}%</span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all duration-300 ${
              status === 'failed' ? 'bg-red-600' : 'bg-blue-600'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Current Step */}
        {status === 'processing' && (
          <div className="flex items-center space-x-2">
            <svg
              className="animate-spin h-5 w-5 text-blue-600"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <p className="text-sm text-gray-700">{getStepText(currentStep)}</p>
          </div>
        )}

        {/* Success Message */}
        {status === 'completed' && (
          <div className="flex items-center space-x-2 text-green-600">
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <p className="text-sm">ประมวลผลเสร็จสิ้น กำลังนำไปยังหน้ายืนยันข้อมูล...</p>
          </div>
        )}

        {/* Error Message */}
        {status === 'failed' && error && (
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
                <h3 className="text-sm font-medium text-red-800">เกิดข้อผิดพลาด</h3>
                <p className="mt-1 text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
