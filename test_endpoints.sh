#!/bin/bash

# =============================================================================
# YouTube API Server - Endpoint Testing Script
# =============================================================================
# This script tests all available endpoints of the YouTube API server
# Make sure the server is running before executing this script
#
# Usage:
#   chmod +x test_endpoints.sh
#   ./test_endpoints.sh
#
# Or specify custom server URL:
#   ./test_endpoints.sh http://localhost:8000
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Server configuration
SERVER_URL=${1:-"http://localhost:8000"}
TIMEOUT=30

# Test video URLs (various languages and types)
ENGLISH_VIDEO="https://www.youtube.com/watch?v=dQw4w9WgXcQ"      # Rick Astley - Never Gonna Give You Up
ENGLISH_VIDEO2="https://www.youtube.com/watch?v=ZUmTsgD8NOM"     # English business video
HINDI_VIDEO="https://www.youtube.com/watch?v=_n-QMUdB8HQ"       # Hindi video
HINDI_VIDEO2="https://www.youtube.com/watch?v=_8FALFC2VZ4"      # Another Hindi video
SHORT_URL="https://youtu.be/dQw4w9WgXcQ"                        # Short YouTube URL format

echo -e "${CYAN}=====================================================${NC}"
echo -e "${CYAN}    YouTube API Server - Endpoint Testing Script${NC}"
echo -e "${CYAN}=====================================================${NC}"
echo -e "Server URL: ${BLUE}$SERVER_URL${NC}"
echo -e "Timeout: ${BLUE}$TIMEOUT seconds${NC}"
echo ""

# Function to print test header
print_test_header() {
    echo -e "\n${PURPLE}--- $1 ---${NC}"
    echo -e "${YELLOW}Endpoint: $2${NC}"
    echo -e "${YELLOW}Method: $3${NC}"
    echo ""
}

# Function to test endpoint with curl
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4

    echo -e "${BLUE}Testing: $description${NC}"
    echo -e "${CYAN}Request:${NC}"

    if [ "$method" = "GET" ]; then
        echo "curl -X $method \"$SERVER_URL$endpoint\""
        echo ""
        echo -e "${CYAN}Response:${NC}"
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X "$method" "$SERVER_URL$endpoint" --max-time $TIMEOUT)
    else
        echo "curl -X $method \"$SERVER_URL$endpoint\" \\"
        echo "  -H \"Content-Type: application/json\" \\"
        echo "  -d '$data'"
        echo ""
        echo -e "${CYAN}Response:${NC}"
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X "$method" "$SERVER_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" \
            --max-time $TIMEOUT)
    fi

    # Extract HTTP status code
    http_status=$(echo "$response" | tail -n1 | sed 's/HTTP_STATUS://')
    response_body=$(echo "$response" | sed '$d')

    # Color code the response based on status
    if [ "$http_status" = "200" ]; then
        echo -e "${GREEN}Status: $http_status OK${NC}"
        echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
    elif [ "$http_status" = "500" ]; then
        echo -e "${RED}Status: $http_status Internal Server Error${NC}"
        echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
    elif [ -z "$http_status" ]; then
        echo -e "${RED}Status: Connection Failed or Timeout${NC}"
        echo "Make sure the server is running at $SERVER_URL"
    else
        echo -e "${YELLOW}Status: $http_status${NC}"
        echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"
    fi

    echo -e "\n${CYAN}=================================================${NC}"
}

# =============================================================================
# TEST 1: Health Check
# =============================================================================
print_test_header "TEST 1: Health Check" "/health" "GET"
test_endpoint "GET" "/health" "" "Server health and proxy status"

# =============================================================================
# TEST 2: Video Data (Metadata)
# =============================================================================
print_test_header "TEST 2: Video Metadata" "/video-data" "POST"

# Test with English video
test_endpoint "POST" "/video-data" "{\"url\": \"$ENGLISH_VIDEO\"}" "Get metadata for English video"

# Test with short URL format
test_endpoint "POST" "/video-data" "{\"url\": \"$SHORT_URL\"}" "Get metadata using short YouTube URL"

# Test with invalid URL
test_endpoint "POST" "/video-data" "{\"url\": \"https://invalid-url.com\"}" "Test with invalid URL (should fail)"

# =============================================================================
# TEST 3: Available Transcript Languages
# =============================================================================
print_test_header "TEST 3: Available Languages" "/video-transcript-languages" "POST"

# Test with English video
test_endpoint "POST" "/video-transcript-languages" "{\"url\": \"$ENGLISH_VIDEO\"}" "List languages for English video"

# Test with Hindi video
test_endpoint "POST" "/video-transcript-languages" "{\"url\": \"$HINDI_VIDEO\"}" "List languages for Hindi video"

# =============================================================================
# TEST 4: Video Captions
# =============================================================================
print_test_header "TEST 4: Video Captions" "/video-captions" "POST"

# Test with English video (no language specified)
test_endpoint "POST" "/video-captions" "{\"url\": \"$ENGLISH_VIDEO\"}" "Get captions (auto-detect language)"

# Test with English video (specify English)
test_endpoint "POST" "/video-captions" "{\"url\": \"$ENGLISH_VIDEO2\", \"languages\": [\"en\"]}" "Get English captions explicitly"

# Test with Hindi video (should fallback to Hindi)
test_endpoint "POST" "/video-captions" "{\"url\": \"$HINDI_VIDEO\", \"languages\": [\"en\", \"hi\"]}" "Get captions with language fallback (en->hi)"

# Test with Hindi video (Hindi only)
test_endpoint "POST" "/video-captions" "{\"url\": \"$HINDI_VIDEO\", \"languages\": [\"hi\"]}" "Get Hindi captions explicitly"

# =============================================================================
# TEST 5: Video Timestamps
# =============================================================================
print_test_header "TEST 5: Video Timestamps" "/video-timestamps" "POST"

# Test with English video
test_endpoint "POST" "/video-timestamps" "{\"url\": \"$ENGLISH_VIDEO\"}" "Get timestamps (auto-detect language)"

# Test with specific language
test_endpoint "POST" "/video-timestamps" "{\"url\": \"$ENGLISH_VIDEO2\", \"languages\": [\"en\"]}" "Get English timestamps explicitly"

# Test with Hindi video (language fallback)
test_endpoint "POST" "/video-timestamps" "{\"url\": \"$HINDI_VIDEO\", \"languages\": [\"en\", \"hi\"]}" "Get timestamps with language fallback"

# =============================================================================
# TEST 6: Error Cases
# =============================================================================
print_test_header "TEST 6: Error Handling" "various" "POST"

# Test with missing URL
test_endpoint "POST" "/video-captions" "{}" "Test with missing URL parameter"

# Test with empty URL
test_endpoint "POST" "/video-captions" "{\"url\": \"\"}" "Test with empty URL"

# Test with malformed JSON
echo -e "${BLUE}Testing: Malformed JSON request${NC}"
echo -e "${CYAN}Request:${NC}"
echo "curl -X POST \"$SERVER_URL/video-captions\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{invalid json}'"
echo ""
echo -e "${CYAN}Response:${NC}"
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST "$SERVER_URL/video-captions" \
    -H "Content-Type: application/json" \
    -d '{invalid json}' \
    --max-time $TIMEOUT 2>/dev/null)

http_status=$(echo "$response" | tail -n1 | sed 's/HTTP_STATUS://')
response_body=$(echo "$response" | sed '$d')

if [ "$http_status" = "422" ]; then
    echo -e "${YELLOW}Status: $http_status Unprocessable Entity${NC}"
else
    echo -e "${RED}Status: $http_status${NC}"
fi
echo "$response_body" | python3 -m json.tool 2>/dev/null || echo "$response_body"

# =============================================================================
# SUMMARY
# =============================================================================
echo -e "\n${CYAN}=====================================================${NC}"
echo -e "${CYAN}                    TEST SUMMARY${NC}"
echo -e "${CYAN}=====================================================${NC}"
echo -e "${GREEN}✓ All endpoint tests completed${NC}"
echo ""
echo -e "${YELLOW}Endpoints tested:${NC}"
echo -e "  ${GREEN}✓${NC} GET  /health"
echo -e "  ${GREEN}✓${NC} POST /video-data"
echo -e "  ${GREEN}✓${NC} POST /video-transcript-languages"
echo -e "  ${GREEN}✓${NC} POST /video-captions"
echo -e "  ${GREEN}✓${NC} POST /video-timestamps"
echo ""
echo -e "${YELLOW}Test scenarios covered:${NC}"
echo -e "  ${GREEN}✓${NC} English videos"
echo -e "  ${GREEN}✓${NC} Hindi videos"
echo -e "  ${GREEN}✓${NC} Language fallback"
echo -e "  ${GREEN}✓${NC} Short URL format"
echo -e "  ${GREEN}✓${NC} Error handling"
echo -e "  ${GREEN}✓${NC} Invalid inputs"
echo ""
echo -e "${BLUE}Note: Some failures are expected (error handling tests)${NC}"
echo -e "${BLUE}Check the server logs for detailed processing information${NC}"
echo -e "\n${CYAN}=====================================================${NC}"
