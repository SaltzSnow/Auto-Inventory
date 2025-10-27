import React, { useState, useEffect } from 'react';
import { useProducts } from '../hooks/useProducts';

interface ProductDropdownProps {
  value: string;
  onChange: (productId: string, productName: string, unit: string) => void;
  disabled?: boolean;
}

export const ProductDropdown: React.FC<ProductDropdownProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const { products, isLoading } = useProducts();
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const filteredProducts = products.filter((product) =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedProduct = products.find((p) => p.id === value);

  const handleSelect = (productId: string) => {
    const product = products.find((p) => p.id === productId);
    if (product) {
      onChange(productId, product.name, product.unit);
      setIsOpen(false);
      setSearchTerm('');
    }
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.product-dropdown')) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative product-dropdown">
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className="w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
      >
        <span className="block truncate text-sm">
          {selectedProduct ? selectedProduct.name : '🔄 เปลี่ยนสินค้า...'}
        </span>
        <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
          <svg
            className="w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </span>
      </button>

      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          <div className="p-2 border-b border-gray-200">
            <input
              type="text"
              placeholder="ค้นหาสินค้า..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
          </div>

          {isLoading ? (
            <div className="p-4 text-center text-gray-500">กำลังโหลด...</div>
          ) : filteredProducts.length === 0 ? (
            <div className="p-4 text-center text-gray-500">ไม่พบสินค้า</div>
          ) : (
            <ul className="py-1">
              {filteredProducts.map((product) => (
                <li key={product.id}>
                  <button
                    type="button"
                    onClick={() => handleSelect(product.id)}
                    className={`w-full px-4 py-2 text-left hover:bg-gray-100 ${
                      value === product.id ? 'bg-blue-50 text-blue-600' : 'text-gray-900'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{product.name}</span>
                      <span className="text-sm text-gray-500">({product.unit})</span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};
