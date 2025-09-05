/* eslint-disable @typescript-eslint/no-explicit-any */
import { useUpload } from "@/context/UploadContext";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Download, FileJson, FileSpreadsheet } from "lucide-react";
import * as XLSX from 'xlsx';
import { Link } from "react-router-dom";
import { UploadQueueItem } from "@/context/UploadContext"; 
import { useToast } from "@/components/ui/use-toast";
import { useState } from "react";

type ResultWithId = UploadQueueItem['result'] & { id: string; file: File };

const Export = () => {
  const { uploadQueue } = useUpload();
  const { toast } = useToast();
  const [loading, setLoading] = useState<string | null>(null);

  const results: ResultWithId[] = uploadQueue
    .filter((item): item is UploadQueueItem & { result: NonNullable<UploadQueueItem['result']> } => 
        item.status === 'completed' && !!item.result
    )
    .map(item => ({
        id: item.id,
        ...item.result,
        file: item.file,
    }));

  const getBaseFileName = (fileName: string) => {
    return fileName.substring(0, fileName.lastIndexOf('.')) || fileName;
  };

  const downloadBlob = (blob: Blob, fileName: string) => {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  };
  
  // Flattens the nested bbox array into separate columns
  const flattenNodeData = (node: any) => {
    const { bbox, ...rest } = node;
    const flattenedNode: any = { ...rest };
    if (Array.isArray(bbox)) {
      flattenedNode['bbox_x1'] = bbox[0];
      flattenedNode['bbox_y1'] = bbox[1];
      flattenedNode['bbox_x2'] = bbox[2];
      flattenedNode['bbox_y2'] = bbox[3];
    }
    return flattenedNode;
  };

  const handleExport = async (format: 'json' | 'csv' | 'excel', result?: ResultWithId) => {
    if (!result) return;

    if (!result.isEnhanced) {
        toast({
            title: "Generation Required",
            description: "Please generate the Component IDs on the Results page before exporting.",
            variant: "destructive",
        });
        return;
    }

    setLoading(`${result.id}-${format}`);

    try {
        const excelResponse = await fetch(result.excelDataUrl!);
        const excelBlob = await excelResponse.blob();

        const formData = new FormData();
        formData.append('image', result.file, result.originalFileName);
        formData.append('excel', excelBlob, `predictions_${getBaseFileName(result.originalFileName)}.xlsx`);

        const apiResponse = await fetch('http://localhost:8000/grp_creation/generate-graph', {
            method: 'POST',
            body: formData,
        });

        if (!apiResponse.ok) {
            const errorData = await apiResponse.json().catch(() => ({ detail: 'An unknown server error occurred.' }));
            throw new Error(errorData.detail || 'Failed to process the files on the server.');
        }

        const responseData = await apiResponse.json();
        const baseName = `pid_graph_${getBaseFileName(result.originalFileName)}`;

        if (format === 'json') {
            const jsonString = JSON.stringify(responseData, null, 2);
            const blob = new Blob([jsonString], { type: 'application/json' });
            downloadBlob(blob, `${baseName}.json`);
        } else {
            const { nodes, edges } = responseData;
            const flattenedNodes = nodes.map(flattenNodeData);

            if (format === 'csv') {
                const nodesSheet = XLSX.utils.json_to_sheet(flattenedNodes);
                const edgesSheet = XLSX.utils.json_to_sheet(edges);

                const nodesCsvString = XLSX.utils.sheet_to_csv(nodesSheet);
                const edgesCsvString = XLSX.utils.sheet_to_csv(edgesSheet);

                // Combine the two CSV strings with a separator for a single file download
                const combinedCsvString = `Nodes\n${nodesCsvString}\n\nEdges\n${edgesCsvString}`;

                const blob = new Blob([combinedCsvString], { type: 'text/csv;charset=utf-8;' });
                downloadBlob(blob, `${baseName}.csv`);

            } else if (format === 'excel') {
                const workbook = XLSX.utils.book_new();
                const nodesSheet = XLSX.utils.json_to_sheet(flattenedNodes);
                const edgesSheet = XLSX.utils.json_to_sheet(edges);
                XLSX.utils.book_append_sheet(workbook, nodesSheet, "Nodes");
                XLSX.utils.book_append_sheet(workbook, edgesSheet, "Edges");
                XLSX.writeFile(workbook, `${baseName}.xlsx`);
            }
        }
    } catch (error: any) {
        toast({
            title: "Export Failed",
            description: error.message || "An unexpected error occurred during export.",
            variant: "destructive",
        });
    } finally {
        setLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-mesh py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Export Graph Data</h1>
          <p className="text-xl text-muted-foreground">
            Download your generated P&ID graph data in various formats.
          </p>
        </div>

        {results.length > 0 ? (
          <div className="space-y-8">
            <div>
              <h2 className="text-2xl font-semibold text-center mb-8">Individual File Exports</h2>
              <div className="space-y-6">
                {results.map(result => (
                  <Card key={result.id} className="p-6">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                      <div className="mb-4 md:mb-0">
                        <p className="text-lg font-semibold text-primary">{result.originalFileName}</p>
                        <p className="text-sm text-muted-foreground">{result.componentData.length} components detected</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" onClick={() => handleExport('excel', result)} disabled={loading === `${result.id}-excel`}>
                          {loading === `${result.id}-excel` ? "Exporting..." : "Export .xlsx"}
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleExport('csv', result)} disabled={loading === `${result.id}-csv`}>
                          {loading === `${result.id}-csv` ? "Exporting..." : "Export .csv"}
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleExport('json', result)} disabled={loading === `${result.id}-json`}>
                          {loading === `${result.id}-json` ? "Exporting..." : "Export .json"}
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <Card className="p-8">
            <p className="text-muted-foreground text-center">
              There is no data to export. Please <Link to="/upload" className="text-primary hover:underline">upload and analyze a P&ID</Link> first.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Export;