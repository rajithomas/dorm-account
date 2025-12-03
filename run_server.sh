#!/usr/bin/env bash
# Convenience script to run a static HTTP server on port 8100
# Usage: ./run_server.sh

PORT=8100
echo "Starting static HTTP server on http://localhost:${PORT} (Serving current directory)"
python3 -m http.server ${PORT}
