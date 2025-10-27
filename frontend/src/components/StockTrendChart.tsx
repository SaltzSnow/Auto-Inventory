import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { StockTrendData } from '../types/dashboard';

interface StockTrendChartProps {
  data: StockTrendData[];
  isLoading: boolean;
}

export const StockTrendChart: React.FC<StockTrendChartProps> = ({
  data,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          แนวโน้มสต็อก 7 วันที่ผ่านมา
        </h2>
        <div className="animate-pulse">
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  // Format date for display (show only day/month)
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('th-TH', {
      day: 'numeric',
      month: 'short',
    }).format(date);
  };

  // Prepare data for chart
  const chartData = data.map((item) => ({
    date: formatDate(item.date),
    จำนวนสินค้า: item.total_items_added,
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        แนวโน้มสต็อก 7 วันที่ผ่านมา
      </h2>

      {data.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          ยังไม่มีข้อมูลแนวโน้ม
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              style={{ fontSize: '12px' }}
              tick={{ fill: '#6B7280' }}
            />
            <YAxis
              style={{ fontSize: '12px' }}
              tick={{ fill: '#6B7280' }}
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #E5E7EB',
                borderRadius: '8px',
              }}
            />
            <Line
              type="monotone"
              dataKey="จำนวนสินค้า"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={{ fill: '#3B82F6', r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
