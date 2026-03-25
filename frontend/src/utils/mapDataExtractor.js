/**
 * Utility to extract map visualization data from MCP tool results
 */

/**
 * Extract Sentinel-2 item IDs from tool results
 * @param {Object} toolCall - The tool call object with name, input, and result
 * @returns {Array} Array of item objects with {itemId, bbox, collection}
 */
export function extractMapData(toolCall) {
  console.log('[MapDataExtractor] Processing tool call:', toolCall);

  if (!toolCall || !toolCall.result) {
    console.log('[MapDataExtractor] No tool call or result found');
    return [];
  }

  const items = [];

  try {
    // Parse result if it's a string
    let result = toolCall.result;
    console.log('[MapDataExtractor] Raw result type:', typeof result);
    console.log('[MapDataExtractor] Raw result:', result);

    if (typeof result === 'string') {
      // Backend now returns proper JSON, so direct parse should work
      try {
        result = JSON.parse(result);
        console.log('[MapDataExtractor] Parsed as JSON:', result);
      } catch (error) {
        console.error('[MapDataExtractor] Failed to parse JSON:', error);
        return [];
      }
    }

    // Extract based on tool name
    const toolName = toolCall.name;
    console.log('[MapDataExtractor] Tool name:', toolName);

    if (toolName === 'search_items' || toolName === 'get_zarr_urls') {
      // Both tools return items array
      if (result.items && Array.isArray(result.items)) {
        console.log('[MapDataExtractor] Found items array:', result.items.length);
        result.items.forEach((item, idx) => {
          // Handle both 'id' and 'item_id' fields
          const itemId = item.item_id || item.id;
          console.log(`[MapDataExtractor] Processing item ${idx}:`, item);
          console.log(`[MapDataExtractor] Item bbox:`, item.bbox);

          if (itemId) {
            items.push({
              itemId: itemId,
              bbox: item.bbox || null,
              collection: item.collection || 'sentinel-2-l2a',
              datetime: item.datetime || null,
              zarrUrl: item.zarr_url || item.zarr_href || null,
            });
          }
        });
      } else {
        console.log('[MapDataExtractor] No items array found in result');
      }
    } else if (toolName === 'get_item') {
      // Single item
      if (result.id) {
        items.push({
          itemId: result.id,
          bbox: result.bbox || null,
          collection: result.collection || 'sentinel-2-l2a',
          datetime: result.datetime || null,
        });
      }
    } else if (toolName === 'get_item_assets') {
      // Assets for a specific item - extract item ID from input
      if (toolCall.input && toolCall.input.item_id) {
        items.push({
          itemId: toolCall.input.item_id,
          bbox: null,
          collection: toolCall.input.collection_id || 'sentinel-2-l2a',
        });
      }
    }
  } catch (error) {
    console.error('[MapDataExtractor] Error extracting map data:', error);
  }

  console.log('[MapDataExtractor] Extracted items:', items);
  return items;
}

/**
 * Check if a tool call contains map-visualizable data
 * @param {Object} toolCall - The tool call object
 * @returns {boolean} True if the tool call contains map data
 */
export function hasMapData(toolCall) {
  if (!toolCall || !toolCall.name) {
    return false;
  }

  const mapVisualizableTools = [
    'search_items',
    'get_zarr_urls',
    'get_item',
    'get_item_assets',
  ];

  return mapVisualizableTools.includes(toolCall.name);
}

/**
 * Calculate center point from bbox
 * @param {Array} bbox - [west, south, east, north]
 * @returns {Array} [lat, lon] center point
 */
export function calculateCenter(bbox) {
  if (!bbox || bbox.length !== 4) {
    return null;
  }

  const [west, south, east, north] = bbox;
  return [(south + north) / 2, (west + east) / 2];
}
