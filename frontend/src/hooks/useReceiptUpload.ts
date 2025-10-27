import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export interface TaskStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  current_step: string;
  result?: {
    items: Array<{
      product_id: string;
      product_name: string;
      quantity: number;
      unit: string;
      confidence: number;
      original_text: string;
    }>;
    receipt_id: string;
    image_url: string;
  };
  error?: string;
}

interface UploadResponse {
  task_id: string;
  receipt_id: string;
  message: string;
}

export const useReceiptUpload = () => {
  const uploadReceipt = useMutation({
    mutationFn: async (file: File): Promise<UploadResponse> => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post<UploadResponse>('/api/receipts/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data;
    },
  });

  return { uploadReceipt };
};

export const useTaskStatus = (taskId: string | null, enabled: boolean = true) => {
  return useQuery<TaskStatus>({
    queryKey: ['taskStatus', taskId],
    queryFn: async (): Promise<TaskStatus> => {
      if (!taskId) {
        throw new Error('Task ID is required');
      }

      const response = await api.get<TaskStatus>(`/api/receipts/task/${taskId}`);
      return response.data;
    },
    enabled: enabled && !!taskId,
    refetchInterval: (query) => {
      // Stop polling if task is completed or failed
      const data = query.state.data;
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      // Poll every 2 seconds while processing
      return 2000;
    },
    retry: 3,
  });
};
