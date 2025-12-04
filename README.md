# Banking Simulator - Core Banking System

A Python-based banking simulator with file-based data stores (CSV), utilities for account analysis, a web UI, and an MCP server.

## Project Structure

```
dorm-account/
├── banking_datastore.py         # Core data management utilities
├── mcp_server.py                # MCP Server with 4 banking analysis tools
├── find_dormant_accounts.py     # Identifies dormant accounts with past large transactions
├── generate_sample_data.py      # Generates 120 customers + 237 accounts + 2356 transactions
├── demo.py                      # Demonstrates data store API usage
├── customers.html               # Interactive web UI (select customer → view accounts → view transactions)
├── run_server.sh                # Convenience script to start HTTP server on port 8100
├── data/
│   ├── customers.csv            # 120 customer records
│   ├── accounts.csv             # 237 account records
│   ├── ledger.csv               # 2356 transaction records
│   └── dormant_accounts_report.csv  # Report of dormant accounts
└── README.md                    # This file
```

## Data Format

### Customers (customers.csv)
| Field | Description |
|-------|-------------|
| customer_id | Unique identifier |
| first_name | First name |
| last_name | Last name |
| email | Email address |
| phone | Phone number |
| address | Residential address |
| date_of_birth | Date of birth |
| created_date | Account creation timestamp (ISO 8601) |
| status | ACTIVE, INACTIVE, or CLOSED |

### Accounts (accounts.csv)
| Field | Description |
|-------|-------------|
| account_id | Unique identifier |
| customer_id | Reference to customer |
| account_type | CHECKING, SAVINGS, or MONEY_MARKET |
| account_number | Bank account number |
| currency | USD, EUR, etc. |
| balance | Current balance |
| status | ACTIVE, FROZEN, or CLOSED |
| interest_rate | Annual interest rate |
| opened_date | Account opening date (ISO 8601) |
| closed_date | Account closing date (if applicable) |

### Ledger (ledger.csv)
| Field | Description |
|-------|-------------|
| transaction_id | Unique transaction identifier |
| account_id | Source/destination account |
| transaction_type | DEBIT or CREDIT |
| amount | Transaction amount |
| description | Transaction description |
| balance_after | Account balance after transaction |
| timestamp | Transaction timestamp (ISO 8601) |
| reference_id | For linking related transactions |
| status | PENDING, COMPLETED, or REVERSED |

## Core API - BankingDataStore

### Customer Operations
```python
BankingDataStore.read_customers()                    # Read all
BankingDataStore.get_customer(customer_id)          # Get by ID
BankingDataStore.add_customer(...)                  # Add new
BankingDataStore.update_customer_status(id, status) # Update status
```

### Account Operations
```python
BankingDataStore.read_accounts()                     # Read all
BankingDataStore.get_account(account_id)            # Get by ID
BankingDataStore.get_customer_accounts(customer_id) # Get by customer
BankingDataStore.add_account(...)                   # Add new
BankingDataStore.update_account_balance(id, balance) # Update balance
BankingDataStore.get_account_balance(account_id)    # Get balance
```

### Ledger Operations
```python
BankingDataStore.read_ledger()                      # Read all
BankingDataStore.get_transaction(transaction_id)    # Get by ID
BankingDataStore.get_account_transactions(account_id, limit=None) # Get by account
BankingDataStore.add_transaction(...)               # Add new
```

### Reporting
```python
BankingDataStore.get_customer_summary(customer_id)  # Customer + accounts
BankingDataStore.get_account_summary(account_id)    # Account + transactions
```

## MCP Server Tools

The `mcp_server.py` provides four banking analysis tools:

### 1. Get Dormant Accounts
Find accounts with no transactions for N days (default: 180).

```bash
python3 mcp_server.py dormant_accounts 180
```

### 2. Dormant Accounts with Large Transactions
Find dormant accounts that had at least one large transaction in the past (default: 180 days dormant, $1000 threshold).

```bash
python3 mcp_server.py dormant_with_large_tx 180 1000
```

### 3. Accounts with Salary Deposits
Find accounts with salary/deposit transactions above a threshold (default: $500).

```bash
python3 mcp_server.py salary_deposits 500
```

### 4. Accounts with High Balance
Find accounts with balance above a threshold (default: $100,000), sorted by balance descending.

```bash
python3 mcp_server.py high_balance 100000
```

## Web UI

Interactive HTML interface to browse customers, accounts, and transactions.

### Start the server
```bash
./run_server.sh
# or
python3 -m http.server 8100
```

### Open in browser
http://localhost:8100/customers.html

### Features
- **Customer List** (left panel): Search by name/email, click to select
- **Accounts** (right panel): Shows accounts for selected customer
- **Dormant Filter**: Toggle "Show only dormant accounts" with configurable inactivity threshold (default: 180 days)
- **Transactions**: Click an account row to view the last 10 transactions

## Servers & URLs

This project provides multiple server interfaces for different use cases.

### 1. Static Web UI Server (Port 8100)
**Purpose:** Browse customers, accounts, and transactions in an interactive web interface.

**Start:**
```bash
./run_server.sh
# or
python3 -m http.server 8100
```

**URL:**
- `http://localhost:8100/customers.html` — Interactive customer/account browser

---

### 2. SSE / Dashboard Server (Port 5010)
**Purpose:** Real-time event streaming and REST API for banking tools.

**Start:**
```bash
python3 sse_server.py
```

**Endpoints:**
- Dashboard (web UI): `http://localhost:5010/`
- SSE stream: `http://localhost:5010/sse` (text/event-stream)
- API stats: `http://localhost:5010/api/stats`
- REST tool calls (POST): `http://localhost:5010/api/tool/{tool_name}`
  - Available tools: `dormant_accounts`, `dormant_with_large_tx`, `salary_deposits`, `high_balance`

**Example REST call:**
```bash
curl -X POST http://localhost:5010/api/tool/dormant_accounts \
  -H "Content-Type: application/json" \
  -d '{"days":180}'
```

---

### 3. FastAPI HTTP Wrapper (Port 8200)
**Purpose:** REST and JSON-RPC-over-HTTP interface for the banking tools.

**Install dependencies:**
```bash
pip install fastapi uvicorn python-multipart
```

**Start:**
```bash
uvicorn mcp_server_fastapi:app --host 0.0.0.0 --port 8200
```

**Endpoints:**
- Base: `http://localhost:8200/`
- REST tools (POST): `http://localhost:8200/api/tool/{tool_name}`
- JSON-RPC (POST): `http://localhost:8200/rpc`

**Example REST call:**
```bash
curl -X POST http://localhost:8200/api/tool/dormant_with_large_tx \
  -H "Content-Type: application/json" \
  -d '{"days_inactive":180, "threshold_amount":1000}'
```

**Example JSON-RPC call:**
```bash
curl -X POST http://localhost:8200/rpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "method":"get_dormant_with_large_transactions",
    "params":{"days_inactive":180,"threshold_amount":1000},
    "id":1
  }'
```

---

### 4. MCP Protocol Server (stdio)
**Purpose:** Integration with Claude and other MCP-compatible clients via JSON-RPC over stdio.

**Start (MCP server only):**
```bash
python3 mcp_server_mcp.py
```

**Start (MCP server + FastAPI wrapper):**
```bash
python3 mcp_server_mcp.py --start-fastapi
```

**Start with Supergateway (HTTP gateway to MCP):**
```bash
npx -y supergateway --stdio "python3 /Users/rajithomas/lab/dorm-account/mcp_server_mcp.py"
```

Supergateway will expose the MCP server via HTTP on port 8000:
- SSE endpoint: `http://localhost:8000/sse`
- POST messages: `http://localhost:8000/message`

**Or use the shell wrapper:**
```bash
npx -y supergateway --stdio "bash /Users/rajithomas/lab/dorm-account/run_mcp_server.sh"
```

**Configuration for Claude:**

Add to your Claude settings (`.claude_config.json` or via Claude settings UI):

```json
{
  "mcpServers": {
    "banking-simulator": {
      "command": "python3",
      "args": [
        "/Users/rajithomas/lab/dorm-account/mcp_server_mcp.py"
      ]
    }
  }
}
```

Or use the provided `mcp_config.json`:
```bash
cat mcp_config.json
```

**MCP Tools (available in Claude):**
1. `get_dormant_accounts` — Find dormant accounts (days_inactive parameter)
2. `get_dormant_with_large_transactions` — Find dormant accounts with past large transactions
3. `get_accounts_with_salary_deposits` — Find accounts with salary deposits
4. `get_accounts_with_high_balance` — Find accounts with high balances

**Important:** Do NOT point MCP clients to the SSE endpoint (`http://localhost:5010/sse`). Use the stdio server or the FastAPI `/rpc` endpoint for JSON-RPC over HTTP.

---

### Summary of URLs

| Service | URL | Protocol | Purpose |
|---------|-----|----------|---------|
| Static UI | `http://localhost:8100/customers.html` | HTTP | Customer/account browser |
| SSE Dashboard | `http://localhost:5010/` | HTTP | Event dashboard |
| SSE Stream | `http://localhost:5010/sse` | SSE | Real-time events |
| REST Tools (SSE) | `http://localhost:5010/api/tool/{tool}` | HTTP POST | REST tool calls |
| REST Tools (FastAPI) | `http://localhost:8200/api/tool/{tool}` | HTTP POST | REST tool calls |
| JSON-RPC (FastAPI) | `http://localhost:8200/rpc` | HTTP POST | JSON-RPC over HTTP |
| MCP Server | stdio | JSON-RPC | Claude / MCP clients |

---

## Scripts

### Generate Sample Data
```bash
python3 generate_sample_data.py
```
Creates 120 customers, 237 accounts, and 2356 transactions with realistic data and timestamps.

### Find Dormant Accounts Report
```bash
python3 find_dormant_accounts.py
```
Generates `data/dormant_accounts_report.csv` with accounts dormant for 180+ days that had at least one transaction > $1000.

### Demo
```bash
python3 demo.py
```
Demonstrates the data store API with examples of reading, adding, and updating records.

## Example Usage

### Python API
```python
from banking_datastore import BankingDataStore

# Get all customers
customers = BankingDataStore.read_customers()

# Get customer summary
summary = BankingDataStore.get_customer_summary('C0001')
print(f"Customer: {summary['customer']['first_name']}")
print(f"Total Balance: ${summary['total_balance']:.2f}")

# Add a transaction
BankingDataStore.add_transaction(
    transaction_id='T0000100',
    account_id='A00001',
    transaction_type='DEBIT',
    amount='500.00',
    description='ATM Withdrawal',
    balance_after='4500.00'
)
```

### MCP Server
```bash
# Find all dormant accounts (180+ days)
python3 mcp_server.py dormant_accounts 180

# Find dormant accounts with past large transactions
python3 mcp_server.py dormant_with_large_tx 180 1000

# Find accounts with salary deposits
python3 mcp_server.py salary_deposits 500

# Find wealthy accounts
python3 mcp_server.py high_balance 100000
```

## Requirements

- Python 3.7+
- No external dependencies (uses only standard library)

## Development Notes

- All timestamps use ISO 8601 format with UTC (Z suffix)
- Balances are stored as floating-point decimals (2 decimal places)
- CSV files are the single source of truth (file-based data store)
- All operations read/write entire CSV files (suitable for smaller datasets)
