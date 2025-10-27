import React from 'react';
import { useDashboard } from '../hooks/useDashboard';
import { StockSummaryCard } from '../components/StockSummaryCard';
import { RecentTransactionsCard } from '../components/RecentTransactionsCard';
import { LowStockAlertCard } from '../components/LowStockAlertCard';
import { StockTrendChart } from '../components/StockTrendChart';

export const DashboardPage: React.FC = () => {
  const {
    summary,
    recentTransactions,
    lowStockAlerts,
    stockTrend,
    isLoadingSummary,
    isLoadingRecent,
    isLoadingLowStock,
    isLoadingTrend,
    isError,
  } = useDashboard();

  if (isError) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-600">
            เกิดข้อผิดพลาดในการโหลดข้อมูล กรุณาลองใหม่อีกครั้ง
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">แดชบอร์ด</h1>
        <p className="mt-2 text-gray-600">
          ยินดีต้อนรับสู่ระบบจัดการคลังสินค้าด้วย AI
        </p>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Summary and Alerts */}
        <div className="lg:col-span-1 space-y-6">
          <StockSummaryCard summary={summary} isLoading={isLoadingSummary} />
          <LowStockAlertCard
            products={lowStockAlerts}
            isLoading={isLoadingLowStock}
          />
        </div>

        {/* Right Column - Transactions and Trend */}
        <div className="lg:col-span-2 space-y-6">
          <RecentTransactionsCard
            transactions={recentTransactions}
            isLoading={isLoadingRecent}
          />
          <StockTrendChart data={stockTrend} isLoading={isLoadingTrend} />
        </div>
      </div>
    </div>
  );
};
