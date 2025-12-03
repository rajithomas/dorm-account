"""generate_sample_data.py

Generate sample CSV data for the banking simulator.

Creates these files under `data/`:
 - customers.csv (>= 100 customers)
 - accounts.csv (1-3 accounts per customer)
 - ledger.csv (multiple transactions per account, varied timestamps and amounts)

This script uses only Python standard library so it runs without extra deps.
"""

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'
CUSTOMERS_FILE = DATA_DIR / 'customers.csv'
ACCOUNTS_FILE = DATA_DIR / 'accounts.csv'
LEDGER_FILE = DATA_DIR / 'ledger.csv'


FIRST_NAMES = [
    'James','Mary','John','Patricia','Robert','Jennifer','Michael','Linda','William','Elizabeth',
    'David','Barbara','Richard','Susan','Joseph','Jessica','Thomas','Sarah','Charles','Karen',
    'Christopher','Nancy','Daniel','Lisa','Matthew','Betty','Anthony','Margaret','Mark','Sandra',
    'Donald','Ashley','Steven','Kimberly','Paul','Emily','Andrew','Donna','Joshua','Michelle'
]

LAST_NAMES = [
    'Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez',
    'Hernandez','Lopez','Gonzalez','Wilson','Anderson','Thomas','Taylor','Moore','Jackson','Martin',
    'Lee','Perez','Thompson','White','Harris','Sanchez','Clark','Ramirez','Lewis','Robinson'
]

STREETS = ['Main St','Oak Ave','Pine Rd','Maple St','Cedar Ln','Elm St','Birch Dr','Walnut Ave']
CITIES = ['New York NY','Los Angeles CA','Chicago IL','Houston TX','Phoenix AZ','Philadelphia PA','San Antonio TX']


def rand_date(start_year=2018, end_year=None):
    if end_year is None:
        end_year = datetime.now().year
    start = datetime(start_year, 1, 1, tzinfo=timezone.utc)
    end = datetime(end_year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    delta = end - start
    seconds = random.randrange(int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def generate_customers(n_customers=120):
    rows = []
    for i in range(1, n_customers + 1):
        cid = f"C{str(i).zfill(4)}"
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        phone = f"555-{random.randint(1000,9999)}"
        address = f"{random.randint(10,999)} {random.choice(STREETS)} {random.choice(CITIES)} {random.randint(10000,99999)}"
        dob = (datetime.now() - timedelta(days=random.randint(20*365, 70*365))).date().isoformat()
        created = rand_date(2019).isoformat()
        status = random.choices(['ACTIVE','INACTIVE','CLOSED'], weights=[0.85,0.10,0.05])[0]

        rows.append({
            'customer_id': cid,
            'first_name': first,
            'last_name': last,
            'email': email,
            'phone': phone,
            'address': address,
            'date_of_birth': dob,
            'created_date': created,
            'status': status
        })
    return rows


def generate_accounts(customers):
    rows = []
    aid = 1
    for c in customers:
        # 1-3 accounts per customer
        for _ in range(random.randint(1,3)):
            account_id = f"A{str(aid).zfill(5)}"
            account_number = str(1000000000 + aid)
            account_type = random.choices(['CHECKING','SAVINGS','MONEY_MARKET'], weights=[0.6,0.3,0.1])[0]
            balance = round(random.uniform(0, 200000), 2)
            currency = 'USD'
            interest_rate = '0.0'
            if account_type == 'SAVINGS':
                interest_rate = f"{round(random.uniform(0.1,3.5),2)}"
            if account_type == 'MONEY_MARKET':
                interest_rate = f"{round(random.uniform(1.0,4.0),2)}"
            status = random.choices(['ACTIVE','FROZEN','CLOSED'], weights=[0.9,0.05,0.05])[0]
            opened_date = rand_date(2019).isoformat()
            rows.append({
                'account_id': account_id,
                'customer_id': c['customer_id'],
                'account_type': account_type,
                'account_number': account_number,
                'currency': currency,
                'balance': f"{balance:.2f}",
                'status': status,
                'interest_rate': interest_rate,
                'opened_date': opened_date,
                'closed_date': ''
            })
            aid += 1
    return rows


def generate_ledger(accounts):
    rows = []
    tid = 1
    now = datetime.now(timezone.utc)
    for acc in accounts:
        # 0-20 transactions per account
        n_tx = random.choices(range(0,21), weights=[2]+[1]*20, k=1)[0]
        last_tx_date = None
        for _ in range(n_tx):
            ts = rand_date(2019, now.year)
            tx_type = random.choice(['DEBIT','CREDIT'])
            # create amounts with some large ones to meet threshold
            if random.random() < 0.08:
                amount = round(random.uniform(1000, 50000), 2)
            else:
                amount = round(random.uniform(1, 2000), 2)
            description = random.choice(['ATM Withdrawal','POS Purchase','Salary Deposit','Transfer In','Transfer Out','Interest Credit','Fee'])
            # compute a rough balance_after (not strict ledger balancing)
            balance_after = f"{round(float(acc['balance']) + random.uniform(-500,500),2)}"
            rows.append({
                'transaction_id': f"T{str(tid).zfill(7)}",
                'account_id': acc['account_id'],
                'transaction_type': tx_type,
                'amount': f"{amount:.2f}",
                'description': description,
                'balance_after': balance_after,
                'timestamp': ts.isoformat(),
                'reference_id': '',
                'status': 'COMPLETED'
            })
            tid += 1
            last_tx_date = ts

        # To create dormant accounts, randomly ensure some accounts have older last_tx
        # (we already use dates back to 2019, so dormancy will naturally appear)

    # Shuffle transactions to simulate real ledger order
    random.shuffle(rows)
    return rows


def write_csv(path: Path, rows, fieldnames):
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    ensure_data_dir()
    customers = generate_customers(n_customers=120)
    accounts = generate_accounts(customers)
    ledger = generate_ledger(accounts)

    write_csv(CUSTOMERS_FILE, customers, ['customer_id','first_name','last_name','email','phone','address','date_of_birth','created_date','status'])
    write_csv(ACCOUNTS_FILE, accounts, ['account_id','customer_id','account_type','account_number','currency','balance','status','interest_rate','opened_date','closed_date'])
    write_csv(LEDGER_FILE, ledger, ['transaction_id','account_id','transaction_type','amount','description','balance_after','timestamp','reference_id','status'])

    print(f"Wrote {len(customers)} customers to {CUSTOMERS_FILE}")
    print(f"Wrote {len(accounts)} accounts to {ACCOUNTS_FILE}")
    print(f"Wrote {len(ledger)} transactions to {LEDGER_FILE}")


if __name__ == '__main__':
    main()
