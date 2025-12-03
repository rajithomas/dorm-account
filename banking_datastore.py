import csv
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Data directory path
DATA_DIR = Path(__file__).parent / "data"


class BankingDataStore:
    """Utility class to manage banking data files (CSV-based)"""

    # File paths
    CUSTOMERS_FILE = DATA_DIR / "customers.csv"
    ACCOUNTS_FILE = DATA_DIR / "accounts.csv"
    LEDGER_FILE = DATA_DIR / "ledger.csv"

    @staticmethod
    def ensure_data_dir():
        """Ensure data directory exists"""
        DATA_DIR.mkdir(exist_ok=True)

    # ==================== CUSTOMER OPERATIONS ====================

    @staticmethod
    def read_customers() -> List[Dict]:
        """Read all customers from CSV"""
        BankingDataStore.ensure_data_dir()
        customers = []
        if BankingDataStore.CUSTOMERS_FILE.exists():
            with open(BankingDataStore.CUSTOMERS_FILE, 'r') as f:
                reader = csv.DictReader(f)
                customers = list(reader)
        return customers

    @staticmethod
    def get_customer(customer_id: str) -> Optional[Dict]:
        """Get a specific customer by ID"""
        customers = BankingDataStore.read_customers()
        for customer in customers:
            if customer['customer_id'] == customer_id:
                return customer
        return None

    @staticmethod
    def add_customer(customer_id: str, first_name: str, last_name: str, 
                     email: str, phone: str, address: str, 
                     date_of_birth: str, status: str = "ACTIVE") -> bool:
        """Add a new customer"""
        BankingDataStore.ensure_data_dir()
        
        # Check if customer already exists
        if BankingDataStore.get_customer(customer_id):
            print(f"Customer {customer_id} already exists")
            return False

        customer = {
            'customer_id': customer_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'address': address,
            'date_of_birth': date_of_birth,
            'created_date': datetime.utcnow().isoformat() + 'Z',
            'status': status
        }

        customers = BankingDataStore.read_customers()
        customers.append(customer)
        
        # Write back to file
        if customers:
            fieldnames = customers[0].keys()
            with open(BankingDataStore.CUSTOMERS_FILE, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(customers)
            return True
        return False

    @staticmethod
    def update_customer_status(customer_id: str, status: str) -> bool:
        """Update customer status"""
        customers = BankingDataStore.read_customers()
        for customer in customers:
            if customer['customer_id'] == customer_id:
                customer['status'] = status
                if customers:
                    fieldnames = customers[0].keys()
                    with open(BankingDataStore.CUSTOMERS_FILE, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(customers)
                return True
        return False

    # ==================== ACCOUNT OPERATIONS ====================

    @staticmethod
    def read_accounts() -> List[Dict]:
        """Read all accounts from CSV"""
        BankingDataStore.ensure_data_dir()
        accounts = []
        if BankingDataStore.ACCOUNTS_FILE.exists():
            with open(BankingDataStore.ACCOUNTS_FILE, 'r') as f:
                reader = csv.DictReader(f)
                accounts = list(reader)
        return accounts

    @staticmethod
    def get_account(account_id: str) -> Optional[Dict]:
        """Get a specific account by ID"""
        accounts = BankingDataStore.read_accounts()
        for account in accounts:
            if account['account_id'] == account_id:
                return account
        return None

    @staticmethod
    def get_customer_accounts(customer_id: str) -> List[Dict]:
        """Get all accounts for a customer"""
        accounts = BankingDataStore.read_accounts()
        return [acc for acc in accounts if acc['customer_id'] == customer_id]

    @staticmethod
    def add_account(account_id: str, customer_id: str, account_type: str,
                    account_number: str, currency: str, balance: str,
                    interest_rate: str = "0.0", status: str = "ACTIVE") -> bool:
        """Add a new account"""
        BankingDataStore.ensure_data_dir()
        
        if BankingDataStore.get_account(account_id):
            print(f"Account {account_id} already exists")
            return False

        account = {
            'account_id': account_id,
            'customer_id': customer_id,
            'account_type': account_type,
            'account_number': account_number,
            'currency': currency,
            'balance': balance,
            'status': status,
            'interest_rate': interest_rate,
            'opened_date': datetime.utcnow().isoformat() + 'Z',
            'closed_date': ''
        }

        accounts = BankingDataStore.read_accounts()
        accounts.append(account)
        
        if accounts:
            fieldnames = accounts[0].keys()
            with open(BankingDataStore.ACCOUNTS_FILE, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(accounts)
            return True
        return False

    @staticmethod
    def update_account_balance(account_id: str, new_balance: str) -> bool:
        """Update account balance"""
        accounts = BankingDataStore.read_accounts()
        for account in accounts:
            if account['account_id'] == account_id:
                account['balance'] = new_balance
                if accounts:
                    fieldnames = accounts[0].keys()
                    with open(BankingDataStore.ACCOUNTS_FILE, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(accounts)
                return True
        return False

    @staticmethod
    def get_account_balance(account_id: str) -> Optional[float]:
        """Get current account balance"""
        account = BankingDataStore.get_account(account_id)
        if account:
            return float(account['balance'])
        return None

    # ==================== LEDGER OPERATIONS ====================

    @staticmethod
    def read_ledger() -> List[Dict]:
        """Read all transactions from ledger"""
        BankingDataStore.ensure_data_dir()
        transactions = []
        if BankingDataStore.LEDGER_FILE.exists():
            with open(BankingDataStore.LEDGER_FILE, 'r') as f:
                reader = csv.DictReader(f)
                transactions = list(reader)
        return transactions

    @staticmethod
    def get_transaction(transaction_id: str) -> Optional[Dict]:
        """Get a specific transaction by ID"""
        transactions = BankingDataStore.read_ledger()
        for txn in transactions:
            if txn['transaction_id'] == transaction_id:
                return txn
        return None

    @staticmethod
    def get_account_transactions(account_id: str, limit: int = None) -> List[Dict]:
        """Get all transactions for an account"""
        transactions = BankingDataStore.read_ledger()
        account_txns = [txn for txn in transactions if txn['account_id'] == account_id]
        if limit:
            return account_txns[-limit:]
        return account_txns

    @staticmethod
    def add_transaction(transaction_id: str, account_id: str, transaction_type: str,
                       amount: str, description: str, balance_after: str,
                       reference_id: str = "", status: str = "COMPLETED") -> bool:
        """Add a new transaction to ledger"""
        BankingDataStore.ensure_data_dir()

        transaction = {
            'transaction_id': transaction_id,
            'account_id': account_id,
            'transaction_type': transaction_type,
            'amount': amount,
            'description': description,
            'balance_after': balance_after,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'reference_id': reference_id,
            'status': status
        }

        transactions = BankingDataStore.read_ledger()
        transactions.append(transaction)
        
        if transactions:
            fieldnames = transactions[0].keys()
            with open(BankingDataStore.LEDGER_FILE, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(transactions)
            return True
        return False

    # ==================== REPORTING ====================

    @staticmethod
    def get_customer_summary(customer_id: str) -> Optional[Dict]:
        """Get complete summary for a customer"""
        customer = BankingDataStore.get_customer(customer_id)
        if not customer:
            return None
        
        accounts = BankingDataStore.get_customer_accounts(customer_id)
        total_balance = sum(float(acc['balance']) for acc in accounts)
        
        return {
            'customer': customer,
            'accounts': accounts,
            'total_balance': total_balance,
            'account_count': len(accounts)
        }

    @staticmethod
    def get_account_summary(account_id: str) -> Optional[Dict]:
        """Get complete summary for an account"""
        account = BankingDataStore.get_account(account_id)
        if not account:
            return None
        
        transactions = BankingDataStore.get_account_transactions(account_id)
        
        return {
            'account': account,
            'transactions': transactions,
            'transaction_count': len(transactions),
            'current_balance': float(account['balance'])
        }
