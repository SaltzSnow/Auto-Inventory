import React, { useState } from 'react';
import { useProducts } from '../hooks/useProducts';
import { SearchBar } from '../components/SearchBar';
import { ProductForm } from '../components/ProductForm';
import { ProductDetailModal } from '../components/ProductDetailModal';
import { EmbeddingFailureModal } from '../components/EmbeddingFailureModal';
import { Product, ProductCreate, ProductUpdate } from '../types/product';

export const InventoryPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | undefined>();
  const [selectedProduct, setSelectedProduct] = useState<Product | undefined>();
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [embeddingError, setEmbeddingError] = useState<{
    message: string;
    details: any;
    productData: ProductCreate;
  } | null>(null);

  const {
    products,
    isLoading,
    isError,
    createProduct,
    updateProduct,
    deleteProduct,
    isCreating,
    isUpdating,
    isDeleting,
  } = useProducts(searchQuery);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleEmbeddingFailureConfirm = () => {
    if (!embeddingError) return;

    // Retry with force_without_embedding flag
    const dataWithForce = {
      ...embeddingError.productData,
      force_without_embedding: true,
    };

    createProduct(dataWithForce, {
      onSuccess: () => {
        setShowForm(false);
        setEmbeddingError(null);
        alert('เพิ่มสินค้าสำเร็จ (โดยไม่มี Embedding)');
      },
      onError: (error: any) => {
        const errorData = error.response?.data;
        alert(
          `เกิดข้อผิดพลาด: ${errorData?.detail || errorData?.message || error.message}`
        );
      },
    });
  };

  const handleEmbeddingFailureCancel = () => {
    setEmbeddingError(null);
  };

  const handleCreateProduct = (data: ProductCreate) => {
    createProduct(data, {
      onSuccess: () => {
        setShowForm(false);
        setEmbeddingError(null);
        alert('เพิ่มสินค้าสำเร็จ');
      },
      onError: (error: any) => {
        // Check if it's an embedding failure error
        const errorData = error.response?.data;
        if (errorData?.code === 'EMBEDDING_FAILURE') {
          setEmbeddingError({
            message: errorData.message,
            details: errorData.details,
            productData: data,
          });
        } else {
          alert(
            `เกิดข้อผิดพลาด: ${errorData?.detail || errorData?.message || error.message}`
          );
        }
      },
    });
  };

  const handleUpdateProduct = (data: ProductUpdate) => {
    if (!editingProduct) return;

    updateProduct(
      { id: editingProduct.id, data },
      {
        onSuccess: () => {
          setShowForm(false);
          setEditingProduct(undefined);
          setSelectedProduct(undefined);
          alert('แก้ไขสินค้าสำเร็จ');
        },
        onError: (error: any) => {
          alert(
            `เกิดข้อผิดพลาด: ${error.response?.data?.detail || error.message}`
          );
        },
      }
    );
  };

  const handleDeleteProduct = (id: string) => {
    if (deleteConfirm !== id) {
      setDeleteConfirm(id);
      return;
    }

    deleteProduct(id, {
      onSuccess: () => {
        setSelectedProduct(undefined);
        setDeleteConfirm(null);
        alert('ลบสินค้าสำเร็จ');
      },
      onError: (error: any) => {
        alert(
          `เกิดข้อผิดพลาด: ${error.response?.data?.detail || error.message}`
        );
      },
    });
  };

  const handleEdit = (product: Product) => {
    setEditingProduct(product);
    setSelectedProduct(undefined);
    setShowForm(true);
  };

  const handleAddNew = () => {
    setEditingProduct(undefined);
    setShowForm(true);
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingProduct(undefined);
  };

  const handleFormSubmit = (data: ProductCreate | ProductUpdate) => {
    if (editingProduct) {
      handleUpdateProduct(data as ProductUpdate);
    } else {
      handleCreateProduct(data as ProductCreate);
    }
  };

  const isLowStock = (product: Product) =>
    product.quantity < product.reorder_point;

  if (isError) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">
            เกิดข้อผิดพลาดในการโหลดข้อมูล กรุณาลองใหม่อีกครั้ง
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">คลังสินค้า</h1>
        <p className="mt-2 text-gray-600">จัดการรายการสินค้าในคลัง</p>
      </div>

      <div className="mb-6 flex justify-between items-center">
        <div className="w-96">
          <SearchBar
            onSearch={handleSearch}
            placeholder="ค้นหาสินค้า..."
            debounceMs={300}
          />
        </div>
        <button
          onClick={handleAddNew}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          + เพิ่มสินค้าใหม่
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : products.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
          <h3 className="mt-2 text-lg font-medium text-gray-900">
            {searchQuery ? 'ไม่พบสินค้า' : 'ยังไม่มีสินค้าในคลัง'}
          </h3>
          <p className="mt-1 text-gray-500">
            {searchQuery
              ? 'ลองค้นหาด้วยคำอื่น'
              : 'เริ่มต้นด้วยการเพิ่มสินค้าแรกของคุณ'}
          </p>
          {!searchQuery && (
            <button
              onClick={handleAddNew}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              เพิ่มสินค้าแรก
            </button>
          )}
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ชื่อสินค้า
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  จำนวน
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  หน่วย
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  จุดสั่งซื้อ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  สถานะ
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  การจัดการ
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {products.map((product) => (
                <tr
                  key={product.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => setSelectedProduct(product)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {product.name}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div
                      className={`text-sm ${
                        isLowStock(product)
                          ? 'text-red-600 font-semibold'
                          : 'text-gray-900'
                      }`}
                    >
                      {product.quantity}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{product.unit}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {product.reorder_point}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {isLowStock(product) ? (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                        ใกล้หมด
                      </span>
                    ) : (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        ปกติ
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEdit(product);
                      }}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      แก้ไข
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteProduct(product.id);
                      }}
                      className={`${
                        deleteConfirm === product.id
                          ? 'text-red-900 font-semibold'
                          : 'text-red-600'
                      } hover:text-red-900`}
                      disabled={isDeleting}
                    >
                      {deleteConfirm === product.id ? 'ยืนยันลบ?' : 'ลบ'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <ProductForm
          product={editingProduct}
          onSubmit={handleFormSubmit}
          onCancel={handleCloseForm}
          isSubmitting={isCreating || isUpdating}
        />
      )}

      {selectedProduct && !showForm && (
        <ProductDetailModal
          product={selectedProduct}
          onClose={() => setSelectedProduct(undefined)}
          onEdit={() => handleEdit(selectedProduct)}
          onDelete={() => handleDeleteProduct(selectedProduct.id)}
        />
      )}

      {embeddingError && (
        <EmbeddingFailureModal
          message={embeddingError.message}
          details={embeddingError.details}
          onConfirm={handleEmbeddingFailureConfirm}
          onCancel={handleEmbeddingFailureCancel}
        />
      )}
    </div>
  );
};
