#!/bin/bash

# ==============================================================================
# Django Development Server Startup Script
# ==============================================================================
# This script starts the Django development server for the Fundraise application.
#
# Usage:
#   ./startserver.sh          - Start server on default port 8000
#   ./startserver.sh 8080     - Start server on custom port (e.g., 8080)
#
# ==============================================================================

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Fundraise Development Server${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Default port
PORT=${1:-8000}

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found in $SCRIPT_DIR${NC}"
    echo "Please ensure you're running this script from the project root."
    exit 1
fi

# Check if port is in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port $PORT is already in use.${NC}"
    echo "You can specify a different port: ./startserver.sh <port_number>"
    echo ""
    read -p "Do you want to kill the process on port $PORT? (y/n): " choice
    if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
        lsof -ti:$PORT | xargs kill -9 2>/dev/null
        echo -e "${GREEN}Process killed. Starting server...${NC}"
    else
        echo "Exiting..."
        exit 1
    fi
fi

echo -e "${YELLOW}Starting Django development server on port $PORT...${NC}"
echo -e "Access the application at: ${GREEN}http://127.0.0.1:$PORT${NC}"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

# Run the Django development server
python3 manage.py runserver $PORT
