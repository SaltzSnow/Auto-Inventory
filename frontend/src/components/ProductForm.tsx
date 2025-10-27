import React, { useState, useEffect } from 'react';
import { Product, ProductCreate, ProductUpdate } from '../types/product';

interface ProductFormProps {
  product?: Product;
  onSubmit: (data: ProductCreate | ProductUpdate) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export const ProductForm: React.FC<ProductFormProps> = ({
  product,
  onSubmit,
  onCancel,
  isSubmitting = false,
}) => {
  const [formData, setFormData] = useState({
    name: product?.name || '',
    unit: product?.unit || '',
    quantity: product?.quantity?.toString() || '0',
    reorder_point: product?.reorder_point?.toString() || '0',
    description: product?.description || '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Allowed units matching backend validation
  const allowedUnits = [
    'ชิ้น', 'กระป๋อง', 'ขวด', 'แพ็ค', 'กล่อง', 'ถุง',
    'ห่อ', 'ลัง', 'โหล', 'กิโลกรัม', 'กรัม', 'ลิตร',
    'มิลลิลิตร', 'เมตร', 'เซนติเมตร', 'อัน', 'แผ่น'
  ];

  useEffect(() => {
    if (product) {
      setFormData({
        name: product.name,
        unit: product.unit,
        quantity: product.quantity.toString(),
        reorder_point: product.reorder_point.toString(),
        description: product.description || '',
      });
    }
  }, [product]);

  const validate = () => {
    const newErrors: Record<string, string> = {};

    // Validate name
    if (!formData.name.trim()) {
      newErrors.name = 'กรุณากรอกชื่อสินค้า';
    } else if (formData.name.trim().length > 255) {
      newErrors.name = 'ชื่อสินค้าต้องไม่เกิน 255 ตัวอักษร';
    }

    // Validate unit
    if (!formData.unit.trim()) {
      newErrors.unit = 'กรุณากรอกหน่วยนับ';
    } else if (!allowedUnits.includes(formData.unit.trim())) {
      newErrors.unit = `หน่วยนับไม่ถูกต้อง กรุณาเลือกจาก: ${allowedUnits.join(', ')}`;
    }

    // Validate quantity
    const quantity = parseInt(formData.quantity);
    if (isNaN(quantity) || quantity < 0) {
      newErrors.quantity = 'จำนวนต้องเป็นตัวเลขที่มากกว่าหรือเท่ากับ 0';
    }

    // Validate reorder point
    const reorderPoint = parseInt(formData.reorder_point);
    if (isNaN(reorderPoint) || reorderPoint < 0) {
      newErrors.reorder_point = 'จุดสั่งซื้อต้องเป็นตัวเลขที่มากกว่าหรือเท่ากับ 0';
    }

    // Validate description length
    if (formData.description && formData.description.length > 1000) {
      newErrors.description = 'รายละเอียดต้องไม่เกิน 1000 ตัวอักษร';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    const data = {
      name: formData.name.trim(),
      unit: formData.unit.trim(),
      quantity: parseInt(formData.quantity),
      reorder_point: parseInt(formData.reorder_point),
      description: formData.description.trim() || undefined,
    };

    onSubmit(data);
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
            {product ? 'แก้ไขสินค้า' : 'เพิ่มสินค้าใหม่'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                ชื่อสินค้า <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm ${
                  errors.name ? 'border-red-500' : ''
                }`}
                placeholder="เช่น โค้ก 325 มล."
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                หน่วยนับ <span className="text-red-500">*</span>
              </label>
              <select
                name="unit"
                value={formData.unit}
                onChange={(e) => handleChange(e as any)}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm ${
                  errors.unit ? 'border-red-500' : ''
                }`}
              >
                <option value="">เลือกหน่วยนับ</option>
                {allowedUnits.map((unit) => (
                  <option key={unit} value={unit}>
                    {unit}
                  </option>
                ))}
              </select>
              {errors.unit && (
                <p className="mt-1 text-sm text-red-600">{errors.unit}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                จำนวนในคลัง
              </label>
              <input
                type="number"
                name="quantity"
                value={formData.quantity}
                onChange={handleChange}
                min="0"
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm ${
                  errors.quantity ? 'border-red-500' : ''
                }`}
              />
              {errors.quantity && (
                <p className="mt-1 text-sm text-red-600">{errors.quantity}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                จุดสั่งซื้อ
              </label>
              <input
                type="number"
                name="reorder_point"
                value={formData.reorder_point}
                onChange={handleChange}
                min="0"
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm ${
                  errors.reorder_point ? 'border-red-500' : ''
                }`}
              />
              {errors.reorder_point && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.reorder_point}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                รายละเอียดเพิ่มเติม
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={3}
                maxLength={1000}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm ${
                  errors.description ? 'border-red-500' : ''
                }`}
                placeholder="รายละเอียดเพิ่มเติมเกี่ยวกับสินค้า"
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600">{errors.description}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                {formData.description.length}/1000 ตัวอักษร
              </p>
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onCancel}
                disabled={isSubmitting}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                ยกเลิก
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {isSubmitting ? 'กำลังบันทึก...' : 'บันทึก'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
