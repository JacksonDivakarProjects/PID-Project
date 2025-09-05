/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from 'react';
import { useUpload } from '../context/UploadContext';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
    Eye,
    FileText,
    CheckCircle,
    Zap,
    Clock,
    AlertTriangle,
    ArrowRight,
    Sparkles,
    Loader2
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import ImageViewer from '@/components/ImageViewer';
import * as XLSX from 'xlsx';

const Results = () => {
    const { uploadQueue, updateEnhancedExcel } = useUpload();
    const [viewingImage, setViewingImage] = useState<string | null>(null);
    const [enhancingId, setEnhancingId] = useState<string | null>(null);
    const [apiError, setApiError] = useState<string | null>(null);
    const navigate = useNavigate();

    const getBaseFileName = (fileName: string) => {
        if (!fileName) return '';
        return fileName.substring(0, fileName.lastIndexOf('.')) || fileName;
    };

    const handleNavigateToExport = (item: any) => {
        if (!item.result?.excelDataUrl) return;
        navigate('/export', {
            state: {
                excelDataUrl: item.result.excelDataUrl,
                originalFileName: item.file.name,
            },
        });
    };

    const handleEnhanceExcel = async (item: any) => {
        if (!item.result?.excelDataUrl || !item.file) {
            setApiError("Cannot generate report: Missing original image or initial Excel file.");
            return;
        }

        setEnhancingId(item.id);
        setApiError(null);

        try {
            const excelResponse = await fetch(item.result.excelDataUrl);
            const excelBlob = await excelResponse.blob();

            const formData = new FormData();
            formData.append('image_file', item.file, item.file.name);
            formData.append('excel_file', excelBlob, `predictions_${getBaseFileName(item.file.name)}.xlsx`);

            const apiResponse = await fetch('http://localhost:8000/excel_ocr/process-excel-with-image', {
                method: 'POST',
                body: formData,
            });

            if (!apiResponse.ok) {
                const errorData = await apiResponse.json().catch(() => ({ detail: 'An unknown server error occurred.' }));
                throw new Error(errorData.detail || 'Failed to process the files on the server.');
            }

            const responseData = await apiResponse.json();
            if (!responseData.file_base64 || !responseData.filename) {
                throw new Error("API response is missing the required file data.");
            }

            const binaryString = window.atob(responseData.file_base64);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            const newExcelBlob = new Blob([bytes], { type: responseData.mime_type });
            
            const arrayBuffer = await newExcelBlob.arrayBuffer();
            const workbook = XLSX.read(arrayBuffer, { type: 'array' });
            const sheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[sheetName];
            const newComponentData = XLSX.utils.sheet_to_json(worksheet) as any[];

            // --- MODIFIED & MORE ROBUST CHECK ---
            const needsReview = newComponentData.some(row => 
                !row.component_id || String(row.component_id).trim().toLowerCase() === 'nothing'
            );
            
            await updateEnhancedExcel(item.id, newExcelBlob, needsReview);

        } catch (err: any) {
            console.error("Enhancement failed:", err);
            setApiError(err.message || "An unexpected error occurred while generating the report.");
        } finally {
            setEnhancingId(null);
        }
    };

    return (
        <>
            <div className="min-h-screen bg-gradient-mesh py-20">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-12">
                        <h1 className="text-4xl font-bold mb-4">Upload History & Status</h1>
                        <p className="text-xl text-muted-foreground">
                            Review the status and results of all your uploaded files.
                        </p>
                    </div>

                    {apiError && (
                         <Card className="p-4 mb-6 bg-destructive/10 text-destructive border-destructive">
                            <div className="flex items-center">
                                <AlertTriangle className="h-5 w-5 mr-3 flex-shrink-0" />
                                <p>{apiError}</p>
                            </div>
                        </Card>
                    )}

                    <div className="space-y-8">
                        {uploadQueue.length > 0 ? (
                            [...uploadQueue].reverse().map((item) => {
                                const isEnhanced = item.result?.isEnhanced;
                                const needsReview = item.result?.needsReview;

                                return (
                                <Card key={item.id} className="p-6 transition-all">
                                    <div className="flex items-center mb-4 border-b pb-4">
                                        <FileText className="h-6 w-6 text-primary mr-3 flex-shrink-0" />
                                        <h2 className="text-xl font-semibold truncate" title={item.file.name}>
                                            {item.file.name}
                                        </h2>
                                    </div>

                                    {item.status === 'completed' && item.result && (
                                        <div className="text-center">
                                            <div className="flex items-center justify-center text-green-500 mb-6">
                                                <CheckCircle className="h-5 w-5 mr-2" />
                                                <p className="font-medium">Analysis Completed</p>
                                            </div>
                                            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 flex-wrap">
                                                {item.result.annotatedImage && (
                                                    <Button size="lg" variant="outline" onClick={() => setViewingImage(item.result!.annotatedImage)}>
                                                        <Eye className="mr-2 h-5 w-5" />
                                                        View Annotated Image
                                                    </Button>
                                                )}

                                                {item.result.excelDataUrl && !needsReview && (
                                                    <Button size="lg" variant="outline" onClick={() => handleNavigateToExport(item)}>
                                                        <ArrowRight className="mr-2 h-5 w-5" />
                                                        Export Data
                                                    </Button>
                                                )}

                                                {item.result.excelDataUrl && (
                                                    isEnhanced ? (
                                                        needsReview ? (
                                                            <Button asChild size="lg" variant="destructive">
                                                                <Link to="/review" state={{ 
                                                                    itemId: item.id,
                                                                    annotatedImage: item.result.annotatedImage,
                                                                    componentData: item.result.componentData,
                                                                    originalFileName: item.file.name
                                                                }}>
                                                                    <AlertTriangle className="mr-2 h-5 w-5" />
                                                                    Review Needed
                                                                </Link>
                                                            </Button>
                                                        ) : (
                                                            <Button size="lg" disabled>
                                                                <CheckCircle className="mr-2 h-5 w-5" />
                                                                Component IDs Generated
                                                            </Button>
                                                        )
                                                    ) : (
                                                        <Button
                                                            size="lg"
                                                            onClick={() => handleEnhanceExcel(item)}
                                                            disabled={enhancingId === item.id}
                                                        >
                                                            {enhancingId === item.id ? (
                                                                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                                            ) : (
                                                                <Sparkles className="mr-2 h-5 w-5" />
                                                            )}
                                                            {enhancingId === item.id ? 'Generating...' : 'Get Component ID'}
                                                        </Button>
                                                    )
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {item.status === 'processing' && ( <div className="flex items-center justify-center p-4"> <Zap className="h-6 w-6 text-primary mr-3 animate-pulse" /> <p className="text-lg font-medium text-muted-foreground">Analysis in Progress...</p> </div> )}
                                    {item.status === 'queued' && ( <div className="flex items-center justify-center p-4"> <Clock className="h-6 w-6 text-amber-500 mr-3" /> <p className="text-lg font-medium text-muted-foreground">Queued for Processing</p> </div> )}
                                    {item.status === 'error' && ( <div className="flex items-center bg-destructive/10 text-destructive p-4 rounded-md"> <AlertTriangle className="h-6 w-6 mr-3 flex-shrink-0" /> <div> <h3 className="font-semibold">Processing Failed</h3> <p className="text-sm">{item.error || "An unknown error occurred."}</p> </div> </div> )}
                                </Card>
                            )})
                        ) : (
                            <Card className="p-8">
                                <p className="text-muted-foreground text-center">
                                    No files have been uploaded yet. Please <Link to="/upload" className="text-primary hover:underline">upload a P&ID</Link> to get started.
                                </p>
                            </Card>
                        )}
                    </div>
                </div>
            </div>

            {viewingImage && (
                <ImageViewer
                    imageUrl={viewingImage}
                    onClose={() => setViewingImage(null)}
                />
            )}
        </>
    );
};

export default Results;