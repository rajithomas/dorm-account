"""
Demo script showing how to use the BankingDataStore utilities
"""

from banking_datastore import BankingDataStore
import uuid


def demo():
    print("=" * 60)
    print("BANKING SIMULATOR - DATA STORE DEMO")
    print("=" * 60)

    # ==================== READ EXISTING DATA ====================
    print("\n1. READ EXISTING CUSTOMERS")
    print("-" * 60)
    customers = BankingDataStore.read_customers()
    for customer in customers:
        print(f"  {customer['customer_id']}: {customer['first_name']} {customer['last_name']} ({customer['status']})")

    print("\n2. READ ACCOUNTS FOR CUSTOMER C001")
    print("-" * 60)
    accounts = BankingDataStore.get_customer_accounts("C001")
    for account in accounts:
        print(f"  {account['account_id']}: {account['account_type']} - Balance: ${account['balance']}")

    print("\n3. READ TRANSACTIONS FOR ACCOUNT A001")
    print("-" * 60)
    transactions = BankingDataStore.get_account_transactions("A001")
    for txn in transactions:
        print(f"  {txn['transaction_id']}: {txn['transaction_type']} ${txn['amount']} - {txn['description']}")

    # ==================== ADD NEW DATA ====================
    print("\n4. ADD NEW CUSTOMER")
    print("-" * 60)
    new_customer_id = "C004"
    success = BankingDataStore.add_customer(
        customer_id=new_customer_id,
        first_name="Michael",
        last_name="Williams",
        email="michael.w@email.com",
        phone="555-0104",
        address="321 Elm St Houston TX 77001",
        date_of_birth="1988-11-30"
    )
    print(f"  Added customer: {success}")

    print("\n5. ADD NEW ACCOUNT FOR C004")
    print("-" * 60)
    new_account_id = "A006"
    success = BankingDataStore.add_account(
        account_id=new_account_id,
        customer_id=new_customer_id,
        account_type="CHECKING",
        account_number="1004004001",
        currency="USD",
        balance="10000.00",
        interest_rate="0.0"
    )
    print(f"  Added account: {success}")

    # ==================== PERFORM TRANSACTION ====================
    print("\n6. ADD TRANSACTION - DEBIT")
    print("-" * 60)
    current_balance = float(BankingDataStore.get_account_balance(new_account_id))
    withdrawal_amount = 500.00
    new_balance = current_balance - withdrawal_amount
    
    transaction_id = f"T{str(uuid.uuid4())[:8].upper()}"
    success = BankingDataStore.add_transaction(
        transaction_id=transaction_id,
        account_id=new_account_id,
        transaction_type="DEBIT",
        amount=str(withdrawal_amount),
        description="ATM Withdrawal",
        balance_after=str(new_balance)
    )
    print(f"  Added transaction: {success}")

    # Update account balance
    BankingDataStore.update_account_balance(new_account_id, str(new_balance))
    print(f"  Updated account balance: ${current_balance} -> ${new_balance}")

    # ==================== GENERATE SUMMARIES ====================
    print("\n7. CUSTOMER SUMMARY (C001)")
    print("-" * 60)
    summary = BankingDataStore.get_customer_summary("C001")
    if summary:
        print(f"  Name: {summary['customer']['first_name']} {summary['customer']['last_name']}")
        print(f"  Email: {summary['customer']['email']}")
        print(f"  Total Accounts: {summary['account_count']}")
        print(f"  Total Balance: ${summary['total_balance']:.2f}")

    print("\n8. ACCOUNT SUMMARY (A001)")
    print("-" * 60)
    summary = BankingDataStore.get_account_summary("A001")
    if summary:
        print(f"  Account Type: {summary['account']['account_type']}")
        print(f"  Current Balance: ${summary['current_balance']:.2f}")
        print(f"  Total Transactions: {summary['transaction_count']}")
        print(f"  Status: {summary['account']['status']}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    demo()
