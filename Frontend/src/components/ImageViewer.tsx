import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';

interface ImageViewerProps {
  imageUrl: string;
  onClose: () => void;
}

const ImageViewer = ({ imageUrl, onClose }: ImageViewerProps) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Effect for keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
      <div className="w-full h-full p-4 flex flex-col" ref={containerRef}>
        {/* Header with Close Button */}
        <div className="flex justify-end mb-4 z-10">
          <Button onClick={onClose} variant="destructive" size="icon" title="Close">
            <X />
          </Button>
        </div>
        
        {/* Image Container */}
        <div className="flex-1 overflow-hidden flex items-center justify-center">
          <img
            src={imageUrl}
            alt="Annotated P&ID"
            className="max-w-full max-h-full object-contain"
          />
        </div>
      </div>
    </div>
  );
};

export default ImageViewer;