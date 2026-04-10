-- ═══════════════════════════════════════════════════════════════
-- Migration 001 (v3 - MINIMAL)
-- Uses ALTER TABLE ... ADD COLUMN IF NOT EXISTS (Postgres 9.6+)
-- No DO $$ blocks. Paste this directly into Supabase SQL Editor.
-- Does NOT touch auth.users or user_profiles.
-- ═══════════════════════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── businesses (safe create) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS businesses (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gstin         VARCHAR(15) UNIQUE NOT NULL,
    legal_name    TEXT NOT NULL,
    trade_name    TEXT,
    address       TEXT,
    state         TEXT,
    pin_code      VARCHAR(6),
    contact_email TEXT,
    contact_phone TEXT,
    is_verified   BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── invoices: create skeleton if missing ──────────────────────
CREATE TABLE IF NOT EXISTS invoices (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── invoices: add every column individually ───────────────────
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS seller_id           UUID;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS buyer_id            UUID;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS invoice_number      TEXT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS invoice_date        DATE;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS invoice_type        TEXT DEFAULT 'tax_invoice';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS seller_gstin        VARCHAR(15);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS seller_name         TEXT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS buyer_gstin         VARCHAR(15);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS buyer_name          TEXT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS place_of_supply     TEXT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS grand_total         NUMERIC(15,2);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS due_date            DATE;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS file_url            TEXT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS raw_ocr_text        TEXT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS ai_extracted_data   JSONB;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS gst_breakdown       JSONB;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS confidence_score    NUMERIC(3,2);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS validation_issues   TEXT[];
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS status              TEXT DEFAULT 'pending';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS payment_status      TEXT DEFAULT 'unpaid';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS buyer_action_reason TEXT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS shared_at           TIMESTAMPTZ;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS buyer_actioned_at   TIMESTAMPTZ;

-- ── invoices: indexes ─────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_invoices_seller_id    ON invoices(seller_id);
CREATE INDEX IF NOT EXISTS idx_invoices_buyer_id     ON invoices(buyer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_seller_gstin ON invoices(seller_gstin);
CREATE INDEX IF NOT EXISTS idx_invoices_buyer_gstin  ON invoices(buyer_gstin);
CREATE INDEX IF NOT EXISTS idx_invoices_status       ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_date         ON invoices(invoice_date);

-- ── payments ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payments (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id       UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    recorded_by      UUID NOT NULL,
    amount_paid      NUMERIC(15,2) NOT NULL,
    payment_date     DATE NOT NULL,
    payment_mode     TEXT,
    reference_number TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);

-- ── gst_returns ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gst_returns (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gstin             VARCHAR(15) NOT NULL,
    return_type       TEXT NOT NULL,
    tax_period        TEXT NOT NULL,
    status            TEXT DEFAULT 'draft',
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

-- ── missing_invoice_requests ──────────────────────────────────
CREATE TABLE IF NOT EXISTS missing_invoice_requests (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_id                UUID NOT NULL,
    seller_gstin            VARCHAR(15) NOT NULL,
    expected_invoice_number TEXT,
    period                  TEXT,
    description             TEXT,
    status                  TEXT DEFAULT 'pending',
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ── invoice_modifications ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS invoice_modifications (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id        UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    requested_by      UUID NOT NULL,
    suggested_changes JSONB NOT NULL,
    reason            TEXT,
    status            TEXT DEFAULT 'pending',
    seller_response   TEXT,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_modifications_invoice ON invoice_modifications(invoice_id);

-- ── inventory ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS inventory (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gstin        VARCHAR(15) NOT NULL,
    hsn_sac_code TEXT NOT NULL,
    description  TEXT,
    quantity     NUMERIC(15,3) DEFAULT 0,
    unit         TEXT,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(gstin, hsn_sac_code)
);
CREATE INDEX IF NOT EXISTS idx_inventory_gstin ON inventory(gstin);

-- ── inventory_logs ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS inventory_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gstin           VARCHAR(15) NOT NULL,
    hsn_sac_code    TEXT,
    direction       TEXT,
    quantity_change NUMERIC(15,3),
    invoice_number  TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- RLS Policies
-- Drop before create so this is always safe to re-run.
-- ═══════════════════════════════════════════════════════════════

ALTER TABLE invoices              ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments              ENABLE ROW LEVEL SECURITY;
ALTER TABLE gst_returns           ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_modifications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS invoice_seller_select       ON invoices;
DROP POLICY IF EXISTS invoice_seller_insert       ON invoices;
DROP POLICY IF EXISTS invoice_seller_update       ON invoices;
DROP POLICY IF EXISTS invoice_buyer_select        ON invoices;
DROP POLICY IF EXISTS payment_select              ON payments;
DROP POLICY IF EXISTS gst_return_select           ON gst_returns;
DROP POLICY IF EXISTS modifications_buyer_select  ON invoice_modifications;
DROP POLICY IF EXISTS modifications_seller_select ON invoice_modifications;
DROP POLICY IF EXISTS modifications_buyer_insert  ON invoice_modifications;

CREATE POLICY invoice_seller_select ON invoices
    FOR SELECT USING (seller_id = auth.uid());

CREATE POLICY invoice_seller_insert ON invoices
    FOR INSERT WITH CHECK (seller_id = auth.uid());

CREATE POLICY invoice_seller_update ON invoices
    FOR UPDATE USING (seller_id = auth.uid());

CREATE POLICY invoice_buyer_select ON invoices
    FOR SELECT USING (
        buyer_id = auth.uid()
        OR buyer_gstin IN (
            SELECT b.gstin FROM businesses b
            JOIN   user_profiles u ON u.business_id = b.id
            WHERE  u.id = auth.uid()
        )
    );

CREATE POLICY payment_select ON payments
    FOR SELECT USING (
        invoice_id IN (SELECT id FROM invoices WHERE seller_id = auth.uid())
    );

CREATE POLICY gst_return_select ON gst_returns
    FOR SELECT USING (
        gstin IN (
            SELECT b.gstin FROM businesses b
            JOIN   user_profiles u ON u.business_id = b.id
            WHERE  u.id = auth.uid()
        )
    );

CREATE POLICY modifications_buyer_select ON invoice_modifications
    FOR SELECT USING (requested_by = auth.uid());

CREATE POLICY modifications_seller_select ON invoice_modifications
    FOR SELECT USING (
        invoice_id IN (SELECT id FROM invoices WHERE seller_id = auth.uid())
    );

CREATE POLICY modifications_buyer_insert ON invoice_modifications
    FOR INSERT WITH CHECK (requested_by = auth.uid());
