"""find_dormant_accounts.py

Find accounts that are dormant (no transactions in the last N days)
but have performed at least one transaction above a given amount in the past.

Outputs a CSV report to `data/dormant_accounts_report.csv` and prints a summary.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from banking_datastore import BankingDataStore


DATA_DIR = Path(__file__).parent / "data"
REPORT_FILE = DATA_DIR / "dormant_accounts_report.csv"


def _parse_iso(s: str) -> datetime:
    # Handle ISO strings that end with Z (UTC)
    if s is None or s == "":
        return None
    try:
        if s.endswith('Z'):
            return datetime.fromisoformat(s.replace('Z', '+00:00'))
        return datetime.fromisoformat(s)
    except Exception:
        # Fallback: try common formats
        try:
            return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return None


def find_dormant_accounts(days_inactive: int = 180, threshold_amount: float = 1000.0,
                          require_status: str = None) -> List[Dict]:
    """Return accounts meeting the criteria.

    - days_inactive: number of days since last transaction to be considered dormant
    - threshold_amount: minimum historical transaction amount
    - require_status: if set, only consider accounts with this `status` (e.g., 'ACTIVE')
    """
    now = datetime.now(timezone.utc)

    accounts = BankingDataStore.read_accounts()
    transactions = BankingDataStore.read_ledger()

    # Index transactions by account
    tx_by_account = {}
    for tx in transactions:
        acc_id = tx.get('account_id')
        if acc_id not in tx_by_account:
            tx_by_account[acc_id] = []
        tx_by_account[acc_id].append(tx)

    results = []

    for acc in accounts:
        account_id = acc['account_id']
        if require_status and acc.get('status') != require_status:
            continue

        acc_txns = tx_by_account.get(account_id, [])
        if not acc_txns:
            # No transactions at all -> skip because we require a past large txn
            continue

        # Determine most recent transaction timestamp and largest txn amount
        latest_ts = None
        largest_amount = 0.0
        had_large = False
        for tx in acc_txns:
            ts = _parse_iso(tx.get('timestamp', ''))
            if ts:
                if latest_ts is None or ts > latest_ts:
                    latest_ts = ts

            try:
                amt = abs(float(tx.get('amount', '0') or 0))
            except Exception:
                amt = 0.0
            if amt > largest_amount:
                largest_amount = amt
            if amt >= threshold_amount:
                had_large = True

        if latest_ts is None:
            # Unparseable timestamps - treat as not dormant
            continue

        # Compute inactivity period in days
        delta = now - latest_ts
        days_since = delta.days

        if days_since >= days_inactive and had_large:
            results.append({
                'account_id': account_id,
                'customer_id': acc.get('customer_id', ''),
                'account_number': acc.get('account_number', ''),
                'last_transaction_date': latest_ts.isoformat(),
                'days_inactive': days_since,
                'largest_transaction_amount': f"{largest_amount:.2f}",
                'account_status': acc.get('status', ''),
                'current_balance': acc.get('balance', '')
            })

    return results


def write_report(rows: List[Dict]):
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not rows:
        print("No dormant accounts matching criteria found.")
        # Remove report file if exists
        if REPORT_FILE.exists():
            REPORT_FILE.unlink()
        return

    fieldnames = list(rows[0].keys())
    with open(REPORT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote report: {REPORT_FILE} ({len(rows)} rows)")


def main():
    # Default parameters; adjust as needed
    DAYS_INACTIVE = 180
    THRESHOLD = 1000.0

    print(f"Searching for accounts dormant >= {DAYS_INACTIVE} days with past tx >= ${THRESHOLD}")
    rows = find_dormant_accounts(days_inactive=DAYS_INACTIVE, threshold_amount=THRESHOLD,
                                require_status=None)

    write_report(rows)

    # Print a brief summary
    if rows:
        print("Summary:")
        for r in rows:
            print(f" - {r['account_id']} (cust {r['customer_id']}): last_tx={r['last_transaction_date']}, days_inactive={r['days_inactive']}, largest=${r['largest_transaction_amount']}")


if __name__ == '__main__':
    main()
