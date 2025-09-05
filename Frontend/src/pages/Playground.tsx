/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useRef, useEffect } from 'react';
import { Stage, Layer, Image, Text, Transformer, Group, Line } from 'react-konva';
import * as XLSX from 'xlsx';
import Konva from 'konva';
import { useTheme } from 'next-themes';

// --- Helper Icons ---
const ConnectIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="6" cy="18" r="3" /><circle cx="18" cy="6" r="3" /><line x1="8" y1="16" x2="16" y2="8" />
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
const UndoIcon = () => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 7v6h6"></path>
      <path d="M21 17a9 9 0 0 0-9-9a9 9 0 0 0-6 2.3L3 13"></path>
    </svg>
);
const RedoIcon = () => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 7v6h-6"></path>
      <path d="M3 17a9 9 0 0 1 9-9a9 9 0 0 1 6 2.3l3 2.7"></path>
    </svg>
);


// --- Component Types ---
const COMPONENT_TYPE_IMAGE = 'image';
const COMPONENT_TYPE_TEXT = 'text';

// --- Type Definitions ---
interface ComponentBase {
  id: string;
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

interface Connection {
    id: string;
    from: string;
    to: string;
}

type HistoryState = {
    components: CanvasComponent[];
    connections: Connection[];
};

// --- Main Playground Component ---
export default function PIDPlayground() {
  // --- STATE MANAGEMENT ---
  const [components, setComponents] = useState<CanvasComponent[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [isEditingText, setIsEditingText] = useState(false);
  const [editingText, setEditingText] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingPosition, setEditingPosition] = useState({ x: 0, y: 0 });
  const [stageSize, setStageSize] = useState({ width: 800, height: 600 });
  const [images, setImages] = useState<Record<string, HTMLImageElement>>({});
  const [isConnecting, setIsConnecting] = useState(false);
  const [startComponent, setStartComponent] = useState<string | null>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  
  const [history, setHistory] = useState<HistoryState[]>([{ components: [], connections: [] }]);
  const [historyIndex, setHistoryIndex] = useState(0);

  const { theme } = useTheme();

  // --- REFS ---
  const stageRef = useRef<Konva.Stage>(null);
  const transformerRef = useRef<Konva.Transformer>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const componentImages = Array.from({ length: 32 }, (_, i) => ({
    classNumber: i + 1,
    url: `/Class_Images/${i + 1}.jpg`,
  }));
  
  // --- HISTORY MANAGEMENT ---
  const pushToHistory = (newComponents: CanvasComponent[], newConnections: Connection[]) => {
    const currentState = { components: newComponents, connections: newConnections };
    const newHistory = history.slice(0, historyIndex + 1);
    setHistory([...newHistory, currentState]);
    setHistoryIndex(newHistory.length);
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      const prevState = history[newIndex];
      setComponents(prevState.components);
      setConnections(prevState.connections);
      setHistoryIndex(newIndex);
      setSelectedId(null);
      setSelectedEdgeId(null);
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1;
      const nextState = history[newIndex];
      setComponents(nextState.components);
      setConnections(nextState.connections);
      setHistoryIndex(newIndex);
      setSelectedId(null);
      setSelectedEdgeId(null);
    }
  };
  
  // --- INITIALIZATION ---
  useEffect(() => {
    const updateStageSize = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setStageSize({
          width: width - 256,
          height: height - 64,
        });
      }
    };
    
    updateStageSize();
    window.addEventListener('resize', updateStageSize);
    
    const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
            setIsConnecting(false);
            setStartComponent(null);
            setSelectedId(null);
            setSelectedEdgeId(null);
        }
        if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
            e.preventDefault();
            handleUndo();
        }
        if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
            e.preventDefault();
            handleRedo();
        }
    };
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('resize', updateStageSize);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [historyIndex, history]);

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
      setSelectedEdgeId(null);
      setIsEditingText(false);
      setIsConnecting(false);
      setStartComponent(null);
    }
  };

  const handleComponentClick = (id: string) => {
    if (isConnecting) {
        if (startComponent === null) {
            setStartComponent(id);
        } else if (startComponent !== id) {
            const newConnection = { id: `${startComponent}-${id}-${Date.now()}`, from: startComponent, to: id };
            const newConnections = [...connections, newConnection];
            setConnections(newConnections);
            pushToHistory(components, newConnections);
            setStartComponent(null);
            setIsConnecting(false);
        }
    } else {
        setSelectedId(id);
        setSelectedEdgeId(null);
    }
  };

  const handleEdgeClick = (id: string) => {
      setSelectedId(null);
      setSelectedEdgeId(id);
      setIsConnecting(false);
  };
  
  const handleDragMove = (e: Konva.KonvaEventObject<DragEvent>, id: string) => {
    const node = e.target as Konva.Node;
    setComponents(prevComponents =>
      prevComponents.map(comp =>
        comp.id === id
          ? { ...comp, x: node.x(), y: node.y() }
          : comp
      )
    );
  };

  const handleDragEnd = (e: Konva.KonvaEventObject<DragEvent>, id: string) => {
    const node = e.target as Konva.Node;
    const newComponents = components.map(comp =>
        comp.id === id ? { ...comp, x: node.x(), y: node.y() } : comp
    );
    setComponents(newComponents);
    pushToHistory(newComponents, connections);
  };
  
  // MODIFIED: This function now correctly resizes text font size.
  const handleTransformEnd = (e: Konva.KonvaEventObject<Event>, id: string) => {
    const node = e.target as Konva.Node;

    const newComponents = components.map(comp => {
      if (comp.id === id) {
        const scaleX = node.scaleX();
        const scaleY = node.scaleY();

        // important: reset scale for next transformations
        node.scaleX(1);
        node.scaleY(1);

        const newProps = {
          x: node.x(),
          y: node.y(),
          rotation: node.rotation(),
          width: Math.max(20, node.width() * scaleX), // enforce a minimum width
          height: Math.max(10, node.height() * scaleY), // enforce a minimum height
        };
        
        // If it's a text component, we also update the font size
        if (comp.type === COMPONENT_TYPE_TEXT) {
          return {
            ...comp,
            ...newProps,
            fontSize: Math.round(comp.fontSize * scaleY),
          };
        }
        
        // For other components (like images), just update the props
        return {
          ...comp,
          ...newProps,
        };
      }
      return comp;
    });

    setComponents(newComponents);
    pushToHistory(newComponents, connections);
  };
  
  const handleTextDblClick = (e: Konva.KonvaEventObject<Event>, id: string, text: string) => {
    const textNode = e.target as Konva.Text;
    setIsEditingText(true);
    setEditingText(text);
    setEditingId(id);
    setEditingPosition({ x: textNode.getAbsolutePosition().x, y: textNode.getAbsolutePosition().y });
  };
  
  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEditingText(e.target.value);
  };
  
  const handleTextBlur = () => {
    if (editingId !== null) {
      const newComponents = components.map(comp =>
          comp.id === editingId && comp.type === COMPONENT_TYPE_TEXT
            ? { ...comp, text: editingText }
            : comp
      );
      setComponents(newComponents);
      pushToHistory(newComponents, connections);
    }
    setIsEditingText(false);
    setEditingId(null);
  };
  
  const handleZoomIn = () => {
    const stage = stageRef.current;
    if (stage) {
      const newScale = Math.min(stage.scaleX() * 1.1, 2);
      stage.scale({ x: newScale, y: newScale });
      setZoomLevel(newScale);
    }
  };
  
  const handleZoomOut = () => {
    const stage = stageRef.current;
    if (stage) {
      const newScale = Math.max(stage.scaleX() / 1.1, 0.5);
      stage.scale({ x: newScale, y: newScale });
      setZoomLevel(newScale);
    }
  };
  
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
    setZoomLevel(newScale);
  };

  const handleMouseMove = (e: Konva.KonvaEventObject<MouseEvent>) => {
      if (isConnecting && startComponent !== null) {
          const stage = e.target.getStage();
          if (stage) {
              const pos = stage.getRelativePointerPosition();
              if (pos) {
                  setMousePosition(pos);
              }
          }
      }
  };
  
  const addNewComponent = (classNumber: number, imageUrl: string) => {
    const newId = `comp-${Date.now()}`;
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
    const newComponents = [...components, newComponent];
    setComponents(newComponents);
    pushToHistory(newComponents, connections);
    setSelectedId(newId);
  };
  
  const addText = () => {
    const newId = `text-${Date.now()}`;
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
    const newComponents = [...components, newText];
    setComponents(newComponents);
    pushToHistory(newComponents, connections);
    setSelectedId(newId);
  };
  
  const handleDelete = () => {
    let newComponents = [...components];
    let newConnections = [...connections];

    if (selectedId) {
      newComponents = components.filter(c => c.id !== selectedId);
      newConnections = connections.filter(conn => conn.from !== selectedId && conn.to !== selectedId);
      setSelectedId(null);
    }
    if (selectedEdgeId) {
        newConnections = connections.filter(conn => conn.id !== selectedEdgeId);
        setSelectedEdgeId(null);
    }

    setComponents(newComponents);
    setConnections(newConnections);
    pushToHistory(newComponents, newConnections);
  };

  const findClosestComponent = (point: number[], componentsToSearch: CanvasComponent[]) => {
      let closestComponent: CanvasComponent | null = null;
      let minDistance = Infinity;
      componentsToSearch.forEach(component => {
          const componentCenter = { x: component.x + component.width / 2, y: component.y + component.height / 2 };
          const distance = Math.sqrt(Math.pow(point[0] - componentCenter.x, 2) + Math.pow(point[1] - componentCenter.y, 2));
          if (distance < minDistance) {
              minDistance = distance;
              closestComponent = component;
          }
      });
      return closestComponent;
  };
  
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const fileContent = event.target?.result as string;
        const data = JSON.parse(fileContent);

        if (!data.components || !data.lines || !data.lines.segments) {
          alert('Error: Invalid JSON format. Missing "components" or "lines.segments" array.');
          return;
        }

        const newComponents: CanvasComponent[] = data.components.map((comp: any, index: number) => {
            const classNumber = parseInt(comp.class, 10);
            return {
                id: `comp-${index}-${Date.now()}`, type: COMPONENT_TYPE_IMAGE, classNumber,
                x: comp.x - comp.width / 2, y: comp.y - comp.height / 2, width: comp.width, height: comp.height,
                imageUrl: componentImages.find(img => img.classNumber === classNumber)?.url || '',
            };
        });

        const newConnections: Connection[] = data.lines.segments.map((segment: any[], index: number) => {
            const fromComponent = findClosestComponent(segment[0], newComponents);
            const toComponent = findClosestComponent(segment[segment.length - 1], newComponents);
            if (fromComponent && toComponent && fromComponent.id !== toComponent.id) {
                return { id: `edge-${index}-${Date.now()}`, from: fromComponent.id, to: toComponent.id };
            }
            return null;
        }).filter((conn: Connection | null): conn is Connection => conn !== null);

        setComponents(newComponents);
        setConnections(newConnections);
        pushToHistory(newComponents, newConnections);

      } catch (error) {
        console.error('Error parsing JSON file:', error);
        alert('Error parsing JSON file. Please check the file format.');
      } finally {
        if (fileInputRef.current) fileInputRef.current.value = '';
      }
    };
    reader.readAsText(file);
  };

  const exportToJSON = () => {
    const exportData = { components, connections };
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = 'pid-layout.json';
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };
  
  const exportToXLS = () => {
    const exportData = components
      .filter((comp): comp is ImageComponent => comp.type === COMPONENT_TYPE_IMAGE)
      .map(comp => ({ id: comp.id, class_number: comp.classNumber, x: comp.x, y: comp.y, width: comp.width, height: comp.height }));
    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Components');
    XLSX.writeFile(workbook, 'pid-layout.xlsx');
  };
  
  useEffect(() => {
    if (selectedId !== null && transformerRef.current) {
      const selectedNode = stageRef.current?.findOne(`#${selectedId}`);
      if (selectedNode) {
        transformerRef.current.nodes([selectedNode]);
        transformerRef.current.getLayer()?.batchDraw();
      }
    } else if (transformerRef.current) {
      transformerRef.current.nodes([]);
    }
  }, [selectedId]);

  const getComponentCenter = (componentId: string) => {
    const component = components.find(c => c.id === componentId);
    if (!component) return { x: 0, y: 0 };
    return { x: component.x + component.width / 2, y: component.y + component.height / 2 };
  };

  const isDarkMode = theme === 'dark';

  return (
    <div className={`flex flex-col h-screen font-sans ${isDarkMode ? 'dark bg-gray-900 text-gray-100' : 'bg-gray-100 text-gray-900'}`}>
      <header className={`p-3 flex items-center justify-between z-10 shadow-sm ${isDarkMode ? 'bg-gray-800 border-b border-gray-700' : 'bg-white border-b border-gray-200'}`}>
        <div className="flex items-center space-x-2">
          <button onClick={handleZoomIn} className={`p-2 rounded-md flex items-center ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`} title="Zoom In"><ZoomInIcon /></button>
          <span className={`text-sm font-medium w-12 text-center ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{(zoomLevel * 100).toFixed(0)}%</span>
          <button onClick={handleZoomOut} className={`p-2 rounded-md flex items-center ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`} title="Zoom Out"><ZoomOutIcon /></button>
          <div className={`border-l h-6 mx-1 ${isDarkMode ? 'border-gray-600' : 'border-gray-300'}`}></div>
          <button onClick={handleUndo} disabled={historyIndex === 0} className={`p-2 rounded-md flex items-center disabled:opacity-50 disabled:cursor-not-allowed ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`} title="Undo (Ctrl+Z)"><UndoIcon /></button>
          <button onClick={handleRedo} disabled={historyIndex >= history.length - 1} className={`p-2 rounded-md flex items-center disabled:opacity-50 disabled:cursor-not-allowed ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`} title="Redo (Ctrl+Y)"><RedoIcon /></button>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className={`text-sm font-bold ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>Components: {components.length}</span>
          <div className={`border-l h-6 mx-1 ${isDarkMode ? 'border-gray-600' : 'border-gray-300'}`}></div>
          <button 
            onClick={() => { setIsConnecting(prev => !prev); setStartComponent(null); setSelectedId(null); }}
            className={`p-2 rounded-md flex items-center space-x-1 ${isConnecting ? (isDarkMode ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-600') : (isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200')}`} 
            title="Connect Components"
          >
              <ConnectIcon />
              <span className="text-sm font-medium">Connect</span>
          </button>
          <button onClick={addText} className={`p-2 rounded-md flex items-center space-x-1 ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`} title="Add Text"><TextIcon /><span className="text-sm font-medium">Add Text</span></button>
          {(selectedId || selectedEdgeId) && (
            <button onClick={handleDelete} className={`p-2 rounded-md flex items-center space-x-1 ${isDarkMode ? 'hover:bg-red-900 text-red-400' : 'hover:bg-red-100 text-red-600'}`} title="Delete Selected"><TrashIcon /><span className="text-sm font-medium">Delete</span></button>
          )}
          <div className={`border-l h-6 mx-1 ${isDarkMode ? 'border-gray-600' : 'border-gray-300'}`}></div>
          <button onClick={() => fileInputRef.current?.click()} className={`p-2 rounded-md flex items-center space-x-1 ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`} title="Upload JSON/XLS"><UploadIcon /><span className="text-sm font-medium">Upload</span></button>
          <input type="file" ref={fileInputRef} className="hidden" accept=".json" onChange={handleFileUpload} />
          <div className="relative group">
            <button className={`p-2 rounded-md flex items-center space-x-1 ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`} title="Export"><ExportIcon /><span className="text-sm font-medium">Export</span></button>
            <div className={`absolute right-0 mt-1 w-48 rounded-md shadow-lg py-1 z-20 hidden group-hover:block ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
              <button onClick={exportToJSON} className={`block px-4 py-2 text-sm w-full text-left ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-100'}`}>Export as JSON</button>
              <button onClick={exportToXLS} className={`block px-4 py-2 text-sm w-full text-left ${isDarkMode ? 'text-gray-300 hover:bg-gray-700' : 'text-gray-700 hover:bg-gray-100'}`}>Export as XLS</button>
            </div>
          </div>
        </div>
      </header>
      
      <div className="flex flex-1 overflow-hidden">
        <aside className={`w-64 p-4 flex flex-col overflow-y-auto ${isDarkMode ? 'bg-gray-800 border-r border-gray-700' : 'bg-white border-r border-gray-200'}`}>
          <h2 className={`text-lg font-bold mb-4 ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>Components</h2>
          <div className="grid grid-cols-3 gap-3">
            {componentImages.map(img => (
              <button key={img.classNumber} onClick={() => addNewComponent(img.classNumber, img.url)} className={`rounded-lg p-1 transition-all duration-200 ${isDarkMode ? 'border border-gray-600 hover:bg-gray-700 hover:border-blue-400' : 'border border-gray-300 hover:bg-gray-100 hover:border-blue-500'}`} title={`Add Component C${img.classNumber}`}>
                <img src={img.url} alt={`Component C${img.classNumber}`} className={`w-full h-auto object-contain ${isDarkMode ? 'bg-gray-300' : ''}`} onError={(e) => { const target = e.target as HTMLImageElement; target.src = `https://placehold.co/100x100/E2E8F0/4A5568?text=C${img.classNumber}`; }} />
              </button>
            ))}
          </div>
        </aside>
        
        <main className={`flex-1 overflow-auto relative ${isConnecting ? 'cursor-crosshair' : ''} ${isDarkMode ? 'bg-gray-900' : 'bg-gray-50'}`} ref={containerRef}>
          <Stage
            width={stageSize.width}
            height={stageSize.height}
            ref={stageRef}
            onWheel={handleWheel}
            onClick={handleStageClick}
            onMouseMove={handleMouseMove}
            draggable
          >
            <Layer>
              {connections.map(conn => {
                  const fromCenter = getComponentCenter(conn.from);
                  const toCenter = getComponentCenter(conn.to);
                  return (
                      <Line
                          key={conn.id}
                          points={[fromCenter.x, fromCenter.y, toCenter.x, toCenter.y]}
                          stroke={selectedEdgeId === conn.id ? "red" : (isDarkMode ? "white" : "black")}
                          strokeWidth={selectedEdgeId === conn.id ? 4 : 2}
                          onClick={() => handleEdgeClick(conn.id)}
                          onTap={() => handleEdgeClick(conn.id)}
                          hitStrokeWidth={10}
                      />
                  );
              })}

              {components.map(component => {
                if (component.type === COMPONENT_TYPE_IMAGE) {
                  return (
                    <Group
                      key={component.id} id={String(component.id)}
                      x={component.x} y={component.y}
                      width={component.width} height={component.height}
                      rotation={component.rotation}
                      draggable
                      onDragMove={(e) => handleDragMove(e, component.id)}
                      onDragEnd={(e) => handleDragEnd(e, component.id)}
                      onTransformEnd={(e) => handleTransformEnd(e, component.id)}
                      onClick={() => handleComponentClick(component.id)}
                      onTap={() => handleComponentClick(component.id)}
                    >
                      <Image image={images[component.imageUrl]} width={component.width} height={component.height}/>
                    </Group>
                  );
                }
                
                if (component.type === COMPONENT_TYPE_TEXT) {
                  return (
                    <Text
                      key={component.id} id={String(component.id)}
                      x={component.x} y={component.y}
                      text={component.text} fontSize={component.fontSize}
                      fill={isDarkMode ? 'white' : 'black'}
                      draggable
                      width={component.width} // Use width for wrapping
                      onDragMove={(e) => handleDragMove(e, component.id)}
                      onDragEnd={(e) => handleDragEnd(e, component.id)}
                      onTransformEnd={(e) => handleTransformEnd(e, component.id)}
                      onClick={() => handleComponentClick(component.id)}
                      onTap={() => handleComponentClick(component.id)}
                      onDblClick={(e) => handleTextDblClick(e, component.id, component.text)}
                      onDblTap={(e) => handleTextDblClick(e, component.id, component.text)}
                    />
                  );
                }
                return null;
              })}

              {isConnecting && startComponent && (
                  <Line
                      points={[
                          getComponentCenter(startComponent).x, getComponentCenter(startComponent).y,
                          mousePosition.x, mousePosition.y
                      ]}
                      stroke="dodgerblue" strokeWidth={2} dash={[4, 4]}
                  />
              )}
              
              <Transformer
                ref={transformerRef}
                enabledAnchors={['top-left', 'top-right', 'bottom-left', 'bottom-right']}
                boundBoxFunc={(oldBox, newBox) => {
                  if (newBox.width < 20 || newBox.height < 20) return oldBox;
                  return newBox;
                }}
              />
            </Layer>
          </Stage>
          
          {isEditingText && (
             <div style={{ position: 'absolute', top: editingPosition.y, left: editingPosition.x, }}>
                <input
                    type="text" value={editingText}
                    onChange={handleTextChange} onBlur={handleTextBlur}
                    autoFocus
                    style={{
                        fontSize: `${16 * zoomLevel}px`, border: '1px solid #ccc',
                        padding: '2px', margin: 0,
                        background: isDarkMode ? '#374151' : 'white',
                        color: isDarkMode ? 'white' : 'black'
                    }}
                />
             </div>
          )}
          
          <div className={`absolute bottom-4 right-4 rounded-lg shadow-md p-2 flex items-center space-x-2 ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
            <button onClick={handleZoomOut} className={`p-1 rounded-md ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`} title="Zoom Out"><ZoomOutIcon /></button>
            <span className={`text-sm font-medium w-12 text-center ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{(zoomLevel * 100).toFixed(0)}%</span>
            <button onClick={handleZoomIn} className={`p-1 rounded-md ${isDarkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-200'}`} title="Zoom In"><ZoomInIcon /></button>
          </div>
        </main>
      </div>
    </div>
  );
}