import React, { useState, useCallback } from 'react';
import { useProducts } from '../hooks/useProducts';
import { SearchBar } from '../components/SearchBar';
import { ProductForm } from '../components/ProductForm';
import { ProductDetailModal } from '../components/ProductDetailModal';
import { EmbeddingFailureModal } from '../components/EmbeddingFailureModal';
import { Product, ProductCreate, ProductUpdate } from '../types/product';
import api from '../services/api';

type EmbeddingProgress = {
  total: number;
  processed: number;
  success: number;
  failure: number;
  currentBatch: number;
  hasMore: boolean;
  batchSize: number;
};

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
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [embeddingProgress, setEmbeddingProgress] = useState<EmbeddingProgress | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(20);

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

  const handleSearch = useCallback((query: string) => {
    setSearchQuery((prev) => {
      if (prev !== query) {
        setCurrentPage(1);
        return query;
      }
      return prev;
    });
  }, []);

  // Pagination calculations
  const totalPages = Math.ceil(products.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentProducts = products.slice(startIndex, endIndex);

  // Debug logging - only log when explicitly needed, not on every render
  console.log('Current page:', currentPage, 'First product:', currentProducts[0]?.name);

  const handlePageChange = (page: number) => {
    console.log('handlePageChange called with page:', page, 'totalPages:', totalPages);
    if (page < 1 || page > totalPages) {
      console.log('Page out of range, ignoring');
      return;
    }
    console.log('Setting currentPage to:', page);
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleItemsPerPageChange = (items: number) => {
    setItemsPerPage(items);
    setCurrentPage(1);
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

  const handleRegenerateEmbeddings = async () => {
    if (!window.confirm('คุณต้องการสร้าง embeddings ใหม่สำหรับสินค้าทั้งหมดหรือไม่?\n\nการดำเนินการนี้จะใช้เวลาสักครู่และจะช่วยปรับปรุงความแม่นยำในการจับคู่สินค้าจากใบเสร็จ')) {
      return;
    }

    setIsRegenerating(true);
    const batchSize = 20;
    let offset = 0;
    let totalProcessed = 0;
    let totalSuccess = 0;
    let totalFailure = 0;
    let totalProducts = 0;
    let batchNumber = 0;

    setEmbeddingProgress({
      total: 0,
      processed: 0,
      success: 0,
      failure: 0,
      currentBatch: 0,
      hasMore: true,
      batchSize,
    });

    try {
      while (true) {
        batchNumber += 1;
        const response = await api.post(
          '/api/products/regenerate-embeddings',
          {},
          {
            params: {
              batch_size: batchSize,
              offset,
            },
          }
        );

        const result = response.data;
        totalProducts = result.total ?? totalProducts;
        totalProcessed += result.processed ?? 0;
        totalSuccess += result.success ?? 0;
        totalFailure += result.failure ?? 0;

        setEmbeddingProgress({
          total: totalProducts,
          processed: totalProcessed,
          success: totalSuccess,
          failure: totalFailure,
          currentBatch: batchNumber,
          hasMore: result.has_more,
          batchSize,
        });

        if (!result.has_more) {
          break;
        }

        offset = result.next_offset ?? offset + (result.processed ?? batchSize);
        await new Promise((resolve) => setTimeout(resolve, 1500));
      }

      alert(
        `สร้าง embeddings ใหม่เสร็จสิ้น\n\n` +
        `ทั้งหมด: ${totalProducts} รายการ\n` +
        `สำเร็จ: ${totalSuccess} รายการ\n` +
        `ล้มเหลว: ${totalFailure} รายการ`
      );
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || 'เกิดข้อผิดพลาด';
      alert(`เกิดข้อผิดพลาด: ${errorMsg}`);
    } finally {
      setIsRegenerating(false);
      setEmbeddingProgress(null);
    }
  };

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
        <div className="flex flex-col gap-2 items-end">
          <button
            onClick={handleRegenerateEmbeddings}
            disabled={isRegenerating}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
            title="สร้าง embeddings ใหม่เพื่อปรับปรุงความแม่นยำในการจับคู่สินค้า"
          >
            {isRegenerating ? '⏳ กำลังสร้าง...' : '🔄 อัปเดต AI'}
          </button>
          {embeddingProgress && (
            <div className="text-xs text-gray-600">
              กำลังอัปเดต: {embeddingProgress.processed}/{embeddingProgress.total || '?'} รายการ
              {' '}(Batch {embeddingProgress.currentBatch}, {embeddingProgress.batchSize}/ครั้ง)
            </div>
          )}
          <button
            onClick={handleAddNew}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            + เพิ่มสินค้าใหม่
          </button>
        </div>
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
          <table className="min-w-full divide-y divide-gray-200" key={`table-page-${currentPage}`}>
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
            <tbody className="bg-white divide-y divide-gray-200" key={`tbody-page-${currentPage}`}>
              {currentProducts.map((product) => (
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
          
          {/* Pagination Controls */}
          {products.length > 0 && (
            <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  ก่อนหน้า
                </button>
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  ถัดไป
                </button>
              </div>
              
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div className="flex items-center gap-4">
                  <p className="text-sm text-gray-700">
                    แสดง <span className="font-medium">{startIndex + 1}</span> ถึง{' '}
                    <span className="font-medium">{Math.min(endIndex, products.length)}</span> จาก{' '}
                    <span className="font-medium">{products.length}</span> รายการ
                  </p>
                  
                  <div className="flex items-center gap-2">
                    <label htmlFor="items-per-page" className="text-sm text-gray-700">
                      แสดงต่อหน้า:
                    </label>
                    <select
                      id="items-per-page"
                      value={itemsPerPage}
                      onChange={(e) => handleItemsPerPageChange(Number(e.target.value))}
                      className="border border-gray-300 rounded-md text-sm py-1 px-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value={10}>10</option>
                      <option value={20}>20</option>
                      <option value={50}>50</option>
                      <option value={100}>100</option>
                    </select>
                  </div>
                </div>
                
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span className="sr-only">ก่อนหน้า</span>
                      <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </button>
                    
                    {/* Page numbers */}
                    {Array.from({ length: totalPages }, (_, i) => i + 1)
                      .filter(page => {
                        // Show first page, last page, current page and 2 pages around current
                        return (
                          page === 1 ||
                          page === totalPages ||
                          (page >= currentPage - 2 && page <= currentPage + 2)
                        );
                      })
                      .map((page, index, array) => {
                        // Add ellipsis
                        const showEllipsisBefore = index > 0 && page - array[index - 1] > 1;
                        
                        return (
                          <React.Fragment key={page}>
                            {showEllipsisBefore && (
                              <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                                ...
                              </span>
                            )}
                            <button
                              onClick={() => handlePageChange(page)}
                              className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                currentPage === page
                                  ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                  : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                              }`}
                            >
                              {page}
                            </button>
                          </React.Fragment>
                        );
                      })}
                    
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span className="sr-only">ถัดไป</span>
                      <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          )}
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
