-- Supabase schema for Retail POS Dashboard
-- Paste this into Supabase SQL Editor and click Run

CREATE TABLE IF NOT EXISTS stores (
    store_id    VARCHAR(64)  PRIMARY KEY,
    store_name  VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(128) NOT NULL,
    is_active   BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales_vouchers (
    id             SERIAL       PRIMARY KEY,
    store_id       VARCHAR(64)  NOT NULL REFERENCES stores(store_id),
    voucher_number VARCHAR(128) NOT NULL,
    voucher_date   DATE         NOT NULL,
    total_amount   NUMERIC(12, 2) NOT NULL,
    cgst_amount    NUMERIC(10, 2) DEFAULT 0,
    sgst_amount    NUMERIC(10, 2) DEFAULT 0,
    igst_amount    NUMERIC(10, 2) DEFAULT 0,
    created_at     TIMESTAMP    DEFAULT NOW(),
    UNIQUE (store_id, voucher_number)
);
CREATE INDEX IF NOT EXISTS idx_sv_store  ON sales_vouchers (store_id);
CREATE INDEX IF NOT EXISTS idx_sv_date   ON sales_vouchers (voucher_date);

CREATE TABLE IF NOT EXISTS sales_voucher_items (
    id          SERIAL       PRIMARY KEY,
    voucher_id  INTEGER      NOT NULL REFERENCES sales_vouchers(id) ON DELETE CASCADE,
    item_name   VARCHAR(255) NOT NULL,
    quantity    NUMERIC(10, 3) DEFAULT 0,
    unit        VARCHAR(32)  DEFAULT '',
    rate        NUMERIC(10, 2) DEFAULT 0,
    amount      NUMERIC(12, 2) DEFAULT 0,
    gst_rate    VARCHAR(16)  DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_svi_voucher ON sales_voucher_items (voucher_id);

CREATE TABLE IF NOT EXISTS purchase_vouchers (
    id             SERIAL       PRIMARY KEY,
    store_id       VARCHAR(64)  NOT NULL REFERENCES stores(store_id),
    voucher_number VARCHAR(128) NOT NULL,
    voucher_date   DATE         NOT NULL,
    total_amount   NUMERIC(12, 2) NOT NULL,
    cgst_amount    NUMERIC(10, 2) DEFAULT 0,
    sgst_amount    NUMERIC(10, 2) DEFAULT 0,
    igst_amount    NUMERIC(10, 2) DEFAULT 0,
    created_at     TIMESTAMP    DEFAULT NOW(),
    UNIQUE (store_id, voucher_number)
);
CREATE INDEX IF NOT EXISTS idx_pv_store  ON purchase_vouchers (store_id);
CREATE INDEX IF NOT EXISTS idx_pv_date   ON purchase_vouchers (voucher_date);

CREATE TABLE IF NOT EXISTS purchase_voucher_items (
    id          SERIAL       PRIMARY KEY,
    voucher_id  INTEGER      NOT NULL REFERENCES purchase_vouchers(id) ON DELETE CASCADE,
    item_name   VARCHAR(255) NOT NULL,
    quantity    NUMERIC(10, 3) DEFAULT 0,
    unit        VARCHAR(32)  DEFAULT '',
    rate        NUMERIC(10, 2) DEFAULT 0,
    amount      NUMERIC(12, 2) DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_pvi_voucher ON purchase_voucher_items (voucher_id);

CREATE TABLE IF NOT EXISTS stock_items (
    id            SERIAL       PRIMARY KEY,
    store_id      VARCHAR(64)  NOT NULL REFERENCES stores(store_id),
    item_name     VARCHAR(255) NOT NULL,
    item_group    VARCHAR(255) DEFAULT '',
    unit          VARCHAR(32)  DEFAULT '',
    closing_qty   NUMERIC(12, 3) DEFAULT 0,
    closing_rate  NUMERIC(10, 2) DEFAULT 0,
    closing_value NUMERIC(14, 2) DEFAULT 0,
    snapshot_date DATE         NOT NULL,
    UNIQUE (store_id, item_name, snapshot_date)
);
CREATE INDEX IF NOT EXISTS idx_si_store ON stock_items (store_id);

CREATE TABLE IF NOT EXISTS ledger_entries (
    id              SERIAL       PRIMARY KEY,
    store_id        VARCHAR(64)  NOT NULL REFERENCES stores(store_id),
    ledger_group    VARCHAR(255) NOT NULL,
    closing_balance NUMERIC(14, 2) DEFAULT 0,
    snapshot_date   DATE         NOT NULL,
    UNIQUE (store_id, ledger_group, snapshot_date)
);
CREATE INDEX IF NOT EXISTS idx_le_store ON ledger_entries (store_id);

CREATE TABLE IF NOT EXISTS payment_entries (
    id             SERIAL       PRIMARY KEY,
    store_id       VARCHAR(64)  NOT NULL REFERENCES stores(store_id),
    voucher_number VARCHAR(128) NOT NULL,
    voucher_date   DATE         NOT NULL,
    payment_type   VARCHAR(32)  NOT NULL,
    bank_or_cash   VARCHAR(32)  DEFAULT '',
    amount         NUMERIC(12, 2) DEFAULT 0,
    created_at     TIMESTAMP    DEFAULT NOW(),
    UNIQUE (store_id, voucher_number)
);
CREATE INDEX IF NOT EXISTS idx_pe_store ON payment_entries (store_id);
CREATE INDEX IF NOT EXISTS idx_pe_date  ON payment_entries (voucher_date);

CREATE TABLE IF NOT EXISTS sync_logs (
    id              SERIAL      PRIMARY KEY,
    store_id        VARCHAR(64) NOT NULL REFERENCES stores(store_id),
    sync_started_at TIMESTAMP   NOT NULL,
    sync_ended_at   TIMESTAMP,
    status          VARCHAR(32) NOT NULL DEFAULT 'started',
    from_date       DATE,
    to_date         DATE,
    sales_count     INTEGER     DEFAULT 0,
    purchase_count  INTEGER     DEFAULT 0,
    error_message   TEXT
);
CREATE INDEX IF NOT EXISTS idx_sl_store ON sync_logs (store_id);

CREATE TABLE IF NOT EXISTS udhar (
    id            SERIAL       PRIMARY KEY,
    store_id      VARCHAR(64)  NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    phone         VARCHAR(32)  NOT NULL DEFAULT '',
    items         TEXT         NOT NULL DEFAULT '',
    amount        NUMERIC(10, 2) NOT NULL,
    date_given    DATE         NOT NULL,
    due_date      DATE         NOT NULL,
    status        VARCHAR(32)  NOT NULL DEFAULT 'Pending',
    created_at    TIMESTAMP    DEFAULT NOW(),
    updated_at    TIMESTAMP    DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_udhar_store    ON udhar (store_id);
CREATE INDEX IF NOT EXISTS idx_udhar_customer ON udhar (customer_name);

CREATE TABLE IF NOT EXISTS followup (
    id                 SERIAL       PRIMARY KEY,
    store_id           VARCHAR(64)  NOT NULL,
    customer_name      VARCHAR(255) NOT NULL,
    phone              VARCHAR(32)  NOT NULL DEFAULT '',
    salesperson        VARCHAR(255) NOT NULL,
    notes              TEXT         NOT NULL DEFAULT '',
    followup_date      DATE         NOT NULL,
    next_followup_date DATE,
    status             VARCHAR(32)  NOT NULL DEFAULT 'Open',
    created_at         TIMESTAMP    DEFAULT NOW(),
    updated_at         TIMESTAMP    DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_followup_store    ON followup (store_id);
CREATE INDEX IF NOT EXISTS idx_followup_customer ON followup (customer_name);

-- Seed your first store (replace values as needed):
-- INSERT INTO stores (store_id, store_name, api_key_hash, is_active)
-- VALUES ('STORE001', 'Hariom Enterprise', 'direct-supabase-no-hash', true);
