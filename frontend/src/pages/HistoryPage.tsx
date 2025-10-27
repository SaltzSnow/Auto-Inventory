import React, { useState, useEffect } from 'react';
import { TransactionList } from '../components/TransactionList';
import { DateRangePicker } from '../components/DateRangePicker';
import { SearchBar } from '../components/SearchBar';
import { useTransactions, useTransactionSearch } from '../hooks/useTransactions';

const ITEMS_PER_PAGE = 20;

export const HistoryPage: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // Determine if we should use search or regular query
  const shouldSearch = searchQuery || startDate || endDate;

  // Regular transactions query
  const {
    transactions: regularTransactions,
    isLoading: isLoadingRegular,
    refetch: refetchRegular,
  } = useTransactions(currentPage * ITEMS_PER_PAGE, ITEMS_PER_PAGE);

  // Search transactions query
  const {
    transactions: searchTransactions,
    isLoading: isLoadingSearch,
    refetch: refetchSearch,
  } = useTransactionSearch({
    q: searchQuery || undefined,
    start_date: startDate || undefined,
    end_date: endDate || undefined,
    skip: currentPage * ITEMS_PER_PAGE,
    limit: ITEMS_PER_PAGE,
  });

  // Use appropriate data based on search state
  const transactions = shouldSearch ? searchTransactions : regularTransactions;
  const isLoading = shouldSearch ? isLoadingSearch : isLoadingRegular;

  // Reset to first page when search params change
  useEffect(() => {
    setCurrentPage(0);
    setIsSearching(!!shouldSearch);
  }, [searchQuery, startDate, endDate, shouldSearch]);

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setStartDate('');
    setEndDate('');
    setCurrentPage(0);
  };

  const hasMore = transactions.length === ITEMS_PER_PAGE;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">ประวัติการทำรายการ</h1>
        <p className="mt-2 text-sm text-gray-600">
          ดูประวัติการอัปเดตสต็อกทั้งหมดจากการอัปโหลดใบเสร็จ
        </p>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <SearchBar
              onSearch={setSearchQuery}
              placeholder="ค้นหาตามชื่อสินค้า..."
            />
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <DateRangePicker
            startDate={startDate}
            endDate={endDate}
            onStartDateChange={setStartDate}
            onEndDateChange={setEndDate}
            onClear={handleClearFilters}
          />
          
          {(searchQuery || startDate || endDate) && (
            <div className="text-sm text-gray-600">
              {isSearching && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  กำลังค้นหา
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Transaction List */}
      <TransactionList
        transactions={transactions}
        isLoading={isLoading}
        currentPage={currentPage}
        itemsPerPage={ITEMS_PER_PAGE}
        onPageChange={handlePageChange}
        hasMore={hasMore}
      />
    </div>
  );
};
