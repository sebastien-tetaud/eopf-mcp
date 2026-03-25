import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export const TitilerTestWindow = () => {
  const navigate = useNavigate();
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const sentinelLayerRef = useRef(null);
  const [showCode, setShowCode] = useState(false);
  const [itemId, setItemId] = useState('S2B_MSIL2A_20251024T101029_N0511_R022_T32TQR_20251024T122954');
  const [inputValue, setInputValue] = useState('S2B_MSIL2A_20251024T101029_N0511_R022_T32TQR_20251024T122954');
  const [bbox, setBbox] = useState(null);
  const [loading, setLoading] = useState(false);
  const [bandMode, setBandMode] = useState('true-color');

  // Fetch item metadata to get bbox
  useEffect(() => {
    if (!itemId) return;

    const fetchItemBbox = async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `https://stac.core.eopf.eodc.eu/collections/sentinel-2-l2a/items/${itemId}`
        );
        if (response.ok) {
          const data = await response.json();
          if (data.bbox) {
            setBbox(data.bbox);
            console.log('[TitilerTestWindow] Fetched bbox:', data.bbox);
          }
        }
      } catch (error) {
        console.error('[TitilerTestWindow] Error fetching item bbox:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchItemBbox();
  }, [itemId]);

  useEffect(() => {
    if (!mapRef.current) return;

    // Calculate center from bbox if available [lat, lon] for Leaflet
    let mapCenter = [45.8, 12.3]; // Default [lat, lon]
    if (bbox && Array.isArray(bbox) && bbox.length === 4) {
      const [west, south, east, north] = bbox;
      mapCenter = [(south + north) / 2, (west + east) / 2]; // [lat, lon]
      console.log('[TitilerTestWindow] Calculated center from bbox:', mapCenter);
    }

    // Initialize map only once
    if (!mapInstanceRef.current) {
      const map = L.map(mapRef.current).setView(mapCenter, 11);

      // Add base layer (EOX OSM)
      L.tileLayer('https://tiles.maps.eox.at/wmts/1.0.0/osm_3857/default/g/{z}/{y}/{x}.jpg', {
        attribution: 'Data: Copernicus Sentinel-2 | Processing: EOPF',
        maxZoom: 18,
      }).addTo(map);

      mapInstanceRef.current = map;
      console.log('[TitilerTestWindow] Leaflet map created');
    } else if (bbox) {
      // Update map center when bbox changes
      mapInstanceRef.current.setView(mapCenter, 11);
    }

    // Remove existing Sentinel layer if present
    if (sentinelLayerRef.current) {
      mapInstanceRef.current.removeLayer(sentinelLayerRef.current);
      sentinelLayerRef.current = null;
    }

    // Add Sentinel-2 layer
    if (itemId && mapInstanceRef.current) {
      // Define band configurations
      let variables;
      if (bandMode === 'false-color-infrared') {
        // False color infrared (vegetation): NIR (B08), Red (B04), Green (B03)
        variables = [
          'variables=/measurements/reflectance:b08',
          'variables=/measurements/reflectance:b04',
          'variables=/measurements/reflectance:b03'
        ].join('&');
      } else {
        // True color RGB: Red (B04), Green (B03), Blue (B02)
        variables = [
          'variables=/measurements/reflectance:b04',
          'variables=/measurements/reflectance:b03',
          'variables=/measurements/reflectance:b02'
        ].join('&');
      }

      const tileUrl =
        `/titiler/collections/sentinel-2-l2a/items/${itemId}/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?` +
        `${variables}&` +
        `rescale=0,1&` +
        `color_formula=gamma rgb 1.3, sigmoidal rgb 6 0.1, saturation 1.2`;

      console.log('[TitilerTestWindow] Titiler URL:', tileUrl);

      // Add Titiler layer
      const sentinelLayer = L.tileLayer(tileUrl, {
        opacity: 0.8,
        maxZoom: 18,
      });

      sentinelLayer.addTo(mapInstanceRef.current);
      sentinelLayerRef.current = sentinelLayer;
    }

    // Cleanup on unmount
    return () => {
      if (mapInstanceRef.current && !mapRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        sentinelLayerRef.current = null;
      }
    };
  }, [itemId, bbox, bandMode]);

  const handleLoadItem = () => {
    setItemId(inputValue.trim());
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleLoadItem();
    }
  };

  const codeSnippet = `import L from 'leaflet';

// Create Leaflet map
const map = L.map('map').setView([45.8, 12.3], 11);

// Add base layer
L.tileLayer('https://tiles.maps.eox.at/wmts/1.0.0/osm_3857/default/g/{z}/{y}/{x}.jpg').addTo(map);

// Build Titiler URL
const tileUrl =
  "https://api.explorer.eopf.copernicus.eu/raster/collections/sentinel-2-l2a/items/${itemId}/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?" +
  "variables=/measurements/reflectance:b04&" +
  "variables=/measurements/reflectance:b03&" +
  "variables=/measurements/reflectance:b02&" +
  "rescale=0,1&" +
  "color_formula=gamma rgb 1.3, sigmoidal rgb 6 0.1, saturation 1.2";

// Add Titiler layer
const sentinelLayer = L.tileLayer(tileUrl, {
  opacity: 0.8,
  attribution: 'Data: Copernicus Sentinel-2 | Processing: EOPF'
});

sentinelLayer.addTo(map);`;

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#f5f5f0] overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-[#d4d0c8] px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-[#2c2923]">
              Titiler Test Window
            </h1>
            <p className="text-sm text-[#706b5e] mt-1">
              Sentinel-2 L2A Visualization
            </p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-[#a9754f] hover:bg-[#8b5f3f] text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            Back to Chat
          </button>
        </div>
      </div>

      {/* Item ID Input */}
      <div className="px-6 py-3 bg-white border-b border-[#d4d0c8]">
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Enter Sentinel-2 Item ID"
            className="flex-1 px-4 py-2 bg-[#f5f5f0] border border-[#d4d0c8] rounded-lg text-[#2c2923] placeholder-[#a39d8d] focus:outline-none focus:border-[#a9754f]"
          />
          <button
            onClick={handleLoadItem}
            disabled={loading}
            className="px-6 py-2 bg-[#5a8f5a] hover:bg-[#4a7a4a] disabled:bg-[#d4d0c8] disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Loading...
              </>
            ) : (
              <>
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                  />
                </svg>
                Load Map
              </>
            )}
          </button>
          <button
            onClick={() => setShowCode(!showCode)}
            className="px-4 py-2 bg-[#a9754f] hover:bg-[#8b5f3f] text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
              />
            </svg>
            {showCode ? 'Hide Code' : 'Show Code'}
          </button>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-[#706b5e]">Band Mode:</label>
          <select
            value={bandMode}
            onChange={(e) => setBandMode(e.target.value)}
            className="px-3 py-1.5 bg-[#f5f5f0] border border-[#d4d0c8] rounded text-[#2c2923] text-sm focus:outline-none focus:border-[#a9754f]"
          >
            <option value="true-color">True Color RGB (B04, B03, B02)</option>
            <option value="false-color-infrared">False Color Infrared (B08, B04, B03)</option>
          </select>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          {/* Map Container */}
          <div className="rounded-lg overflow-hidden border border-[#d4d0c8] shadow-lg">
            <div
              ref={mapRef}
              className="w-full"
              style={{ height: '600px' }}
            />
          </div>

          {/* Current Item Info */}
          <div className="mt-4 p-4 bg-white rounded-lg border border-[#d4d0c8]">
            <h3 className="text-sm font-semibold text-[#a9754f] mb-2">
              Current Item
            </h3>
            <div className="bg-[#f5f5f0] rounded p-3 border border-[#d4d0c8]">
              <code className="text-xs text-[#5a8f5a] break-all">
                {itemId}
              </code>
            </div>
          </div>

          {/* Map Info */}
          <div className="mt-4 p-4 bg-white rounded-lg border border-[#d4d0c8]">
            <h3 className="text-sm font-semibold text-[#a9754f] mb-2">
              Map Configuration
            </h3>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-[#706b5e]">Center:</dt>
                <dd className="text-[#2c2923] font-mono">
                  {bbox && bbox.length === 4
                    ? `[${((bbox[0] + bbox[2]) / 2).toFixed(2)}, ${((bbox[1] + bbox[3]) / 2).toFixed(2)}]`
                    : '[12.3, 45.8]'}
                </dd>
              </div>
              <div>
                <dt className="text-[#706b5e]">Zoom:</dt>
                <dd className="text-[#2c2923] font-mono">11</dd>
              </div>
              {bbox && bbox.length === 4 && (
                <div className="col-span-2">
                  <dt className="text-[#706b5e]">BBox:</dt>
                  <dd className="text-[#2c2923] font-mono text-xs">
                    [{bbox.map(v => v.toFixed(4)).join(', ')}]
                  </dd>
                </div>
              )}
              <div className="col-span-2">
                <dt className="text-[#706b5e]">Mode:</dt>
                <dd className="text-[#2c2923]">
                  {bandMode === 'false-color-infrared' ? (
                    <>
                      <span className="font-semibold text-[#c47a4a]">False Color Infrared</span>
                      <div className="text-xs text-[#706b5e] mt-1">
                        <span className="text-[#c44a4a]">NIR (B08)</span>,{' '}
                        <span className="text-[#5a8f5a]">Red (B04)</span>,{' '}
                        <span className="text-[#4a7ac4]">Green (B03)</span>
                      </div>
                    </>
                  ) : (
                    <>
                      <span className="font-semibold text-[#4a7ac4]">True Color RGB</span>
                      <div className="text-xs text-[#706b5e] mt-1">
                        <span className="text-[#c44a4a]">Red (B04)</span>,{' '}
                        <span className="text-[#5a8f5a]">Green (B03)</span>,{' '}
                        <span className="text-[#4a7ac4]">Blue (B02)</span>
                      </div>
                    </>
                  )}
                </dd>
              </div>
              <div className="col-span-2">
                <dt className="text-[#706b5e]">Color Adjustments:</dt>
                <dd className="text-[#2c2923] font-mono text-xs">
                  gamma rgb 1.3, sigmoidal rgb 6 0.1, saturation 1.2
                </dd>
              </div>
            </dl>
          </div>

          {/* Important Note */}
          <div className="mt-4 p-4 bg-[#fff9e6] rounded-lg border border-[#e6d9a3]">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-[#c47a4a] flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm">
                <p className="font-semibold text-[#2c2923] mb-1">Visualization Availability</p>
                <p className="text-[#706b5e]">
                  Not all Sentinel-2 items in the STAC catalog are available for visualization. Only items that have been processed and ingested into the Titiler service can be displayed on the map. If you see a blank map or errors, the item may not be available yet.
                </p>
              </div>
            </div>
          </div>

          {/* Code Display */}
          {showCode && (
            <div className="mt-4 p-4 bg-[#2c2923] rounded-lg border border-[#d4d0c8]">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-[#a9754f]">
                  Leaflet Implementation
                </h3>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(codeSnippet);
                    alert('Code copied to clipboard!');
                  }}
                  className="px-3 py-1 text-xs bg-[#3a3933] hover:bg-[#4a4943] text-[#e8e6df] rounded transition-colors"
                >
                  Copy Code
                </button>
              </div>
              <pre className="overflow-x-auto">
                <code className="text-xs text-[#5a8f5a] font-mono">
                  {codeSnippet}
                </code>
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
