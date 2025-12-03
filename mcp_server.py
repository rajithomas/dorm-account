#!/usr/bin/env python3
"""
MCP Server for Banking Simulator.

Provides four tools to analyze customer accounts via CLI or MCP:
1. Get dormant accounts (no transactions for N days)
2. Dormant accounts with large transactions in the past
3. Accounts with salary deposits above threshold
4. Accounts with balance above threshold
"""

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

from banking_datastore import BankingDataStore


class BankingAnalyzer:
    """Banking analysis tools."""

    @staticmethod
    def get_dormant_accounts(days_inactive: int = 180) -> List[Dict[str, Any]]:
        """Find accounts dormant for at least N days (no recent transactions)."""
        now = datetime.now(timezone.utc)
        accounts = BankingDataStore.read_accounts()
        ledger = BankingDataStore.read_ledger()

        tx_by_account = {}
        for tx in ledger:
            acc_id = tx.get('account_id')
            if acc_id not in tx_by_account:
                tx_by_account[acc_id] = []
            tx_by_account[acc_id].append(tx)

        results = []
        for acc in accounts:
            account_id = acc['account_id']
            txns = tx_by_account.get(account_id, [])

            if not txns:
                results.append({
                    'account_id': account_id,
                    'customer_id': acc.get('customer_id', ''),
                    'account_number': acc.get('account_number', ''),
                    'balance': float(acc.get('balance', 0)),
                    'status': acc.get('status', ''),
                    'last_transaction': None,
                    'days_inactive': None,
                })
                continue

            latest_ts = None
            for tx in txns:
                try:
                    ts_str = tx.get('timestamp', '')
                    if ts_str.endswith('Z'):
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    else:
                        ts = datetime.fromisoformat(ts_str)
                    if latest_ts is None or ts > latest_ts:
                        latest_ts = ts
                except Exception:
                    pass

            if latest_ts is None:
                continue

            days_since = (now - latest_ts).days
            if days_since >= days_inactive:
                results.append({
                    'account_id': account_id,
                    'customer_id': acc.get('customer_id', ''),
                    'account_number': acc.get('account_number', ''),
                    'balance': float(acc.get('balance', 0)),
                    'status': acc.get('status', ''),
                    'last_transaction': latest_ts.isoformat(),
                    'days_inactive': days_since,
                })

        return results

    @staticmethod
    def get_dormant_with_large_transactions(days_inactive: int = 180,
                                           threshold_amount: float = 1000.0) -> List[Dict[str, Any]]:
        """Find dormant accounts that had large transactions in the past."""
        now = datetime.now(timezone.utc)
        accounts = BankingDataStore.read_accounts()
        ledger = BankingDataStore.read_ledger()

        tx_by_account = {}
        for tx in ledger:
            acc_id = tx.get('account_id')
            if acc_id not in tx_by_account:
                tx_by_account[acc_id] = []
            tx_by_account[acc_id].append(tx)

        results = []
        for acc in accounts:
            account_id = acc['account_id']
            txns = tx_by_account.get(account_id, [])

            if not txns:
                continue

            latest_ts = None
            largest_amount = 0.0
            had_large = False
            for tx in txns:
                try:
                    ts_str = tx.get('timestamp', '')
                    if ts_str.endswith('Z'):
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    else:
                        ts = datetime.fromisoformat(ts_str)
                    if latest_ts is None or ts > latest_ts:
                        latest_ts = ts
                except Exception:
                    pass

                try:
                    amt = abs(float(tx.get('amount', 0)))
                    if amt > largest_amount:
                        largest_amount = amt
                    if amt >= threshold_amount:
                        had_large = True
                except Exception:
                    pass

            if latest_ts is None or not had_large:
                continue

            days_since = (now - latest_ts).days
            if days_since >= days_inactive:
                results.append({
                    'account_id': account_id,
                    'customer_id': acc.get('customer_id', ''),
                    'account_number': acc.get('account_number', ''),
                    'balance': float(acc.get('balance', 0)),
                    'status': acc.get('status', ''),
                    'last_transaction': latest_ts.isoformat(),
                    'days_inactive': days_since,
                    'largest_transaction_amount': largest_amount,
                })

        return results

    @staticmethod
    def get_accounts_with_salary_deposits(min_amount: float = 500.0) -> List[Dict[str, Any]]:
        """Find accounts with salary deposits above min_amount."""
        accounts = BankingDataStore.read_accounts()
        ledger = BankingDataStore.read_ledger()

        tx_by_account = {}
        for tx in ledger:
            acc_id = tx.get('account_id')
            if acc_id not in tx_by_account:
                tx_by_account[acc_id] = []
            tx_by_account[acc_id].append(tx)

        results = []
        for acc in accounts:
            account_id = acc['account_id']
            txns = tx_by_account.get(account_id, [])

            salary_txns = []
            for tx in txns:
                desc = (tx.get('description', '') or '').lower()
                if 'salary' in desc or 'deposit' in desc:
                    try:
                        amt = float(tx.get('amount', 0))
                        if amt >= min_amount:
                            salary_txns.append({
                                'transaction_id': tx.get('transaction_id', ''),
                                'amount': amt,
                                'timestamp': tx.get('timestamp', ''),
                                'description': tx.get('description', ''),
                            })
                    except Exception:
                        pass

            if salary_txns:
                max_salary = max(t['amount'] for t in salary_txns)
                results.append({
                    'account_id': account_id,
                    'customer_id': acc.get('customer_id', ''),
                    'account_number': acc.get('account_number', ''),
                    'balance': float(acc.get('balance', 0)),
                    'status': acc.get('status', ''),
                    'salary_transactions_count': len(salary_txns),
                    'max_salary_deposit': max_salary,
                    'recent_salary_deposits': salary_txns[-3:],
                })

        return results

    @staticmethod
    def get_accounts_with_high_balance(min_balance: float = 100000.0) -> List[Dict[str, Any]]:
        """Find accounts with balance above min_balance."""
        accounts = BankingDataStore.read_accounts()

        results = []
        for acc in accounts:
            try:
                balance = float(acc.get('balance', 0))
                if balance >= min_balance:
                    results.append({
                        'account_id': acc.get('account_id', ''),
                        'customer_id': acc.get('customer_id', ''),
                        'account_number': acc.get('account_number', ''),
                        'account_type': acc.get('account_type', ''),
                        'balance': balance,
                        'status': acc.get('status', ''),
                        'interest_rate': float(acc.get('interest_rate', 0)),
                    })
            except Exception:
                pass

        results.sort(key=lambda x: x['balance'], reverse=True)
        return results


def main():
    """CLI interface for testing."""
    if len(sys.argv) < 2:
        print("Usage: mcp_server.py <tool> [args...]")
        print("\nTools:")
        print("  dormant_accounts [days=180]")
        print("  dormant_with_large_tx [days=180] [amount=1000]")
        print("  salary_deposits [min_amount=500]")
        print("  high_balance [min_balance=100000]")
        sys.exit(1)

    tool_name = sys.argv[1]

    try:
        if tool_name == 'dormant_accounts':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 180
            result = BankingAnalyzer.get_dormant_accounts(days_inactive=days)
            print(json.dumps(result, indent=2))

        elif tool_name == 'dormant_with_large_tx':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 180
            threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 1000.0
            result = BankingAnalyzer.get_dormant_with_large_transactions(
                days_inactive=days, threshold_amount=threshold)
            print(json.dumps(result, indent=2))

        elif tool_name == 'salary_deposits':
            min_amt = float(sys.argv[2]) if len(sys.argv) > 2 else 500.0
            result = BankingAnalyzer.get_accounts_with_salary_deposits(min_amount=min_amt)
            print(json.dumps(result, indent=2))

        elif tool_name == 'high_balance':
            min_bal = float(sys.argv[2]) if len(sys.argv) > 2 else 100000.0
            result = BankingAnalyzer.get_accounts_with_high_balance(min_balance=min_bal)
            print(json.dumps(result, indent=2))

        else:
            print(f"Unknown tool: {tool_name}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
