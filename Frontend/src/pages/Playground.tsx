// pages/pid-playground.js
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Stage, Layer, Image, Text, Transformer, Group } from 'react-konva';
import * as XLSX from 'xlsx';
import Konva from 'konva';
// --- Helper Icons (unchanged) ---
const MoveIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 9l-3 3 3 3M9 5l3-3 3 3M15 19l-3 3-3-3M19 9l3 3-3 3M2 12h20M12 2v20"/>
  </svg>
);
const ZoomInIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line>
  </svg>
);
const ZoomOutIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="8" y1="11" x2="14" y2="11"></line>
  </svg>
);
const TextIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 6.1H7a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-11a1 1 0 0 0-1-1Z" /><path d="M12 18V7" /><path d="M9 7h6" />
  </svg>
);
const TrashIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 6h18" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /><line x1="10" y1="11" x2="10" y2="17" /><line x1="14" y1="11" x2="14" y2="17" />
  </svg>
);
const ExportIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line>
  </svg>
);
const UploadIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line>
  </svg>
);
// --- Component Types ---
const COMPONENT_TYPE_IMAGE = 'image';
const COMPONENT_TYPE_TEXT = 'text';
// --- Type Definitions ---
interface ComponentBase {
  id: number;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation?: number;
  scaleX?: number;
  scaleY?: number;
}
interface ImageComponent extends ComponentBase {
  type: typeof COMPONENT_TYPE_IMAGE;
  classNumber: number;
  imageUrl: string;
}
interface TextComponent extends ComponentBase {
  type: typeof COMPONENT_TYPE_TEXT;
  text: string;
  fontSize: number;
}
type CanvasComponent = ImageComponent | TextComponent;
interface XLSComponentData {
  class_number: number;
  x: number;
  y: number;
  width: number;
  height: number;
}
// --- Main Playground Component ---
export default function PIDPlayground() {
  // --- STATE MANAGEMENT ---
  const [components, setComponents] = useState<CanvasComponent[]>([]);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [isEditingText, setIsEditingText] = useState(false);
  const [editingText, setEditingText] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingPosition, setEditingPosition] = useState({ x: 0, y: 0 });
  const [stageSize, setStageSize] = useState({ width: 800, height: 600 });
  const [images, setImages] = useState<Record<string, HTMLImageElement>>({});
  
  // --- REFS ---
  const stageRef = useRef<Konva.Stage>(null);
  const transformerRef = useRef<Konva.Transformer>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // --- MOCK DATA ---
  // Updated to use actual class images from the class_images folder
  const componentImages = Array.from({ length: 32 }, (_, i) => ({
    classNumber: i + 1,
    url: `/class_images/${i + 1}.jpg`, // Updated path to actual images
  }));
  
  // --- INITIALIZATION ---
  useEffect(() => {
    // Load initial mock data
    const initialComponentData: XLSComponentData[] = [
      { class_number: 1, x: 100, y: 150, width: 80, height: 80 },
      { class_number: 5, x: 300, y: 250, width: 100, height: 60 },
      { class_number: 12, x: 500, y: 100, width: 70, height: 120 },
      { class_number: 28, x: 450, y: 400, width: 90, height: 90 },
    ];
    
    const initialItems: CanvasComponent[] = initialComponentData.map((item, index) => ({
      id: index + 1,
      type: COMPONENT_TYPE_IMAGE,
      classNumber: item.class_number,
      x: item.x,
      y: item.y,
      width: item.width,
      height: item.height,
      imageUrl: componentImages.find(img => img.classNumber === item.class_number)?.url || '',
    }));
    
    setComponents(initialItems);
    
    // Set stage size based on container
    const updateStageSize = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setStageSize({
          width: width - 256, // Subtract sidebar width
          height: height - 64, // Subtract toolbar height
        });
      }
    };
    
    updateStageSize();
    window.addEventListener('resize', updateStageSize);
    
    return () => {
      window.removeEventListener('resize', updateStageSize);
    };
  }, []);
  // FIX: Centralized image loader
  // This effect runs whenever `components` changes and loads new images.
  useEffect(() => {
    const newImagesToLoad = components.filter(
      (comp): comp is ImageComponent => comp.type === COMPONENT_TYPE_IMAGE && !!comp.imageUrl && !images[comp.imageUrl]
    );
    
    newImagesToLoad.forEach(component => {
      const img = new window.Image();
      img.src = component.imageUrl;
      img.onload = () => {
        setImages(prev => ({ ...prev, [component.imageUrl]: img }));
      };
      img.onerror = () => {
        console.error(`Failed to load image: ${component.imageUrl}`);
      };
    });
  }, [components, images]);
  
  // --- HANDLERS ---
  const handleStageClick = (e: Konva.KonvaEventObject<MouseEvent>) => {
    if (e.target === e.target.getStage()) {
      setSelectedId(null);
      setIsEditingText(false);
    }
  };
  
  const handleDragEnd = (e: Konva.KonvaEventObject<DragEvent>, id: number) => {
    const node = e.target as Konva.Node;
    setComponents(prevComponents =>
      prevComponents.map(comp =>
        comp.id === id
          ? { ...comp, x: node.x(), y: node.y() }
          : comp
      )
    );
  };
  
  const handleTransformEnd = (e: Konva.KonvaEventObject<Event>, id: number) => {
    const node = e.target as Konva.Node;
    
    // Get the new dimensions directly from the Konva node.
    const newWidth = node.width() * node.scaleX();
    const newHeight = node.height() * node.scaleY();
    const newX = node.x();
    const newY = node.y();
    const newRotation = node.rotation();
    
    // Update the component in state with the new values.
    setComponents(prevComponents =>
      prevComponents.map(comp =>
        comp.id === id
          ? {
              ...comp,
              x: newX,
              y: newY,
              width: newWidth,
              height: newHeight,
              rotation: newRotation,
              scaleX: 1,
              scaleY: 1,
            }
          : comp
      )
    );
    
    node.scaleX(1);
    node.scaleY(1);
  };  
  const handleTextDblClick = (e: Konva.KonvaEventObject<MouseEvent>, id: number, text: string) => {
    const textNode = e.target as Konva.Text;
    setIsEditingText(true);
    setEditingText(text);
    setEditingId(id);
    setEditingPosition({
      x: textNode.x(),
      y: textNode.y(),
    });
  };
  
  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEditingText(e.target.value);
  };
  
  const handleTextBlur = () => {
    if (editingId !== null) {
      setComponents(prevComponents =>
        prevComponents.map(comp =>
          comp.id === editingId && comp.type === COMPONENT_TYPE_TEXT
            ? { ...comp, text: editingText }
            : comp
        )
      );
    }
    setIsEditingText(false);
    setEditingId(null);
  };
  
  // Zoom controls using Konva's built-in methods
  const handleZoomIn = () => {
    const stage = stageRef.current;
    if (stage) {
      const newScale = Math.min(stage.scaleX() * 1.1, 2);
      stage.scale({ x: newScale, y: newScale });
      stage.batchDraw();
      setZoomLevel(newScale);
    }
  };
  
  const handleZoomOut = () => {
    const stage = stageRef.current;
    if (stage) {
      const newScale = Math.max(stage.scaleX() / 1.1, 0.5);
      stage.scale({ x: newScale, y: newScale });
      stage.batchDraw();
      setZoomLevel(newScale);
    }
  };
  
  // Handle wheel event for zooming using Konva's methods
  const handleWheel = (e: Konva.KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault();
    const stage = stageRef.current;
    if (!stage) return;
    
    const oldScale = stage.scaleX();
    const pointer = stage.getPointerPosition();
    if (!pointer) return;
    
    const mousePointTo = {
      x: (pointer.x - stage.x()) / oldScale,
      y: (pointer.y - stage.y()) / oldScale,
    };
    
    const newScale = e.evt.deltaY < 0 ? oldScale * 1.05 : oldScale / 1.05;
    
    stage.scale({ x: newScale, y: newScale });
    
    const newPos = {
      x: pointer.x - mousePointTo.x * newScale,
      y: pointer.y - mousePointTo.y * newScale,
    };
    
    stage.position(newPos);
    stage.batchDraw();
    setZoomLevel(newScale);
  };
  
  const addNewComponent = (classNumber: number, imageUrl: string) => {
    const newId = Date.now();
    const newComponent: ImageComponent = {
      id: newId,
      type: COMPONENT_TYPE_IMAGE,
      classNumber,
      imageUrl,
      x: 100,
      y: 100,
      width: 80,
      height: 80,
    };
    setComponents(prev => [...prev, newComponent]);
    setSelectedId(newId);
  };
  
  const addText = () => {
    const newId = Date.now();
    const newText: TextComponent = {
      id: newId,
      type: COMPONENT_TYPE_TEXT,
      x: 150,
      y: 150,
      width: 150,
      height: 30,
      text: 'Editable Text',
      fontSize: 16,
    };
    setComponents(prev => [...prev, newText]);
    setSelectedId(newId);
  };
  
  const deleteSelectedComponent = () => {
    if (selectedId === null) return;
    setComponents(prev => prev.filter(c => c.id !== selectedId));
    setSelectedId(null);
  };
  
  // FIX: This function now creates text components from the Excel data.
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
          const file = e.target.files?.[0];
          if (!file) return;
          
          const reader = new FileReader();
          reader.onload = (event) => {
             try {
                const data = new Uint8Array(event.target?.result as ArrayBuffer);
                const workbook = XLSX.read(data, { type: 'array' });
                const firstSheetName = workbook.SheetNames[0];
                const worksheet = workbook.Sheets[firstSheetName];
                const jsonData = XLSX.utils.sheet_to_json(worksheet) as XLSComponentData[];
                
                if (jsonData.length === 0 || !('class_number' in jsonData[0])) {
                   alert('Error: Could not parse components. Please ensure your Excel file has the exact headers: class_number, x, y, width, height.');
                   return;
                }
                
                const newComponents: CanvasComponent[] = jsonData.map((item, index) => {
                   
              // FIX: Convert the class_number from the Excel data to a number
              const excelClassNumber = Number(item.class_number);
                   const imageUrl = componentImages.find(img => img.classNumber === excelClassNumber)?.url || '';
                   
                   console.log(`Excel class_number: ${item.class_number} (Type: ${typeof item.class_number}), imageUrl:`, imageUrl);
                   
                   return {
                      id: Date.now() + index,
                      type: COMPONENT_TYPE_IMAGE,
                      classNumber: excelClassNumber,
                      x: item.x ,
                      y: item.y ,
                      width: item.width,
                      height: item.height,
                      imageUrl,
                   };
                });
                
                setComponents(newComponents);
             } catch (error) {
                console.error('Error parsing XLS file:', error);
                alert('Error parsing XLS file. Please check the file format.');
             } finally {
                if (fileInputRef.current) {
                   fileInputRef.current.value = '';
                }
             }
          };
          reader.readAsArrayBuffer(file);
    };
  const exportToJSON = () => {
    const dataStr = JSON.stringify(components, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = 'pid-layout.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };
  
  const exportToXLS = () => {
    const exportData = components
      .filter(comp => comp.type === COMPONENT_TYPE_IMAGE)
      .map(comp => ({
        id: comp.id,
        class_number: (comp as ImageComponent).classNumber,
        x: comp.x,
        y: comp.y,
        width: comp.width,
        height: comp.height,
      }));
    
    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Components');
    
    XLSX.writeFile(workbook, 'pid-layout.xlsx');
  };
  
  // --- EFFECTS ---
  useEffect(() => {
    if (selectedId !== null && transformerRef.current) {
      const selectedNode = stageRef.current?.findOne(`#${selectedId}`);
      if (selectedNode) {
        selectedNode.scale({ x: 1, y: 1 });
        selectedNode.width(selectedNode.width());
        selectedNode.height(selectedNode.height());
        transformerRef.current.nodes([selectedNode]);
        transformerRef.current.getLayer()?.batchDraw();
      }
    } else if (transformerRef.current) {
      transformerRef.current.nodes([]);
    }
  }, [selectedId]);
  // This effect is now obsolete as we are rendering text. You can remove it for now.
  // useEffect(() => {
  //   const newImagesToLoad = components.filter(
  //     (comp): comp is ImageComponent => comp.type === COMPONENT_TYPE_IMAGE && !!comp.imageUrl && !images[comp.imageUrl]
  //   );
  //   newImagesToLoad.forEach(component => {
  //     const img = new window.Image();
  //     img.src = component.imageUrl;
  //     img.onload = () => {
  //       setImages(prev => ({ ...prev, [component.imageUrl]: img }));
  //     };
  //     img.onerror = () => {
  //       console.error(`Failed to load image: ${component.imageUrl}`);
  //     };
  //   });
  // }, [components, images]);
  
  // --- RENDER LOGIC ---
  return (
    <div className="flex flex-col h-screen bg-gray-100 font-sans">
      {/* --- Toolbar --- */}
      <header className="bg-white border-b border-gray-200 p-3 flex items-center justify-between z-10 shadow-sm">
        <div className="flex items-center space-x-2">
          <button 
            onClick={handleZoomIn} 
            className="p-2 rounded-md hover:bg-gray-200 flex items-center" 
            title="Zoom In"
          >
            <ZoomInIcon />
          </button>
          <span className="text-sm font-medium text-gray-600 w-12 text-center">{(zoomLevel * 100).toFixed(0)}%</span>
          <button 
            onClick={handleZoomOut} 
            className="p-2 rounded-md hover:bg-gray-200 flex items-center" 
            title="Zoom Out"
          >
            <ZoomOutIcon />
          </button>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-sm font-bold text-gray-700">Components: {components.length}</span>
          <div className="border-l border-gray-300 h-6 mx-1"></div>
          
          <button 
            onClick={addText} 
            className="p-2 rounded-md hover:bg-gray-200 flex items-center space-x-1" 
            title="Add Text"
          >
            <TextIcon />
            <span className="text-sm font-medium">Add Text</span>
          </button>
          
          {selectedId && (
            <button 
              onClick={deleteSelectedComponent} 
              className="p-2 rounded-md hover:bg-red-100 text-red-600 flex items-center space-x-1" 
              title="Delete Selected"
            >
              <TrashIcon />
              <span className="text-sm font-medium">Delete</span>
            </button>
          )}
          
          <div className="border-l border-gray-300 h-6 mx-1"></div>
          
          <button 
            onClick={() => fileInputRef.current?.click()} 
            className="p-2 rounded-md hover:bg-gray-200 flex items-center space-x-1" 
            title="Upload XLS"
          >
            <UploadIcon />
            <span className="text-sm font-medium">Upload</span>
          </button>
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden" 
            accept=".xlsx,.xls" 
            onChange={handleFileUpload} 
          />
          
          <div className="relative group">
            <button className="p-2 rounded-md hover:bg-gray-200 flex items-center space-x-1" title="Export">
              <ExportIcon />
              <span className="text-sm font-medium">Export</span>
            </button>
            <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg py-1 z-20 hidden group-hover:block">
              <button 
                onClick={exportToJSON} 
                className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
              >
                Export as JSON
              </button>
              <button 
                onClick={exportToXLS} 
                className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
              >
                Export as XLS
              </button>
            </div>
          </div>
        </div>
      </header>
      
      <div className="flex flex-1 overflow-hidden">
        {/* --- Component Palette Sidebar --- */}
        <aside className="w-64 bg-white border-r border-gray-200 p-4 flex flex-col overflow-y-auto">
          <h2 className="text-lg font-bold text-gray-700 mb-4">Components</h2>
          <div className="grid grid-cols-3 gap-3">
            {componentImages.map(img => (
              <button
                key={img.classNumber}
                onClick={() => addNewComponent(img.classNumber, img.url)}
                className="border border-gray-300 rounded-lg p-1 hover:bg-gray-100 hover:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200"
                title={`Add Component C${img.classNumber}`}
              >
                <img 
                  src={img.url} 
                  alt={`Component C${img.classNumber}`} 
                  className="w-full h-auto object-contain"
                  onError={(e) => {
                    // Fallback to placeholder if image fails to load
                    const target = e.target as HTMLImageElement;
                    target.src = `https://placehold.co/100x100/E2E8F0/4A5568?text=C${img.classNumber}`;
                  }}
                />
              </button>
            ))}
          </div>
        </aside>
        
        {/* --- Canvas Area --- */}
        <main className="flex-1 bg-gray-50 overflow-auto relative" ref={containerRef}>
          <Stage
            width={stageSize.width}
            height={stageSize.height}
            ref={stageRef}
            onWheel={handleWheel}
            onClick={handleStageClick}
            draggable
          >
            <Layer>
              {/* FIX: Updated rendering logic to handle both image and text components */}
              {components.map(component => {
                if (component.type === COMPONENT_TYPE_IMAGE) {
                  return (
                    <Group
                      key={component.id}
                      id={component.id.toString()}
                      x={component.x}
                      y={component.y}
                      width={component.width}
                      height={component.height}
                      draggable
                      onDragEnd={(e) => handleDragEnd(e, component.id)}
                      onTransformEnd={(e) => handleTransformEnd(e, component.id)}
                      onClick={() => setSelectedId(component.id)}
                    >
                      <Image
                        width={component.width}
                        height={component.height}
                        image={images[component.imageUrl]}
                      />
                    </Group>
                  );
                }
                
                if (component.type === COMPONENT_TYPE_TEXT) {
                  return (
                    <Text
                      key={component.id}
                      id={component.id.toString()}
                      x={component.x}
                      y={component.y}
                      text={component.text}
                      fontSize={component.fontSize}
                      draggable
                      onDragEnd={(e) => handleDragEnd(e, component.id)}
                      onTransformEnd={(e) => handleTransformEnd(e, component.id)}
                      onClick={() => setSelectedId(component.id)}
                      onDblClick={(e) => handleTextDblClick(e, component.id, component.text)}
                    />
                  );
                }
                
                return null;
              })}
              
              <Transformer
                ref={transformerRef}
                enabledAnchors={['top-left', 'top-right', 'bottom-left', 'bottom-right']}
                boundBoxFunc={(oldBox, newBox) => {
                  // Limit resize
                  if (newBox.width < 20 || newBox.height < 20) {
                    return oldBox;
                  }
                  return newBox;
                }}
              />
            </Layer>
          </Stage>
          
          {/* Text Editor Overlay */}
          {isEditingText && (
            <div
              className="absolute bg-white border border-blue-500 rounded shadow-lg p-2 z-10"
              style={{
                left: editingPosition.x * zoomLevel,
                top: editingPosition.y * zoomLevel,
                transform: `scale(${zoomLevel})`,
                transformOrigin: 'top left',
              }}
            >
              <input
                type="text"
                value={editingText}
                onChange={handleTextChange}
                onBlur={handleTextBlur}
                autoFocus
                className="outline-none border-none bg-transparent"
                style={{ fontSize: '16px' }}
              />
            </div>
          )}
          
          {/* Zoom Controls */}
          <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-md p-2 flex items-center space-x-2">
            <button 
              onClick={handleZoomOut} 
              className="p-1 rounded-md hover:bg-gray-200"
              title="Zoom Out"
            >
              <ZoomOutIcon />
            </button>
            <span className="text-sm font-medium text-gray-600 w-12 text-center">{(zoomLevel * 100).toFixed(0)}%</span>
            <button 
              onClick={handleZoomIn} 
              className="p-1 rounded-md hover:bg-gray-200"
              title="Zoom In"
            >
              <ZoomInIcon />
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}