import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { Transaction, TransactionSearchParams } from '../types/transaction';

// API functions
const getTransactions = async (skip: number = 0, limit: number = 20): Promise<Transaction[]> => {
  const response = await api.get('/api/transactions', {
    params: { skip, limit },
  });
  return response.data;
};

const getTransactionById = async (id: string): Promise<Transaction> => {
  const response = await api.get(`/api/transactions/${id}`);
  return response.data;
};

const searchTransactions = async (params: TransactionSearchParams): Promise<Transaction[]> => {
  const response = await api.get('/api/transactions/search', {
    params,
  });
  return response.data;
};

// Custom hook for transactions list
export const useTransactions = (skip: number = 0, limit: number = 20) => {
  const transactionsQuery = useQuery<Transaction[]>({
    queryKey: ['transactions', skip, limit],
    queryFn: () => getTransactions(skip, limit),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
  });

  return {
    transactions: transactionsQuery.data || [],
    isLoading: transactionsQuery.isLoading,
    isError: transactionsQuery.isError,
    error: transactionsQuery.error,
    refetch: transactionsQuery.refetch,
  };
};

// Custom hook for single transaction
export const useTransaction = (id: string) => {
  const transactionQuery = useQuery<Transaction>({
    queryKey: ['transaction', id],
    queryFn: () => getTransactionById(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  return {
    transaction: transactionQuery.data,
    isLoading: transactionQuery.isLoading,
    isError: transactionQuery.isError,
    error: transactionQuery.error,
  };
};

// Custom hook for searching transactions
export const useTransactionSearch = (params: TransactionSearchParams) => {
  const searchQuery = useQuery<Transaction[]>({
    queryKey: ['transactions', 'search', params],
    queryFn: () => searchTransactions(params),
    enabled: !!(params.q || params.start_date || params.end_date),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
  });

  return {
    transactions: searchQuery.data || [],
    isLoading: searchQuery.isLoading,
    isError: searchQuery.isError,
    error: searchQuery.error,
    refetch: searchQuery.refetch,
  };
};
