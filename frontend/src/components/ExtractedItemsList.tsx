import React from 'react';
import { ItemEditForm } from './ItemEditForm';

interface ExtractedItem {
  product_id: string;
  product_name: string;
  quantity: number;
  unit: string;
  confidence: number;
  original_text: string;
}

interface ExtractedItemsListProps {
  items: ExtractedItem[];
  onUpdateItem: (index: number, updates: Partial<ExtractedItem>) => void;
  onRemoveItem: (index: number) => void;
}

export const ExtractedItemsList: React.FC<ExtractedItemsListProps> = ({
  items,
  onUpdateItem,
  onRemoveItem,
}) => {
  if (items.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">ไม่พบรายการสินค้า</h3>
        <p className="mt-1 text-sm text-gray-500">
          ไม่สามารถสกัดรายการสินค้าจากใบเสร็จได้
        </p>
      </div>
    );
  }

  const lowConfidenceCount = items.filter((item) => item.confidence < 0.8).length;

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">รายการสินค้าที่สกัดได้</h2>
        <p className="mt-1 text-sm text-gray-600">
          ตรวจสอบและแก้ไขข้อมูลก่อนยืนยัน ({items.length} รายการ)
        </p>
        {lowConfidenceCount > 0 && (
          <div className="mt-2 flex items-center text-sm text-yellow-700 bg-yellow-50 px-3 py-2 rounded-md">
            <svg
              className="w-5 h-5 mr-2"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            มี {lowConfidenceCount} รายการที่ต้องตรวจสอบ (ความมั่นใจต่ำกว่า 80%)
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ข้อความจากใบเสร็จ
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                สินค้า
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                จำนวน
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                หน่วย
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ความมั่นใจ
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ลบ
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {items.map((item, index) => (
              <React.Fragment key={index}>
                <ItemEditForm
                  item={item}
                  index={index}
                  onUpdate={onUpdateItem}
                />
                <tr>
                  <td colSpan={5}></td>
                  <td className="px-4 py-3 border-b">
                    <button
                      onClick={() => onRemoveItem(index)}
                      className="text-red-600 hover:text-red-800"
                      title="ลบรายการนี้"
                    >
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
                  </td>
                </tr>
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
