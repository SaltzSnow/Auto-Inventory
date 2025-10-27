export interface TransactionItem {
  id: string;
  transaction_id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit: string;
  original_text: string;
  created_at: string;
}

export interface Transaction {
  id: string;
  receipt_id: string;
  total_items: number;
  created_at: string;
  items: TransactionItem[];
}

export interface TransactionSearchParams {
  q?: string;
  start_date?: string;
  end_date?: string;
  skip?: number;
  limit?: number;
}
