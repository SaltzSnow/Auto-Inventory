export interface Product {
  id: string;
  name: string;
  unit: string;
  quantity: number;
  reorder_point: number;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  name: string;
  unit: string;
  quantity?: number;
  reorder_point?: number;
  description?: string;
  force_without_embedding?: boolean;
}

export interface ProductUpdate {
  name?: string;
  unit?: string;
  quantity?: number;
  reorder_point?: number;
  description?: string;
}
