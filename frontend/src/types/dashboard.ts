export interface DashboardSummary {
  total_products: number;
  total_quantity: number;
  low_stock_count: number;
}

export interface RecentTransaction {
  transaction_id: string;
  receipt_id: string;
  created_at: string;
  total_items: number;
  items_summary: string[];
}

export interface LowStockProduct {
  product_id: string;
  product_name: string;
  quantity: number;
  unit: string;
  reorder_point: number;
}

export interface StockTrendData {
  date: string;
  total_items_added: number;
}
