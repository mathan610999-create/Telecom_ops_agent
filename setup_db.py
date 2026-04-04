"""
setup_db.py - Creates and seeds the Telecom Ops SQLite database
Run this once before starting the agent.
"""

import sqlite3
import os

DB_PATH = "telecom_ops.db"

def setup_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # ── 1. CUSTOMERS ──────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE customers (
        customer_id     TEXT PRIMARY KEY,
        full_name       TEXT,
        phone_number    TEXT,
        plan_type       TEXT,        -- PREPAID | POSTPAID
        account_status  TEXT,        -- ACTIVE | SUSPENDED | CLOSED
        region          TEXT,
        kyc_status      TEXT,        -- VERIFIED | PENDING | FAILED
        created_at      TEXT
    )""")

    customers = [
        ("C001", "Arjun Mehta",     "+447911123401", "POSTPAID", "ACTIVE",    "UK-North",  "VERIFIED", "2022-03-10"),
        ("C002", "Sofia Reyes",     "+447911123402", "PREPAID",  "ACTIVE",    "UK-South",  "VERIFIED", "2021-07-22"),
        ("C003", "James O'Brien",   "+447911123403", "POSTPAID", "SUSPENDED", "UK-East",   "PENDING",  "2020-11-05"),
        ("C004", "Priya Nair",      "+447911123404", "PREPAID",  "ACTIVE",    "UK-West",   "VERIFIED", "2023-01-18"),
        ("C005", "Marcus Adeyemi",  "+447911123405", "POSTPAID", "ACTIVE",    "UK-North",  "FAILED",   "2022-09-30"),
        ("C006", "Lena Fischer",    "+447911123406", "PREPAID",  "ACTIVE",    "UK-South",  "VERIFIED", "2021-04-14"),
        ("C007", "Tariq Hassan",    "+447911123407", "POSTPAID", "ACTIVE",    "UK-East",   "VERIFIED", "2023-05-02"),
        ("C008", "Yuki Tanaka",     "+447911123408", "PREPAID",  "CLOSED",    "UK-West",   "VERIFIED", "2019-12-20"),
        ("C009", "Olu Adebayo",     "+447911123409", "POSTPAID", "ACTIVE",    "UK-North",  "PENDING",  "2023-08-11"),
        ("C010", "Emma Carroll",    "+447911123410", "PREPAID",  "ACTIVE",    "UK-South",  "VERIFIED", "2022-06-07"),
    ]
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?,?)", customers)

    # ── 2. MNP REQUESTS ───────────────────────────────────────────
    cur.execute("""
    CREATE TABLE mnp_requests (
        mnp_id          TEXT PRIMARY KEY,
        customer_id     TEXT,
        donor_network   TEXT,
        recipient_network TEXT,
        request_status  TEXT,   -- SUBMITTED | CARRIER_VALIDATION | DB_UPDATE | COMPLETED | FAILED
        stuck_since     TEXT,   -- NULL if not stuck
        last_updated    TEXT,
        retry_count     INTEGER,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )""")

    mnp_requests = [
        ("MNP001", "C001", "Vodafone",  "Liberty Global", "CARRIER_VALIDATION", "2024-12-09 10:30:00", "2024-12-09 10:30:00", 2),
        ("MNP002", "C002", "O2",        "Liberty Global", "COMPLETED",           None,                  "2024-12-10 14:00:00", 0),
        ("MNP003", "C003", "EE",        "Liberty Global", "DB_UPDATE",           "2024-12-08 08:15:00", "2024-12-08 08:15:00", 5),
        ("MNP004", "C004", "Three",     "Liberty Global", "SUBMITTED",           None,                  "2024-12-11 09:00:00", 0),
        ("MNP005", "C005", "Vodafone",  "Liberty Global", "FAILED",              "2024-12-07 16:45:00", "2024-12-07 16:45:00", 3),
        ("MNP006", "C007", "O2",        "Liberty Global", "CARRIER_VALIDATION", "2024-12-10 11:00:00", "2024-12-10 11:00:00", 1),
        ("MNP007", "C009", "EE",        "Liberty Global", "DB_UPDATE",           "2024-12-09 07:30:00", "2024-12-09 07:30:00", 4),
    ]
    cur.executemany("INSERT INTO mnp_requests VALUES (?,?,?,?,?,?,?,?)", mnp_requests)

    # ── 3. INCIDENTS ──────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE incidents (
        incident_id     TEXT PRIMARY KEY,
        customer_id     TEXT,
        mnp_id          TEXT,
        incident_type   TEXT,   -- MNP_STUCK | KYC_FAIL | ETL_FAIL | BILLING | NETWORK
        priority        TEXT,   -- P1 | P2 | P3
        status          TEXT,   -- OPEN | IN_PROGRESS | RESOLVED | ESCALATED
        rca             TEXT,
        created_at      TEXT,
        resolved_at     TEXT,
        assigned_team   TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )""")

    incidents = [
        ("INC001", "C001", "MNP001", "MNP_STUCK",  "P2", "OPEN",        "Carrier API timeout at validation stage",           "2024-12-09 11:00:00", None,                  "NOC-Team-A"),
        ("INC002", "C003", "MNP003", "MNP_STUCK",  "P1", "ESCALATED",   "DB lock during number portability update",          "2024-12-08 09:00:00", None,                  "DB-Team"),
        ("INC003", "C005", "MNP005", "KYC_FAIL",   "P2", "IN_PROGRESS", "KYC document mismatch - ID scan failed threshold",  "2024-12-07 17:00:00", None,                  "KYC-Team"),
        ("INC004", "C006", None,     "BILLING",    "P3", "RESOLVED",    "Duplicate charge due to plan migration race cond",  "2024-12-05 10:00:00", "2024-12-06 15:00:00", "Billing-Team"),
        ("INC005", "C007", "MNP006", "MNP_STUCK",  "P2", "OPEN",        "Carrier validation pending - awaiting ACK",         "2024-12-10 11:30:00", None,                  "NOC-Team-B"),
        ("INC006", "C009", "MNP007", "MNP_STUCK",  "P1", "IN_PROGRESS", "DB_UPDATE stage hanging - retry loop detected",     "2024-12-09 08:00:00", None,                  "DB-Team"),
        ("INC007", "C010", None,     "NETWORK",    "P3", "RESOLVED",    "Signal degradation in UK-South due to tower maint", "2024-12-08 06:00:00", "2024-12-08 20:00:00", "Network-Team"),
    ]
    cur.executemany("INSERT INTO incidents VALUES (?,?,?,?,?,?,?,?,?,?)", incidents)

    # ── 4. ETL PIPELINE LOGS ──────────────────────────────────────
    cur.execute("""
    CREATE TABLE etl_pipeline_logs (
        log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
        job_name        TEXT,    -- KYC_VERIFICATION | AML_CHECK | MNP_SYNC | BILLING_RECON
        file_name       TEXT,
        file_size_kb    INTEGER,
        status          TEXT,    -- SUCCESS | FAILED | RUNNING | SKIPPED
        stage           TEXT,    -- INGESTION | VALIDATION | TRANSFORMATION | LOAD | KRONJOB
        error_message   TEXT,
        started_at      TEXT,
        failed_at       TEXT,
        retry_count     INTEGER,
        customer_id     TEXT
    )""")

    etl_logs = [
        (1,  "KYC_VERIFICATION", "kyc_batch_20241211_001.csv", 1240, "FAILED",  "VALIDATION",     "Schema mismatch: 'dob' field format invalid (got DD/MM/YY, expected YYYY-MM-DD)", "2024-12-11 02:00:00", "2024-12-11 02:03:12", 0, "C005"),
        (2,  "KYC_VERIFICATION", "kyc_batch_20241211_002.csv", 980,  "SUCCESS", "LOAD",           None,                                                                             "2024-12-11 02:05:00", None,                  0, None),
        (3,  "AML_CHECK",        "aml_mpesa_20241211_001.xml", 3400, "FAILED",  "INGESTION",      "File encoding error: UTF-16 detected, expected UTF-8",                          "2024-12-11 03:00:00", "2024-12-11 03:00:45", 2, None),
        (4,  "AML_CHECK",        "aml_mpesa_20241210_003.xml", 2800, "SUCCESS", "LOAD",           None,                                                                             "2024-12-10 03:00:00", None,                  0, None),
        (5,  "MNP_SYNC",         "mnp_sync_20241211.json",     540,  "FAILED",  "TRANSFORMATION", "NullPointerException: carrier_code null for 3 records",                         "2024-12-11 04:00:00", "2024-12-11 04:01:33", 1, None),
        (6,  "BILLING_RECON",    "billing_dec_week2.csv",      8800, "SUCCESS", "LOAD",           None,                                                                             "2024-12-11 05:00:00", None,                  0, None),
        (7,  "KYC_VERIFICATION", "kyc_batch_20241210_005.csv", 1100, "FAILED",  "KRONJOB",        "Cron trigger missed: previous job still running, lock not released",            "2024-12-10 02:00:00", "2024-12-10 02:00:05", 3, None),
        (8,  "AML_CHECK",        "aml_mpesa_20241209_002.xml", 3100, "FAILED",  "VALIDATION",     "AML threshold breach: transaction amount exceeds $50,000 limit for unverified", "2024-12-09 03:00:00", "2024-12-09 03:02:10", 0, "C005"),
        (9,  "MNP_SYNC",         "mnp_sync_20241210.json",     510,  "SUCCESS", "LOAD",           None,                                                                             "2024-12-10 04:00:00", None,                  0, None),
        (10, "KYC_VERIFICATION", "kyc_batch_20241209_003.csv", 950,  "FAILED",  "VALIDATION",     "Duplicate customer_id detected in batch: C003 appears 3 times",                 "2024-12-09 02:00:00", "2024-12-09 02:01:55", 1, "C003"),
    ]
    cur.executemany("INSERT INTO etl_pipeline_logs VALUES (?,?,?,?,?,?,?,?,?,?,?)", etl_logs)

    conn.commit()
    conn.close()
    print("✅ Database created: telecom_ops.db")
    print("   Tables: customers, mnp_requests, incidents, etl_pipeline_logs")
    print("   Sample data loaded — ready for the agent!")

if __name__ == "__main__":
    setup_database()
