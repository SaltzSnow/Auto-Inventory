import React from 'react';

interface ReceiptImageViewerProps {
  imageUrl: string;
  isOpen: boolean;
  onClose: () => void;
}

export const ReceiptImageViewer: React.FC<ReceiptImageViewerProps> = ({
  imageUrl,
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75"
      onClick={onClose}
    >
      <div className="relative max-w-4xl max-h-screen p-4">
        <button
          onClick={onClose}
          className="absolute top-6 right-6 text-white hover:text-gray-300 text-4xl font-bold z-10"
          aria-label="ปิด"
        >
          ×
        </button>
        <img
          src={imageUrl}
          alt="ใบเสร็จ"
          loading="lazy"
          className="max-w-full max-h-screen object-contain"
          onClick={(e) => e.stopPropagation()}
        />
      </div>
    </div>
  );
};
