# Supabase Setup Guide

Complete guide to set up your free Supabase database and connect both the local Tally connector and the Streamlit dashboard.

---

## Part 1 — Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up (free, no credit card needed).

2. Click **New Project**.

3. Fill in:
   | Field | Value |
   |-------|-------|
   | Organization | your name or business |
   | Project name | `retail-pos` (or anything) |
   | Database Password | **Create a strong password — copy it now, you cannot see it again** |
   | Region | **Southeast Asia (Singapore)** — closest to India |

4. Click **Create new project**. Wait ~2 minutes for provisioning.

---

## Part 2 — Initialize the Schema

1. In the Supabase dashboard, click **SQL Editor** (left sidebar).

2. Click **+ New query**.

3. Open `pos-cloud/schema.sql` from this repo, copy the entire contents, and paste into the editor.

4. Click **Run** (or Ctrl+Enter). You should see "Success. No rows returned."

5. Click **Table Editor** (left sidebar) — you should see all 11 tables listed.

### Insert your first store

Run this in the SQL Editor — replace values with your actual store details:

```sql
INSERT INTO stores (store_id, store_name, api_key_hash, is_active)
VALUES ('STORE001', 'Hariom Enterprise', 'direct-db-auth', true);
```

**What each column means:**

| Column | Example | What it does |
|--------|---------|--------------|
| `store_id` | `'STORE001'` | Short code **you choose**. No spaces, uppercase. Used in `config.ini` on the Tally PC and typed into the Streamlit dashboard to view that store's data. |
| `store_name` | `'Hariom Enterprise'` | Full business name. For your reference only — not checked by code. |
| `api_key_hash` | `'direct-db-auth'` | Always use this exact value. It's a leftover column from the old HTTP API design. In the Supabase setup, authorization is the DB password — this column is never checked. |
| `is_active` | `true` | Set `false` to disable a store without deleting its data. |

**Rules for `store_id`:**
- Keep it short and simple: `HARIOM01`, `STORE001`, `SHOP002`
- No spaces or special characters
- Must match **exactly** what you put in `config.ini` → `store_id =` on the Tally PC
- This is what you type in the Streamlit dashboard Store ID box

**Adding a second store** (run separately for each new store):
```sql
INSERT INTO stores (store_id, store_name, api_key_hash, is_active)
VALUES ('STORE002', 'Second Shop Name', 'direct-db-auth', true);
```

Each store gets its own `config.ini` on its own Tally PC with its unique `store_id`. All stores share the same Supabase database — data is separated by `store_id`.

---

## Part 3 — Disable Row Level Security (RLS)

Supabase enables RLS by default. Since we connect via the direct Postgres password (which bypasses RLS for the `postgres` user), this is usually fine — but to be safe, run this in the SQL Editor to ensure all tables are accessible:

```sql
ALTER TABLE stores               DISABLE ROW LEVEL SECURITY;
ALTER TABLE sales_vouchers       DISABLE ROW LEVEL SECURITY;
ALTER TABLE sales_voucher_items  DISABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_vouchers    DISABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_voucher_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE stock_items          DISABLE ROW LEVEL SECURITY;
ALTER TABLE ledger_entries       DISABLE ROW LEVEL SECURITY;
ALTER TABLE payment_entries      DISABLE ROW LEVEL SECURITY;
ALTER TABLE sync_logs            DISABLE ROW LEVEL SECURITY;
ALTER TABLE udhar                DISABLE ROW LEVEL SECURITY;
ALTER TABLE followup             DISABLE ROW LEVEL SECURITY;
```

---

## Part 4 — Get the Connection String

1. In the Supabase dashboard, click **Connect** (top of the page, next to the project name).

2. On the "Connect to your project" page:
   - **Type** → `URI`
   - **Source** → `Primary database`
   - **Method** → `Session pooler` ← important, select this one

3. Copy the connection string shown. It looks like:
   ```
   postgresql://postgres.fjjqkxemjrkzhgahubyc:[YOUR-PASSWORD]@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres
   ```

4. Replace `[YOUR-PASSWORD]` with the database password you saved when creating the project.

   Final result:
   ```
   postgresql://postgres.fjjqkxemjrkzhgahubyc:MyActualPassword@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres
   ```

> **Why Session pooler and not the others?**
> - **Transaction pooler** — resets after every statement. Our sync does `INSERT ... RETURNING id` then uses that id for child rows in the same connection. Transaction mode breaks this.
> - **Direct Connection** — works but uses a persistent TCP connection. Session pooler is preferred for apps that connect/disconnect frequently (like scheduled sync tasks).
> - **Session pooler** ✓ — stable connection per session, IPv4 compatible (works on all internet connections).

---

## Part 5 — Configure the Local Connector

Open `pos-cloud/local-connector/config.ini` and replace the placeholder values:

```ini
[tally]
host = localhost
port = 9000

[supabase]
db_url = postgresql://postgres.fjjqkxemjrkzhgahubyc:YOUR_PASSWORD@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres
store_id = STORE001

[sync]
initial_lookback_days = 7
max_days_per_sync = 30
```

- `db_url` → the Session mode connection string from Step 4
- `store_id` → must match exactly what you inserted in Part 2 (e.g. `STORE001`)

### Test the connection

If Python is available on the machine:
```bash
cd pos-cloud/local-connector
pip install -r requirements.txt
python tally_connector.py
```

If using the installed `.exe`:
```
Double-click  C:\TallySync\tally_sync.exe
```

After a successful run, go to Supabase → **Table Editor** → `sync_logs` — you should see a row with `status = success`.

---

## Part 6 — Configure the Streamlit Dashboard

### Deploy to Streamlit Community Cloud

1. Push the `pos-cloud/streamlit-app/` folder to a GitHub repository.

2. Go to [streamlit.io/cloud](https://streamlit.io/cloud) → **New app**.

3. Connect your GitHub repo, set:
   - **Main file path**: `streamlit-app/app.py`

4. Click **Advanced settings** → **Secrets**, and paste:

```toml
SUPABASE_DB_URL = "postgresql://postgres.fjjqkxemjrkzhgahubyc:YOUR_PASSWORD@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"
GROQ_API_KEY    = "gsk_your_groq_api_key_here"
```

5. Click **Deploy**. Your app will be live at `https://yourappname.streamlit.app`.

### Get your Groq API key

1. Go to [console.groq.com](https://console.groq.com) → **API Keys** → **Create API Key**.
2. Copy the key (starts with `gsk_`).
3. Paste it as `GROQ_API_KEY` in the Streamlit secrets above.

---

## Summary Checklist

| Step | Done? |
|------|-------|
| Supabase project created (Singapore region) | ☐ |
| DB password saved securely | ☐ |
| `schema.sql` run in SQL Editor — 11 tables created | ☐ |
| Store row inserted (`STORE001`) | ☐ |
| RLS disabled on all tables | ☐ |
| Session mode connection string copied | ☐ |
| `config.ini` updated with db_url + store_id | ☐ |
| Test sync run — `sync_logs` shows success | ☐ |
| Streamlit secrets set (SUPABASE_DB_URL + GROQ_API_KEY) | ☐ |
| Dashboard live at streamlit.app | ☐ |

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `connection refused` | Wrong host/port in connection string | Use Session mode URL, port 5432 |
| `password authentication failed` | Wrong password | Re-check DB password in Supabase settings |
| `relation "stores" does not exist` | schema.sql not run | Run schema.sql in SQL Editor |
| `store_id not found` | Store not inserted | Run the INSERT INTO stores SQL |
| Streamlit shows blank / no data | Wrong SUPABASE_DB_URL in secrets | Re-check secrets in Streamlit Cloud settings |
| AI Insights returns error | Wrong GROQ_API_KEY | Re-generate key at console.groq.com |
| Supabase DB paused | Free tier pauses after 1 week inactivity | Click "Restore project" in Supabase dashboard. Nightly syncs will keep it active. |
