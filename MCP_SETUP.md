# MCP Server Setup for Banking Simulator

## Overview

The Banking Simulator now has a proper **MCP (Model Context Protocol) server** that integrates with Claude and other MCP clients.

## Two Server Options

### 1. Flask SSE Server (Web Dashboard + REST API)
**File:** `sse_server.py`  
**Port:** 5010  
**URL:** http://localhost:5010

Features:
- Interactive web dashboard with banking tools
- REST API for tool execution
- Server-Sent Events (SSE) for real-time event streaming
- Event history and statistics

**Start:**
```bash
python3 sse_server.py
```

### 2. MCP Protocol Server (Claude Integration)
**File:** `mcp_server_mcp.py`  
**Protocol:** JSON-RPC over stdio  
**Format:** Model Context Protocol (MCP)

Features:
- Four banking analysis tools as MCP tools
- Direct integration with Claude
- JSON-RPC message format
- Proper MCP schema and validation

**Start:**
```bash
python3 mcp_server_mcp.py
```

## Using with Claude

### Step 1: Get the MCP Server Path
```bash
pwd
# /Users/rajithomas/lab/dorm-account
```

### Step 2: Configure in Claude Settings
1. Open Claude → Settings → Developers → API Keys & Custom Tools
2. Add a new tool server or edit `.claude_config.json`:

```json
{
  "mcpServers": {
    "banking-simulator": {
      "command": "python3",
      "args": [
        "/Users/rajithomas/lab/dorm-account/mcp_server_mcp.py"
      ],
      "env": {}
    }
  }
}
```

Or use the provided config:
```bash
cat mcp_config.json
```

### Step 3: Restart Claude
Close and reopen Claude to load the MCP server.

### Step 4: Use the Tools in Claude
Ask Claude to use the banking tools:

> "Find all dormant accounts that have been inactive for 180 days"
> "Show me accounts with salary deposits over $500"
> "What are the richest accounts in the system?"
> "Find dormant accounts with large transactions in the past"

## Four Banking Analysis Tools

### 1. `get_dormant_accounts`
**Description:** Find accounts with no transactions for N days

**Parameters:**
- `days_inactive` (integer, default: 180): Inactivity threshold in days

**Example:**
```python
# Via CLI
python3 mcp_server.py dormant_accounts 180

# Via MCP (Claude)
"Find dormant accounts"
```

### 2. `get_dormant_with_large_transactions`
**Description:** Find dormant accounts that had large transactions in the past

**Parameters:**
- `days_inactive` (integer, default: 180): Dormancy threshold
- `threshold_amount` (float, default: 1000): Minimum transaction amount

**Example:**
```python
# Via CLI
python3 mcp_server.py dormant_with_large_tx 180 1000

# Via MCP (Claude)
"Show dormant accounts with past transactions over $2000"
```

### 3. `get_accounts_with_salary_deposits`
**Description:** Find accounts with salary/deposit transactions above threshold

**Parameters:**
- `min_amount` (float, default: 500): Minimum deposit amount

**Example:**
```python
# Via CLI
python3 mcp_server.py salary_deposits 500

# Via MCP (Claude)
"Which accounts have salary deposits over $1000?"
```

### 4. `get_accounts_with_high_balance`
**Description:** Find accounts with balance above threshold (sorted descending)

**Parameters:**
- `min_balance` (float, default: 100000): Minimum balance

**Example:**
```python
# Via CLI
python3 mcp_server.py high_balance 100000

# Via MCP (Claude)
"Show me all accounts with balance over $150,000"
```

## Testing the MCP Server

### Direct Test (No Claude)
```bash
# Start server
python3 mcp_server_mcp.py

# In another terminal, send test messages (this requires MCP client library)
# Or just verify it starts without errors
```

### With Claude
1. Start the MCP server: `python3 mcp_server_mcp.py`
2. Configure Claude to use it (see Step 2 above)
3. Ask Claude to use the banking tools

## Troubleshooting

### Error: "Address already in use"
Port 5010 is in use. Kill it:
```bash
lsof -ti:5010 | xargs kill -9
```

### Error: "Module not found: mcp"
Install the MCP package:
```bash
pip install mcp
```

### Error: "JSONRPCMessage validation error"
Make sure you're using `mcp_server_mcp.py` (not `mcp_server.py` or `sse_server.py`) for Claude integration.

### Server won't connect to Claude
1. Verify Python path is correct in config
2. Test server starts: `python3 mcp_server_mcp.py` (should not error)
3. Restart Claude
4. Check Claude's developer console for errors

## Architecture

```
Banking Simulator
├── banking_datastore.py          # Core data management (CSV)
├── mcp_server.py                 # CLI tool interface
├── mcp_server_mcp.py             # MCP Protocol server (for Claude)
├── sse_server.py                 # Flask web server (REST + SSE)
├── mcp_config.json               # Claude configuration
└── data/
    ├── customers.csv
    ├── accounts.csv
    └── ledger.csv
```

## Files Created

- `mcp_server_mcp.py` — Proper MCP server for Claude integration
- `mcp_config.json` — Configuration for Claude settings
- `sse_server.py` — Flask web dashboard (separate from MCP)
- `mcp_server.py` — CLI tool runner (can also be imported by MCP server)

## Next Steps

1. **Start MCP Server:**
   ```bash
   python3 mcp_server_mcp.py
   ```

2. **Configure Claude** with the mcp_config.json

3. **Use in Claude:**
   - Ask Claude to analyze dormant accounts
   - Request salary deposit reports
   - Query high-balance accounts
   - Or use the Flask web dashboard at http://localhost:5001

---

**Note:** The MCP server uses stdio communication (standard input/output), which is the correct protocol for Claude integration. Do not use HTTP for MCP—it uses JSON-RPC over stdio.
