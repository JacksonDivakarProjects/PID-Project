/* eslint-disable @typescript-eslint/no-explicit-any */
import { useUpload } from '@/context/UploadContext';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ScrollArea } from '@/components/ui/scroll-area';
import { Link } from 'react-router-dom';
import { AlertTriangle, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';

const Review = () => {
  const { uploadQueue } = useUpload();

  // Find all items in the queue that have been marked as needing review.
  const itemsToReview = uploadQueue.filter(
    (item) => item.status === 'completed' && item.result?.needsReview
  );

  if (itemsToReview.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-mesh py-20 flex items-center justify-center">
        <Card className="p-8 text-center max-w-lg">
          <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-4">No Data to Review</h2>
          <p className="text-muted-foreground mb-6">
            All components were identified successfully. There is nothing to review.
          </p>
          <Button asChild>
            <Link to="/results">Back to Results</Link>
          </Button>
        </Card>
      </div>
    );
  }

  // --- NEW ROBUST HELPER FUNCTIONS ---

  // This function now correctly prioritizes "Component Name" over "class" or "label".
  const getComponentName = (row: any) => {
    return row['Component Name'] || row.class || row.label || 'Unknown Component';
  };

  // This function now calculates the bounding box from x, y, width, and height.
  const getBoundingBox = (row: any) => {
    const { x, y, width, height } = row;
    if (x !== undefined && y !== undefined && width !== undefined && height !== undefined) {
      // Assuming x, y are the center, calculate the top-left and bottom-right corners.
      const x1 = Math.round(x - width / 2);
      const y1 = Math.round(y - height / 2);
      const x2 = Math.round(x + width / 2);
      const y2 = Math.round(y + height / 2);
      return `[${x1}, ${y1}, ${x2}, ${y2}]`;
    }
    return 'Location Not Available';
  };

  return (
    <div className="min-h-screen bg-gradient-mesh py-10">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-2">Review & Validation</h1>
          <p className="text-xl text-muted-foreground">
            The following files have components that could not be identified.
          </p>
        </div>

        <div className="space-y-8">
          {itemsToReview.map((item) => {
            const componentsToDisplay = item.result?.componentData.filter(
              (row: any) => !row.component_id || String(row.component_id).trim().toLowerCase() === 'nothing'
            ) || [];

            return (
              <Card key={item.id} className="p-6 shadow-lg">
                <div className="flex items-center mb-4 border-b pb-4">
                  <FileText className="h-6 w-6 text-primary mr-3 flex-shrink-0" />
                  <h2 className="text-2xl font-semibold truncate" title={item.file.name}>
                    {item.file.name}
                  </h2>
                </div>
                <ScrollArea className="flex-1" style={{ maxHeight: '400px' }}>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Component Name</TableHead>
                        <TableHead>Location (Bounding Box)</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {componentsToDisplay.length > 0 ? (
                        componentsToDisplay.map((row: any, rowIndex: number) => (
                          <TableRow key={rowIndex}>
                            <TableCell className="font-medium">{getComponentName(row)}</TableCell>
                            <TableCell>{getBoundingBox(row)}</TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={2} className="text-center text-muted-foreground">
                            No components were flagged for review in this file.
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </ScrollArea>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Review;