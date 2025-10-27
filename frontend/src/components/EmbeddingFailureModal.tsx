import React from 'react';

interface EmbeddingFailureModalProps {
  message: string;
  details: {
    product_name: string;
    error: string;
    can_force_create?: boolean;
  };
  onConfirm: () => void;
  onCancel: () => void;
}

export const EmbeddingFailureModal: React.FC<EmbeddingFailureModalProps> = ({
  message,
  details,
  onConfirm,
  onCancel,
}) => {
  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-[60]">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          {/* Warning Icon */}
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100">
            <svg
              className="h-6 w-6 text-yellow-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>

          {/* Title */}
          <h3 className="text-lg font-medium leading-6 text-gray-900 text-center mt-4 mb-2">
            ⚠️ ไม่สามารถสร้าง Embedding ได้
          </h3>

          {/* Message */}
          <div className="mt-4 px-7 py-3">
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
              <p className="text-sm text-yellow-800 whitespace-pre-wrap">
                {message}
              </p>
            </div>

            {/* Details */}
            <div className="bg-gray-50 border border-gray-200 rounded-md p-4 mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">
                รายละเอียดเพิ่มเติม:
              </h4>
              <div className="space-y-2 text-sm text-gray-600">
                <p>
                  <span className="font-medium">สินค้า:</span> {details.product_name}
                </p>
                <div>
                  <span className="font-medium">Error:</span>
                  <pre className="mt-1 text-xs bg-white p-2 rounded border border-gray-200 overflow-x-auto">
                    {details.error}
                  </pre>
                </div>
              </div>
            </div>

            {/* Warning Message */}
            <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
              <p className="text-sm text-red-800">
                <strong>⚠️ คำเตือน:</strong> หากสร้างสินค้าโดยไม่มี embedding:
              </p>
              <ul className="mt-2 text-sm text-red-700 list-disc list-inside space-y-1">
                <li>ฟีเจอร์ค้นหาด้วย AI จะไม่ทำงานกับสินค้านี้</li>
                <li>ระบบจะไม่สามารถจับคู่สินค้าจากใบเสร็จโดยอัตโนมัติได้</li>
                <li>ยังสามารถค้นหาด้วยชื่อปกติได้</li>
              </ul>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex justify-end space-x-3 px-7 pb-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            >
              ยกเลิก
            </button>
            {details.can_force_create && (
              <button
                onClick={onConfirm}
                className="px-4 py-2 text-sm font-medium text-white bg-yellow-600 border border-transparent rounded-md hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
              >
                ดำเนินการต่อแบบไม่มี Embedding
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
