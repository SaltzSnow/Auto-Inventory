import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useTaskStatus, TaskStatus } from '../hooks/useReceiptUpload';
import { useConfirmation } from '../hooks/useConfirmation';
import { ExtractedItemsList } from '../components/ExtractedItemsList';
import { Toast } from '../components/Toast';
import { API_BASE_URL } from '../services/api';

interface ExtractedItem {
  product_id: string;
  product_name: string;
  quantity: number;
  unit: string;
  confidence: number;
  original_text: string;
}

export const ConfirmationPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: taskStatus, isLoading } = useTaskStatus(taskId || null, !!taskId) as { data: TaskStatus | undefined; isLoading: boolean };
  const { confirmReceipt } = useConfirmation();

  const [items, setItems] = useState<ExtractedItem[]>([]);
  const [receiptImageUrl, setReceiptImageUrl] = useState<string>('');
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState<'success' | 'error' | 'info'>('success');

  const resolveImageUrl = (url: string): string => {
    if (!url) return '';
    if (/^https?:\/\//i.test(url)) {
      return url;
    }
    try {
      const base = API_BASE_URL.endsWith('/') ? API_BASE_URL : `${API_BASE_URL}/`;
      return new URL(url, base).toString();
    } catch (error) {
      console.error('Failed to resolve image URL', error);
      return url;
    }
  };

  useEffect(() => {
    if (taskStatus?.result?.items) {
      setItems(taskStatus.result.items);
      setReceiptImageUrl(taskStatus.result.image_url || '');
    }
  }, [taskStatus]);

  const handleUpdateItem = (index: number, updates: Partial<ExtractedItem>) => {
    setItems((prevItems) =>
      prevItems.map((item, i) => (i === index ? { ...item, ...updates } : item))
    );
  };

  const handleRemoveItem = (index: number) => {
    setItems((prevItems) => prevItems.filter((_, i) => i !== index));
  };

  const handleConfirm = async () => {
    if (!taskStatus?.result?.receipt_id || items.length === 0) return;

    try {
      const validatedItems = items.map((item) => ({
        product_id: item.product_id,
        product_name: item.product_name,
        quantity: item.quantity,
        unit: item.unit,
        original_text: item.original_text,
      }));

      const response = await confirmReceipt.mutateAsync({
        receipt_id: taskStatus.result.receipt_id,
        items: validatedItems,
      });

      // Invalidate queries to refresh data on Dashboard and Inventory pages
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['products'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard'] }),
      ]);

      // Show success toast
      setToastMessage(`อัปเดตสต็อกสำเร็จ! อัปเดต ${response.total_items} รายการ`);
      setToastType('success');
      setShowToast(true);

      // Navigate to dashboard after a short delay
      setTimeout(() => {
        navigate('/');
      }, 2000);
    } catch (error: any) {
      console.error('Confirmation failed:', error);
      
      // Show error toast
      const errorMessage = error.response?.data?.message || 'เกิดข้อผิดพลาดในการอัปเดตสต็อก';
      setToastMessage(errorMessage);
      setToastType('error');
      setShowToast(true);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <svg
              className="animate-spin h-12 w-12 text-blue-600 mx-auto"
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
            <p className="mt-4 text-gray-600">กำลังโหลดข้อมูล...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!taskStatus || taskStatus.status !== 'completed') {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <svg
              className="h-5 w-5 text-yellow-400"
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
              <h3 className="text-sm font-medium text-yellow-800">ไม่พบข้อมูล</h3>
              <p className="mt-1 text-sm text-yellow-700">
                ไม่พบข้อมูลการประมวลผล หรือการประมวลผลยังไม่เสร็จสิ้น
              </p>
              <button
                onClick={() => navigate('/upload')}
                className="mt-3 text-sm font-medium text-yellow-800 hover:text-yellow-900"
              >
                กลับไปหน้าอัปโหลด →
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {showToast && (
        <Toast
          message={toastMessage}
          type={toastType}
          onClose={() => setShowToast(false)}
        />
      )}

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">ยืนยันข้อมูล</h1>
        <p className="mt-2 text-gray-600">
          ตรวจสอบและแก้ไขข้อมูลที่ AI สกัดได้ก่อนอัปเดตสต็อก
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Receipt Image */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-4 sticky top-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">ใบเสร็จ</h3>
            {receiptImageUrl ? (
              <img
                src={resolveImageUrl(receiptImageUrl)}
                alt="Receipt"
                loading="lazy"
                className="w-full h-auto rounded-lg border border-gray-200"
              />
            ) : (
              <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                <p className="text-gray-500">ไม่มีรูปภาพ</p>
              </div>
            )}
          </div>
        </div>

        {/* Extracted Items */}
        <div className="lg:col-span-2">
          <ExtractedItemsList
            items={items}
            onUpdateItem={handleUpdateItem}
            onRemoveItem={handleRemoveItem}
          />

          {/* Error Message */}
          {confirmReceipt.isError && !showToast && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
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
                  <p className="mt-1 text-sm text-red-700">
                    ไม่สามารถอัปเดตสต็อกได้ กรุณาลองใหม่อีกครั้ง
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-6 flex justify-end space-x-4">
            <button
              onClick={() => navigate('/upload')}
              disabled={confirmReceipt.isPending}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ยกเลิก
            </button>
            <button
              onClick={handleConfirm}
              disabled={items.length === 0 || confirmReceipt.isPending}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {confirmReceipt.isPending ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
                  กำลังอัปเดต...
                </>
              ) : (
                'ยืนยันและอัปเดตสต็อก'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
