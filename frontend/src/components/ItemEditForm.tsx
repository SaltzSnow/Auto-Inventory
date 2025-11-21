import React from 'react';
import { ProductDropdown } from './ProductDropdown';

interface ExtractedItem {
  product_id: string;
  product_name: string;
  quantity: number;
  unit: string;
  confidence: number;
  original_text: string;
}

interface ItemEditFormProps {
  item: ExtractedItem;
  index: number;
  onUpdate: (index: number, updates: Partial<ExtractedItem>) => void;
}

export const ItemEditForm: React.FC<ItemEditFormProps> = ({ item, index, onUpdate }) => {
  const isLowConfidence = item.confidence < 0.7;

  return (
    <tr className={isLowConfidence ? 'bg-yellow-50' : ''}>
      <td className="px-4 py-3 text-sm text-gray-700 border-b">
        {isLowConfidence && (
          <div className="flex items-center mb-1">
            <svg
              className="w-4 h-4 text-yellow-500 mr-1"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-xs text-yellow-700">ความมั่นใจต่ำ - กรุณาตรวจสอบ</span>
          </div>
        )}
        <div className="font-medium text-gray-900">{item.original_text}</div>
      </td>

      <td className="px-4 py-3 border-b">
        <div className="space-y-2">
          {/* Display matched product name */}
          <div className="flex items-center">
            <svg
              className="w-4 h-4 text-green-500 mr-2 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="font-medium text-gray-900">{item.product_name}</span>
          </div>
          
          {/* Optional: Allow changing product */}
          <div className="text-xs">
            <ProductDropdown
              value={item.product_id}
              onChange={(productId, productName, unit) => {
                onUpdate(index, {
                  product_id: productId,
                  product_name: productName,
                  unit: unit,
                });
              }}
            />
          </div>
        </div>
      </td>

      <td className="px-4 py-3 border-b">
        <input
          type="number"
          min="1"
          value={item.quantity}
          onChange={(e) => {
            const value = parseInt(e.target.value, 10);
            if (!isNaN(value) && value > 0) {
              onUpdate(index, { quantity: value });
            }
          }}
          className="w-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </td>

      <td className="px-4 py-3 text-sm text-gray-700 border-b">
        {item.unit}
      </td>

      <td className="px-4 py-3 border-b">
        <div className="flex items-center">
          <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
            <div
              className={`h-2 rounded-full ${
                item.confidence >= 0.7 ? 'bg-green-500' : 'bg-yellow-500'
              }`}
              style={{ width: `${item.confidence * 100}%` }}
            />
          </div>
          <span className="text-sm text-gray-600">
            {(item.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </td>
    </tr>
  );
};
