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
