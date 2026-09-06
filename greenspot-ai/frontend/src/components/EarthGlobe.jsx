import React, { useRef, useEffect } from 'react';
import Globe from 'react-globe.gl';
import { regionsData } from '../regionsData';

export default function EarthGlobe({ layerMode, onRegionSelect }) {
  const globeEl = useRef();

  useEffect(() => {
    if (globeEl.current) {
      globeEl.current.controls().autoRotate = true;
      globeEl.current.controls().autoRotateSpeed = 0.8;
      globeEl.current.controls().enableZoom = false;
    }
  }, []);

  const getCarbonColor = (carbon) => {
    if (carbon > 500) return '#ef4444'; // Red (High)
    if (carbon > 200) return '#f59e0b'; // Amber (Med)
    return '#10b981'; // Green (Low)
  };

  const getLayerData = () => {
    if (layerMode === 'carbon') {
      return regionsData.map(h => ({
        ...h,
        color: getCarbonColor(h.carbon),
        size: Math.max(0.2, h.carbon / 350),
        label: `${h.name} (Carbon: ${h.carbon}g)`
      }));
    }
    if (layerMode === 'electricity') {
      return regionsData.map(h => ({
        ...h,
        color: '#3b82f6',
        size: 0.6,
        label: `${h.name} Data Center`
      }));
    }
    if (layerMode === 'sources') {
      return regionsData.map(h => ({
        ...h,
        color: h.source.includes('Hydro') || h.source.includes('Solar') || h.source.includes('Nuclear') ? '#10b981' : '#f97316',
        size: 0.4,
        label: `${h.name} (${h.source})`
      }));
    }
    return [];
  };

  const handlePointClick = (point) => {
    if (onRegionSelect) {
      onRegionSelect(point);
      // Optional: stop rotation on click so they can view it
      if (globeEl.current) {
         globeEl.current.controls().autoRotate = false;
         // Resume rotation after 5 seconds
         setTimeout(() => {
            if (globeEl.current) globeEl.current.controls().autoRotate = true;
         }, 5000);
      }
    }
  };

  return (
    <div className="w-full h-full flex items-center justify-center relative cursor-grab active:cursor-grabbing">
      <Globe
        ref={globeEl}
        globeImageUrl="https://unpkg.com/three-globe/example/img/earth-night.jpg"
        bumpImageUrl="https://unpkg.com/three-globe/example/img/earth-topology.png"
        backgroundImageUrl="https://unpkg.com/three-globe/example/img/night-sky.png"
        pointsData={getLayerData()}
        pointLat="lat"
        pointLng="lng"
        pointColor="color"
        pointAltitude="size"
        pointRadius={1.0} 
        pointsMerge={false}
        pointResolution={64}
        onPointClick={handlePointClick}
        onLabelClick={handlePointClick}
        labelsData={getLayerData()}
        labelLat="lat"
        labelLng="lng"
        labelText="label"
        labelSize={1.8}
        labelDotRadius={1.0}
        labelColor={() => 'rgba(255, 255, 255, 0.95)'}
        labelResolution={3}
        animateIn={true}
        width={typeof window !== 'undefined' ? window.innerWidth : 800}
        height={typeof window !== 'undefined' ? window.innerHeight : 600}
        backgroundColor="rgba(0,0,0,0)"
      />
    </div>
  );
}
