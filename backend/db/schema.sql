-- ═══════════════════════════════════════════════════════════
-- Supabase PostgreSQL Schema
-- AI-Powered B2B Invoice Tracking & GST Compliance System
-- Run this in Supabase SQL Editor to set up all tables
-- ═══════════════════════════════════════════════════════════

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Businesses ───────────────────────────────────────────────
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

-- ── User Profiles ─────────────────────────────────────────────
-- Extends Supabase auth.users
CREATE TABLE IF NOT EXISTS user_profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT NOT NULL,
    full_name   TEXT,
    role        TEXT NOT NULL DEFAULT 'seller',   -- seller | buyer | both | admin
    business_id UUID REFERENCES businesses(id),
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── Invoices ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS invoices (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_id           UUID REFERENCES user_profiles(id),
    buyer_id            UUID REFERENCES user_profiles(id),
    invoice_number      TEXT,
    invoice_date        DATE,
    seller_gstin        VARCHAR(15),
    seller_name         TEXT,
    buyer_gstin         VARCHAR(15),
    buyer_name          TEXT,
    place_of_supply     TEXT,
    invoice_type        TEXT DEFAULT 'tax_invoice',
    status              TEXT DEFAULT 'pending',
    payment_status      TEXT DEFAULT 'unpaid',
    grand_total         NUMERIC(15, 2),
    due_date            DATE,
    file_url            TEXT,
    raw_ocr_text        TEXT,
    ai_extracted_data   JSONB,
    confidence_score    NUMERIC(3, 2),
    validation_issues   TEXT[],
    buyer_action_reason TEXT,
    shared_at           TIMESTAMPTZ,
    buyer_actioned_at   TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast seller/buyer lookups
CREATE INDEX IF NOT EXISTS idx_invoices_seller_gstin ON invoices(seller_gstin);
CREATE INDEX IF NOT EXISTS idx_invoices_buyer_gstin  ON invoices(buyer_gstin);
CREATE INDEX IF NOT EXISTS idx_invoices_status       ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_date         ON invoices(invoice_date);

-- ── Payments ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payments (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id       UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    recorded_by      UUID REFERENCES user_profiles(id),
    amount_paid      NUMERIC(15, 2) NOT NULL,
    payment_date     DATE NOT NULL,
    payment_mode     TEXT,    -- NEFT | RTGS | UPI | Cheque
    reference_number TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);

-- ── GST Returns ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gst_returns (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gstin            VARCHAR(15) NOT NULL,
    return_type      TEXT NOT NULL,   -- GSTR-1 | GSTR-3B | GSTR-9
    tax_period       TEXT NOT NULL,   -- YYYY-MM
    status           TEXT DEFAULT 'draft',
    tax_summary      JSONB,
    outward_summary  JSONB,
    inward_summary   JSONB,
    net_tax_liability JSONB,
    invoice_ids      UUID[],
    invoice_count    INTEGER DEFAULT 0,
    filed_at         TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gst_returns_gstin  ON gst_returns(gstin);
CREATE INDEX IF NOT EXISTS idx_gst_returns_period ON gst_returns(tax_period);

-- ── Missing Invoice Requests ──────────────────────────────────
CREATE TABLE IF NOT EXISTS missing_invoice_requests (
    id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_id                 UUID REFERENCES user_profiles(id),
    seller_gstin             VARCHAR(15) NOT NULL,
    expected_invoice_number  TEXT,
    period                   TEXT,
    description              TEXT,
    status                   TEXT DEFAULT 'pending',
    created_at               TIMESTAMPTZ DEFAULT NOW()
);

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
    direction        TEXT,   -- 'in' | 'out'
    quantity_change  NUMERIC(15, 3),
    invoice_number   TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════
-- Row Level Security (RLS) Policies
-- Enable RLS then add policies so users only see their data
-- ═══════════════════════════════════════════════════════════

ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE gst_returns ENABLE ROW LEVEL SECURITY;

-- Sellers see their own invoices; buyers see invoices addressed to them
CREATE POLICY invoice_seller_select ON invoices
    FOR SELECT USING (seller_id = auth.uid());

CREATE POLICY invoice_buyer_select ON invoices
    FOR SELECT USING (
        buyer_gstin IN (
            SELECT b.gstin FROM businesses b
            JOIN user_profiles u ON u.business_id = b.id
            WHERE u.id = auth.uid()
        )
    );

CREATE POLICY invoice_seller_insert ON invoices
    FOR INSERT WITH CHECK (seller_id = auth.uid());

-- Payments: visible to invoice owner
CREATE POLICY payment_select ON payments
    FOR SELECT USING (
        invoice_id IN (
            SELECT id FROM invoices WHERE seller_id = auth.uid()
        )
    );

-- GST Returns: visible only to the GSTIN owner
CREATE POLICY gst_return_select ON gst_returns
    FOR SELECT USING (
        gstin IN (
            SELECT b.gstin FROM businesses b
            JOIN user_profiles u ON u.business_id = b.id
            WHERE u.id = auth.uid()
        )
    );