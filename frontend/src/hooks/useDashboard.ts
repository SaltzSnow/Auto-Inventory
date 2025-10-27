import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import {
  DashboardSummary,
  RecentTransaction,
  LowStockProduct,
  StockTrendData,
} from '../types/dashboard';

// API functions
const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const response = await api.get('/api/dashboard/summary');
  return response.data;
};

const getRecentTransactions = async (): Promise<RecentTransaction[]> => {
  const response = await api.get('/api/dashboard/recent-transactions');
  return response.data;
};

const getLowStockAlerts = async (): Promise<LowStockProduct[]> => {
  const response = await api.get('/api/dashboard/low-stock-alerts');
  return response.data;
};

const getStockTrend = async (): Promise<StockTrendData[]> => {
  const response = await api.get('/api/dashboard/stock-trend');
  return response.data;
};

// Custom hook
export const useDashboard = () => {
  // Query for dashboard summary
  const summaryQuery = useQuery<DashboardSummary>({
    queryKey: ['dashboard', 'summary'],
    queryFn: getDashboardSummary,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  // Query for recent transactions
  const recentTransactionsQuery = useQuery<RecentTransaction[]>({
    queryKey: ['dashboard', 'recent-transactions'],
    queryFn: getRecentTransactions,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  // Query for low stock alerts
  const lowStockQuery = useQuery<LowStockProduct[]>({
    queryKey: ['dashboard', 'low-stock-alerts'],
    queryFn: getLowStockAlerts,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  // Query for stock trend
  const stockTrendQuery = useQuery<StockTrendData[]>({
    queryKey: ['dashboard', 'stock-trend'],
    queryFn: getStockTrend,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  return {
    summary: summaryQuery.data,
    recentTransactions: recentTransactionsQuery.data || [],
    lowStockAlerts: lowStockQuery.data || [],
    stockTrend: stockTrendQuery.data || [],
    isLoadingSummary: summaryQuery.isLoading,
    isLoadingRecent: recentTransactionsQuery.isLoading,
    isLoadingLowStock: lowStockQuery.isLoading,
    isLoadingTrend: stockTrendQuery.isLoading,
    isError:
      summaryQuery.isError ||
      recentTransactionsQuery.isError ||
      lowStockQuery.isError ||
      stockTrendQuery.isError,
  };
};
