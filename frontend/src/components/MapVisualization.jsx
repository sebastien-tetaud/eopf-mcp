import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export const MapVisualization = ({ itemId, bbox, center, zoom = 11, bandMode = 'true-color' }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const sentinelLayerRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current) return;

    // Determine map center [lat, lon] format for Leaflet
    let mapCenter = [45.8, 12.3]; // Default fallback [lat, lon]

    // Priority: bbox > center prop > default
    if (bbox && Array.isArray(bbox) && bbox.length === 4) {
      const [west, south, east, north] = bbox;
      mapCenter = [(south + north) / 2, (west + east) / 2]; // [lat, lon]
      console.log('[MapVisualization] Calculated center from bbox:', mapCenter);
    } else if (center) {
      mapCenter = center;
      console.log('[MapVisualization] Using provided center:', mapCenter);
    } else {
      console.log('[MapVisualization] Using default center:', mapCenter);
    }

    // Create map if it doesn't exist
    if (!mapInstanceRef.current) {
      const map = L.map(mapRef.current).setView(mapCenter, zoom);

      // Add base layer (EOX OSM)
      L.tileLayer('https://tiles.maps.eox.at/wmts/1.0.0/osm_3857/default/g/{z}/{y}/{x}.jpg', {
        attribution: 'Data: Copernicus Sentinel-2 | Processing: EOPF',
        maxZoom: 18,
      }).addTo(map);

      mapInstanceRef.current = map;
      console.log('[MapVisualization] Leaflet map created');
    } else {
      // Update map center if it already exists
      mapInstanceRef.current.setView(mapCenter, zoom);
    }

    // Remove existing Sentinel layer if present
    if (sentinelLayerRef.current) {
      mapInstanceRef.current.removeLayer(sentinelLayerRef.current);
      sentinelLayerRef.current = null;
    }

    // Add Sentinel-2 layer if itemId is provided
    if (itemId) {
      console.log('[MapVisualization] Adding Sentinel-2 layer for:', itemId);
      console.log('[MapVisualization] Band mode:', bandMode);

      // Define band configurations based on mode
      let variables;
      if (bandMode === 'false-color-infrared') {
        // False color infrared (vegetation): NIR (B08), Red (B04), Green (B03)
        variables = [
          'variables=/measurements/reflectance:b08',
          'variables=/measurements/reflectance:b04',
          'variables=/measurements/reflectance:b03'
        ].join('&');
        console.log('[MapVisualization] Using false-color-infrared bands (B08, B04, B03)');
      } else {
        // True color RGB: Red (B04), Green (B03), Blue (B02)
        variables = [
          'variables=/measurements/reflectance:b04',
          'variables=/measurements/reflectance:b03',
          'variables=/measurements/reflectance:b02'
        ].join('&');
        console.log('[MapVisualization] Using true-color bands (B04, B03, B02)');
      }

      // Build Titiler URL (using proxy to avoid CORS)
      const tileUrl =
        `/titiler/collections/sentinel-2-l2a/items/${itemId}/tiles/WebMercatorQuad/{z}/{x}/{y}.png?` +
        `${variables}&` +
        `rescale=0,1&` +
        `color_formula=gamma rgb 1.3, sigmoidal rgb 6 0.1, saturation 1.2`;

      console.log('[MapVisualization] Titiler URL:', tileUrl);

      // Add Titiler layer
      const sentinelLayer = L.tileLayer(tileUrl, {
        opacity: 0.8,
        maxZoom: 18,
      });

      sentinelLayer.addTo(mapInstanceRef.current);
      sentinelLayerRef.current = sentinelLayer;

      console.log('[MapVisualization] Sentinel-2 layer added successfully');
    }

    // Cleanup on unmount
    return () => {
      if (mapInstanceRef.current && !mapRef.current) {
        // Only remove map if the DOM element is gone
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        sentinelLayerRef.current = null;
      }
    };
  }, [itemId, bbox, center, zoom, bandMode]);

  return (
    <div className="rounded-lg overflow-hidden">
      <div
        ref={mapRef}
        className="w-full h-96"
        style={{ minHeight: '384px' }}
      />
      {itemId && (
        <div className="bg-[#f5f5f0] px-3 py-2 text-xs text-[#706b5e] border-t border-[#d4d0c8]">
          <span className="font-medium text-[#2c2923]">Item:</span> {itemId}
        </div>
      )}
    </div>
  );
};
