import sqlite3
import os

DB_PATH = os.environ.get('DB_PATH', 'portal.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name2 TEXT,
        dob TEXT,
        dob2 TEXT,
        age INTEGER,
        age2 INTEGER,
        ssn_last4 TEXT,
        ssn_last4_2 TEXT,
        monthly_salary REAL DEFAULT 0,
        monthly_expenses REAL DEFAULT 0,
        insurance_deductibles REAL DEFAULT 0,
        is_married INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_report_date TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        owner TEXT DEFAULT 'client1',
        account_type TEXT,
        account_category TEXT,
        last4 TEXT,
        institution TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS liabilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        liability_type TEXT,
        interest_rate REAL,
        FOREIGN KEY(client_id) REFERENCES clients(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        report_date TEXT DEFAULT CURRENT_TIMESTAMP,
        quarter TEXT,
        inflow REAL DEFAULT 0,
        outflow REAL DEFAULT 0,
        excess REAL DEFAULT 0,
        private_reserve_balance REAL DEFAULT 0,
        private_reserve_target REAL DEFAULT 0,
        grand_total REAL DEFAULT 0,
        liabilities_total REAL DEFAULT 0,
        report_data TEXT,
        FOREIGN KEY(client_id) REFERENCES clients(id)
    )''')

    conn.commit()
    conn.close()

def seed_demo_data():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM clients")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    # Demo client 1: married couple
    c.execute('''INSERT INTO clients (name, name2, dob, dob2, age, age2, ssn_last4, ssn_last4_2,
        monthly_salary, monthly_expenses, insurance_deductibles, is_married)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        ('James Whitfield', 'Patricia Whitfield', '1965-03-14', '1967-08-22',
         60, 58, '4821', '7392', 15000, 11000, 3500, 1))
    client1_id = c.lastrowid

    accounts1 = [
        (client1_id, 'client1', 'Roth IRA', 'retirement', '2341', 'Charles Schwab'),
        (client1_id, 'client1', 'Traditional IRA', 'retirement', '8823', 'Charles Schwab'),
        (client1_id, 'client2', 'Roth IRA', 'retirement', '5512', 'Charles Schwab'),
        (client1_id, 'joint', 'Brokerage', 'non-retirement', '9901', 'Charles Schwab'),
        (client1_id, 'joint', 'Checking', 'non-retirement', '3347', 'Pinnacle Bank'),
        (client1_id, 'trust', 'Primary Residence', 'trust', '', 'Zillow'),
    ]
    c.executemany('INSERT INTO accounts (client_id, owner, account_type, account_category, last4, institution) VALUES (?,?,?,?,?,?)', accounts1)

    c.execute('INSERT INTO liabilities (client_id, liability_type, interest_rate) VALUES (?,?,?)',
              (client1_id, 'Mortgage', 3.25))
    c.execute('INSERT INTO liabilities (client_id, liability_type, interest_rate) VALUES (?,?,?)',
              (client1_id, 'Auto Loan', 4.9))

    # Demo client 2: single
    c.execute('''INSERT INTO clients (name, dob, age, ssn_last4, monthly_salary, monthly_expenses, insurance_deductibles, is_married)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        ('Robert Callahan', '1958-11-05', 66, '6104', 22000, 14000, 5200, 0))
    client2_id = c.lastrowid

    accounts2 = [
        (client2_id, 'client1', '401(k)', 'retirement', '7721', 'Fidelity'),
        (client2_id, 'client1', 'Roth IRA', 'retirement', '4490', 'Charles Schwab'),
        (client2_id, 'client1', 'Brokerage', 'non-retirement', '1183', 'Charles Schwab'),
        (client2_id, 'trust', 'Primary Residence', 'trust', '', 'Zillow'),
    ]
    c.executemany('INSERT INTO accounts (client_id, owner, account_type, account_category, last4, institution) VALUES (?,?,?,?,?,?)', accounts2)

    c.execute('INSERT INTO liabilities (client_id, liability_type, interest_rate) VALUES (?,?,?)',
              (client2_id, 'Mortgage', 2.875))

    conn.commit()
    conn.close()
