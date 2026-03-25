#!/bin/bash
# Simple curl-based example for the EOPF STAC Chat API
#
# Usage:
#   1. Start the API server:
#      uv run python src/api_server.py
#
#   2. Run this script:
#      ./examples/api_curl_example.sh

set -e

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "EOPF STAC Chat API - Curl Example"
echo "=========================================="
echo

# Health check
echo "1. Health Check"
echo "----------------"
curl -s "$BASE_URL/" | jq
echo

# Create session
echo "2. Create Session"
echo "----------------"
SESSION_JSON=$(curl -s -X POST "$BASE_URL/api/sessions" \
  -H "Content-Type: application/json" \
  -d '{"title": "Curl Example Session"}')

SESSION_ID=$(echo "$SESSION_JSON" | jq -r '.id')
echo "Session ID: $SESSION_ID"
echo "$SESSION_JSON" | jq
echo

# Send message
echo "3. Send Message"
echo "----------------"
curl -s -X POST "$BASE_URL/api/chat/send" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"List all STAC collections\"}" | jq
echo

# Stream response
echo "4. Stream Response (SSE)"
echo "----------------"
echo "Streaming response from: $BASE_URL/api/chat/stream/$SESSION_ID"
echo
curl -N "$BASE_URL/api/chat/stream/$SESSION_ID"
echo

# Get session details
echo "5. Get Session Details"
echo "----------------"
curl -s "$BASE_URL/api/sessions/$SESSION_ID" | jq '.messages | length' | \
  xargs -I {} echo "Session has {} messages"
echo

# List all sessions
echo "6. List All Sessions"
echo "----------------"
curl -s "$BASE_URL/api/sessions" | jq '. | length' | \
  xargs -I {} echo "Total sessions: {}"
echo

echo "=========================================="
echo "✓ Example complete!"
echo "=========================================="
