import { useMutation } from '@tanstack/react-query';
import { api } from '../services/api';

interface ValidatedItem {
  product_id: string;
  product_name: string;
  quantity: number;
  unit: string;
  original_text: string;
}

interface ConfirmReceiptRequest {
  receipt_id: string;
  items: ValidatedItem[];
}

interface ConfirmReceiptResponse {
  transaction_id: string;
  total_items: number;
  message: string;
}

export const useConfirmation = () => {
  const confirmReceipt = useMutation({
    mutationFn: async (data: ConfirmReceiptRequest): Promise<ConfirmReceiptResponse> => {
      const response = await api.post<ConfirmReceiptResponse>('/api/receipts/confirm', data);
      return response.data;
    },
  });

  return { confirmReceipt };
};
