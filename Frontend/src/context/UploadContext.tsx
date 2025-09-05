/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { createContext, useState, useContext, ReactNode, useEffect } from 'react';
import * as XLSX from 'xlsx';
import { v4 as uuidv4 } from 'uuid'; // For unique IDs

// --- INTERFACES ---

export interface ComponentData {
  [key: string]: any;
}

export interface AnalysisResult {
  annotatedImage: string | null;
  excelDataUrl: string | null;
  originalFileName: string;
  componentData: ComponentData[];
  isEnhanced?: boolean;
  needsReview?: boolean; // ADDED: Flag for items needing review
}

export interface UploadQueueItem {
  id: string;
  file: File;
  status: 'queued' | 'processing' | 'completed' | 'error';
  result?: AnalysisResult;
  error?: string;
}

// Define the shape of the context value
interface UploadContextType {
  uploadQueue: UploadQueueItem[];
  isProcessing: boolean;
  handleFileUpload: (selectedFiles: File[]) => void;
  updateEnhancedExcel: (itemId: string, newExcelBlob: Blob, needsReview: boolean) => Promise<void>;
}

// --- CONTEXT AND PROVIDER ---

const UploadContext = createContext<UploadContextType | undefined>(undefined);

export const UploadProvider = ({ children }: { children: ReactNode }) => {
  const [uploadQueue, setUploadQueue] = useState<UploadQueueItem[]>([]);
  const isProcessing = uploadQueue.some(item => item.status === 'processing');

  const handleFileUpload = (selectedFiles: File[]) => {
    const newQueueItems: UploadQueueItem[] = selectedFiles.map(file => ({
      id: uuidv4(),
      file,
      status: 'queued',
    }));
    setUploadQueue(prevQueue => [...prevQueue, ...newQueueItems]);
  };
  
  const updateEnhancedExcel = async (itemId: string, newExcelBlob: Blob, needsReview: boolean) => {
    try {
      const newExcelDataUrl = URL.createObjectURL(newExcelBlob);
      const arrayBuffer = await newExcelBlob.arrayBuffer();
      const workbook = XLSX.read(arrayBuffer, { type: 'array' });
      const sheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[sheetName];
      const newComponentData = XLSX.utils.sheet_to_json(worksheet) as ComponentData[];

      setUploadQueue(prevQueue =>
        prevQueue.map(item => {
          if (item.id === itemId && item.result) {
            if (item.result.excelDataUrl) {
                URL.revokeObjectURL(item.result.excelDataUrl);
            }
            
            const updatedResult: AnalysisResult = {
              ...item.result,
              excelDataUrl: newExcelDataUrl,
              componentData: newComponentData,
              isEnhanced: true,
              needsReview, // SET the new flag
            };

            return { ...item, result: updatedResult };
          }
          return item;
        })
      );
    } catch (error) {
        console.error("Failed to update context with enhanced Excel:", error);
    }
  };

  // --- Queue Processor Effect (no changes needed here) ---
  useEffect(() => {
    if (isProcessing) {
      return;
    }

    const nextItem = uploadQueue.find(item => item.status === 'queued');

    if (nextItem) {
      setUploadQueue(prevQueue =>
        prevQueue.map(item =>
          item.id === nextItem.id ? { ...item, status: 'processing' } : item
        )
      );

      const processItem = async (itemToProcess: UploadQueueItem) => {
        const { file } = itemToProcess;
        const formData = new FormData();
        formData.append("file", file);

        try {
          const response = await fetch("http://localhost:8000/img_pred/predict-upload-json/", {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred.' }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
          }

          const data = await response.json();
          
          const newResult: AnalysisResult = {
            originalFileName: file.name,
            annotatedImage: null,
            excelDataUrl: null,
            componentData: [],
            isEnhanced: false,
            needsReview: false, // Initialize to false
          };

          if (data.annotated_image_base64) {
            newResult.annotatedImage = `data:image/png;base64,${data.annotated_image_base64}`;
          }

          if (data.excel_data_base64) {
            const excelBytes = atob(data.excel_data_base64);
            const excelArray = new Uint8Array(excelBytes.length).map((_, i) => excelBytes.charCodeAt(i));
            
            const excelBlob = new Blob([excelArray], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            newResult.excelDataUrl = URL.createObjectURL(excelBlob);
            
            const workbook = XLSX.read(excelArray, { type: 'array' });
            const sheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[sheetName];
            newResult.componentData = XLSX.utils.sheet_to_json(worksheet) as ComponentData[];
          }
          
          setUploadQueue(prevQueue =>
            prevQueue.map(item =>
              item.id === itemToProcess.id
                ? { ...item, status: 'completed', result: newResult }
                : item
            )
          );

        } catch (err: any) {
          console.error("Error uploading file:", err);
          let errorMessage = "An unexpected error occurred. Please try again.";
          if (err instanceof TypeError && err.message === 'Failed to fetch') {
            errorMessage = "Could not connect to the server at http://localhost:8000.";
          } else {
            errorMessage = err.message;
          }

          setUploadQueue(prevQueue =>
            prevQueue.map(item =>
              item.id === itemToProcess.id
                ? { ...item, status: 'error', error: errorMessage }
                : item
            )
          );
        }
      };

      processItem(nextItem);
    }
  }, [uploadQueue, isProcessing]);

  const value = {
    uploadQueue,
    isProcessing,
    handleFileUpload,
    updateEnhancedExcel,
  };

  return (
    <UploadContext.Provider value={value}>
      {children}
    </UploadContext.Provider>
  );
};

// --- CUSTOM HOOK ---

export const useUpload = () => {
  const context = useContext(UploadContext);
  if (context === undefined) {
    throw new Error('useUpload must be used within an UploadProvider');
  }
  return context;
};