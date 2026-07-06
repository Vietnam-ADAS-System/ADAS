import { useEffect, useState } from "react";

function calculateContainedRect(sourceWidth, sourceHeight, targetWidth, targetHeight) {
  if (!sourceWidth || !sourceHeight || !targetWidth || !targetHeight) {
    return { x: 0, y: 0, width: targetWidth, height: targetHeight };
  }
  const scale = Math.min(targetWidth / sourceWidth, targetHeight / sourceHeight);
  return {
    x: (targetWidth - sourceWidth * scale) / 2,
    y: (targetHeight - sourceHeight * scale) / 2,
    width: sourceWidth * scale,
    height: sourceHeight * scale,
  };
}

export default function CameraCanvas({ frame, children, onViewportChange }) {
  const containerRef = { current: null };
  const [viewport, setViewport] = useState(null);

  useEffect(() => {
    // Viewport is determined by container size
    const container = containerRef.current;
    if (!container) return;

    const updateViewport = () => {
      const rect = container.getBoundingClientRect();
      const cssWidth = Math.max(1, rect.width);
      const cssHeight = Math.max(1, rect.height);
      const dpr = window.devicePixelRatio || 1;
      
      const sourceWidth = frame?.width || 960;
      const sourceHeight = frame?.height || 540;
      const contentRect = calculateContainedRect(sourceWidth, sourceHeight, cssWidth, cssHeight);
      
      const nextViewport = {
        width: cssWidth,
        height: cssHeight,
        dpr,
        contentRect,
        sourceSize: { width: sourceWidth, height: sourceHeight },
      };
      
      setViewport(nextViewport);
      onViewportChange?.(nextViewport);
    };

    updateViewport();
    
    const observer = new ResizeObserver(updateViewport);
    observer.observe(container);
    return () => observer.disconnect();
  }, [frame, onViewportChange]);

  return (
    <div 
      className="camera-canvas-shell" 
      ref={(el) => { containerRef.current = el; }}
      style={{ position: 'relative', width: '100%', height: '100%' }}
    >
      {typeof children === "function" ? children(viewport) : children}
    </div>
  );
}
