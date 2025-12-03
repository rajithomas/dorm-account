"""FastAPI-based MCP-like server

Provides HTTP/REST endpoints that implement the same tools as the stdio MCP server
and a lightweight JSON-RPC-over-HTTP endpoint (`/rpc`) for clients that prefer RPC
over HTTP. This is not a replacement for a stdio MCP server required by some MCP
clients (like Claude), but it can be useful for local integrations and testing.

Run:
    pip install fastapi uvicorn python-multipart
    uvicorn mcp_server_fastapi:app --host 0.0.0.0 --port 8200

Endpoints:
  POST /api/tool/{tool_name}    - REST tool call with JSON body of params
  POST /rpc                     - JSON-RPC 2.0 over HTTP

"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, timezone
import logging

from banking_datastore import BankingDataStore

app = FastAPI(title="Fast MCP-like Server")

# Allow local CORS for browser testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_fastapi")


def _parse_iso(ts: str) -> datetime:
    if not ts:
        raise ValueError("empty timestamp")
    # ledger timestamps use ISO with trailing Z, convert to offset-aware
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except Exception:
        # fallback - try parsing naive
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")


def find_dormant_accounts(days_inactive: int = 180) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days_inactive)

    accounts = BankingDataStore.read_accounts()
    ledger = BankingDataStore.read_ledger()

    # map account_id -> last txn datetime
    last_tx_by_account: Dict[str, Optional[datetime]] = {acc['account_id']: None for acc in accounts}
    for txn in ledger:
        acct = txn.get('account_id')
        ts = txn.get('timestamp')
        if not acct or not ts:
            continue
        try:
            t = _parse_iso(ts)
        except Exception:
            continue
        prev = last_tx_by_account.get(acct)
        if prev is None or t > prev:
            last_tx_by_account[acct] = t

    dormant = []
    for acc in accounts:
        acct_id = acc['account_id']
        last = last_tx_by_account.get(acct_id)
        if last is None or last < cutoff:
            dormant.append({**acc, 'last_transaction': last.isoformat() if last else None})

    return dormant


def find_dormant_with_large_tx(days_inactive: int = 180, threshold_amount: float = 1000.0) -> List[Dict[str, Any]]:
    dormant = find_dormant_accounts(days_inactive=days_inactive)
    ledger = BankingDataStore.read_ledger()

    # index transactions by account
    tx_by_account: Dict[str, List[Dict]] = {}
    for txn in ledger:
        tx_by_account.setdefault(txn['account_id'], []).append(txn)

    result = []
    for acc in dormant:
        acct_id = acc['account_id']
        txs = tx_by_account.get(acct_id, [])
        largest = 0.0
        largest_tx = None
        for t in txs:
            try:
                amt = abs(float(t.get('amount', '0') or 0))
            except Exception:
                amt = 0.0
            if amt > largest:
                largest = amt
                largest_tx = t
        if largest_tx and largest >= threshold_amount:
            acc_copy = dict(acc)
            acc_copy['largest_transaction_amount'] = largest
            acc_copy['largest_transaction'] = largest_tx
            result.append(acc_copy)

    return result


def find_accounts_with_salary_deposits(min_amount: float = 500.0) -> List[Dict[str, Any]]:
    ledger = BankingDataStore.read_ledger()
    accounts = BankingDataStore.read_accounts()
    acc_map = {a['account_id']: a for a in accounts}

    matching_accounts: Dict[str, Dict[str, Any]] = {}
    for txn in ledger:
        desc = (txn.get('description') or '').lower()
        try:
            amt = float(txn.get('amount', '0') or 0)
        except Exception:
            continue
        if amt >= min_amount and ('salary' in desc or 'pay' in desc or 'payroll' in desc):
            acct_id = txn['account_id']
            if acct_id not in matching_accounts:
                matching_accounts[acct_id] = {
                    'account': acc_map.get(acct_id),
                    'salary_deposits': []
                }
            matching_accounts[acct_id]['salary_deposits'].append(txn)

    return list(matching_accounts.values())


def find_accounts_with_high_balance(min_balance: float = 100000.0) -> List[Dict[str, Any]]:
    accounts = BankingDataStore.read_accounts()
    result = []
    for acc in accounts:
        try:
            bal = float(acc.get('balance', '0') or 0)
        except Exception:
            bal = 0.0
        if bal >= min_balance:
            result.append({**acc, 'balance': bal})
    # sort descending
    result.sort(key=lambda a: a['balance'], reverse=True)
    return result


class RPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None


@app.get("/", tags=["info"])
def root():
    return {"status": "ok", "message": "Fast MCP-like server. Use /api/tool/{tool_name} or /rpc"}


@app.post("/api/tool/{tool_name}")
async def run_tool(tool_name: str, request: Request):
    params = await request.json() if request.headers.get('content-type', '').startswith('application/json') else {}
    try:
        if tool_name == 'dormant_accounts':
            days = int(params.get('days_inactive', 180))
            return {'result': find_dormant_accounts(days)}
        if tool_name == 'dormant_with_large_tx':
            days = int(params.get('days_inactive', 180))
            thr = float(params.get('threshold_amount', 1000.0))
            return {'result': find_dormant_with_large_tx(days, thr)}
        if tool_name == 'salary_deposits':
            min_amt = float(params.get('min_amount', 500.0))
            return {'result': find_accounts_with_salary_deposits(min_amt)}
        if tool_name == 'high_balance':
            min_bal = float(params.get('min_balance', 100000.0))
            return {'result': find_accounts_with_high_balance(min_bal)}
    except Exception as e:
        logger.exception("tool error")
        raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=404, detail="tool not found")


@app.post('/rpc')
async def rpc_call(req: RPCRequest):
    # Simple JSON-RPC 2.0 dispatcher over HTTP
    method = req.method
    params = req.params or {}
    rpc_id = req.id
    try:
        if method == 'get_dormant_accounts':
            days = int(params.get('days_inactive', 180))
            res = find_dormant_accounts(days)
        elif method == 'get_dormant_with_large_transactions':
            days = int(params.get('days_inactive', 180))
            thr = float(params.get('threshold_amount', 1000.0))
            res = find_dormant_with_large_tx(days, thr)
        elif method == 'get_accounts_with_salary_deposits':
            min_amt = float(params.get('min_amount', 500.0))
            res = find_accounts_with_salary_deposits(min_amt)
        elif method == 'get_accounts_with_high_balance':
            min_bal = float(params.get('min_balance', 100000.0))
            res = find_accounts_with_high_balance(min_bal)
        else:
            return {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": rpc_id}

        return {"jsonrpc": "2.0", "result": res, "id": rpc_id}
    except Exception as e:
        logger.exception("rpc error")
        return {"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}, "id": rpc_id}


if __name__ == '__main__':
    print("This file is a FastAPI app. Start with uvicorn (port 8200 recommended):")
    print("  uvicorn mcp_server_fastapi:app --host 0.0.0.0 --port 8200")
