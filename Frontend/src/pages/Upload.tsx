import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Upload as UploadIcon, FileImage, FileText, Zap, CheckCircle } from "lucide-react";

const Upload = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [files, setFiles] = useState<File[]>([]);

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
    const droppedFiles = Array.from(e.dataTransfer.files);
    setFiles(droppedFiles);
    simulateUpload();
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(selectedFiles);
      simulateUpload();
    }
  };

  const simulateUpload = () => {
    setUploadProgress(0);
    setIsProcessing(true);
    
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => setIsProcessing(false), 500);
          return 100;
        }
        return prev + Math.random() * 15;
      });
    }, 200);
  };

  return (
    <div className="min-h-screen bg-gradient-mesh py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Upload Your P&ID</h1>
          <p className="text-xl text-muted-foreground">
            Drag and drop your process diagrams or browse to select files
          </p>
        </div>

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
            <div className="space-y-6">
              <div className={`mx-auto w-24 h-24 rounded-full bg-gradient-primary flex items-center justify-center ${isDragging ? 'animate-glow-pulse' : ''}`}>
                <UploadIcon className="h-12 w-12 text-primary-foreground" />
              </div>
              
              <div>
                <h3 className="text-xl font-semibold mb-2">
                  {isDragging ? "Drop files here" : "Upload P&ID Files"}
                </h3>
                <p className="text-muted-foreground mb-4">
                  Supports PDF, PNG, JPG, DWG, and other engineering formats
                </p>
                
                <input
                  type="file"
                  multiple
                  accept=".pdf,.png,.jpg,.jpeg,.dwg,.svg"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                
                <Button asChild variant="gradient" size="lg">
                  <label htmlFor="file-upload" className="cursor-pointer">
                    Browse Files
                  </label>
                </Button>
              </div>

              <div className="flex justify-center space-x-4 text-sm text-muted-foreground">
                <div className="flex items-center">
                  <FileText className="h-4 w-4 mr-1" />
                  PDF
                </div>
                <div className="flex items-center">
                  <FileImage className="h-4 w-4 mr-1" />
                  Images
                </div>
                <div className="flex items-center">
                  <FileText className="h-4 w-4 mr-1" />
                  CAD
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* File List */}
        {files.length > 0 && (
          <Card className="p-6 mb-8">
            <h3 className="text-lg font-semibold mb-4">Selected Files</h3>
            <div className="space-y-3">
              {files.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="flex items-center">
                    <FileText className="h-5 w-5 text-primary mr-3" />
                    <span className="font-medium">{file.name}</span>
                    <span className="text-sm text-muted-foreground ml-2">
                      ({(file.size / 1024 / 1024).toFixed(2)} MB)
                    </span>
                  </div>
                  {uploadProgress === 100 && (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Processing Status */}
        {isProcessing && (
          <Card className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Processing P&ID</h3>
                <div className="flex items-center text-primary">
                  <Zap className="h-5 w-5 mr-2 animate-pulse" />
                  AI Analyzing...
                </div>
              </div>
              
              <Progress value={uploadProgress} className="h-2" />
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
                <div className="flex items-center text-sm">
                  <div className="w-2 h-2 bg-primary rounded-full mr-2 animate-pulse" />
                  Scanning symbols
                </div>
                <div className="flex items-center text-sm">
                  <div className="w-2 h-2 bg-secondary rounded-full mr-2 animate-pulse" />
                  Extracting connections
                </div>
                <div className="flex items-center text-sm">
                  <div className="w-2 h-2 bg-primary rounded-full mr-2 animate-pulse" />
                  Validating data
                </div>
              </div>
            </div>
          </Card>
        )}

        {uploadProgress === 100 && !isProcessing && (
          <Card className="p-6 border-green-200 bg-green-50 dark:bg-green-900/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <CheckCircle className="h-6 w-6 text-green-500 mr-3" />
                <div>
                  <h3 className="font-semibold text-green-800 dark:text-green-300">
                    Processing Complete!
                  </h3>
                  <p className="text-green-600 dark:text-green-400">
                    Your P&ID has been successfully analyzed and converted.
                  </p>
                </div>
              </div>
              <Button className="bg-green-600 hover:bg-green-700">
                View Results
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Upload;