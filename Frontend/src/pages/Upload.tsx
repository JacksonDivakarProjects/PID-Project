import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Upload as UploadIcon, FileImage, FileText, Zap, CheckCircle, AlertTriangle, Download, Clock } from "lucide-react";
import { Link } from "react-router-dom";
import { useUpload } from "@/context/UploadContext"; // Assuming useUpload is updated

// Analysis messages remain the same
const ANALYSIS_MESSAGES = [
  "Calibrating neural pathways...",
  "Decoding engineering schematics...",
  "Initializing cognitive processors...",
  "Segmenting pipelines from background noise...",
  // ... (rest of the messages)
  "Almost there, just polishing the results...",
];

// Helper function to get file icon based on type
const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    if (['png', 'jpg', 'jpeg', 'svg'].includes(extension || '')) {
        return <FileImage className="h-5 w-5 text-primary mr-3 flex-shrink-0" />;
    }
    return <FileText className="h-5 w-5 text-primary mr-3 flex-shrink-0" />;
};


const Upload = () => {
  const [isDragging, setIsDragging] = useState(false);
  
  // State for the progress bar and animated loading text
  const [progress, setProgress] = useState(0);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [isTextFading, setIsTextFading] = useState(false);

  // --- MODIFIED: Assuming useUpload is updated for queue management ---
  // The hook now returns a queue of file objects, each with its own status.
  const {
    uploadQueue,    // e.g., [{ id, file, status, result, error }, ...]
    isProcessing,     // This is now true if ANY file is processing
    handleFileUpload,
  } = useUpload();
  // --- END MODIFICATION ---

  // Find the single file that is currently being processed
  const currentlyProcessingFile = uploadQueue.find(item => item.status === 'processing');
  
  // UPDATED: Effect for a smoother, time-based progress bar
  // This effect now watches the 'currentlyProcessingFile'
  useEffect(() => {
    if (currentlyProcessingFile) { // Only run if a file is actually processing
      setProgress(0);
      
      const targetDuration = 2.25 * 60 * 1000;
      const updateInterval = 100;
      const maxProgress = 95;
      const increment = (maxProgress / targetDuration) * updateInterval;

      const timer = setInterval(() => {
        setProgress((prevProgress) => {
          if (prevProgress >= maxProgress) {
            clearInterval(timer);
            return maxProgress;
          }
          return prevProgress + increment;
        });
      }, updateInterval);

      return () => clearInterval(timer);
    }
  }, [currentlyProcessingFile]); // Re-trigger when a new file starts processing

  // UPDATED: Effect to cycle through loading messages with a fade animation
  // This effect also watches the 'currentlyProcessingFile'
  useEffect(() => {
    if (currentlyProcessingFile) { // Only run if a file is processing
      setIsTextFading(false);
      setCurrentMessageIndex(0);

      const textTimer = setInterval(() => {
        setIsTextFading(true);
        setTimeout(() => {
          setCurrentMessageIndex((prevIndex) => (prevIndex + 1) % ANALYSIS_MESSAGES.length);
          setIsTextFading(false);
        }, 400);
      }, 2500);

      return () => clearInterval(textTimer);
    }
  }, [currentlyProcessingFile]); // Re-trigger for the new file
  
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (isProcessing) return; // Prevent adding files while a batch is running
    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFileUpload(droppedFiles); // handleFileUpload now accepts an array
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      handleFileUpload(selectedFiles); // handleFileUpload now accepts an array
    }
  };

  const getBaseFileName = (fileName: string) => {
    return fileName.substring(0, fileName.lastIndexOf('.')) || fileName;
  }

  return (
    <div className="min-h-screen bg-gradient-mesh py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header Section */}
        <div className="text-center mb-12">
            <h1 className="text-4xl font-bold mb-4">Upload Your P&IDs</h1>
            <p className="text-xl text-muted-foreground">
                Drag, drop, or browse to add files to the queue for analysis
            </p>
        </div>

        {/* Drag-and-Drop Card */}
        <Card className="p-8 mb-8">
            <div
                className={`border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${
                isDragging
                    ? "border-primary bg-primary/5 scale-105"
                    : "border-border hover:border-primary/50"
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                {/* ... (inner content of drag-drop is mostly the same) ... */}
                <div className="space-y-6">
                    <div className={`mx-auto w-24 h-24 rounded-full bg-gradient-primary flex items-center justify-center ${isDragging ? 'animate-glow-pulse' : ''}`}>
                        <UploadIcon className="h-12 w-12 text-primary-foreground" />
                    </div>
                    <div>
                        <h3 className="text-xl font-semibold mb-2">
                            {isDragging ? "Drop files here" : "Add P&ID Files to Queue"}
                        </h3>
                        <p className="text-muted-foreground mb-4">
                            Supports PDF, PNG, JPG, and other formats
                        </p>
                        <input
                            type="file"
                            accept=".pdf,.png,.jpg,.jpeg,.dwg,.svg"
                            onChange={handleFileSelect}
                            className="hidden"
                            id="file-upload"
                            disabled={isProcessing} // Disable adding more files while queue is active
                            multiple // --- NEW: Allow multiple file selection ---
                        />
                        <Button asChild variant="gradient" size="lg">
                            <label htmlFor="file-upload" className={`cursor-pointer ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}>
                                Browse Files
                            </label>
                        </Button>
                    </div>
                    <div className="flex justify-center space-x-4 text-sm text-muted-foreground">
                        <div className="flex items-center"><FileText className="h-4 w-4 mr-1" />PDF</div>
                        <div className="flex items-center"><FileImage className="h-4 w-4 mr-1" />Images</div>
                        <div className="flex items-center"><FileText className="h-4 w-4 mr-1" />CAD</div>
                    </div>
                </div>
            </div>
        </Card>

        {/* --- NEW: File Queue Display Section --- */}
        {uploadQueue.length > 0 && (
          <Card className="p-6">
            <h2 className="text-2xl font-bold mb-4">Processing Queue</h2>
            <div className="space-y-4">
              {uploadQueue.map((item) => {
                const { file, status, result, error } = item;
                const isThisItemProcessing = status === 'processing';

                return (
                    <div key={item.id} className="border bg-muted/30 rounded-lg p-4 transition-all">
                        {/* File Info Header */}
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center min-w-0">
                                {getFileIcon(file.name)}
                                <div className="flex flex-col min-w-0">
                                    <span className="font-medium truncate">{file.name}</span>
                                    <span className="text-sm text-muted-foreground">
                                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                                    </span>
                                </div>
                            </div>
                            {/* Status Icons */}
                            {status === 'completed' && <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0" />}
                            {status === 'queued' && <Clock className="h-6 w-6 text-amber-500 flex-shrink-0" />}
                            {status === 'error' && <AlertTriangle className="h-6 w-6 text-destructive flex-shrink-0" />}
                            {isThisItemProcessing && <Zap className="h-6 w-6 text-primary animate-pulse flex-shrink-0" />}
                        </div>

                        {/* --- Status-Specific Content --- */}

                        {/* PROCESSING VIEW */}
                        {isThisItemProcessing && (
                            <div className="space-y-3 pt-2">
                                <Progress value={progress} className="w-full" />
                                <p className={`text-center text-muted-foreground text-sm min-h-[20px] transition-opacity duration-300 ease-in-out ${isTextFading ? 'opacity-0' : 'opacity-100'}`}>
                                    {ANALYSIS_MESSAGES[currentMessageIndex]}
                                </p>
                            </div>
                        )}

                        {/* ERROR VIEW */}
                        {status === 'error' && (
                            <div className="flex items-start bg-destructive/10 text-destructive p-3 rounded-md">
                                <AlertTriangle className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" />
                                <p className="text-sm font-medium">{error || "An unknown error occurred."}</p>
                            </div>
                        )}

                        {/* COMPLETED/RESULTS VIEW */}
                        {status === 'completed' && result && (
                            <div className="space-y-4 pt-2">
                                <div className="border rounded-lg overflow-hidden">
                                    <img src={result.annotatedImage} alt={`Annotated P&ID for ${file.name}`} className="w-full h-auto" />
                                </div>
                                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                                    <a href={result.excelDataUrl} download={`predictions_${getBaseFileName(file.name)}.xlsx`}>
                                        <Button size="lg" className="w-full sm:w-auto">
                                            <Download className="mr-2 h-5 w-5" />
                                            Download Excel
                                        </Button>
                                    </a>
                                    <Button asChild variant="outline" size="lg" className="w-full sm:w-auto">
                                        <Link to="/play-ground">
                                            Go to Playground
                                            <Zap className="ml-2 h-5 w-5" />
                                        </Link>
                                    </Button>
                                </div>
                            </div>
                        )}
                    </div>
                );
              })}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Upload;