import React from 'react';
import { useNavigate } from 'react-router-dom';
import { RecentTransaction } from '../types/dashboard';

interface RecentTransactionsCardProps {
  transactions: RecentTransaction[];
  isLoading: boolean;
}

export const RecentTransactionsCard: React.FC<RecentTransactionsCardProps> = ({
  transactions,
  isLoading,
}) => {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          รายการนำเข้าล่าสุด
        </h2>
        <div className="animate-pulse space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('th-TH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          รายการนำเข้าล่าสุด
        </h2>
        <button
          onClick={() => navigate('/history')}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          ดูทั้งหมด →
        </button>
      </div>

      {transactions.length === 0 ? (
        <p className="text-gray-500 text-center py-8">ยังไม่มีรายการนำเข้า</p>
      ) : (
        <div className="space-y-3">
          {transactions.map((transaction) => (
            <div
              key={transaction.transaction_id}
              onClick={() => navigate('/history')}
              className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <div className="flex justify-between items-start mb-2">
                <span className="text-sm text-gray-500">
                  {formatDate(transaction.created_at)}
                </span>
                <span className="text-sm font-medium text-gray-900">
                  {transaction.total_items} รายการ
                </span>
              </div>
              <div className="text-sm text-gray-700">
                {transaction.items_summary.slice(0, 2).map((item, idx) => (
                  <div key={idx} className="truncate">
                    • {item}
                  </div>
                ))}
                {transaction.items_summary.length > 2 && (
                  <div className="text-gray-500 mt-1">
                    และอีก {transaction.items_summary.length - 2} รายการ
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
