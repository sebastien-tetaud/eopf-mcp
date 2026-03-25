/**
 * Utility to detect preferred band mode from user messages
 */

/**
 * Detect if the user wants false color infrared visualization
 * @param {string} message - The user's message
 * @returns {string} 'false-color-infrared' or 'true-color'
 */
export function detectBandMode(message) {
  if (!message || typeof message !== 'string') {
    return 'true-color';
  }

  const lowerMessage = message.toLowerCase();

  // Keywords for false color infrared
  const falseColorKeywords = [
    'false color',
    'false-color',
    'infrared',
    'nir',
    'vegetation',
    'vegetation analysis',
    'vegetation health',
    'ndvi',
    'false colour',
    'band 8',
    'b08',
  ];

  // Keywords for true color
  const trueColorKeywords = [
    'true color',
    'true-color',
    'rgb',
    'natural color',
    'natural colour',
    'real color',
    'visible',
  ];

  // Check for false color keywords
  for (const keyword of falseColorKeywords) {
    if (lowerMessage.includes(keyword)) {
      console.log('[BandModeDetector] Detected false color request:', keyword);
      return 'false-color-infrared';
    }
  }

  // Check for true color keywords
  for (const keyword of trueColorKeywords) {
    if (lowerMessage.includes(keyword)) {
      console.log('[BandModeDetector] Detected true color request:', keyword);
      return 'true-color';
    }
  }

  // Default to true color
  return 'true-color';
}
