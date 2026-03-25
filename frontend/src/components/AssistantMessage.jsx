import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ToolCallCard } from './ToolCallCard';
import { MapVisualization } from './MapVisualization';
import { extractMapData, hasMapData } from '../utils/mapDataExtractor';
import { detectBandMode } from '../utils/bandModeDetector';

export const AssistantMessage = ({ message, userMessage }) => {
  // Detect band mode from user message
  const detectedBandMode = userMessage?.content
    ? detectBandMode(userMessage.content)
    : 'true-color';

  const [bandMode, setBandMode] = useState(detectedBandMode);
  const [showMap, setShowMap] = useState(true);
  const [selectedItemIndex, setSelectedItemIndex] = useState(0);
  const [customItemId, setCustomItemId] = useState('');

  // Collect all map items from all tool calls
  const allMapItems = [];
  if (message.tool_calls && message.tool_calls.length > 0) {
    message.tool_calls.forEach(toolCall => {
      if (hasMapData(toolCall)) {
        const items = extractMapData(toolCall);
        allMapItems.push(...items);
      }
    });
  }

  const hasAnyMapData = allMapItems.length > 0;

  return (
    <div className="mb-8">
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="flex-shrink-0 w-8 h-8 rounded bg-[#a9754f] flex items-center justify-center">
          <span className="text-white text-sm font-medium">AI</span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Text content */}
          <div className="text-[#2c2923] break-words font-normal mb-4 prose prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({node, ...props}) => (
                  <div className="overflow-x-auto my-4">
                    <table className="min-w-full border-collapse border border-[#d4d0c8]" {...props} />
                  </div>
                ),
                thead: ({node, ...props}) => (
                  <thead className="bg-[#f5f5f0]" {...props} />
                ),
                th: ({node, ...props}) => (
                  <th className="border border-[#d4d0c8] px-4 py-2 text-left font-semibold text-[#2c2923]" {...props} />
                ),
                td: ({node, ...props}) => (
                  <td className="border border-[#d4d0c8] px-4 py-2 text-[#2c2923]" {...props} />
                ),
                tr: ({node, ...props}) => (
                  <tr className="hover:bg-[#fafaf8]" {...props} />
                ),
                h1: ({node, ...props}) => (
                  <h1 className="text-2xl font-bold text-[#2c2923] mt-6 mb-4 border-b border-[#d4d0c8] pb-2" {...props} />
                ),
                h2: ({node, ...props}) => (
                  <h2 className="text-xl font-bold text-[#2c2923] mt-5 mb-3 border-b border-[#d4d0c8] pb-1" {...props} />
                ),
                h3: ({node, ...props}) => (
                  <h3 className="text-lg font-semibold text-[#2c2923] mt-4 mb-2" {...props} />
                ),
                h4: ({node, ...props}) => (
                  <h4 className="text-base font-semibold text-[#2c2923] mt-3 mb-2" {...props} />
                ),
                p: ({node, ...props}) => (
                  <p className="mb-3 leading-relaxed" {...props} />
                ),
                ul: ({node, ...props}) => (
                  <ul className="list-disc list-inside mb-3 space-y-1" {...props} />
                ),
                ol: ({node, ...props}) => (
                  <ol className="list-decimal list-inside mb-3 space-y-1" {...props} />
                ),
                li: ({node, ...props}) => (
                  <li className="ml-2" {...props} />
                ),
                code: ({node, inline, className, children, ...props}) => {
                  const match = /language-(\w+)/.exec(className || '');
                  const language = match ? match[1] : '';

                  return !inline && language ? (
                    <SyntaxHighlighter
                      style={oneLight}
                      language={language}
                      PreTag="div"
                      className="rounded border border-[#d4d0c8] my-3 text-sm"
                      customStyle={{
                        margin: 0,
                        padding: '1rem',
                        backgroundColor: '#f5f5f0',
                        fontSize: '0.875rem',
                        lineHeight: '1.5',
                      }}
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : inline ? (
                    <code className="bg-[#f5f5f0] px-1.5 py-0.5 rounded text-sm font-mono text-[#2c2923] border border-[#e8e8e0]" {...props}>
                      {children}
                    </code>
                  ) : (
                    <code className="block bg-[#f5f5f0] p-3 rounded text-sm font-mono text-[#2c2923] border border-[#d4d0c8] overflow-x-auto my-3" {...props}>
                      {children}
                    </code>
                  );
                },
                pre: ({node, ...props}) => (
                  <div {...props} />
                ),
                blockquote: ({node, ...props}) => (
                  <blockquote className="border-l-4 border-[#a9754f] pl-4 py-1 my-3 italic text-[#706b5e]" {...props} />
                ),
                hr: ({node, ...props}) => (
                  <hr className="border-t border-[#d4d0c8] my-6" {...props} />
                ),
                a: ({node, ...props}) => (
                  <a className="text-[#a9754f] hover:text-[#8b5f3f] underline" {...props} />
                ),
                strong: ({node, ...props}) => (
                  <strong className="font-semibold text-[#2c2923]" {...props} />
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Consolidated Map Visualization */}
          {hasAnyMapData && showMap && (
            <div className="mt-4 bg-white border border-[#d4d0c8] rounded-lg overflow-hidden">
              <div className="px-4 py-3 border-b border-[#d4d0c8] space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-[#2c2923]">
                    Map Visualization ({allMapItems.length} item{allMapItems.length > 1 ? 's' : ''})
                  </span>
                  <button
                    onClick={() => setShowMap(false)}
                    className="text-sm text-[#706b5e] hover:text-[#2c2923] transition-colors"
                  >
                    Hide
                  </button>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  {/* Item selector dropdown (if multiple items) */}
                  {allMapItems.length > 1 && (
                    <select
                      value={selectedItemIndex}
                      onChange={(e) => {
                        setSelectedItemIndex(Number(e.target.value));
                        setCustomItemId('');
                      }}
                      className="text-sm bg-white text-[#2c2923] border border-[#d4d0c8] rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#a9754f]"
                    >
                      {allMapItems.map((item, idx) => (
                        <option key={idx} value={idx}>
                          Item {idx + 1}: {item.itemId.substring(0, 30)}...
                        </option>
                      ))}
                    </select>
                  )}

                  {/* Band mode selector */}
                  <select
                    value={bandMode}
                    onChange={(e) => setBandMode(e.target.value)}
                    className="text-sm bg-white text-[#2c2923] border border-[#d4d0c8] rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#a9754f]"
                  >
                    <option value="true-color">True Color (RGB)</option>
                    <option value="false-color-infrared">False Color Infrared</option>
                  </select>
                </div>

                {/* Custom Item ID input */}
                <div className="flex items-center gap-2">
                  <label className="text-sm text-[#2c2923] whitespace-nowrap">Custom Item ID:</label>
                  <input
                    type="text"
                    value={customItemId}
                    onChange={(e) => setCustomItemId(e.target.value)}
                    placeholder="Enter Item ID (e.g., S2A_MSIL2A_20260319T104041...)"
                    className="flex-1 text-sm bg-white text-[#2c2923] border border-[#d4d0c8] rounded px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#a9754f] font-mono"
                  />
                  {customItemId && (
                    <button
                      onClick={() => setCustomItemId('')}
                      className="text-sm text-[#706b5e] hover:text-[#2c2923] transition-colors px-2"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {/* Show selected or custom item on the map */}
              <MapVisualization
                itemId={customItemId || allMapItems[selectedItemIndex]?.itemId}
                bbox={allMapItems[selectedItemIndex]?.bbox}
                zoom={11}
                bandMode={bandMode}
              />

              <div className="px-4 py-2 text-sm text-[#706b5e] border-t border-[#d4d0c8]">
                {customItemId ? (
                  <span>Showing custom Item ID: <code className="font-mono text-xs bg-[#f5f5f0] px-1 py-0.5 rounded">{customItemId}</code></span>
                ) : (
                  <span>Showing item {selectedItemIndex + 1} of {allMapItems.length}: <code className="font-mono text-xs bg-[#f5f5f0] px-1 py-0.5 rounded">{allMapItems[selectedItemIndex]?.itemId}</code></span>
                )}
              </div>
            </div>
          )}

          {hasAnyMapData && !showMap && (
            <div className="mt-4">
              <button
                onClick={() => setShowMap(true)}
                className="text-sm text-[#a9754f] hover:text-[#8b5f3f] transition-colors"
              >
                Show Map
              </button>
            </div>
          )}

          {/* Tool calls */}
          {message.tool_calls && message.tool_calls.length > 0 && (
            <div className="mt-4 space-y-2">
              {message.tool_calls.map((toolCall, idx) => (
                <ToolCallCard
                  key={idx}
                  toolCall={toolCall}
                  userMessage={userMessage}
                  hideMap={true}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
