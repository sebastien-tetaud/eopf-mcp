import React, { useState } from 'react';
import { extractMapData, hasMapData } from '../utils/mapDataExtractor';

export const ToolCallCard = ({ toolCall, userMessage, hideMap = false }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Check if this tool call has map-visualizable data
  const canShowMap = hasMapData(toolCall);
  const mapItems = canShowMap ? extractMapData(toolCall) : [];

  console.log('[ToolCallCard] Received toolCall:', toolCall);
  console.log('[ToolCallCard] canShowMap:', canShowMap, 'mapItems:', mapItems);

  return (
    <div className="bg-white border border-[#d4d0c8] rounded-lg p-3 mb-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          <svg
            className="w-4 h-4 text-[#a9754f]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span className="font-medium text-[#2c2923] text-sm">
            {toolCall.name || 'Unknown'}
          </span>
          {canShowMap && mapItems.length > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-[#f5f5f0] text-[#a9754f] text-xs rounded border border-[#d4d0c8]">
              {mapItems.length} item{mapItems.length > 1 ? 's' : ''}
            </span>
          )}
        </div>
        <svg
          className={`w-4 h-4 text-[#706b5e] transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>


      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-[#d4d0c8]">
          <div className="text-xs font-medium text-[#706b5e] mb-1">Input:</div>
          <pre className="text-xs bg-[#f5f5f0] rounded p-2 overflow-x-auto text-[#2c2923] border border-[#d4d0c8]">
            {JSON.stringify(toolCall.input, null, 2)}
          </pre>

          {toolCall.result && (
            <>
              <div className="text-xs font-medium text-[#706b5e] mb-1 mt-2">Result:</div>
              <pre className="text-xs bg-[#f5f5f0] rounded p-2 overflow-x-auto text-[#2c2923] border border-[#d4d0c8]">
                {typeof toolCall.result === 'string'
                  ? toolCall.result
                  : JSON.stringify(toolCall.result, null, 2)}
              </pre>
            </>
          )}

          {/* Show all items if multiple */}
          {canShowMap && mapItems.length > 1 && (
            <div className="mt-3">
              <div className="text-xs font-medium text-[#a9754f] mb-2">
                All Items ({mapItems.length}):
              </div>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {mapItems.map((item, idx) => (
                  <div
                    key={idx}
                    className="bg-[#f5f5f0] rounded p-2 text-xs border border-[#d4d0c8]"
                  >
                    <div className="text-[#2c2923] font-mono break-all">
                      {item.itemId}
                    </div>
                    {item.bbox && (
                      <div className="text-[#706b5e] mt-1">
                        BBox: [{item.bbox.join(', ')}]
                      </div>
                    )}
                    {item.datetime && (
                      <div className="text-[#706b5e] mt-1">
                        Date: {item.datetime}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
