import React from 'react';
import { useNavigate } from 'react-router-dom';
import { LowStockProduct } from '../types/dashboard';

interface LowStockAlertCardProps {
  products: LowStockProduct[];
  isLoading: boolean;
}

export const LowStockAlertCard: React.FC<LowStockAlertCardProps> = ({
  products,
  isLoading,
}) => {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          แจ้งเตือนสินค้าใกล้หมด
        </h2>
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          แจ้งเตือนสินค้าใกล้หมด
        </h2>
        {products.length > 0 && (
          <button
            onClick={() => navigate('/inventory')}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            ไปที่คลังสินค้า →
          </button>
        )}
      </div>

      {products.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-green-600 text-4xl mb-2">✓</div>
          <p className="text-gray-600">สินค้าทั้งหมดมีจำนวนเพียงพอ</p>
        </div>
      ) : (
        <div className="space-y-3">
          {products.map((product) => (
            <div
              key={product.product_id}
              onClick={() => navigate('/inventory')}
              className="border border-red-200 bg-red-50 rounded-lg p-4 hover:bg-red-100 cursor-pointer transition-colors"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900">
                    {product.product_name}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    จุดสั่งซื้อ: {product.reorder_point} {product.unit}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-red-600">
                    {product.quantity}
                  </div>
                  <div className="text-sm text-gray-600">{product.unit}</div>
                </div>
              </div>
              <div className="mt-2">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-red-600 h-2 rounded-full"
                    style={{
                      width: `${Math.min(
                        (product.quantity / product.reorder_point) * 100,
                        100
                      )}%`,
                    }}
                  ></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
