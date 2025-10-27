import React, { useState } from 'react';
import { Transaction } from '../types/transaction';
import { ReceiptImageViewer } from './ReceiptImageViewer';

interface TransactionDetailModalProps {
  transaction: Transaction | null;
  isOpen: boolean;
  onClose: () => void;
}

export const TransactionDetailModal: React.FC<TransactionDetailModalProps> = ({
  transaction,
  isOpen,
  onClose,
}) => {
  const [isImageViewerOpen, setIsImageViewerOpen] = useState(false);

  if (!isOpen || !transaction) return null;

  const receiptImageUrl = `http://localhost:8000/api/receipts/image/${transaction.receipt_id}`;

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('th-TH', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <>
      <div
        className="fixed inset-0 z-40 flex items-center justify-center bg-black bg-opacity-50"
        onClick={onClose}
      >
        <div
          className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">
              รายละเอียดการทำรายการ
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              aria-label="ปิด"
            >
              ×
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Transaction Info */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  ข้อมูลการทำรายการ
                </h3>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      รหัสรายการ
                    </dt>
                    <dd className="text-sm text-gray-900 font-mono">
                      {transaction.id}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      วันที่-เวลา
                    </dt>
                    <dd className="text-sm text-gray-900">
                      {formatDate(transaction.created_at)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      จำนวนรายการสินค้า
                    </dt>
                    <dd className="text-sm text-gray-900">
                      {transaction.total_items} รายการ
                    </dd>
                  </div>
                </dl>
              </div>

              {/* Receipt Image */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  ใบเสร็จ
                </h3>
                <div
                  className="border border-gray-300 rounded-lg overflow-hidden cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => setIsImageViewerOpen(true)}
                >
                  <img
                    src={receiptImageUrl}
                    alt="ใบเสร็จ"
                    loading="lazy"
                    className="w-full h-48 object-cover"
                  />
                  <div className="bg-gray-50 px-3 py-2 text-center">
                    <span className="text-sm text-gray-600">
                      คลิกเพื่อดูขนาดเต็ม
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Items Table */}
            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                รายการสินค้า
              </h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        ชื่อสินค้า
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        จำนวน
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        หน่วย
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        ข้อความจากใบเสร็จ
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {transaction.items.map((item) => (
                      <tr key={item.id}>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {item.product_name}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {item.quantity}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {item.unit}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {item.original_text}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
            >
              ปิด
            </button>
          </div>
        </div>
      </div>

      {/* Receipt Image Viewer */}
      <ReceiptImageViewer
        imageUrl={receiptImageUrl}
        isOpen={isImageViewerOpen}
        onClose={() => setIsImageViewerOpen(false)}
      />
    </>
  );
};
