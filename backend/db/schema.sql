-- ═══════════════════════════════════════════════════════════════
-- Supabase PostgreSQL Schema
-- AI-Powered B2B Invoice Tracking & GST Compliance System
--
-- SAFE TO RUN on a fresh Supabase project.
-- Does NOT touch auth.users, user_profiles, or any Supabase
-- built-in tables. All user IDs reference auth.users(id) directly.
--
-- Run in: Supabase Dashboard → SQL Editor → Run
-- ═══════════════════════════════════════════════════════════════

-- Enable UUID extension (no-op if already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ── Businesses ────────────────────────────────────────────────
-- One business per GSTIN. Linked to a user via the app layer,
-- not via FK, so we don't depend on user_profiles structure.
CREATE TABLE IF NOT EXISTS businesses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gstin           VARCHAR(15) UNIQUE NOT NULL,
    legal_name      TEXT NOT NULL,
    trade_name      TEXT,
    address         TEXT,
    state           TEXT,
    pin_code        VARCHAR(6),
    contact_email   TEXT,
    contact_phone   TEXT,
    is_verified     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);


-- ── Invoices ──────────────────────────────────────────────────
-- seller_id / buyer_id are auth.users UUIDs stored directly.
-- No FK to user_profiles so this table is self-contained.
CREATE TABLE IF NOT EXISTS invoices (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User IDs (auth.users UUIDs — no FK so we don't depend on profile tables)
    seller_id           UUID NOT NULL,   -- auth.users.id of the uploading seller
    buyer_id            UUID,            -- auth.users.id of buyer (set when shared)

    -- Invoice identity
    invoice_number      TEXT,
    invoice_date        DATE,
    invoice_type        TEXT DEFAULT 'tax_invoice',   -- tax_invoice | credit_note | debit_note

    -- Parties
    seller_gstin        VARCHAR(15),
    seller_name         TEXT,
    buyer_gstin         VARCHAR(15),
    buyer_name          TEXT,
    place_of_supply     TEXT,

    -- Financials
    grand_total         NUMERIC(15, 2),
    due_date            DATE,

    -- OCR / AI output (raw)
    file_url            TEXT,            -- Supabase Storage path
    raw_ocr_text        TEXT,
    ai_extracted_data   JSONB,

    -- Server-side GST calculation result
    -- {gst_type, taxable_value, total_cgst, total_sgst, total_igst, line_items:[...]}
    gst_breakdown       JSONB,

    -- Validation
    confidence_score    NUMERIC(3, 2),
    validation_issues   TEXT[],

    -- Workflow state
    status              TEXT DEFAULT 'pending',   -- pending | shared | accepted | rejected | modified
    payment_status      TEXT DEFAULT 'unpaid',    -- unpaid | partial | paid | overdue
    buyer_action_reason TEXT,
    shared_at           TIMESTAMPTZ,
    buyer_actioned_at   TIMESTAMPTZ,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_invoices_seller_id    ON invoices(seller_id);
CREATE INDEX IF NOT EXISTS idx_invoices_buyer_id     ON invoices(buyer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_seller_gstin ON invoices(seller_gstin);
CREATE INDEX IF NOT EXISTS idx_invoices_buyer_gstin  ON invoices(buyer_gstin);
CREATE INDEX IF NOT EXISTS idx_invoices_status       ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_date         ON invoices(invoice_date);


-- ── Payments ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payments (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id       UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    recorded_by      UUID NOT NULL,      -- auth.users.id
    amount_paid      NUMERIC(15, 2) NOT NULL,
    payment_date     DATE NOT NULL,
    payment_mode     TEXT,               -- NEFT | RTGS | UPI | Cheque
    reference_number TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);


-- ── GST Returns ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gst_returns (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gstin             VARCHAR(15) NOT NULL,
    return_type       TEXT NOT NULL,     -- GSTR-1 | GSTR-3B | GSTR-9
    tax_period        TEXT NOT NULL,     -- YYYY-MM
    status            TEXT DEFAULT 'draft',   -- draft | filed
    tax_summary       JSONB,
    outward_summary   JSONB,
    inward_summary    JSONB,
    net_tax_liability JSONB,
    invoice_ids       UUID[],
    invoice_count     INTEGER DEFAULT 0,
    filed_at          TIMESTAMPTZ,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gst_returns_gstin  ON gst_returns(gstin);
CREATE INDEX IF NOT EXISTS idx_gst_returns_period ON gst_returns(tax_period);


-- ── Missing Invoice Requests ──────────────────────────────────
CREATE TABLE IF NOT EXISTS missing_invoice_requests (
    id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_id                 UUID NOT NULL,   -- auth.users.id
    seller_gstin             VARCHAR(15) NOT NULL,
    expected_invoice_number  TEXT,
    period                   TEXT,            -- YYYY-MM
    description              TEXT,
    status                   TEXT DEFAULT 'pending',
    created_at               TIMESTAMPTZ DEFAULT NOW()
);


-- ── Invoice Modifications (buyer suggestions) ─────────────────
-- Stores field-level change requests from the buyer.
-- invoice.status is set to 'modified' when a row is inserted here.
CREATE TABLE IF NOT EXISTS invoice_modifications (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id        UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    requested_by      UUID NOT NULL,     -- auth.users.id of the buyer
    suggested_changes JSONB NOT NULL,    -- e.g. {"grand_total": 15000, "line_items": [...]}
    reason            TEXT,
    status            TEXT DEFAULT 'pending',   -- pending | applied | rejected
    seller_response   TEXT,             -- seller's reply after reviewing
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_modifications_invoice ON invoice_modifications(invoice_id);


-- ── Inventory ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS inventory (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gstin        VARCHAR(15) NOT NULL,
    hsn_sac_code TEXT NOT NULL,
    description  TEXT,
    quantity     NUMERIC(15, 3) DEFAULT 0,
    unit         TEXT,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(gstin, hsn_sac_code)
);

CREATE INDEX IF NOT EXISTS idx_inventory_gstin ON inventory(gstin);


-- ── Inventory Logs ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS inventory_logs (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gstin            VARCHAR(15) NOT NULL,
    hsn_sac_code     TEXT,
    direction        TEXT,               -- 'in' | 'out'
    quantity_change  NUMERIC(15, 3),
    invoice_number   TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);


-- ═══════════════════════════════════════════════════════════════
-- Row Level Security (RLS)
-- Uses auth.uid() which is always available in Supabase.
-- Policies are dropped first so this script is safe to re-run.
-- ═══════════════════════════════════════════════════════════════

ALTER TABLE invoices               ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments               ENABLE ROW LEVEL SECURITY;
ALTER TABLE gst_returns            ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_modifications  ENABLE ROW LEVEL SECURITY;

-- ── Drop existing policies (idempotent re-run safety) ─────────
DROP POLICY IF EXISTS invoice_seller_select  ON invoices;
DROP POLICY IF EXISTS invoice_buyer_select   ON invoices;
DROP POLICY IF EXISTS invoice_seller_insert  ON invoices;
DROP POLICY IF EXISTS invoice_seller_update  ON invoices;
DROP POLICY IF EXISTS payment_select         ON payments;
DROP POLICY IF EXISTS gst_return_select      ON gst_returns;
DROP POLICY IF EXISTS modifications_buyer_select  ON invoice_modifications;
DROP POLICY IF EXISTS modifications_seller_select ON invoice_modifications;
DROP POLICY IF EXISTS modifications_buyer_insert  ON invoice_modifications;

-- ── Invoice policies ──────────────────────────────────────────

-- Seller sees their own invoices
CREATE POLICY invoice_seller_select ON invoices
    FOR SELECT USING (seller_id = auth.uid());

-- Seller can INSERT their own invoices
CREATE POLICY invoice_seller_insert ON invoices
    FOR INSERT WITH CHECK (seller_id = auth.uid());

-- Seller can UPDATE their own invoices (e.g. share, apply modification)
CREATE POLICY invoice_seller_update ON invoices
    FOR UPDATE USING (seller_id = auth.uid());

-- Buyer sees invoices where their GSTIN matches AND status is shared/accepted/etc.
-- buyer_gstin comes from the business they're linked to
CREATE POLICY invoice_buyer_select ON invoices
    FOR SELECT USING (
        buyer_id = auth.uid()
        OR buyer_gstin IN (
            SELECT b.gstin
            FROM   businesses b
            JOIN   user_profiles u ON u.business_id = b.id
            WHERE  u.id = auth.uid()
        )
    );

-- ── Payment policies ──────────────────────────────────────────

-- Visible to the seller who owns the invoice
CREATE POLICY payment_select ON payments
    FOR SELECT USING (
        invoice_id IN (
            SELECT id FROM invoices WHERE seller_id = auth.uid()
        )
    );

-- ── GST Return policies ───────────────────────────────────────

-- Only visible to the GSTIN owner (via businesses → user_profiles link)
CREATE POLICY gst_return_select ON gst_returns
    FOR SELECT USING (
        gstin IN (
            SELECT b.gstin
            FROM   businesses b
            JOIN   user_profiles u ON u.business_id = b.id
            WHERE  u.id = auth.uid()
        )
    );

-- ── Invoice modification policies ────────────────────────────

-- Buyers see their own modification requests
CREATE POLICY modifications_buyer_select ON invoice_modifications
    FOR SELECT USING (requested_by = auth.uid());

-- Sellers see modifications for their invoices
CREATE POLICY modifications_seller_select ON invoice_modifications
    FOR SELECT USING (
        invoice_id IN (
            SELECT id FROM invoices WHERE seller_id = auth.uid()
        )
    );

-- Buyers can submit modification requests
CREATE POLICY modifications_buyer_insert ON invoice_modifications
    FOR INSERT WITH CHECK (requested_by = auth.uid());