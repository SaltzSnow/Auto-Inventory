import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { Product, ProductCreate, ProductUpdate } from '../types/product';

// API functions
const getProducts = async (): Promise<Product[]> => {
  const response = await api.get('/api/products');
  return response.data;
};

const searchProducts = async (query: string): Promise<Product[]> => {
  const response = await api.get('/api/products/search', {
    params: { q: query },
  });
  return response.data;
};

const createProduct = async (data: ProductCreate): Promise<Product> => {
  const response = await api.post('/api/products', data);
  return response.data;
};

const updateProduct = async ({
  id,
  data,
}: {
  id: string;
  data: ProductUpdate;
}): Promise<Product> => {
  const response = await api.put(`/api/products/${id}`, data);
  return response.data;
};

const deleteProduct = async (id: string): Promise<void> => {
  await api.delete(`/api/products/${id}`);
};

// Custom hook
export const useProducts = (searchQuery?: string) => {
  const queryClient = useQueryClient();

  // Query for getting all products or searching
  const productsQuery = useQuery<Product[]>({
    queryKey: searchQuery ? ['products', 'search', searchQuery] : ['products'],
    queryFn: () => (searchQuery ? searchProducts(searchQuery) : getProducts()),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
  });

  // Mutation for creating product
  const createMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });

  // Mutation for updating product
  const updateMutation = useMutation({
    mutationFn: updateProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });

  // Mutation for deleting product
  const deleteMutation = useMutation({
    mutationFn: deleteProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });

  return {
    products: productsQuery.data || [],
    isLoading: productsQuery.isLoading,
    isError: productsQuery.isError,
    error: productsQuery.error,
    createProduct: createMutation.mutate,
    updateProduct: updateMutation.mutate,
    deleteProduct: deleteMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
};
