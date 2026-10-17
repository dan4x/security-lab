"""
Test database generator for `challenge.db` — simulates a payment ACQUIRER.

This is a SYNTHETIC database, created only for security exercises in this
lab. It mimics the *volume* and *schema* of a card-acquiring financial
institution (POS terminals), so exploitation practice happens under
conditions close to real-world:

  - many tables from different applications sharing the same database;
  - one large table (`transactions`, hundreds of thousands of rows) that
    stresses content scans;
  - a target value (`CW{...}`) hidden in an internal secrets table
    (`internal_config`), NOT in `users` — to exercise schema enumeration.

Deterministic (fixed seed) to be reproducible. All data is fictitious.
"""
import os
import random
import sqlite3

# Portable path: the database is created next to this script (repo root).
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "challenge.db")

# Volume (tunable). `transactions` is the deliberately "heavy" table.
N_MERCHANTS = 5_000
N_TERMINALS = 8_000
N_CARDHOLDERS = 10_000
N_TRANSACTIONS = 300_000
N_SETTLEMENTS = 20_000
N_CHARGEBACKS = 2_000
N_API_KEYS = 6_000
N_AUDIT = 15_000

# Target value — fictitious test string, disguised as an operational secret.
FLAG = "CW{s1mul4t3d_fl4g_ch4ll3ng3}"

random.seed(1337)

if os.path.exists(DB):
    os.remove(DB)

conn = sqlite3.connect(DB)
c = conn.cursor()
# PRAGMAs only to speed up bulk generation.
c.execute("PRAGMA journal_mode=OFF")
c.execute("PRAGMA synchronous=OFF")

BRANDS = ["visa", "mastercard", "elo", "amex", "hipercard"]
STATUS_TX = ["approved", "declined", "reversed", "pending"]
MODELS = ["D195", "S920", "A910", "MP35", "PAX-A50"]

# --- App: merchant registry ------------------------------------------------ #
c.execute("""CREATE TABLE merchants (
    id INTEGER PRIMARY KEY, legal_name TEXT, trade_name TEXT, cnpj TEXT,
    mcc INTEGER, email TEXT, phone TEXT, status TEXT, created_at TEXT)""")
c.executemany(
    "INSERT INTO merchants VALUES (?,?,?,?,?,?,?,?,?)",
    [(i, f"Company {i} LLC", f"Shop {i}",
      f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99)}",
      random.choice([5411, 5812, 5912, 5999, 7372]),
      f"contact{i}@shop{i}.com", f"+1555{random.randint(10**7,10**8-1)}",
      random.choice(["active", "blocked", "pending"]),
      f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}")
     for i in range(1, N_MERCHANTS + 1)])

# --- App: POS terminal fleet ------------------------------------------------ #
c.execute("""CREATE TABLE terminals (
    id INTEGER PRIMARY KEY, merchant_id INTEGER, serial_number TEXT,
    model TEXT, firmware TEXT, status TEXT, activated_at TEXT)""")
c.executemany(
    "INSERT INTO terminals VALUES (?,?,?,?,?,?,?)",
    [(i, random.randint(1, N_MERCHANTS), f"SN{random.randint(10**9,10**10-1)}",
      random.choice(MODELS), f"1.{random.randint(0,9)}.{random.randint(0,20)}",
      random.choice(["active", "inactive"]),
      f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}")
     for i in range(1, N_TERMINALS + 1)])

# --- App: cardholders ------------------------------------------------------ #
c.execute("""CREATE TABLE cardholders (
    id INTEGER PRIMARY KEY, name TEXT, document TEXT, card_bin TEXT,
    card_last4 TEXT, issuer TEXT)""")
c.executemany(
    "INSERT INTO cardholders VALUES (?,?,?,?,?,?)",
    [(i, f"Customer {i}", f"{random.randint(10**10, 10**11-1)}",
      f"{random.randint(400000,599999)}", f"{random.randint(0,9999):04d}",
      random.choice(["Chase", "BankOfAmerica", "Wells Fargo", "Citi", "Capital One"]))
     for i in range(1, N_CARDHOLDERS + 1)])

# --- App: transactions (HEAVY TABLE) ---------------------------------------- #
c.execute("""CREATE TABLE transactions (
    id INTEGER PRIMARY KEY, merchant_id INTEGER, terminal_id INTEGER,
    cardholder_id INTEGER, amount REAL, installments INTEGER, card_brand TEXT,
    auth_code TEXT, nsu TEXT, status TEXT, captured_at TEXT)""")


def _tx_rows():
    for i in range(1, N_TRANSACTIONS + 1):
        yield (i, random.randint(1, N_MERCHANTS), random.randint(1, N_TERMINALS),
               random.randint(1, N_CARDHOLDERS), round(random.uniform(1, 5000), 2),
               random.choice([1, 2, 3, 6, 12]), random.choice(BRANDS),
               f"{random.randint(100000,999999)}", f"{random.randint(10**11,10**12-1)}",
               random.choice(STATUS_TX),
               f"2025-{random.randint(1,10):02d}-{random.randint(1,28):02d}T"
               f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:00")


c.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?)", _tx_rows())

# --- App: settlements -------------------------------------------------- #
c.execute("""CREATE TABLE settlements (
    id INTEGER PRIMARY KEY, merchant_id INTEGER, gross_amount REAL,
    fees REAL, net_amount REAL, settlement_date TEXT, status TEXT)""")
c.executemany(
    "INSERT INTO settlements VALUES (?,?,?,?,?,?,?)",
    [(i, random.randint(1, N_MERCHANTS),
      (g := round(random.uniform(100, 50000), 2)),
      (f := round(g * 0.03, 2)), round(g - f, 2),
      f"2025-{random.randint(1,10):02d}-{random.randint(1,28):02d}",
      random.choice(["settled", "scheduled", "failed"]))
     for i in range(1, N_SETTLEMENTS + 1)])

# --- App: chargebacks ------------------------------------------------------ #
c.execute("""CREATE TABLE chargebacks (
    id INTEGER PRIMARY KEY, transaction_id INTEGER, reason_code TEXT,
    amount REAL, status TEXT, opened_at TEXT)""")
c.executemany(
    "INSERT INTO chargebacks VALUES (?,?,?,?,?,?)",
    [(i, random.randint(1, N_TRANSACTIONS),
      random.choice(["4837", "4855", "4863", "13.1", "10.4"]),
      round(random.uniform(10, 5000), 2),
      random.choice(["opened", "won", "lost"]),
      f"2025-{random.randint(1,10):02d}-{random.randint(1,28):02d}")
     for i in range(1, N_CHARGEBACKS + 1)])

# --- App: MDR/fees table ---------------------------------------------------- #
c.execute("""CREATE TABLE fees_config (
    id INTEGER PRIMARY KEY, mcc INTEGER, brand TEXT, installments INTEGER,
    mdr_rate REAL)""")
c.executemany(
    "INSERT INTO fees_config VALUES (?,?,?,?,?)",
    [(i, random.choice([5411, 5812, 5912, 5999, 7372]), random.choice(BRANDS),
      random.choice([1, 2, 6, 12]), round(random.uniform(0.9, 4.5), 2))
     for i in range(1, 400)])

# --- App: internal users (admin panel) -------------------------------------- #
c.execute("""CREATE TABLE users (
    id INTEGER PRIMARY KEY, username TEXT, email TEXT, password_hash TEXT,
    role TEXT)""")
c.executemany(
    "INSERT INTO users VALUES (?,?,?,?,?)",
    [(i, f"operator{i}", f"operator{i}@acquirer.local",
      f"$2b$12${random.getrandbits(128):032x}",
      random.choice(["operator", "analyst", "admin"]))
     for i in range(1, 51)] +
    [(999, "admin", "admin@acquirer.local",
      f"$2b$12${random.getrandbits(128):032x}", "superadmin")])

# --- App: merchant API keys -------------------------------------------------- #
c.execute("""CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY, merchant_id INTEGER, key_hash TEXT, scope TEXT,
    created_at TEXT)""")
c.executemany(
    "INSERT INTO api_keys VALUES (?,?,?,?,?)",
    [(i, random.randint(1, N_MERCHANTS), f"sk_live_{random.getrandbits(160):040x}",
      random.choice(["read", "write", "full"]),
      f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}")
     for i in range(1, N_API_KEYS + 1)])

# --- App: audit trail -------------------------------------------------- #
c.execute("""CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY, actor TEXT, action TEXT, detail TEXT, ts TEXT)""")
c.executemany(
    "INSERT INTO audit_log VALUES (?,?,?,?,?)",
    [(i, f"operator{random.randint(1,50)}",
      random.choice(["login", "refund", "block_merchant", "export_report"]),
      f"ref={random.randint(10**5,10**6)}",
      f"2025-{random.randint(1,10):02d}-{random.randint(1,28):02d}")
     for i in range(1, N_AUDIT + 1)])

# --- App: internal config/secrets — THE TARGET VALUE LIVES HERE ------------ #
# Disguised among plausible operational secrets; the exercise is finding it
# by scanning content, without knowing the table/column ahead of time.
c.execute("""CREATE TABLE internal_config (
    id INTEGER PRIMARY KEY, key TEXT, value TEXT)""")
c.executemany(
    "INSERT INTO internal_config (key, value) VALUES (?,?)",
    [("db_version", "9.4.1"),
     ("maintenance_mode", "false"),
     ("acquirer_bin", "506699"),
     ("settlement_window_hours", "24"),
     ("backup_encryption_key", FLAG),  # <- the target value
     ("smtp_host", "smtp.acquirer.local")])

conn.commit()

# Summary
print("test database created at", DB)
for (name,) in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    n = c.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
    print(f"  {name:16s} {n:>8d} rows")
print("size:", round(os.path.getsize(DB) / 1024 / 1024, 1), "MB")
conn.close()
