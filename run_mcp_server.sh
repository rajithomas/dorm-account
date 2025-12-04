#!/bin/bash
# Wrapper script to run the Banking Simulator MCP server
# For use with Supergateway or direct stdio MCP clients

cd "$(dirname "$0")" || exit 1
python3 mcp_server_mcp.py "$@"