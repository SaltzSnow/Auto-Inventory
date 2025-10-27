import React from 'react';
import { DashboardSummary } from '../types/dashboard';

interface StockSummaryCardProps {
  summary: DashboardSummary | undefined;
  isLoading: boolean;
}

export const StockSummaryCard: React.FC<StockSummaryCardProps> = ({
  summary,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">สรุปสต็อก</h2>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">สรุปสต็อก</h2>
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">จำนวนสินค้าทั้งหมด</span>
          <span className="text-2xl font-bold text-blue-600">
            {summary.total_products}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-600">จำนวนสินค้ารวม</span>
          <span className="text-2xl font-bold text-green-600">
            {summary.total_quantity}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-600">สินค้าใกล้หมด</span>
          <span
            className={`text-2xl font-bold ${
              summary.low_stock_count > 0 ? 'text-red-600' : 'text-gray-400'
            }`}
          >
            {summary.low_stock_count}
          </span>
        </div>
      </div>
    </div>
  );
};
