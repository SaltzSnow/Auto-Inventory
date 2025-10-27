import React from 'react';
import { Product } from '../types/product';

interface ProductDetailModalProps {
  product: Product;
  onClose: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export const ProductDetailModal: React.FC<ProductDetailModalProps> = ({
  product,
  onClose,
  onEdit,
  onDelete,
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('th-TH', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const isLowStock = product.quantity < product.reorder_point;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-lg shadow-lg rounded-md bg-white">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-xl font-semibold text-gray-900">
            รายละเอียดสินค้า
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-500">
              ชื่อสินค้า
            </label>
            <p className="mt-1 text-lg text-gray-900">{product.name}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-500">
                หน่วยนับ
              </label>
              <p className="mt-1 text-gray-900">{product.unit}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500">
                จำนวนในคลัง
              </label>
              <p
                className={`mt-1 text-lg font-semibold ${
                  isLowStock ? 'text-red-600' : 'text-gray-900'
                }`}
              >
                {product.quantity} {product.unit}
                {isLowStock && (
                  <span className="ml-2 text-xs font-normal text-red-600">
                    (ใกล้หมด)
                  </span>
                )}
              </p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500">
              จุดสั่งซื้อ
            </label>
            <p className="mt-1 text-gray-900">
              {product.reorder_point} {product.unit}
            </p>
          </div>

          {product.description && (
            <div>
              <label className="block text-sm font-medium text-gray-500">
                รายละเอียด
              </label>
              <p className="mt-1 text-gray-900 whitespace-pre-wrap">
                {product.description}
              </p>
            </div>
          )}

          <div className="border-t pt-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <label className="block text-xs font-medium text-gray-500">
                  สร้างเมื่อ
                </label>
                <p className="mt-1 text-gray-700">
                  {formatDate(product.created_at)}
                </p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500">
                  แก้ไขล่าสุด
                </label>
                <p className="mt-1 text-gray-700">
                  {formatDate(product.updated_at)}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
          <button
            onClick={onDelete}
            className="px-4 py-2 text-sm font-medium text-red-700 bg-white border border-red-300 rounded-md hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            ลบสินค้า
          </button>
          <button
            onClick={onEdit}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            แก้ไข
          </button>
        </div>
      </div>
    </div>
  );
};
