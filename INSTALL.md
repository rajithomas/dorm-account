# Installation & Run Instructions

This file documents how to run the various pieces of the Banking Simulator locally.

Prerequisites
- Python 3.8+ (3.10/3.11 recommended)
- A shell (zsh/bash)

1) Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install required Python packages

```bash
pip install -r requirements.txt
```

3) Static web UI (customers.html)

Start a simple static server (serves the repo root on port 8100):

```bash
./run_server.sh
# or
python3 -m http.server 8100
```

Open the UI in your browser:

http://localhost:8100/customers.html

4) SSE / Dashboard (Flask)

Start the SSE dashboard and REST API (port 5010):

```bash
python3 sse_server.py
```

Endpoints:
- Dashboard: http://localhost:5010/
- SSE stream: http://localhost:5010/sse
- API stats: http://localhost:5010/api/stats

5) MCP stdio Server (for Claude)

Start the proper MCP server (JSON-RPC over stdio). This is what Claude expects:

```bash
python3 mcp_server_mcp.py
```

6) Sample data

Generate sample data (will overwrite `data/*.csv`):

```bash
python3 generate_sample_data.py
```

7) Helpful curl examples

REST tool call (SSE server):

```bash
curl -X POST http://localhost:5010/api/tool/dormant_accounts \
  -H "Content-Type: application/json" \
  -d '{"days_inactive":180}'
```

SSE stream test:

```bash
curl -N -H "Accept: text/event-stream" http://localhost:5010/sse
```

Notes
- The SSE endpoint is a streaming endpoint and is not a JSON-RPC endpoint. Do not point MCP clients at `/sse`.
- Use the stdio MCP server (`mcp_server_mcp.py`) for Claude integration.
- FastMCP HTTP server is available at `http://localhost:8300/mcp` via `python3 mcp_server_fastmcp.py`.
