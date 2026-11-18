--
-- PostgreSQL database dump
--

\restrict 07dLQt0aCP10Ac7ZYuSovyibD3J3X4Ksil4DlwdMX7nbQgaonhAimrqazWrpCo6

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: AcceptanceStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."AcceptanceStatus" AS ENUM (
    'NOT_REQUIRED',
    'PENDING',
    'ACCEPTED',
    'REJECTED'
);


ALTER TYPE public."AcceptanceStatus" OWNER TO nodedr;

--
-- Name: AdKind; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."AdKind" AS ENUM (
    'IMAGE',
    'VIDEO'
);


ALTER TYPE public."AdKind" OWNER TO nodedr;

--
-- Name: BackupStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."BackupStatus" AS ENUM (
    'PENDING',
    'VERIFIED',
    'FAILED'
);


ALTER TYPE public."BackupStatus" OWNER TO nodedr;

--
-- Name: BankTxStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."BankTxStatus" AS ENUM (
    'UNMATCHED',
    'MATCHED',
    'IGNORED'
);


ALTER TYPE public."BankTxStatus" OWNER TO nodedr;

--
-- Name: BuzzerCallState; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."BuzzerCallState" AS ENUM (
    'PENDING',
    'SENT',
    'ACKED',
    'EXPIRED',
    'FAILED'
);


ALTER TYPE public."BuzzerCallState" OWNER TO nodedr;

--
-- Name: BuzzerDriver; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."BuzzerDriver" AS ENUM (
    'SIMULATED',
    'WEBHOOK'
);


ALTER TYPE public."BuzzerDriver" OWNER TO nodedr;

--
-- Name: CampaignChannel; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."CampaignChannel" AS ENUM (
    'SMS',
    'EMAIL',
    'WHATSAPP'
);


ALTER TYPE public."CampaignChannel" OWNER TO nodedr;

--
-- Name: CampaignSegment; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."CampaignSegment" AS ENUM (
    'ALL',
    'LOYAL',
    'LAPSED',
    'BIRTHDAY_MONTH'
);


ALTER TYPE public."CampaignSegment" OWNER TO nodedr;

--
-- Name: CancelSource; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."CancelSource" AS ENUM (
    'STAFF',
    'CUSTOMER',
    'KITCHEN_REJECTED',
    'ONLINE_DECLINED'
);


ALTER TYPE public."CancelSource" OWNER TO nodedr;

--
-- Name: DeliveryStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."DeliveryStatus" AS ENUM (
    'UNASSIGNED',
    'ASSIGNED',
    'PICKED_UP',
    'DELIVERED',
    'FAILED'
);


ALTER TYPE public."DeliveryStatus" OWNER TO nodedr;

--
-- Name: DiscountKind; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."DiscountKind" AS ENUM (
    'PERCENT',
    'FLAT'
);


ALTER TYPE public."DiscountKind" OWNER TO nodedr;

--
-- Name: DocumentCategory; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."DocumentCategory" AS ENUM (
    'SOP',
    'CONTRACT',
    'RECIPE',
    'PURCHASE',
    'OTHER'
);


ALTER TYPE public."DocumentCategory" OWNER TO nodedr;

--
-- Name: GatewayMode; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."GatewayMode" AS ENUM (
    'TEST',
    'LIVE'
);


ALTER TYPE public."GatewayMode" OWNER TO nodedr;

--
-- Name: GatewayPaymentStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."GatewayPaymentStatus" AS ENUM (
    'CREATED',
    'SUCCEEDED',
    'FAILED',
    'EXPIRED',
    'NEEDS_REVIEW'
);


ALTER TYPE public."GatewayPaymentStatus" OWNER TO nodedr;

--
-- Name: GatewayRefundStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."GatewayRefundStatus" AS ENUM (
    'PENDING',
    'SUCCEEDED',
    'FAILED',
    'NEEDS_REVIEW'
);


ALTER TYPE public."GatewayRefundStatus" OWNER TO nodedr;

--
-- Name: IngredientCostMethod; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."IngredientCostMethod" AS ENUM (
    'AVERAGE',
    'MANUAL',
    'RECIPE'
);


ALTER TYPE public."IngredientCostMethod" OWNER TO nodedr;

--
-- Name: IngredientKind; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."IngredientKind" AS ENUM (
    'PURCHASED',
    'PREPARED'
);


ALTER TYPE public."IngredientKind" OWNER TO nodedr;

--
-- Name: IngredientUnit; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."IngredientUnit" AS ENUM (
    'KG',
    'G',
    'L',
    'ML',
    'PIECE',
    'DOZEN',
    'PACK',
    'BOX'
);


ALTER TYPE public."IngredientUnit" OWNER TO nodedr;

--
-- Name: IntegrationStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."IntegrationStatus" AS ENUM (
    'NOT_CONNECTED',
    'PENDING_CONFIGURATION',
    'CONNECTED',
    'SYNC_ERROR',
    'AUTH_EXPIRED',
    'DISABLED'
);


ALTER TYPE public."IntegrationStatus" OWNER TO nodedr;

--
-- Name: InventoryTracking; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."InventoryTracking" AS ENUM (
    'NONE',
    'RECIPE',
    'DIRECT'
);


ALTER TYPE public."InventoryTracking" OWNER TO nodedr;

--
-- Name: KotItemStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."KotItemStatus" AS ENUM (
    'NEW',
    'ACCEPTED',
    'PREPARING',
    'READY',
    'SERVED',
    'CANCELLED'
);


ALTER TYPE public."KotItemStatus" OWNER TO nodedr;

--
-- Name: KotStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."KotStatus" AS ENUM (
    'NEW',
    'ACCEPTED',
    'PREPARING',
    'READY',
    'SERVED',
    'CANCELLED',
    'REJECTED'
);


ALTER TYPE public."KotStatus" OWNER TO nodedr;

--
-- Name: LeaveStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."LeaveStatus" AS ENUM (
    'PENDING',
    'APPROVED',
    'REJECTED'
);


ALTER TYPE public."LeaveStatus" OWNER TO nodedr;

--
-- Name: LeaveType; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."LeaveType" AS ENUM (
    'ANNUAL',
    'SICK',
    'UNPAID',
    'OTHER'
);


ALTER TYPE public."LeaveType" OWNER TO nodedr;

--
-- Name: LicenseStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."LicenseStatus" AS ENUM (
    'ACTIVE',
    'EXPIRED',
    'SUSPENDED'
);


ALTER TYPE public."LicenseStatus" OWNER TO nodedr;

--
-- Name: ManualDiscountType; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."ManualDiscountType" AS ENUM (
    'PERCENT',
    'FIXED'
);


ALTER TYPE public."ManualDiscountType" OWNER TO nodedr;

--
-- Name: ModuleKey; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."ModuleKey" AS ENUM (
    'POS',
    'ORDERS',
    'TABLES',
    'RESERVATIONS',
    'MENU',
    'KDS',
    'CUSTOMERS',
    'INVENTORY',
    'DELIVERY',
    'TEAM',
    'ACCOUNTING',
    'REPORTS',
    'MARKETING',
    'OPERATIONS',
    'ATTENDANCE',
    'SETTINGS',
    'VERIFACTU',
    'INTEGRATIONS'
);


ALTER TYPE public."ModuleKey" OWNER TO nodedr;

--
-- Name: NfcTagMode; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."NfcTagMode" AS ENUM (
    'SECURE',
    'BASIC'
);


ALTER TYPE public."NfcTagMode" OWNER TO nodedr;

--
-- Name: NfcTagStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."NfcTagStatus" AS ENUM (
    'PROVISIONING',
    'ACTIVE',
    'DISABLED'
);


ALTER TYPE public."NfcTagStatus" OWNER TO nodedr;

--
-- Name: OrderChannel; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."OrderChannel" AS ENUM (
    'STAFF',
    'ONLINE'
);


ALTER TYPE public."OrderChannel" OWNER TO nodedr;

--
-- Name: OrderStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."OrderStatus" AS ENUM (
    'OPEN',
    'BILLED',
    'PAID',
    'CANCELLED'
);


ALTER TYPE public."OrderStatus" OWNER TO nodedr;

--
-- Name: OrderType; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."OrderType" AS ENUM (
    'DINE_IN',
    'TAKEAWAY',
    'DELIVERY',
    'DRIVE_THRU',
    'QR_ORDER',
    'KIOSK',
    'PHONE'
);


ALTER TYPE public."OrderType" OWNER TO nodedr;

--
-- Name: PayIntent; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."PayIntent" AS ENUM (
    'CASH',
    'ONLINE'
);


ALTER TYPE public."PayIntent" OWNER TO nodedr;

--
-- Name: PayType; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."PayType" AS ENUM (
    'MONTHLY',
    'HOURLY'
);


ALTER TYPE public."PayType" OWNER TO nodedr;

--
-- Name: PaymentMethod; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."PaymentMethod" AS ENUM (
    'CASH',
    'CARD',
    'UPI',
    'WALLET',
    'BANK_TRANSFER',
    'GIFT_CARD',
    'STORE_CREDIT',
    'OTHER'
);


ALTER TYPE public."PaymentMethod" OWNER TO nodedr;

--
-- Name: PayrollStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."PayrollStatus" AS ENUM (
    'DRAFT',
    'FINALIZED',
    'PAID'
);


ALTER TYPE public."PayrollStatus" OWNER TO nodedr;

--
-- Name: PermissionEffect; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."PermissionEffect" AS ENUM (
    'GRANT',
    'DENY'
);


ALTER TYPE public."PermissionEffect" OWNER TO nodedr;

--
-- Name: ProductionLineRole; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."ProductionLineRole" AS ENUM (
    'INPUT',
    'OUTPUT'
);


ALTER TYPE public."ProductionLineRole" OWNER TO nodedr;

--
-- Name: ProductionStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."ProductionStatus" AS ENUM (
    'DRAFT',
    'POSTED',
    'VOIDED'
);


ALTER TYPE public."ProductionStatus" OWNER TO nodedr;

--
-- Name: PurchaseOrderStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."PurchaseOrderStatus" AS ENUM (
    'DRAFT',
    'SENT',
    'PARTIALLY_RECEIVED',
    'RECEIVED',
    'CANCELLED'
);


ALTER TYPE public."PurchaseOrderStatus" OWNER TO nodedr;

--
-- Name: PurchaseRequestStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."PurchaseRequestStatus" AS ENUM (
    'DRAFT',
    'PENDING_APPROVAL',
    'APPROVED',
    'REJECTED',
    'CONVERTED'
);


ALTER TYPE public."PurchaseRequestStatus" OWNER TO nodedr;

--
-- Name: QuotationStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."QuotationStatus" AS ENUM (
    'DRAFT',
    'RECEIVED',
    'ACCEPTED',
    'REJECTED'
);


ALTER TYPE public."QuotationStatus" OWNER TO nodedr;

--
-- Name: ReferralStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."ReferralStatus" AS ENUM (
    'PENDING',
    'REWARDED'
);


ALTER TYPE public."ReferralStatus" OWNER TO nodedr;

--
-- Name: ReportFrequency; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."ReportFrequency" AS ENUM (
    'DAILY',
    'WEEKLY',
    'MONTHLY'
);


ALTER TYPE public."ReportFrequency" OWNER TO nodedr;

--
-- Name: ReservationStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."ReservationStatus" AS ENUM (
    'RESERVED',
    'CONFIRMED',
    'ARRIVED',
    'COMPLETED',
    'CANCELLED',
    'NO_SHOW'
);


ALTER TYPE public."ReservationStatus" OWNER TO nodedr;

--
-- Name: SpiceLevel; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."SpiceLevel" AS ENUM (
    'NONE',
    'MILD',
    'MEDIUM',
    'HOT',
    'EXTRA_HOT'
);


ALTER TYPE public."SpiceLevel" OWNER TO nodedr;

--
-- Name: StockJournalType; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."StockJournalType" AS ENUM (
    'TRANSFER',
    'WASTE',
    'CORRECTION'
);


ALTER TYPE public."StockJournalType" OWNER TO nodedr;

--
-- Name: StockMovementType; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."StockMovementType" AS ENUM (
    'RECEIPT',
    'WASTE',
    'ADJUSTMENT',
    'CONSUMPTION',
    'REVERSAL',
    'PRODUCTION',
    'OPENING',
    'PRODUCTION_USE'
);


ALTER TYPE public."StockMovementType" OWNER TO nodedr;

--
-- Name: SupplierInvoiceStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."SupplierInvoiceStatus" AS ENUM (
    'UNPAID',
    'PARTIALLY_PAID',
    'PAID',
    'CANCELLED'
);


ALTER TYPE public."SupplierInvoiceStatus" OWNER TO nodedr;

--
-- Name: TableRequestType; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."TableRequestType" AS ENUM (
    'WAITER',
    'BILL'
);


ALTER TYPE public."TableRequestType" OWNER TO nodedr;

--
-- Name: TableSessionStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."TableSessionStatus" AS ENUM (
    'ACTIVE',
    'CLOSED'
);


ALTER TYPE public."TableSessionStatus" OWNER TO nodedr;

--
-- Name: TableStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."TableStatus" AS ENUM (
    'AVAILABLE',
    'OCCUPIED',
    'RESERVED',
    'CLEANING',
    'OUT_OF_SERVICE'
);


ALTER TYPE public."TableStatus" OWNER TO nodedr;

--
-- Name: TaxMode; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."TaxMode" AS ENUM (
    'INCLUSIVE',
    'EXCLUSIVE'
);


ALTER TYPE public."TaxMode" OWNER TO nodedr;

--
-- Name: TaxRegime; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."TaxRegime" AS ENUM (
    'INDIA_GST',
    'US_SALES_TAX',
    'EU_VAT',
    'ES_IVA',
    'CUSTOM'
);


ALTER TYPE public."TaxRegime" OWNER TO nodedr;

--
-- Name: VerifactuEnvironment; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."VerifactuEnvironment" AS ENUM (
    'TEST',
    'PRODUCTION'
);


ALTER TYPE public."VerifactuEnvironment" OWNER TO nodedr;

--
-- Name: VerifactuRecordType; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."VerifactuRecordType" AS ENUM (
    'ALTA',
    'ANULACION'
);


ALTER TYPE public."VerifactuRecordType" OWNER TO nodedr;

--
-- Name: VerifactuStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."VerifactuStatus" AS ENUM (
    'PENDING',
    'ACCEPTED',
    'ACCEPTED_WITH_ERRORS',
    'REJECTED',
    'ERROR'
);


ALTER TYPE public."VerifactuStatus" OWNER TO nodedr;

--
-- Name: WaitlistStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."WaitlistStatus" AS ENUM (
    'WAITING',
    'SEATED',
    'CANCELLED'
);


ALTER TYPE public."WaitlistStatus" OWNER TO nodedr;

--
-- Name: WasteKind; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."WasteKind" AS ENUM (
    'INGREDIENT',
    'FINISHED'
);


ALTER TYPE public."WasteKind" OWNER TO nodedr;

--
-- Name: WasteReason; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."WasteReason" AS ENUM (
    'EXPIRED',
    'SPOILED',
    'DAMAGED',
    'PREP_ERROR',
    'OVER_PRODUCTION',
    'OTHER',
    'RETURNED_PLATE',
    'PREP_TRIM',
    'STORAGE_TEMPERATURE'
);


ALTER TYPE public."WasteReason" OWNER TO nodedr;

--
-- Name: WasteStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."WasteStatus" AS ENUM (
    'POSTED',
    'PENDING_APPROVAL',
    'REJECTED',
    'REVERSED'
);


ALTER TYPE public."WasteStatus" OWNER TO nodedr;

--
-- Name: WebhookStatus; Type: TYPE; Schema: public; Owner: nodedr
--

CREATE TYPE public."WebhookStatus" AS ENUM (
    'PENDING',
    'SUCCESS',
    'FAILED'
);


ALTER TYPE public."WebhookStatus" OWNER TO nodedr;

--
-- Name: sync_install_triggers(); Type: FUNCTION; Schema: public; Owner: nodedr
--

CREATE FUNCTION public.sync_install_triggers() RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE r record; n integer := 0;
BEGIN
  FOR r IN
    SELECT c.oid, c.relname,
           (SELECT string_agg(quote_literal(a.attname), ',' ORDER BY a.attnum)
              FROM pg_attribute a WHERE a.attrelid = c.oid AND a.attnum = ANY (k.conkey)) AS pkargs
      FROM pg_class c JOIN pg_constraint k ON k.conrelid = c.oid AND k.contype = 'p'
     WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'r' AND sync_is_synced_table(c.relname)
  LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid = r.oid AND tgname = 'sync_log') THEN
      EXECUTE format('CREATE TRIGGER sync_log AFTER INSERT OR UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION sync_log_change(%s)', r.relname, r.pkargs);
      n := n + 1;
    END IF;
  END LOOP;
  RETURN n;
END $$;


ALTER FUNCTION public.sync_install_triggers() OWNER TO nodedr;

--
-- Name: sync_is_synced_table(text); Type: FUNCTION; Schema: public; Owner: nodedr
--

CREATE FUNCTION public.sync_is_synced_table(t text) RETURNS boolean
    LANGUAGE sql IMMUTABLE
    AS $$
  SELECT t NOT LIKE 'sync\_%' AND t NOT IN
    ('_prisma_migrations', 'backups', 'backup_config', 'webhook_deliveries', 'download_stats', 'verifactu_records')
$$;


ALTER FUNCTION public.sync_is_synced_table(t text) OWNER TO nodedr;

--
-- Name: sync_log_change(); Type: FUNCTION; Schema: public; Owner: nodedr
--

CREATE FUNCTION public.sync_log_change() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  origin text := coalesce(current_setting('app.sync_origin', true), '');
  en boolean;
  rec jsonb;
  pkv jsonb := '{}';
  c text;
  ts timestamptz;
BEGIN
  IF origin = '__skip' THEN RETURN NULL; END IF;
  SELECT enabled INTO en FROM sync_state WHERE id = 1;
  IF NOT coalesce(en, false) THEN RETURN NULL; END IF;
  IF TG_OP = 'DELETE' THEN rec := to_jsonb(OLD); ELSE rec := to_jsonb(NEW); END IF;
  FOREACH c IN ARRAY TG_ARGV LOOP
    pkv := pkv || jsonb_build_object(c, rec -> c);
  END LOOP;
  ts := coalesce(nullif(current_setting('app.sync_ts', true), '')::timestamptz, clock_timestamp());
  INSERT INTO sync_changes (tbl, pk, "pkKey", op, row, ts, origin)
  VALUES (TG_TABLE_NAME, pkv, pkv::text,
          CASE WHEN TG_OP = 'DELETE' THEN 'D' ELSE 'U' END,
          CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE rec END,
          ts, CASE WHEN origin = '' THEN 'local' ELSE origin END);
  RETURN NULL;
END $$;


ALTER FUNCTION public.sync_log_change() OWNER TO nodedr;

--
-- Name: sync_seed(); Type: FUNCTION; Schema: public; Owner: nodedr
--

CREATE FUNCTION public.sync_seed() RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT c.oid, c.relname,
           (SELECT string_agg(format('%L, t.%I', a.attname, a.attname), ',' ORDER BY a.attnum)
              FROM pg_attribute a WHERE a.attrelid = c.oid AND a.attnum = ANY (k.conkey)) AS pkexpr
      FROM pg_class c JOIN pg_constraint k ON k.conrelid = c.oid AND k.contype = 'p'
     WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'r' AND sync_is_synced_table(c.relname)
  LOOP
    EXECUTE format(
      'INSERT INTO sync_changes (tbl, pk, "pkKey", op, row, ts, origin)
         SELECT %L, jsonb_build_object(%s), jsonb_build_object(%s)::text, ''U'', to_jsonb(t), ''epoch'', ''seed'' FROM %I t',
      r.relname, r.pkexpr, r.pkexpr, r.relname);
  END LOOP;
  UPDATE sync_state SET seeded = true WHERE id = 1;
END $$;


ALTER FUNCTION public.sync_seed() OWNER TO nodedr;

--
-- Name: verifactu_records_guard(); Type: FUNCTION; Schema: public; Owner: nodedr
--

CREATE FUNCTION public.verifactu_records_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE prev_hash TEXT;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'verifactu_records is append-only: delete is not allowed';
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF NEW."id" IS DISTINCT FROM OLD."id" OR NEW."restaurantId" IS DISTINCT FROM OLD."restaurantId"
       OR NEW."branchId" IS DISTINCT FROM OLD."branchId" OR NEW."issuerNif" IS DISTINCT FROM OLD."issuerNif"
       OR NEW."seq" IS DISTINCT FROM OLD."seq" OR NEW."type" IS DISTINCT FROM OLD."type"
       OR NEW."invoiceType" IS DISTINCT FROM OLD."invoiceType" OR NEW."invoiceNumber" IS DISTINCT FROM OLD."invoiceNumber"
       OR NEW."issueDate" IS DISTINCT FROM OLD."issueDate" OR NEW."taxTotalCents" IS DISTINCT FROM OLD."taxTotalCents"
       OR NEW."totalCents" IS DISTINCT FROM OLD."totalCents" OR NEW."generatedAt" IS DISTINCT FROM OLD."generatedAt"
       OR NEW."previousHash" IS DISTINCT FROM OLD."previousHash" OR NEW."hash" IS DISTINCT FROM OLD."hash"
       OR NEW."xml" IS DISTINCT FROM OLD."xml" OR NEW."qrUrl" IS DISTINCT FROM OLD."qrUrl"
       OR NEW."environment" IS DISTINCT FROM OLD."environment" OR NEW."orderId" IS DISTINCT FROM OLD."orderId"
       OR NEW."refundId" IS DISTINCT FROM OLD."refundId" OR NEW."createdAt" IS DISTINCT FROM OLD."createdAt" THEN
      RAISE EXCEPTION 'verifactu_records is append-only: only the submission outcome may change';
    END IF;
    RETURN NEW;
  END IF;
  -- INSERT: the record must continue the issuer's chain exactly.
  IF NEW."seq" = 1 THEN
    IF NEW."previousHash" IS NOT NULL THEN
      RAISE EXCEPTION 'verifactu_records: the first record of a chain has no previous hash';
    END IF;
  ELSE
    SELECT "hash" INTO prev_hash FROM "verifactu_records"
     WHERE "restaurantId" = NEW."restaurantId" AND "issuerNif" = NEW."issuerNif"
       AND "environment" = NEW."environment" AND "seq" = NEW."seq" - 1;
    IF prev_hash IS NULL OR prev_hash IS DISTINCT FROM NEW."previousHash" THEN
      RAISE EXCEPTION 'verifactu_records: record % does not continue the chain', NEW."seq";
    END IF;
  END IF;
  RETURN NEW;
END $$;


ALTER FUNCTION public.verifactu_records_guard() OWNER TO nodedr;

--
-- Name: verifactu_records_no_truncate(); Type: FUNCTION; Schema: public; Owner: nodedr
--

CREATE FUNCTION public.verifactu_records_no_truncate() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN RAISE EXCEPTION 'verifactu_records is append-only: truncate is not allowed'; END $$;


ALTER FUNCTION public.verifactu_records_no_truncate() OWNER TO nodedr;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: _prisma_migrations; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public._prisma_migrations (
    id character varying(36) NOT NULL,
    checksum character varying(64) NOT NULL,
    finished_at timestamp with time zone,
    migration_name character varying(255) NOT NULL,
    logs text,
    rolled_back_at timestamp with time zone,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    applied_steps_count integer DEFAULT 0 NOT NULL
);


ALTER TABLE public._prisma_migrations OWNER TO nodedr;

--
-- Name: attendance; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.attendance (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "userId" text NOT NULL,
    "clockInAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "clockOutAt" timestamp(3) without time zone,
    note text,
    "breakMinutes" integer DEFAULT 0 NOT NULL,
    "clockInKey" text,
    "clockOutKey" text
);


ALTER TABLE public.attendance OWNER TO nodedr;

--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.audit_logs (
    id text NOT NULL,
    "userId" text,
    action text NOT NULL,
    entity text NOT NULL,
    "entityId" text,
    metadata jsonb,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.audit_logs OWNER TO nodedr;

--
-- Name: backup_config; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.backup_config (
    id text DEFAULT 'singleton'::text NOT NULL,
    endpoint text NOT NULL,
    bucket text NOT NULL,
    "accessKeyId" text NOT NULL,
    "secretAccessKey" text NOT NULL,
    region text DEFAULT 'auto'::text NOT NULL,
    "intervalDays" integer DEFAULT 3 NOT NULL,
    "retainCount" integer DEFAULT 2 NOT NULL,
    "updatedById" text,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.backup_config OWNER TO nodedr;

--
-- Name: backups; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.backups (
    id text NOT NULL,
    status public."BackupStatus" DEFAULT 'PENDING'::public."BackupStatus" NOT NULL,
    "sizeBytes" integer,
    "s3KeyDb" text,
    "s3KeyUploads" text,
    sha256 text,
    "triggeredById" text,
    "failureReason" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "verifiedAt" timestamp(3) without time zone
);


ALTER TABLE public.backups OWNER TO nodedr;

--
-- Name: bank_transactions; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.bank_transactions (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "postedOn" date NOT NULL,
    description text NOT NULL,
    reference text DEFAULT ''::text NOT NULL,
    amount numeric(12,2) NOT NULL,
    status public."BankTxStatus" DEFAULT 'UNMATCHED'::public."BankTxStatus" NOT NULL,
    "expenseId" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.bank_transactions OWNER TO nodedr;

--
-- Name: branches; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.branches (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    name text NOT NULL,
    address text,
    phone text,
    "gstNumber" text,
    "isActive" boolean DEFAULT true NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL,
    country text DEFAULT 'IN'::text NOT NULL,
    "taxRegime" public."TaxRegime" DEFAULT 'INDIA_GST'::public."TaxRegime" NOT NULL,
    "taxMode" public."TaxMode" DEFAULT 'INCLUSIVE'::public."TaxMode" NOT NULL,
    "taxLabel" text,
    "taxId" text,
    "autoConfirmOrders" boolean DEFAULT false NOT NULL,
    "autoConfirmReservations" boolean DEFAULT false NOT NULL,
    "kioskToken" text,
    "kioskDineInEnabled" boolean DEFAULT true NOT NULL,
    "kioskTakeawayEnabled" boolean DEFAULT true NOT NULL,
    "printerCodepage" text DEFAULT 'CP858'::text NOT NULL,
    "printerColumns" integer,
    "printerPaperWidthMm" integer DEFAULT 80 NOT NULL,
    "printerConnection" text DEFAULT 'USB'::text NOT NULL,
    "printerHost" text,
    "printerPort" integer DEFAULT 9100 NOT NULL
);


ALTER TABLE public.branches OWNER TO nodedr;

--
-- Name: budgets; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.budgets (
    id text NOT NULL,
    "branchId" text NOT NULL,
    month text NOT NULL,
    category text NOT NULL,
    amount numeric(12,2) NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.budgets OWNER TO nodedr;

--
-- Name: buzzer_calls; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.buzzer_calls (
    id text NOT NULL,
    "buzzerId" text NOT NULL,
    "orderId" text,
    "tableId" text,
    state public."BuzzerCallState" DEFAULT 'PENDING'::public."BuzzerCallState" NOT NULL,
    error text,
    "createdById" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "sentAt" timestamp(3) without time zone,
    "ackedAt" timestamp(3) without time zone,
    "expiresAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.buzzer_calls OWNER TO nodedr;

--
-- Name: buzzers; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.buzzers (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text NOT NULL,
    number text,
    "tableId" text,
    driver public."BuzzerDriver" DEFAULT 'SIMULATED'::public."BuzzerDriver" NOT NULL,
    "webhookUrl" text,
    "webhookSecret" text,
    "deviceToken" text NOT NULL,
    "isActive" boolean DEFAULT true NOT NULL,
    "lastSeenAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.buzzers OWNER TO nodedr;

--
-- Name: campaigns; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.campaigns (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text NOT NULL,
    channel public."CampaignChannel" NOT NULL,
    segment public."CampaignSegment" DEFAULT 'ALL'::public."CampaignSegment" NOT NULL,
    message text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "lastSentAt" timestamp(3) without time zone,
    "lastSentCount" integer
);


ALTER TABLE public.campaigns OWNER TO nodedr;

--
-- Name: cash_closings; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.cash_closings (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "businessDate" date NOT NULL,
    "openingFloat" numeric(12,2) DEFAULT 0 NOT NULL,
    "cashSales" numeric(12,2) NOT NULL,
    "cashExpenses" numeric(12,2) DEFAULT 0 NOT NULL,
    "expectedCash" numeric(12,2) NOT NULL,
    "countedCash" numeric(12,2) NOT NULL,
    variance numeric(12,2) NOT NULL,
    note text,
    "closedById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.cash_closings OWNER TO nodedr;

--
-- Name: combo_components; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.combo_components (
    id text NOT NULL,
    "comboItemId" text NOT NULL,
    "componentItemId" text NOT NULL,
    quantity integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.combo_components OWNER TO nodedr;

--
-- Name: coupons; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.coupons (
    id text NOT NULL,
    "branchId" text NOT NULL,
    code text NOT NULL,
    kind public."DiscountKind" NOT NULL,
    value numeric(12,2) NOT NULL,
    "minOrderAmount" numeric(12,2) DEFAULT 0 NOT NULL,
    "maxDiscount" numeric(12,2),
    "validFrom" timestamp(3) without time zone,
    "validUntil" timestamp(3) without time zone,
    "usageLimit" integer,
    "usedCount" integer DEFAULT 0 NOT NULL,
    "isActive" boolean DEFAULT true NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.coupons OWNER TO nodedr;

--
-- Name: customer_addresses; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.customer_addresses (
    id text NOT NULL,
    "customerId" text NOT NULL,
    label text,
    line1 text NOT NULL,
    street text,
    landmark text,
    city text,
    state text,
    pincode text,
    instructions text,
    "isDefault" boolean DEFAULT false NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.customer_addresses OWNER TO nodedr;

--
-- Name: customers; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.customers (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text,
    phone text,
    email text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    address text,
    allergies text,
    anniversary timestamp(3) without time zone,
    birthday timestamp(3) without time zone,
    "loyaltyPoints" integer DEFAULT 0 NOT NULL,
    notes text,
    "walletBalance" numeric(12,2) DEFAULT 0 NOT NULL,
    "marketingOptOut" boolean DEFAULT false NOT NULL,
    "referralCode" text
);


ALTER TABLE public.customers OWNER TO nodedr;

--
-- Name: delivery_assignments; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.delivery_assignments (
    id text NOT NULL,
    "orderId" text NOT NULL,
    "branchId" text NOT NULL,
    "fromDriverId" text,
    "toDriverId" text,
    reason text,
    "assignedById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.delivery_assignments OWNER TO nodedr;

--
-- Name: delivery_zones; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.delivery_zones (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text NOT NULL,
    fee numeric(12,2) DEFAULT 0 NOT NULL,
    "minOrderAmount" numeric(12,2) DEFAULT 0 NOT NULL,
    "etaMinutes" integer DEFAULT 45 NOT NULL,
    pincodes text[],
    "isActive" boolean DEFAULT true NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.delivery_zones OWNER TO nodedr;

--
-- Name: departments; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.departments (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    name text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.departments OWNER TO nodedr;

--
-- Name: device_tokens; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.device_tokens (
    id text NOT NULL,
    "userId" text NOT NULL,
    token text NOT NULL,
    platform text NOT NULL,
    "appVersion" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "lastSeenAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.device_tokens OWNER TO nodedr;

--
-- Name: display_ads; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.display_ads (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "terminalId" text,
    kind public."AdKind" NOT NULL,
    url text NOT NULL,
    title text,
    "durationSec" integer,
    "sortOrder" integer DEFAULT 0 NOT NULL,
    "isActive" boolean DEFAULT true NOT NULL,
    "startsOn" timestamp(3) without time zone,
    "endsOn" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.display_ads OWNER TO nodedr;

--
-- Name: display_terminals; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.display_terminals (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text NOT NULL,
    token text NOT NULL,
    "idleSeconds" integer DEFAULT 45 NOT NULL,
    "thankYouSeconds" integer DEFAULT 8 NOT NULL,
    "adSlideSeconds" integer DEFAULT 10 NOT NULL,
    "adFit" text DEFAULT 'contain'::text NOT NULL,
    "isActive" boolean DEFAULT true NOT NULL,
    state jsonb,
    "stateAt" timestamp(3) without time zone,
    "lastSeenAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.display_terminals OWNER TO nodedr;

--
-- Name: document_files; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.document_files (
    id text NOT NULL,
    "documentId" text NOT NULL,
    "fileName" text NOT NULL,
    "mimeType" text NOT NULL,
    size integer NOT NULL,
    data bytea NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.document_files OWNER TO nodedr;

--
-- Name: documents; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.documents (
    id text NOT NULL,
    "branchId" text NOT NULL,
    title text NOT NULL,
    category public."DocumentCategory" DEFAULT 'SOP'::public."DocumentCategory" NOT NULL,
    body text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.documents OWNER TO nodedr;

--
-- Name: download_stats; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.download_stats (
    channel text NOT NULL,
    count integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.download_stats OWNER TO nodedr;

--
-- Name: equipment; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.equipment (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text NOT NULL,
    location text,
    "serviceIntervalDays" integer,
    "lastServicedAt" date,
    "nextDueAt" date,
    notes text,
    "isActive" boolean DEFAULT true NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.equipment OWNER TO nodedr;

--
-- Name: expenses; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.expenses (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "spentOn" date NOT NULL,
    category text NOT NULL,
    amount numeric(12,2) NOT NULL,
    note text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "paidFromCash" boolean DEFAULT false NOT NULL,
    "clientRequestId" text
);


ALTER TABLE public.expenses OWNER TO nodedr;

--
-- Name: floor_layouts; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.floor_layouts (
    id text NOT NULL,
    "floorId" text NOT NULL,
    name text NOT NULL,
    "isActive" boolean DEFAULT false NOT NULL,
    "sortOrder" integer DEFAULT 0 NOT NULL,
    tables jsonb DEFAULT '[]'::jsonb NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.floor_layouts OWNER TO nodedr;

--
-- Name: floors; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.floors (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text NOT NULL,
    "sortOrder" integer DEFAULT 0 NOT NULL,
    "isActive" boolean DEFAULT true NOT NULL
);


ALTER TABLE public.floors OWNER TO nodedr;

--
-- Name: gateway_payments; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.gateway_payments (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    "branchId" text NOT NULL,
    "orderId" text NOT NULL,
    provider text NOT NULL,
    mode public."GatewayMode" NOT NULL,
    "amountMinor" integer NOT NULL,
    currency text NOT NULL,
    status public."GatewayPaymentStatus" DEFAULT 'CREATED'::public."GatewayPaymentStatus" NOT NULL,
    "providerRef" text,
    "providerPaymentId" text,
    "checkoutUrl" text,
    note text,
    "createdById" text NOT NULL,
    "appliedAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.gateway_payments OWNER TO nodedr;

--
-- Name: gateway_refunds; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.gateway_refunds (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    "gatewayPaymentId" text NOT NULL,
    "orderId" text NOT NULL,
    provider text NOT NULL,
    "amountMinor" integer NOT NULL,
    currency text NOT NULL,
    status public."GatewayRefundStatus" DEFAULT 'PENDING'::public."GatewayRefundStatus" NOT NULL,
    "providerRefundId" text,
    "refundId" text,
    reason text,
    note text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.gateway_refunds OWNER TO nodedr;

--
-- Name: gateway_webhook_events; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.gateway_webhook_events (
    id text NOT NULL,
    provider text NOT NULL,
    mode public."GatewayMode" NOT NULL,
    "eventId" text NOT NULL,
    "receivedAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.gateway_webhook_events OWNER TO nodedr;

--
-- Name: gift_card_redemptions; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.gift_card_redemptions (
    id text NOT NULL,
    "giftCardId" text NOT NULL,
    "orderId" text NOT NULL,
    amount numeric(12,2) NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.gift_card_redemptions OWNER TO nodedr;

--
-- Name: gift_cards; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.gift_cards (
    id text NOT NULL,
    "branchId" text NOT NULL,
    code text NOT NULL,
    "initialValue" numeric(12,2) NOT NULL,
    balance numeric(12,2) NOT NULL,
    "customerId" text,
    "isActive" boolean DEFAULT true NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.gift_cards OWNER TO nodedr;

--
-- Name: goods_receipt_items; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.goods_receipt_items (
    id text NOT NULL,
    "goodsReceiptId" text NOT NULL,
    "ingredientId" text NOT NULL,
    "purchaseOrderItemId" text,
    quantity numeric(12,3) NOT NULL,
    "unitCost" numeric(12,4) NOT NULL,
    "batchNumber" text NOT NULL,
    "expiryDate" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.goods_receipt_items OWNER TO nodedr;

--
-- Name: goods_receipts; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.goods_receipts (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "purchaseOrderId" text,
    "supplierId" text NOT NULL,
    "grnNumber" text NOT NULL,
    notes text,
    "receivedById" text NOT NULL,
    "receivedAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.goods_receipts OWNER TO nodedr;

--
-- Name: ingredients; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.ingredients (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text NOT NULL,
    sku text,
    unit public."IngredientUnit" NOT NULL,
    "reorderLevel" numeric(12,3) DEFAULT 0 NOT NULL,
    "currentStock" numeric(12,3) DEFAULT 0 NOT NULL,
    "costPerUnit" numeric(12,4) DEFAULT 0 NOT NULL,
    "isActive" boolean DEFAULT true NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL,
    conversions jsonb DEFAULT '[]'::jsonb NOT NULL,
    "costMethod" public."IngredientCostMethod" DEFAULT 'AVERAGE'::public."IngredientCostMethod" NOT NULL,
    kind public."IngredientKind" DEFAULT 'PURCHASED'::public."IngredientKind" NOT NULL,
    "purchasePrice" numeric(12,2),
    "purchaseQuantity" numeric(12,3),
    "purchaseUnit" public."IngredientUnit",
    version integer DEFAULT 1 NOT NULL,
    "yieldPercent" numeric(5,2) DEFAULT 100 NOT NULL,
    category text,
    "storageLocation" text,
    "wasteApprovalQty" numeric(12,3),
    "parLevel" numeric(12,3)
);


ALTER TABLE public.ingredients OWNER TO nodedr;

--
-- Name: integration_api_keys; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.integration_api_keys (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    "branchId" text,
    name text NOT NULL,
    "tokenHash" text NOT NULL,
    "lastFour" text NOT NULL,
    scopes text[],
    "createdById" text NOT NULL,
    "lastUsedAt" timestamp(3) without time zone,
    "revokedAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "expiresAt" timestamp(3) without time zone
);


ALTER TABLE public.integration_api_keys OWNER TO nodedr;

--
-- Name: integration_connections; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.integration_connections (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    provider text NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    status public."IntegrationStatus" DEFAULT 'PENDING_CONFIGURATION'::public."IntegrationStatus" NOT NULL,
    "externalAccountId" text,
    "credentialsEnc" text,
    config jsonb,
    "lastSyncAt" timestamp(3) without time zone,
    "lastSuccessAt" timestamp(3) without time zone,
    "lastError" text,
    "createdById" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.integration_connections OWNER TO nodedr;

--
-- Name: integration_logs; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.integration_logs (
    id text NOT NULL,
    "connectionId" text NOT NULL,
    level text NOT NULL,
    event text NOT NULL,
    message text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.integration_logs OWNER TO nodedr;

--
-- Name: kitchen_stations; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.kitchen_stations (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text NOT NULL,
    "printerName" text
);


ALTER TABLE public.kitchen_stations OWNER TO nodedr;

--
-- Name: kot_items; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.kot_items (
    id text NOT NULL,
    "kotId" text NOT NULL,
    "orderItemId" text NOT NULL,
    status public."KotItemStatus" DEFAULT 'NEW'::public."KotItemStatus" NOT NULL
);


ALTER TABLE public.kot_items OWNER TO nodedr;

--
-- Name: kots; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.kots (
    id text NOT NULL,
    "orderId" text NOT NULL,
    "stationId" text,
    "ticketNumber" text NOT NULL,
    status public."KotStatus" DEFAULT 'NEW'::public."KotStatus" NOT NULL,
    "isPriority" boolean DEFAULT false NOT NULL,
    "printedCount" integer DEFAULT 0 NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "acceptedAt" timestamp(3) without time zone,
    "readyAt" timestamp(3) without time zone,
    "servedAt" timestamp(3) without time zone,
    "printedAt" timestamp(3) without time zone,
    "lastPrintError" text,
    "acceptedById" text,
    "rejectedAt" timestamp(3) without time zone,
    "rejectedById" text,
    "rejectReason" text
);


ALTER TABLE public.kots OWNER TO nodedr;

--
-- Name: leave_requests; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.leave_requests (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "userId" text NOT NULL,
    type public."LeaveType" DEFAULT 'ANNUAL'::public."LeaveType" NOT NULL,
    "startDate" date NOT NULL,
    "endDate" date NOT NULL,
    reason text,
    status public."LeaveStatus" DEFAULT 'PENDING'::public."LeaveStatus" NOT NULL,
    "decidedById" text,
    "decidedAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.leave_requests OWNER TO nodedr;

--
-- Name: licenses; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.licenses (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    status public."LicenseStatus" DEFAULT 'ACTIVE'::public."LicenseStatus" NOT NULL,
    "validFrom" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "validUntil" timestamp(3) without time zone NOT NULL,
    "gracePeriodDays" integer DEFAULT 3 NOT NULL,
    "maxBranches" integer DEFAULT 1 NOT NULL,
    "maxUsers" integer DEFAULT 10 NOT NULL,
    "enabledModules" public."ModuleKey"[] DEFAULT ARRAY['POS'::public."ModuleKey", 'ORDERS'::public."ModuleKey", 'TABLES'::public."ModuleKey", 'MENU'::public."ModuleKey", 'CUSTOMERS'::public."ModuleKey", 'SETTINGS'::public."ModuleKey"],
    notes text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.licenses OWNER TO nodedr;

--
-- Name: location_transfers; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.location_transfers (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "ingredientId" text NOT NULL,
    "fromLocationId" text,
    "toLocationId" text NOT NULL,
    quantity numeric(12,3) NOT NULL,
    note text,
    "idempotencyKey" text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.location_transfers OWNER TO nodedr;

--
-- Name: menu_categories; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.menu_categories (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text NOT NULL,
    "sortOrder" integer DEFAULT 0 NOT NULL,
    "isActive" boolean DEFAULT true NOT NULL,
    "showOnWebsite" boolean DEFAULT true NOT NULL
);


ALTER TABLE public.menu_categories OWNER TO nodedr;

--
-- Name: menu_item_costings; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.menu_item_costings (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "menuItemId" text NOT NULL,
    "batchOutputQty" numeric(12,3) DEFAULT 1 NOT NULL,
    overheads jsonb DEFAULT '[]'::jsonb NOT NULL,
    "halfPortionRatio" numeric(5,3) DEFAULT 0.5 NOT NULL,
    "targetMarginPercent" numeric(5,2),
    "targetMarkupPercent" numeric(7,2),
    "alertDropPoints" numeric(5,2) DEFAULT 5 NOT NULL,
    "baselineCost" numeric(12,4),
    "baselineAt" timestamp(3) without time zone,
    version integer DEFAULT 1 NOT NULL,
    "updatedById" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.menu_item_costings OWNER TO nodedr;

--
-- Name: menu_item_modifier_groups; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.menu_item_modifier_groups (
    "menuItemId" text NOT NULL,
    "modifierGroupId" text NOT NULL,
    "sortOrder" integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.menu_item_modifier_groups OWNER TO nodedr;

--
-- Name: menu_items; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.menu_items (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "categoryId" text NOT NULL,
    "stationId" text,
    name text NOT NULL,
    sku text,
    description text,
    "imageUrl" text,
    price numeric(12,2) NOT NULL,
    "taxRatePercent" numeric(5,2) DEFAULT 0 NOT NULL,
    "costPrice" numeric(12,2),
    "prepTimeMinutes" integer,
    calories integer,
    "isVeg" boolean DEFAULT true NOT NULL,
    "isVegan" boolean DEFAULT false NOT NULL,
    "isJain" boolean DEFAULT false NOT NULL,
    "isHalal" boolean DEFAULT false NOT NULL,
    "isGlutenFree" boolean DEFAULT false NOT NULL,
    "spiceLevel" public."SpiceLevel" DEFAULT 'NONE'::public."SpiceLevel" NOT NULL,
    allergens text[] DEFAULT ARRAY[]::text[],
    "availableFrom" text,
    "availableTo" text,
    "isSeasonal" boolean DEFAULT false NOT NULL,
    "seasonStart" timestamp(3) without time zone,
    "seasonEnd" timestamp(3) without time zone,
    barcode text,
    "isActive" boolean DEFAULT true NOT NULL,
    "isCombo" boolean DEFAULT false NOT NULL,
    "sortOrder" integer DEFAULT 0 NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL,
    "inventoryTracking" public."InventoryTracking" DEFAULT 'NONE'::public."InventoryTracking" NOT NULL,
    "stockIngredientId" text,
    "stockQuantityPerSale" numeric(12,3) DEFAULT 1 NOT NULL,
    "halfPrice" numeric(12,2)
);


ALTER TABLE public.menu_items OWNER TO nodedr;

--
-- Name: menu_price_changes; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.menu_price_changes (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "menuItemId" text NOT NULL,
    "oldPrice" numeric(12,2) NOT NULL,
    "newPrice" numeric(12,2) NOT NULL,
    "changedById" text NOT NULL,
    "changedAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    source text DEFAULT 'STOCK_JOURNAL'::text NOT NULL,
    "productionEntryId" text,
    "unitCostAtChange" numeric(14,4)
);


ALTER TABLE public.menu_price_changes OWNER TO nodedr;

--
-- Name: modifier_groups; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.modifier_groups (
    id text NOT NULL,
    name text NOT NULL,
    "minSelect" integer DEFAULT 0 NOT NULL,
    "maxSelect" integer DEFAULT 1 NOT NULL,
    "isRequired" boolean DEFAULT false NOT NULL,
    "branchId" text NOT NULL
);


ALTER TABLE public.modifier_groups OWNER TO nodedr;

--
-- Name: modifier_ingredients; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.modifier_ingredients (
    id text NOT NULL,
    "modifierId" text NOT NULL,
    "ingredientId" text NOT NULL,
    quantity numeric(12,3) NOT NULL,
    unit public."IngredientUnit"
);


ALTER TABLE public.modifier_ingredients OWNER TO nodedr;

--
-- Name: modifiers; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.modifiers (
    id text NOT NULL,
    "groupId" text NOT NULL,
    name text NOT NULL,
    "priceAdjustment" numeric(12,2) DEFAULT 0 NOT NULL,
    "taxRatePercent" numeric(5,2),
    "kitchenNote" text,
    "isDefault" boolean DEFAULT false NOT NULL,
    "sortOrder" integer DEFAULT 0 NOT NULL,
    "isActive" boolean DEFAULT true NOT NULL
);


ALTER TABLE public.modifiers OWNER TO nodedr;

--
-- Name: nfc_tags; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.nfc_tags (
    id text NOT NULL,
    "publicRef" text NOT NULL,
    "branchId" text NOT NULL,
    "tableId" text NOT NULL,
    label text,
    mode public."NfcTagMode" DEFAULT 'SECURE'::public."NfcTagMode" NOT NULL,
    status public."NfcTagStatus" DEFAULT 'PROVISIONING'::public."NfcTagStatus" NOT NULL,
    uid text,
    "keyVersion" integer DEFAULT 1 NOT NULL,
    "metaKeySealed" text,
    "fileKeySealed" text,
    "lastCounter" integer DEFAULT '-1'::integer NOT NULL,
    "lastAuthAt" timestamp(3) without time zone,
    "disabledAt" timestamp(3) without time zone,
    "disabledReason" text,
    "replacesId" text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.nfc_tags OWNER TO nodedr;

--
-- Name: nfc_taps; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.nfc_taps (
    id text NOT NULL,
    "tagId" text NOT NULL,
    "branchId" text NOT NULL,
    counter integer,
    result text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.nfc_taps OWNER TO nodedr;

--
-- Name: notifications; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.notifications (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "recipientUserId" text,
    type text NOT NULL,
    title text NOT NULL,
    body text NOT NULL,
    entity text,
    "entityId" text,
    "readAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.notifications OWNER TO nodedr;

--
-- Name: order_item_costs; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.order_item_costs (
    "orderItemId" text NOT NULL,
    "unitCost" numeric(12,4) NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.order_item_costs OWNER TO nodedr;

--
-- Name: order_item_modifiers; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.order_item_modifiers (
    id text NOT NULL,
    "orderItemId" text NOT NULL,
    "modifierId" text NOT NULL,
    "nameSnapshot" text NOT NULL,
    "priceAdjSnapshot" numeric(12,2) NOT NULL
);


ALTER TABLE public.order_item_modifiers OWNER TO nodedr;

--
-- Name: order_item_stock_returns; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.order_item_stock_returns (
    id text NOT NULL,
    "orderItemId" text NOT NULL,
    "refundId" text NOT NULL,
    quantity integer NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.order_item_stock_returns OWNER TO nodedr;

--
-- Name: order_items; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.order_items (
    id text NOT NULL,
    "orderId" text NOT NULL,
    "menuItemId" text NOT NULL,
    "nameSnapshot" text NOT NULL,
    "unitPriceSnapshot" numeric(12,2) NOT NULL,
    "taxRateSnapshot" numeric(5,2) NOT NULL,
    quantity integer DEFAULT 1 NOT NULL,
    "lineTotal" numeric(12,2) NOT NULL,
    "kitchenNote" text,
    status public."KotItemStatus" DEFAULT 'NEW'::public."KotItemStatus" NOT NULL,
    portion text,
    "portionRatio" numeric(5,3) DEFAULT 1 NOT NULL
);


ALTER TABLE public.order_items OWNER TO nodedr;

--
-- Name: order_ratings; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.order_ratings (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "orderId" text NOT NULL,
    stars integer NOT NULL,
    comment text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.order_ratings OWNER TO nodedr;

--
-- Name: orders; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.orders (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "orderNumber" text NOT NULL,
    type public."OrderType" DEFAULT 'DINE_IN'::public."OrderType" NOT NULL,
    status public."OrderStatus" DEFAULT 'OPEN'::public."OrderStatus" NOT NULL,
    "tableId" text,
    "guestCount" integer,
    "customerId" text,
    "createdById" text NOT NULL,
    subtotal numeric(12,2) DEFAULT 0 NOT NULL,
    "discountAmount" numeric(12,2) DEFAULT 0 NOT NULL,
    "taxAmount" numeric(12,2) DEFAULT 0 NOT NULL,
    "totalAmount" numeric(12,2) DEFAULT 0 NOT NULL,
    notes text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL,
    "billedAt" timestamp(3) without time zone,
    "loyaltyDiscountAmount" numeric(12,2) DEFAULT 0 NOT NULL,
    "loyaltyPointsRedeemed" integer DEFAULT 0 NOT NULL,
    "tipAmount" numeric(12,2) DEFAULT 0 NOT NULL,
    "guestName" text,
    channel public."OrderChannel" DEFAULT 'STAFF'::public."OrderChannel" NOT NULL,
    acceptance public."AcceptanceStatus" DEFAULT 'NOT_REQUIRED'::public."AcceptanceStatus" NOT NULL,
    "deliveryZoneId" text,
    "deliveryFee" numeric(12,2) DEFAULT 0 NOT NULL,
    "deliveryAddress" text,
    "deliveryPincode" text,
    "deliveryPhone" text,
    "deliveryStatus" public."DeliveryStatus",
    "driverId" text,
    "deliveryEtaAt" timestamp(3) without time zone,
    "deliveredAt" timestamp(3) without time zone,
    "scheduledFor" timestamp(3) without time zone,
    "couponCode" text,
    "promotionName" text,
    "clientRequestId" text,
    "cancelReason" text,
    "cancelledAt" timestamp(3) without time zone,
    "cancelledById" text,
    "cancelSource" public."CancelSource",
    "acceptedAt" timestamp(3) without time zone,
    "acceptedById" text,
    "discountType" public."ManualDiscountType",
    "discountValue" numeric(12,2),
    "integrationKeyId" text,
    "clientRequestHash" text,
    "discountReason" text,
    "externalSource" text,
    "externalOrderId" text,
    "externalCustomerRef" text,
    "requestedRedeemPoints" integer DEFAULT 0 NOT NULL,
    "assignedAt" timestamp(3) without time zone,
    "deliveryFailedReason" text,
    "pickedUpAt" timestamp(3) without time zone,
    "deliveryLat" double precision,
    "deliveryLng" double precision,
    "deliveryPlace" text,
    "heldForPayment" boolean DEFAULT false NOT NULL,
    "payIntent" public."PayIntent"
);


ALTER TABLE public.orders OWNER TO nodedr;

--
-- Name: payment_gateway_catalog; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.payment_gateway_catalog (
    id text NOT NULL,
    "restaurantId" text,
    key text NOT NULL,
    name text NOT NULL,
    countries text[],
    integration text NOT NULL,
    "docsUrl" text NOT NULL,
    adapter text,
    notes text,
    sources text[],
    "researchedAt" text,
    active boolean DEFAULT true NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.payment_gateway_catalog OWNER TO nodedr;

--
-- Name: payment_gateway_connections; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.payment_gateway_connections (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    provider text NOT NULL,
    country text NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    mode public."GatewayMode" DEFAULT 'TEST'::public."GatewayMode" NOT NULL,
    "liveConfirmedAt" timestamp(3) without time zone,
    "liveConfirmedById" text,
    "testCredentialsEnc" text,
    "liveCredentialsEnc" text,
    "testKeys" text[],
    "liveKeys" text[],
    "lastError" text,
    "lastTestedAt" timestamp(3) without time zone,
    "lastTestOk" boolean,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.payment_gateway_connections OWNER TO nodedr;

--
-- Name: payments; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.payments (
    id text NOT NULL,
    "orderId" text NOT NULL,
    method public."PaymentMethod" NOT NULL,
    amount numeric(12,2) NOT NULL,
    reference text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    tendered numeric(12,2),
    "changeGiven" numeric(12,2),
    "createdById" text,
    "clientRequestId" text
);


ALTER TABLE public.payments OWNER TO nodedr;

--
-- Name: payroll_lines; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.payroll_lines (
    id text NOT NULL,
    "runId" text NOT NULL,
    "userId" text NOT NULL,
    "hoursWorked" numeric(8,2) NOT NULL,
    "basePay" numeric(12,2) NOT NULL,
    "tipShare" numeric(12,2) DEFAULT 0 NOT NULL,
    "unpaidLeaveDeduction" numeric(12,2) DEFAULT 0 NOT NULL,
    "netPay" numeric(12,2) NOT NULL,
    allowances numeric(12,2) DEFAULT 0 NOT NULL,
    bonus numeric(12,2) DEFAULT 0 NOT NULL,
    "advanceRecovery" numeric(12,2) DEFAULT 0 NOT NULL,
    "otherDeductions" numeric(12,2) DEFAULT 0 NOT NULL,
    "adjustmentNote" text,
    "calcInputs" jsonb,
    "overtimeHours" numeric(8,2) DEFAULT 0 NOT NULL,
    "overtimePay" numeric(12,2) DEFAULT 0 NOT NULL,
    "absenceDeduction" numeric(12,2) DEFAULT 0 NOT NULL,
    "absentDays" integer DEFAULT 0 NOT NULL,
    "lateDeduction" numeric(12,2) DEFAULT 0 NOT NULL,
    "lateMinutes" integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.payroll_lines OWNER TO nodedr;

--
-- Name: payroll_runs; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.payroll_runs (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "periodStart" date NOT NULL,
    "periodEnd" date NOT NULL,
    status public."PayrollStatus" DEFAULT 'DRAFT'::public."PayrollStatus" NOT NULL,
    "tipPool" numeric(12,2) DEFAULT 0 NOT NULL,
    "totalNet" numeric(12,2) DEFAULT 0 NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "finalizedAt" timestamp(3) without time zone,
    "paidAt" timestamp(3) without time zone,
    "paidById" text,
    "paymentMethod" text,
    "paymentRef" text
);


ALTER TABLE public.payroll_runs OWNER TO nodedr;

--
-- Name: permissions; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.permissions (
    id text NOT NULL,
    key text NOT NULL,
    label text NOT NULL,
    category text NOT NULL
);


ALTER TABLE public.permissions OWNER TO nodedr;

--
-- Name: phone_till_closings; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.phone_till_closings (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "deviceId" text NOT NULL,
    "deviceName" text NOT NULL,
    "businessDate" date NOT NULL,
    "openingFloat" numeric(12,2) DEFAULT 0 NOT NULL,
    "cashSales" numeric(12,2) NOT NULL,
    "cashRefunds" numeric(12,2) DEFAULT 0 NOT NULL,
    "cashExpenses" numeric(12,2) DEFAULT 0 NOT NULL,
    "expectedCash" numeric(12,2) NOT NULL,
    "countedCash" numeric(12,2) NOT NULL,
    variance numeric(12,2) NOT NULL,
    "netSales" numeric(12,2) DEFAULT 0 NOT NULL,
    "closedByName" text,
    "closedAt" timestamp(3) without time zone NOT NULL,
    "syncedById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.phone_till_closings OWNER TO nodedr;

--
-- Name: points_ledger; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.points_ledger (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "customerId" text NOT NULL,
    delta integer NOT NULL,
    reason text NOT NULL,
    "referralId" text,
    "orderId" text,
    "idempotencyKey" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.points_ledger OWNER TO nodedr;

--
-- Name: pos_devices; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.pos_devices (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    "userId" text NOT NULL,
    "deviceId" text NOT NULL,
    name text NOT NULL,
    platform text,
    "appVersion" text,
    "enrolledAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "lastSeenAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "lastSyncAt" timestamp(3) without time zone,
    "pendingCount" integer DEFAULT 0 NOT NULL,
    "failedCount" integer DEFAULT 0 NOT NULL,
    "lastError" text,
    "revokedAt" timestamp(3) without time zone,
    "revokedById" text
);


ALTER TABLE public.pos_devices OWNER TO nodedr;

--
-- Name: preparation_lines; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.preparation_lines (
    id text NOT NULL,
    "preparationId" text NOT NULL,
    "ingredientId" text NOT NULL,
    quantity numeric(12,3) NOT NULL,
    unit public."IngredientUnit"
);


ALTER TABLE public.preparation_lines OWNER TO nodedr;

--
-- Name: preparations; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.preparations (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "outputIngredientId" text NOT NULL,
    "batchOutputQty" numeric(12,3) NOT NULL,
    overheads jsonb DEFAULT '[]'::jsonb NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.preparations OWNER TO nodedr;

--
-- Name: product_recipe_lines; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.product_recipe_lines (
    id text NOT NULL,
    "recipeId" text NOT NULL,
    "ingredientId" text NOT NULL,
    quantity numeric(12,3) NOT NULL,
    unit public."IngredientUnit" NOT NULL
);


ALTER TABLE public.product_recipe_lines OWNER TO nodedr;

--
-- Name: product_recipes; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.product_recipes (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "outputIngredientId" text NOT NULL,
    name text NOT NULL,
    "baseOutputQty" numeric(12,3) NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    "isActive" boolean DEFAULT true NOT NULL,
    notes text,
    "createdById" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.product_recipes OWNER TO nodedr;

--
-- Name: production_costs; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.production_costs (
    id text NOT NULL,
    "entryId" text NOT NULL,
    category text NOT NULL,
    description text,
    amount numeric(14,2) NOT NULL,
    included boolean DEFAULT true NOT NULL
);


ALTER TABLE public.production_costs OWNER TO nodedr;

--
-- Name: production_entries; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.production_entries (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "entryNo" text NOT NULL,
    status public."ProductionStatus" DEFAULT 'DRAFT'::public."ProductionStatus" NOT NULL,
    "producedAt" timestamp(3) without time zone NOT NULL,
    shift text,
    location text,
    "batchRef" text,
    notes text,
    "responsibleId" text,
    "idempotencyKey" text,
    "deviceId" text,
    "correctsEntryId" text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "postedById" text,
    "postedAt" timestamp(3) without time zone,
    "voidedById" text,
    "voidedAt" timestamp(3) without time zone,
    "voidReason" text,
    "additionalCost" numeric(14,4),
    costed boolean DEFAULT false NOT NULL,
    "expectedPrice" numeric(12,2),
    "expiryDate" timestamp(3) without time zone,
    "ingredientCost" numeric(14,4),
    "manufacturedOn" timestamp(3) without time zone,
    "priceChangeId" text,
    "priceMenuItemId" text,
    "proposedPrice" numeric(12,2),
    "totalCost" numeric(14,4),
    "unitCost" numeric(14,4),
    "menuItemId" text,
    "sellingPriceAtPost" numeric(12,2),
    "qualityResult" text,
    "qualityGrade" text,
    "qualityNotes" text,
    "qualityById" text,
    "qualityAt" timestamp(3) without time zone,
    "allocationMethod" text,
    "recipeId" text,
    "recipeKind" text,
    "recipeName" text,
    "recipeSnapshot" jsonb,
    "sourcePoId" text,
    "sourcePoNumber" text,
    "sourceSupplier" text
);


ALTER TABLE public.production_entries OWNER TO nodedr;

--
-- Name: production_lines; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.production_lines (
    id text NOT NULL,
    "entryId" text NOT NULL,
    role public."ProductionLineRole" NOT NULL,
    "ingredientId" text NOT NULL,
    "enteredQuantity" numeric(12,3) NOT NULL,
    "enteredUnit" public."IngredientUnit" NOT NULL,
    quantity numeric(12,3) NOT NULL,
    "lineCost" numeric(16,4),
    "unitRate" numeric(14,4),
    "allocatedCost" numeric(16,4),
    "allocationPercent" numeric(7,3),
    "directToIngredientId" text,
    "expectedQuantity" numeric(12,3),
    "goodUnitCost" numeric(14,4),
    "locationId" text,
    "locationName" text,
    "lotNumber" text,
    "rejectedQuantity" numeric(12,3) DEFAULT 0 NOT NULL
);


ALTER TABLE public.production_lines OWNER TO nodedr;

--
-- Name: production_runs; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.production_runs (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "preparationId" text NOT NULL,
    "idempotencyKey" text NOT NULL,
    batches numeric(12,3) NOT NULL,
    "outputQty" numeric(12,3) NOT NULL,
    "ingredientCost" numeric(12,4) NOT NULL,
    "overheadCost" numeric(12,4) NOT NULL,
    "totalCost" numeric(12,4) NOT NULL,
    "unitCost" numeric(12,4) NOT NULL,
    note text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.production_runs OWNER TO nodedr;

--
-- Name: promotions; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.promotions (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text NOT NULL,
    kind public."DiscountKind" NOT NULL,
    value numeric(12,2) NOT NULL,
    "daysOfWeek" integer[],
    "startMinute" integer NOT NULL,
    "endMinute" integer NOT NULL,
    "isActive" boolean DEFAULT true NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.promotions OWNER TO nodedr;

--
-- Name: public_order_keys; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.public_order_keys (
    id text NOT NULL,
    "branchId" text NOT NULL,
    key text NOT NULL,
    "orderId" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.public_order_keys OWNER TO nodedr;

--
-- Name: purchase_order_items; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.purchase_order_items (
    id text NOT NULL,
    "purchaseOrderId" text NOT NULL,
    "ingredientId" text NOT NULL,
    "quantityOrdered" numeric(12,3) NOT NULL,
    "unitCost" numeric(12,4) NOT NULL,
    "quantityReceived" numeric(12,3) DEFAULT 0 NOT NULL
);


ALTER TABLE public.purchase_order_items OWNER TO nodedr;

--
-- Name: purchase_orders; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.purchase_orders (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "supplierId" text NOT NULL,
    "poNumber" text NOT NULL,
    status public."PurchaseOrderStatus" DEFAULT 'DRAFT'::public."PurchaseOrderStatus" NOT NULL,
    "expectedDate" timestamp(3) without time zone,
    notes text,
    "totalAmount" numeric(12,2) DEFAULT 0 NOT NULL,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.purchase_orders OWNER TO nodedr;

--
-- Name: purchase_request_items; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.purchase_request_items (
    id text NOT NULL,
    "purchaseRequestId" text NOT NULL,
    "ingredientId" text NOT NULL,
    "quantityRequested" numeric(12,3) NOT NULL,
    notes text
);


ALTER TABLE public.purchase_request_items OWNER TO nodedr;

--
-- Name: purchase_requests; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.purchase_requests (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "requestNumber" text NOT NULL,
    status public."PurchaseRequestStatus" DEFAULT 'DRAFT'::public."PurchaseRequestStatus" NOT NULL,
    notes text,
    "requestedById" text NOT NULL,
    "approvedById" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.purchase_requests OWNER TO nodedr;

--
-- Name: recipe_ingredients; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.recipe_ingredients (
    id text NOT NULL,
    "menuItemId" text NOT NULL,
    "ingredientId" text NOT NULL,
    quantity numeric(12,3) NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL,
    unit public."IngredientUnit"
);


ALTER TABLE public.recipe_ingredients OWNER TO nodedr;

--
-- Name: referrals; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.referrals (
    id text NOT NULL,
    "branchId" text NOT NULL,
    code text NOT NULL,
    "referrerId" text NOT NULL,
    "referredId" text NOT NULL,
    "sharedItemId" text,
    status public."ReferralStatus" DEFAULT 'PENDING'::public."ReferralStatus" NOT NULL,
    "referrerPoints" integer,
    "referredPoints" integer,
    "qualifyingOrderId" text,
    "rewardedAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.referrals OWNER TO nodedr;

--
-- Name: refunds; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.refunds (
    id text NOT NULL,
    "orderId" text NOT NULL,
    amount numeric(12,2) NOT NULL,
    reason text,
    method public."PaymentMethod" NOT NULL,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "clientRequestId" text
);


ALTER TABLE public.refunds OWNER TO nodedr;

--
-- Name: report_schedules; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.report_schedules (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "reportKey" text NOT NULL,
    frequency public."ReportFrequency" NOT NULL,
    format text DEFAULT 'xlsx'::text NOT NULL,
    recipients text[],
    "isActive" boolean DEFAULT true NOT NULL,
    "lastSentAt" timestamp(3) without time zone,
    "lastError" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.report_schedules OWNER TO nodedr;

--
-- Name: reservations; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.reservations (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "customerName" text NOT NULL,
    phone text,
    email text,
    "guestCount" integer NOT NULL,
    "reservedAt" timestamp(3) without time zone NOT NULL,
    "durationMinutes" integer DEFAULT 90 NOT NULL,
    "tableId" text,
    "specialRequests" text,
    deposit numeric(12,2),
    status public."ReservationStatus" DEFAULT 'RESERVED'::public."ReservationStatus" NOT NULL,
    "reminderSentAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL,
    channel public."OrderChannel" DEFAULT 'STAFF'::public."OrderChannel" NOT NULL
);


ALTER TABLE public.reservations OWNER TO nodedr;

--
-- Name: restaurants; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.restaurants (
    id text NOT NULL,
    name text NOT NULL,
    "legalName" text,
    currency text DEFAULT 'INR'::text NOT NULL,
    timezone text DEFAULT 'Asia/Kolkata'::text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL,
    "loyaltyEarnPerCurrency" integer DEFAULT 100 NOT NULL,
    "loyaltyPointValue" numeric(6,2) DEFAULT 1 NOT NULL,
    "logoUrl" text,
    "upiVpa" text,
    "upiPayeeName" text,
    "maxManualDiscountPercent" numeric(5,2) DEFAULT 100 NOT NULL,
    "requireDiscountReason" boolean DEFAULT false NOT NULL,
    "referralEnabled" boolean DEFAULT false NOT NULL,
    "referralReferredPoints" integer DEFAULT 10 NOT NULL,
    "referralSharerPoints" integer DEFAULT 15 NOT NULL,
    "onlineMinOrderAmount" numeric(10,2) DEFAULT 0 NOT NULL,
    "referralMinPurchase" numeric(10,2) DEFAULT 200 NOT NULL,
    "onlinePriceAdjustKind" text DEFAULT 'PERCENT'::text NOT NULL,
    "onlinePriceAdjustValue" numeric(10,2) DEFAULT 0 NOT NULL,
    "manufacturingEnabled" boolean DEFAULT false NOT NULL,
    "requireTableSession" boolean DEFAULT true NOT NULL,
    "autoTableSessions" boolean DEFAULT false NOT NULL,
    "nfcTablesEnabled" boolean DEFAULT false NOT NULL
);


ALTER TABLE public.restaurants OWNER TO nodedr;

--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.role_permissions (
    "roleId" text NOT NULL,
    "permissionId" text NOT NULL
);


ALTER TABLE public.role_permissions OWNER TO nodedr;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.roles (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    name text NOT NULL,
    label text NOT NULL,
    "isSystem" boolean DEFAULT true NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.roles OWNER TO nodedr;

--
-- Name: service_logs; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.service_logs (
    id text NOT NULL,
    "equipmentId" text NOT NULL,
    "servicedAt" date NOT NULL,
    cost numeric(12,2),
    note text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.service_logs OWNER TO nodedr;

--
-- Name: shifts; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.shifts (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "userId" text NOT NULL,
    "startsAt" timestamp(3) without time zone NOT NULL,
    "endsAt" timestamp(3) without time zone NOT NULL,
    note text
);


ALTER TABLE public.shifts OWNER TO nodedr;

--
-- Name: staff_api_keys; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.staff_api_keys (
    id text NOT NULL,
    "userId" text NOT NULL,
    name text NOT NULL,
    "tokenHash" text NOT NULL,
    "lastFour" text NOT NULL,
    "lastUsedAt" timestamp(3) without time zone,
    "revokedAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.staff_api_keys OWNER TO nodedr;

--
-- Name: staff_pay; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.staff_pay (
    "userId" text NOT NULL,
    "payType" public."PayType" DEFAULT 'MONTHLY'::public."PayType" NOT NULL,
    rate numeric(12,2) DEFAULT 0 NOT NULL,
    "overtimeAfterHours" numeric(5,2),
    "overtimeMultiplier" numeric(4,2) DEFAULT 1.5 NOT NULL,
    "deductAbsence" boolean DEFAULT false NOT NULL,
    "lateGraceMinutes" integer
);


ALTER TABLE public.staff_pay OWNER TO nodedr;

--
-- Name: stock_batches; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.stock_batches (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "ingredientId" text NOT NULL,
    "goodsReceiptItemId" text,
    "batchNumber" text NOT NULL,
    "quantityReceived" numeric(12,3) NOT NULL,
    "quantityRemaining" numeric(12,3) NOT NULL,
    "unitCost" numeric(12,4) NOT NULL,
    "expiryDate" timestamp(3) without time zone,
    "receivedAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.stock_batches OWNER TO nodedr;

--
-- Name: stock_journal_entries; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.stock_journal_entries (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "entryNo" text NOT NULL,
    type public."StockJournalType" NOT NULL,
    status public."ProductionStatus" DEFAULT 'DRAFT'::public."ProductionStatus" NOT NULL,
    "occurredAt" timestamp(3) without time zone NOT NULL,
    reason text,
    notes text,
    "idempotencyKey" text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL,
    "postedById" text,
    "postedAt" timestamp(3) without time zone,
    "voidedById" text,
    "voidedAt" timestamp(3) without time zone,
    "voidReason" text
);


ALTER TABLE public.stock_journal_entries OWNER TO nodedr;

--
-- Name: stock_journal_lines; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.stock_journal_lines (
    id text NOT NULL,
    "entryId" text NOT NULL,
    "ingredientId" text NOT NULL,
    "sortOrder" integer DEFAULT 0 NOT NULL,
    direction text NOT NULL,
    "enteredQuantity" numeric(12,3) NOT NULL,
    "enteredUnit" public."IngredientUnit" NOT NULL,
    quantity numeric(12,3) NOT NULL,
    "fromLocationId" text,
    "fromLocationName" text,
    "toLocationId" text,
    "toLocationName" text,
    "wasteReason" public."WasteReason",
    note text,
    "unitCost" numeric(14,4),
    "wasteEntryId" text
);


ALTER TABLE public.stock_journal_lines OWNER TO nodedr;

--
-- Name: stock_levels; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.stock_levels (
    id text NOT NULL,
    "ingredientId" text NOT NULL,
    "locationId" text NOT NULL,
    quantity numeric(12,3) DEFAULT 0 NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.stock_levels OWNER TO nodedr;

--
-- Name: stock_locations; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.stock_locations (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text NOT NULL,
    "sortOrder" integer DEFAULT 0 NOT NULL,
    "isActive" boolean DEFAULT true NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.stock_locations OWNER TO nodedr;

--
-- Name: stock_movements; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.stock_movements (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "ingredientId" text NOT NULL,
    "batchId" text,
    type public."StockMovementType" NOT NULL,
    quantity numeric(12,3) NOT NULL,
    note text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "orderId" text,
    "deviceId" text,
    "productionEntryId" text,
    "wasteEntryId" text,
    "locationId" text,
    "journalEntryId" text
);


ALTER TABLE public.stock_movements OWNER TO nodedr;

--
-- Name: stock_takes; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.stock_takes (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "takenAt" timestamp(3) without time zone NOT NULL,
    area text,
    note text,
    "idempotencyKey" text,
    "deviceId" text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    lines jsonb NOT NULL
);


ALTER TABLE public.stock_takes OWNER TO nodedr;

--
-- Name: stock_transfers; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.stock_transfers (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    "fromBranchId" text NOT NULL,
    "toBranchId" text NOT NULL,
    "fromBranchName" text NOT NULL,
    "toBranchName" text NOT NULL,
    "ingredientName" text NOT NULL,
    unit text NOT NULL,
    quantity numeric(12,3) NOT NULL,
    "unitCost" numeric(12,4) NOT NULL,
    note text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.stock_transfers OWNER TO nodedr;

--
-- Name: supplier_invoices; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.supplier_invoices (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "supplierId" text NOT NULL,
    "purchaseOrderId" text,
    "goodsReceiptId" text,
    "invoiceNumber" text NOT NULL,
    "invoiceDate" timestamp(3) without time zone NOT NULL,
    "dueDate" timestamp(3) without time zone,
    "totalAmount" numeric(12,2) NOT NULL,
    "amountPaid" numeric(12,2) DEFAULT 0 NOT NULL,
    status public."SupplierInvoiceStatus" DEFAULT 'UNPAID'::public."SupplierInvoiceStatus" NOT NULL,
    notes text,
    "recordedById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.supplier_invoices OWNER TO nodedr;

--
-- Name: supplier_payments; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.supplier_payments (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "supplierInvoiceId" text NOT NULL,
    amount numeric(12,2) NOT NULL,
    "paymentMethod" public."PaymentMethod" NOT NULL,
    reference text,
    "paidAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "recordedById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.supplier_payments OWNER TO nodedr;

--
-- Name: supplier_quotation_items; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.supplier_quotation_items (
    id text NOT NULL,
    "supplierQuotationId" text NOT NULL,
    "ingredientId" text NOT NULL,
    "quantityQuoted" numeric(12,3) NOT NULL,
    "unitPrice" numeric(12,4) NOT NULL
);


ALTER TABLE public.supplier_quotation_items OWNER TO nodedr;

--
-- Name: supplier_quotations; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.supplier_quotations (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "supplierId" text NOT NULL,
    "quotationNumber" text NOT NULL,
    status public."QuotationStatus" DEFAULT 'DRAFT'::public."QuotationStatus" NOT NULL,
    "validUntil" timestamp(3) without time zone,
    notes text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.supplier_quotations OWNER TO nodedr;

--
-- Name: suppliers; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.suppliers (
    id text NOT NULL,
    "branchId" text NOT NULL,
    name text NOT NULL,
    "contactName" text,
    phone text,
    email text,
    address text,
    "gstNumber" text,
    notes text,
    "isActive" boolean DEFAULT true NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL
);


ALTER TABLE public.suppliers OWNER TO nodedr;

--
-- Name: sync_changes; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.sync_changes (
    seq bigint NOT NULL,
    tbl text NOT NULL,
    pk jsonb NOT NULL,
    "pkKey" text NOT NULL,
    op character(1) NOT NULL,
    "row" jsonb,
    ts timestamp(3) with time zone NOT NULL,
    origin text NOT NULL
);


ALTER TABLE public.sync_changes OWNER TO nodedr;

--
-- Name: sync_changes_seq_seq; Type: SEQUENCE; Schema: public; Owner: nodedr
--

CREATE SEQUENCE public.sync_changes_seq_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sync_changes_seq_seq OWNER TO nodedr;

--
-- Name: sync_changes_seq_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: nodedr
--

ALTER SEQUENCE public.sync_changes_seq_seq OWNED BY public.sync_changes.seq;


--
-- Name: sync_state; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.sync_state (
    id integer DEFAULT 1 NOT NULL,
    enabled boolean DEFAULT false NOT NULL,
    role text DEFAULT 'client'::text NOT NULL,
    "deviceId" text DEFAULT md5(((random())::text || (clock_timestamp())::text)) NOT NULL,
    "serverUrl" text,
    "apiKey" text,
    seeded boolean DEFAULT false NOT NULL,
    "lastPullSeq" bigint DEFAULT 0 NOT NULL,
    "lastPushSeq" bigint DEFAULT 0 NOT NULL,
    "lastSyncAt" timestamp(3) without time zone,
    "lastError" text,
    conflicts jsonb DEFAULT '[]'::jsonb NOT NULL,
    CONSTRAINT sync_state_single CHECK ((id = 1))
);


ALTER TABLE public.sync_state OWNER TO nodedr;

--
-- Name: table_accesses; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.table_accesses (
    id text NOT NULL,
    "tableId" text NOT NULL,
    "tagId" text,
    "tokenHash" text NOT NULL,
    "expiresAt" timestamp(3) without time zone NOT NULL,
    "lastUsedAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.table_accesses OWNER TO nodedr;

--
-- Name: table_requests; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.table_requests (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "tableId" text NOT NULL,
    type public."TableRequestType" NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "resolvedAt" timestamp(3) without time zone
);


ALTER TABLE public.table_requests OWNER TO nodedr;

--
-- Name: table_session_grants; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.table_session_grants (
    id text NOT NULL,
    "sessionId" text NOT NULL,
    "tokenHash" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.table_session_grants OWNER TO nodedr;

--
-- Name: table_sessions; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.table_sessions (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "tableId" text NOT NULL,
    status public."TableSessionStatus" DEFAULT 'ACTIVE'::public."TableSessionStatus" NOT NULL,
    "codeHash" text NOT NULL,
    "openedById" text,
    "openedAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "expiresAt" timestamp(3) without time zone NOT NULL,
    "closedAt" timestamp(3) without time zone,
    "closedReason" text,
    "failedTries" integer DEFAULT 0 NOT NULL,
    "lockedUntil" timestamp(3) without time zone,
    "openedVia" text DEFAULT 'STAFF'::text NOT NULL,
    "joinSecret" text
);


ALTER TABLE public.table_sessions OWNER TO nodedr;

--
-- Name: tables; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.tables (
    id text NOT NULL,
    "floorId" text NOT NULL,
    number text NOT NULL,
    name text,
    capacity integer DEFAULT 2 NOT NULL,
    status public."TableStatus" DEFAULT 'AVAILABLE'::public."TableStatus" NOT NULL,
    "posX" double precision DEFAULT 0 NOT NULL,
    "posY" double precision DEFAULT 0 NOT NULL,
    width double precision DEFAULT 80 NOT NULL,
    height double precision DEFAULT 80 NOT NULL,
    rotation double precision DEFAULT 0 NOT NULL,
    shape text DEFAULT 'square'::text NOT NULL,
    color text,
    "assignedWaiterId" text,
    notes text,
    "qrToken" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL,
    "statusSince" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    hidden boolean DEFAULT false NOT NULL
);


ALTER TABLE public.tables OWNER TO nodedr;

--
-- Name: user_branches; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.user_branches (
    "userId" text NOT NULL,
    "branchId" text NOT NULL
);


ALTER TABLE public.user_branches OWNER TO nodedr;

--
-- Name: user_permission_overrides; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.user_permission_overrides (
    "userId" text NOT NULL,
    "permissionId" text NOT NULL,
    effect public."PermissionEffect" NOT NULL,
    reason text,
    "expiresAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.user_permission_overrides OWNER TO nodedr;

--
-- Name: users; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.users (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    "roleId" text NOT NULL,
    name text NOT NULL,
    email text,
    phone text,
    "passwordHash" text NOT NULL,
    "pinHash" text,
    "isActive" boolean DEFAULT true NOT NULL,
    "twoFactorSecret" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp(3) without time zone NOT NULL,
    "twoFactorEnabled" boolean DEFAULT false NOT NULL,
    "twoFactorLastStep" integer,
    "twoFactorRecoveryHashes" text[] DEFAULT ARRAY[]::text[],
    "dashboardPrefs" jsonb,
    "riderLat" double precision,
    "riderLng" double precision,
    "riderLocationAt" timestamp(3) without time zone,
    "riderOnline" boolean DEFAULT false NOT NULL,
    "departmentId" text,
    "sessionsValidFrom" timestamp(3) without time zone,
    "isSuperAdmin" boolean DEFAULT false NOT NULL
);


ALTER TABLE public.users OWNER TO nodedr;

--
-- Name: verifactu_records; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.verifactu_records (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    "branchId" text NOT NULL,
    "issuerNif" text NOT NULL,
    seq integer NOT NULL,
    type public."VerifactuRecordType" NOT NULL,
    "invoiceType" text NOT NULL,
    "invoiceNumber" text NOT NULL,
    "issueDate" text NOT NULL,
    "taxTotalCents" integer NOT NULL,
    "totalCents" integer NOT NULL,
    "generatedAt" text NOT NULL,
    "previousHash" text,
    hash text NOT NULL,
    xml text NOT NULL,
    "qrUrl" text,
    environment public."VerifactuEnvironment" NOT NULL,
    "orderId" text,
    "refundId" text,
    status public."VerifactuStatus" DEFAULT 'PENDING'::public."VerifactuStatus" NOT NULL,
    attempts integer DEFAULT 0 NOT NULL,
    "nextAttemptAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    csv text,
    "errorCode" text,
    "errorText" text,
    "responseXml" text,
    "submittedAt" timestamp(3) without time zone,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.verifactu_records OWNER TO nodedr;

--
-- Name: verifactu_settings; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.verifactu_settings (
    id text NOT NULL,
    "branchId" text NOT NULL,
    enabled boolean DEFAULT false NOT NULL,
    environment public."VerifactuEnvironment" DEFAULT 'TEST'::public."VerifactuEnvironment" NOT NULL,
    "seriesPrefix" text DEFAULT 'T1'::text NOT NULL,
    "nextNumber" integer DEFAULT 1 NOT NULL,
    "nextRefundNumber" integer DEFAULT 1 NOT NULL,
    "installationNumber" text NOT NULL,
    "certEncrypted" bytea,
    "certPasswordEncrypted" bytea,
    "certSubject" text,
    "certExpiresAt" timestamp(3) without time zone,
    "updatedAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.verifactu_settings OWNER TO nodedr;

--
-- Name: waitlist_entries; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.waitlist_entries (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "customerName" text NOT NULL,
    phone text,
    "partySize" integer NOT NULL,
    "quotedWaitMinutes" integer,
    notes text,
    status public."WaitlistStatus" DEFAULT 'WAITING'::public."WaitlistStatus" NOT NULL,
    "tableId" text,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "seatedAt" timestamp(3) without time zone
);


ALTER TABLE public.waitlist_entries OWNER TO nodedr;

--
-- Name: waste_entries; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.waste_entries (
    id text NOT NULL,
    "branchId" text NOT NULL,
    kind public."WasteKind" NOT NULL,
    "ingredientId" text NOT NULL,
    "enteredQuantity" numeric(12,3) NOT NULL,
    "enteredUnit" public."IngredientUnit" NOT NULL,
    quantity numeric(12,3) NOT NULL,
    reason public."WasteReason" NOT NULL,
    shift text,
    location text,
    note text,
    "occurredAt" timestamp(3) without time zone NOT NULL,
    "includedInProduction" boolean DEFAULT false NOT NULL,
    "productionEntryId" text,
    status public."WasteStatus" DEFAULT 'POSTED'::public."WasteStatus" NOT NULL,
    "idempotencyKey" text,
    "deviceId" text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "approvedById" text,
    "approvedAt" timestamp(3) without time zone,
    "decisionNote" text,
    "reversedById" text,
    "reversedAt" timestamp(3) without time zone,
    "reverseReason" text,
    "photoUrl" text
);


ALTER TABLE public.waste_entries OWNER TO nodedr;

--
-- Name: waste_logs; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.waste_logs (
    id text NOT NULL,
    "branchId" text NOT NULL,
    "ingredientId" text NOT NULL,
    "batchId" text,
    quantity numeric(12,3) NOT NULL,
    reason public."WasteReason" NOT NULL,
    "unitCostAtWaste" numeric(12,4) NOT NULL,
    notes text,
    "createdById" text NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "entryId" text
);


ALTER TABLE public.waste_logs OWNER TO nodedr;

--
-- Name: webhook_deliveries; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.webhook_deliveries (
    id text NOT NULL,
    "endpointId" text NOT NULL,
    event text NOT NULL,
    payload jsonb NOT NULL,
    status public."WebhookStatus" DEFAULT 'PENDING'::public."WebhookStatus" NOT NULL,
    attempts integer DEFAULT 0 NOT NULL,
    "lastStatusCode" integer,
    "lastError" text,
    "nextAttemptAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "deliveredAt" timestamp(3) without time zone
);


ALTER TABLE public.webhook_deliveries OWNER TO nodedr;

--
-- Name: webhook_endpoints; Type: TABLE; Schema: public; Owner: nodedr
--

CREATE TABLE public.webhook_endpoints (
    id text NOT NULL,
    "restaurantId" text NOT NULL,
    url text NOT NULL,
    secret text NOT NULL,
    events text[] DEFAULT ARRAY[]::text[],
    description text,
    "isActive" boolean DEFAULT true NOT NULL,
    "createdAt" timestamp(3) without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.webhook_endpoints OWNER TO nodedr;

--
-- Name: sync_changes seq; Type: DEFAULT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.sync_changes ALTER COLUMN seq SET DEFAULT nextval('public.sync_changes_seq_seq'::regclass);


--
-- Data for Name: _prisma_migrations; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public._prisma_migrations (id, checksum, finished_at, migration_name, logs, rolled_back_at, started_at, applied_steps_count) FROM stdin;
37758d6c-16d0-47bb-b07f-10a262afb8b9	830712d8344385da11e5db92b55d19385dc19f8b121df445231b6d11c9e4f5bf	2026-11-18 05:53:22.127547+00	20261004030500_expense_paid_from_cash	\N	\N	2026-11-18 05:53:22.12618+00	1
877c175f-4ddd-4146-bcc9-6139e06363d5	7998c786b7ba2f87e354f73251a5d014bfa10c10d7e23abcc55b838b4026ef2b	2026-11-18 05:53:21.930902+00	20260803053615_init	\N	\N	2026-11-18 05:53:21.852523+00	1
311927c9-4312-47bd-b432-756ce4409835	6b4e9e962b532a6fe63be70815034e8c8f8f79fa30f94cdff6d462a914b3d6f6	2026-11-18 05:53:22.071964+00	20260820143603_add_table_status_since	\N	\N	2026-11-18 05:53:22.070686+00	1
61d3d0b7-1634-4922-ae8f-904efa55a66a	d18f1101cc5793feffeac2a32389ee49747a07c82f9b47167b494a03595ca05b	2026-11-18 05:53:21.941049+00	20260803070032_add_reservations_waitlist	\N	\N	2026-11-18 05:53:21.931365+00	1
b862a72a-c90f-4532-bc04-e30caf8b292b	bfa874ab49a3a2d5e48a640b72d4d93afc657e60a29de91cdb5339ea337fdadc	2026-11-18 05:53:21.958155+00	20260803073234_add_crm_loyalty_giftcards_combos	\N	\N	2026-11-18 05:53:21.941478+00	1
84ceffb2-925a-41d7-a271-67359e655473	36170d63a7924b84d269f9c6ff0937ac33d75886eb7b00235fc318f1a630c22d	2026-11-18 05:53:22.000183+00	20260803182111_phase4_inventory_procurement	\N	\N	2026-11-18 05:53:21.958674+00	1
db420754-d95b-4cb3-bdf8-5795f08ede07	629cc8f109058cc10091de4e68add5e750f4612cd008f9774eb20e81901fc002	2026-11-18 05:53:22.074188+00	20260927071500_multi_region_tax	\N	\N	2026-11-18 05:53:22.072298+00	1
6de94c17-8f1d-4de3-a54b-a0e2cb892d37	5e96f76de87478fef94db7585644a5f784a3ec682e5878f5441127a6aea65329	2026-11-18 05:53:22.002398+00	20260804115252_add_loyalty_config_to_restaurant	\N	\N	2026-11-18 05:53:22.000608+00	1
418710b3-3679-443f-b45a-9ec74348a5aa	a44f7eba4e3085530ded8625dd12fff00d2528b4f73caa1cd85635a9e8cdcd05	2026-11-18 05:53:22.004286+00	20260812160455_add_guest_name_to_orders	\N	\N	2026-11-18 05:53:22.002864+00	1
70ec89c6-0b71-4cfa-a988-eb7c7207fe3c	3bbba73ec5438e32d541033d11fd5524ef2aee26d5937c9ec89af7e69a911a27	2026-11-18 05:53:22.192624+00	20261017000000_kiosk	\N	\N	2026-11-18 05:53:22.188917+00	1
39acda6f-1a32-4b2e-bbf0-517665740982	80e89068093ad141b8235a2fdc16dde751cbcfd5340056fd62bb4a0dca175084	2026-11-18 05:53:22.033812+00	20260814182524_add_procurement_depth	\N	\N	2026-11-18 05:53:22.004729+00	1
d3a27ec6-10e8-477a-9846-154c08c23fd1	0285757d2bc3f7c11fe1412b35c34b0c36724928ad5bfb551824857eb9df1cdf	2026-11-18 05:53:22.075609+00	20260930010000_add_restaurant_logo_url	\N	\N	2026-11-18 05:53:22.074518+00	1
10cca852-0131-4bd6-ad5b-51c67fccfcaf	0fceb30ad8c1370d374087aa252cd926bff62b0904a7698e8e6bec0e7f279dfa	2026-11-18 05:53:22.037133+00	20260815065428_modifier_group_branch_scoping	\N	\N	2026-11-18 05:53:22.034184+00	1
440f6eed-105e-431c-b1d9-3deec5d57d8f	d7796a038557d7cecd3551e1fda156ddaf2e7fe19d9fa8b458aea02faa608d0b	2026-11-18 05:53:22.040925+00	20260815072322_add_download_stats	\N	\N	2026-11-18 05:53:22.03751+00	1
14532db7-8856-49f7-81f0-31d1e54f90cc	35b6727d0a5190c9eeff42ae9981265bad326da266dd4ee166e577899349bf08	2026-11-18 05:53:22.150734+00	20261004040000_marketing_maintenance_documents	\N	\N	2026-11-18 05:53:22.127922+00	1
b6e1a684-86b6-4ec5-996f-3bc2ccb6822a	5ab0289c1c64775672a89e044c00c23fa4d3b530facab22300cfc45cb0728c09	2026-11-18 05:53:22.046795+00	20260815123739_make_role_name_string	\N	\N	2026-11-18 05:53:22.041284+00	1
4573472a-7df1-4e50-a113-083fbcaeb3c2	570aafaa945a376c92f77e740f9243f52db46098b7c60de4c5db10d4470aaf9a	2026-11-18 05:53:22.078099+00	20261003000000_order_acceptance	\N	\N	2026-11-18 05:53:22.07593+00	1
a600be65-df5f-41fc-adeb-7c57cc86fa89	cbcb8ecc97a1144bb038490161acb423e81543318c2eebc00b45b4368f48f7eb	2026-11-18 05:53:22.051818+00	20260815125111_add_notifications	\N	\N	2026-11-18 05:53:22.047128+00	1
a8ac7f04-f5a7-40c5-a295-04738f756972	f8b906af9b611081170965e77799597fa0f56f6672ef516b19936e6ddf846f70	2026-11-18 05:53:22.058652+00	20260815131448_add_backup	\N	\N	2026-11-18 05:53:22.052175+00	1
e17436b6-7261-43f0-93c5-7e7964e5b632	3369509972544cf5748c025c4125d3f8fcba9bb95655bb7096b423854fb3cd17	2026-11-18 05:53:22.070327+00	20260820135007_add_api_keys	\N	\N	2026-11-18 05:53:22.058994+00	1
d5b17dfa-f0e2-4b6e-a80a-e025323827b0	ec0ee54944fff3fe3657d3523a3ae86b93f68d12a00dc3fd621f76a90c296a31	2026-11-18 05:53:22.083651+00	20261004000000_staff_attendance	\N	\N	2026-11-18 05:53:22.078435+00	1
2979b11b-84c6-4e3f-ae25-9aa1ca288468	113208c98c4949945954302e400f30654fd1b8523ecdc12536f358314e80910a	2026-11-18 05:53:22.185419+00	20261011010000_phase6_7_completions	\N	\N	2026-11-18 05:53:22.165867+00	1
b314a03a-0ceb-46ae-8d5c-2dedb5aba404	559d8769ddf2fc37f20c1409a3bb5711e05e3642352a5d4ac95362ac055c1ef6	2026-11-18 05:53:22.091449+00	20261004010000_delivery	\N	\N	2026-11-18 05:53:22.084007+00	1
76cddafb-1975-47fa-99d2-83f529533802	5983ee15307c3f88d1fda1e1c6f708218a54dd18e07e0cf2635937457d18fe43	2026-11-18 05:53:22.152895+00	20261004050000_two_factor_auth	\N	\N	2026-11-18 05:53:22.1511+00	1
4d5560a2-fe69-4b7b-8f6d-0bbe18a0c479	fa196910b195f05a028b04c098bfa4985079dd42f67886d476d5994e7ee79699	2026-11-18 05:53:22.09762+00	20261004020000_table_requests	\N	\N	2026-11-18 05:53:22.09176+00	1
f918c7da-5eaf-473e-ba52-b567c87e13ea	c05b6fbae2265cf51402f670d72033e00bf09680931a5403f9bb503ee2b29d00	2026-11-18 05:53:22.125804+00	20261004030000_staff_payroll_accounting	\N	\N	2026-11-18 05:53:22.098018+00	1
1918e8a2-2863-44a0-8c63-f4d60a5c8ca9	baba232d01e150e7654324f9a065ac08d2f34f4de07942638890345afb15a5be	2026-11-18 05:53:22.162109+00	20261004060000_webhooks	\N	\N	2026-11-18 05:53:22.153257+00	1
1c28e461-2685-4386-944c-07980e1a2dd7	af56c5d867f598460731869a26c1e3d7593b0ace6d78762b20d42e6f92b36f08	2026-11-18 05:53:22.186939+00	20261011020000_payment_method_other	\N	\N	2026-11-18 05:53:22.18579+00	1
ab6608a0-e461-414f-8d5e-b26c5e1b87d1	e0431996965fd636b70768ad01905dd2a70e505a2319b074f8ba97ff139afeb8	2026-11-18 05:53:22.163943+00	20261004070000_campaign_sending_optout	\N	\N	2026-11-18 05:53:22.162465+00	1
a8919dab-962a-44ef-afc7-da93554ad7da	fa9e3e0aa28b517b1011e921101c8b3f5026355bb535c2893b9ce8cf7741dc32	2026-11-18 05:53:22.165492+00	20261011000000_upi_payee	\N	\N	2026-11-18 05:53:22.164283+00	1
cffdd893-5d7e-4691-b552-dca46c0aaa24	b0154e53092e19d15a7a2d5d010cb3277a422f52e2dd27debb3604b2d36851c1	2026-11-18 05:53:22.208452+00	20261019000000_kot_printing_and_cancel_audit	\N	\N	2026-11-18 05:53:22.206403+00	1
5757c456-b62c-474a-a078-f716ccb38f32	12eaf5f05b3be9ae61199c0de9de5f3d2b3a9aa5163a1dad4c8b9ffe747e010c	2026-11-18 05:53:22.188574+00	20261014010000_category_show_on_website	\N	\N	2026-11-18 05:53:22.18727+00	1
2bbf4ae9-0b92-4a1f-a80d-daab762b66dd	a95792ab8904bb889a8653728e6562e99e56589109f6c27baf4bfd305295f740	2026-11-18 05:53:22.206056+00	20261018020000_printer_settings	\N	\N	2026-11-18 05:53:22.204137+00	1
26754e78-2b7c-4278-a596-932bc5f44561	2cfbea46184ac2e5589aa56a03b6de8baa3d2768f799ec8a43bdc6b91ba58404	2026-11-18 05:53:22.195012+00	20261018000000_read_permissions	\N	\N	2026-11-18 05:53:22.192951+00	1
3b5e4b82-bcd9-413c-9d35-e39a0a2e5459	c1b82ffd960e712ebaa466b82f7aaa228ce01827e28bb054028d52524c9e80f6	2026-11-18 05:53:22.20377+00	20261018010000_inventory_tracking_and_returns	\N	\N	2026-11-18 05:53:22.195355+00	1
24dac505-2ec1-40cf-b6fc-42ac1dbc875d	0c1a4e6767948de81dddac79bbde550fcfb39f6fc07273d03aed3f1765641cf5	2026-11-18 05:53:22.212479+00	20261020000000_order_flow_hardening	\N	\N	2026-11-18 05:53:22.208817+00	1
240e6039-d6a6-4d69-be23-3ec99d4ec401	0af5ed7f78778b2c850fc45cc096199b3929d0456ef401229b7831e0e4e074d2	2026-11-18 05:53:22.213997+00	20261021000000_menu_item_half_price	\N	\N	2026-11-18 05:53:22.212768+00	1
dd67d54e-b39c-4cc9-bc7a-43393588df94	b89f588c255683aa9d0dc7467b34ba73167a46f0d702d02ca937eeca07128a76	2026-11-18 05:53:22.228023+00	20261022000000_verifactu	\N	\N	2026-11-18 05:53:22.214365+00	1
3ca8ecb5-746a-4528-9cb2-66d5f426a3a3	d5e4343e65be7f6a859baec3224db737000c3c1ed75af3f63507b45faaba339f	2026-11-18 05:53:22.781612+00	20261026000000_server_sync	\N	\N	2026-11-18 05:53:22.231845+00	1
33ad99d7-a3ef-4d1d-af86-d50a65f0f8e9	73515e994ab60b30f275522df73cbbe66542ba767f97c03bc9b7be2b6b8cf0a1	2026-11-18 05:53:22.785353+00	20261030000000_integration_order_ownership	\N	\N	2026-11-18 05:53:22.782071+00	1
233a22ab-f8a1-402a-a65b-c37725362082	22678fe96aa9ad15e7239de6c6a533f758d28f57e54c55fdc8d5848c7cdab6fd	2026-11-18 05:53:22.944107+00	20261113150000_attendance_event_keys	\N	\N	2026-11-18 05:53:22.941186+00	1
411f786f-1cf3-42cf-af42-01459c4a82b3	082001341eb5dbb527e7b67a68c30d86cc33b437cf7cacef137f05b3887913bc	2026-11-18 05:53:22.787452+00	20261101000000_discount_guardrails	\N	\N	2026-11-18 05:53:22.785703+00	1
634b1a21-7989-4b40-ba33-c4d00b610148	61a22988c49ac795c1006b04b340d46a74b57dbc70453822488209fe0162f0ec	2026-11-18 05:53:22.896714+00	20261111000000_recipe_costing	\N	\N	2026-11-18 05:53:22.871561+00	1
6d1cfc27-e30f-496e-9e6d-e802fbe42b45	4356bd6297e25b8894fd81de3fcbb2097f0989e353f5614095a7136beafc5aa1	2026-11-18 05:53:22.792217+00	20261101120000_customer_addresses	\N	\N	2026-11-18 05:53:22.787807+00	1
0fba86c4-5729-4eb6-8b1e-36262ae3373b	548353fe04ba294c99c706eefd175db279f3b5d5f0bed460e7a9e87aef8744f1	2026-11-18 05:53:22.794434+00	20261101180000_payroll_adjustments_paid	\N	\N	2026-11-18 05:53:22.792571+00	1
17734fac-c814-4dfe-8ef7-b006320ce13c	277587917e65d394bb3096e6180836a810f29c9c1ed9f0c796a6bd45254b5f69	2026-11-18 05:53:22.795925+00	20261101200000_dashboard_prefs	\N	\N	2026-11-18 05:53:22.794751+00	1
b0e3468e-f971-4b32-a3c5-896c4449b8a1	e951bd019fd40c42e10f25167d1974b9d6cc3d3311da00b579d8c02782379a22	2026-11-18 05:53:22.916835+00	20261113104750_stock_journal_production	\N	\N	2026-11-18 05:53:22.897082+00	1
9edb4f52-c089-416b-a68d-19c45bc641f8	28d766ca8337f282aea8eed0af2afe6d61b232b7e6ccd120271ddef18f557eeb	2026-11-18 05:53:22.807288+00	20261101210000_integration_hub	\N	\N	2026-11-18 05:53:22.796288+00	1
585ecfe6-3d70-460e-ad1c-38fc181b8612	860a0201274034a58f31f501e4df5fb9f07d4e0f1c4cfb98108e02caca56485a	2026-11-18 05:53:22.824734+00	20261102000000_referrals	\N	\N	2026-11-18 05:53:22.807628+00	1
64a7bb6b-bd95-4702-aaae-5e7049c7c498	136273cea9213e19f3d91bc8a17d519f156389243daf4bf75b6fc7adc8ab16d0	2026-11-18 05:53:23.036933+00	20261119000000_delivery_assignment_history	\N	\N	2026-11-18 05:53:23.031052+00	1
8f98b9bd-2a73-4ab6-b6e5-3cc2cbd863d1	a3353c2f82cf80f272f7a22fb44d3cb63425e1ffeac72015b4bf8cc4a1a78915	2026-11-18 05:53:22.826569+00	20261102120000_order_minimums	\N	\N	2026-11-18 05:53:22.825092+00	1
c7755f94-1f24-46c1-89ca-1089bf673ae4	00f6f7f980919c21a3cf6714b8126e3a4f74fb2d26c6e3e73ac98eddc9d917b2	2026-11-18 05:53:22.919093+00	20261113114103_payroll_breaks_overtime	\N	\N	2026-11-18 05:53:22.91725+00	1
4a9e7fb1-4dea-4f95-ab24-0dbb7c9aafd7	5c28ff9409c6a16603c92f7cc961447536f85eb2419c6204e9578f73338a7229	2026-11-18 05:53:22.829927+00	20261102180000_rider_app	\N	\N	2026-11-18 05:53:22.827373+00	1
beb9b101-2dc9-47bb-bff5-18502d516dc3	6cd8fd80a811da94b2b9a7de209910cb875b219693811f10e8cf1aa46457b2f4	2026-11-18 05:53:22.832648+00	20261102210000_online_price_and_location	\N	\N	2026-11-18 05:53:22.830257+00	1
1cba7054-4a31-42e5-b9e8-89f97c42dabe	5176d06d28c3ec35aee3688842abfb0a9e88a1f5a099327bc52c5701737c98a5	2026-11-18 05:53:22.956823+00	20261113151000_stock_locations	\N	\N	2026-11-18 05:53:22.944472+00	1
34276119-acea-4055-b9d2-d276c1be446e	26bc0d6bfffd9103630d548605739d363e9f83f475815d1531ac6e688886ee6c	2026-11-18 05:53:22.839846+00	20261103000000_device_tokens	\N	\N	2026-11-18 05:53:22.833061+00	1
e8953e14-58c9-4a36-ad77-73da5bc1e815	1edcf931244d8338c21d32fee876dcd21500755b569cffc9dc000a5ac74a86f2	2026-11-18 05:53:22.925009+00	20261113114247_floor_layouts	\N	\N	2026-11-18 05:53:22.919439+00	1
e039c3cf-1d2d-49e6-a578-417c8b9d900c	69083401f7fa302dbb3378f47b0a443c30a75be7107bbc44e9e5c6b6dec5934e	2026-11-18 05:53:22.848316+00	20261103120000_department_permission_overrides	\N	\N	2026-11-18 05:53:22.840199+00	1
4e4d0ff5-510d-4142-9588-d86738d12825	6ad2857150e5b722589468112ad504565a35055320c3368909f5e33c5f3740bb	2026-11-18 05:53:22.86496+00	20261106000000_payment_gateways	\N	\N	2026-11-18 05:53:22.848734+00	1
219c669e-face-4773-94cb-f306d95187ee	1328142950fe9e73afa084ae7c56a59f3c7e39d5f92c008b4b0341bb8c022296	2026-11-18 05:53:22.871086+00	20261106120000_gateway_refunds	\N	\N	2026-11-18 05:53:22.865323+00	1
4b7482a0-2793-4c5e-962f-1e6e6b7775b3	21241a5b5fe5a7a37414f5d58ca9709a1c5dd875a676570f37fc935d22452860	2026-11-18 05:53:22.931741+00	20261113114433_pos_devices	\N	\N	2026-11-18 05:53:22.925382+00	1
d943882d-d4b5-4bed-b053-64546ea86a08	17616b68030e6fe8687e408d28e2b38eb86dbd5f4cdac7fbb503e5cdae636328	2026-11-18 05:53:23.018629+00	20261117000000_secure_nfc_tables_and_auto_sessions	\N	\N	2026-11-18 05:53:23.003454+00	1
e76771a5-6e21-4b8f-b7f6-867d7f2d1171	9f94b903ef582f26eddd4138f412d4ab79632f32d637132802c63ab69a51cdc8	2026-11-18 05:53:22.938007+00	20261113130209_late_absence_stock_take	\N	\N	2026-11-18 05:53:22.932158+00	1
09702f16-960d-4b9d-9519-5a5b7888fa81	bb9a5a40116564a19175836f479012f768aca4d848bce54cc97c26c00f909976	2026-11-18 05:53:22.979093+00	20261114100000_table_ordering_paging_display	\N	\N	2026-11-18 05:53:22.957257+00	1
29264c75-d8e1-4bee-8562-fceb93519830	6784b6f7b44a9f3abdd33141f30c18bccac516872b129a223dab95c808d3793d	2026-11-18 05:53:22.939493+00	20261113130306_ingredient_par_level	\N	\N	2026-11-18 05:53:22.938371+00	1
2016c86e-8258-4209-81f8-0d21cb44cbb2	7f268de5adb2240aa6abf0f6ed331ac91b53ebed78aa6d57af331380559ea5c4	2026-11-18 05:53:22.940883+00	20261113131053_waste_photo	\N	\N	2026-11-18 05:53:22.939768+00	1
c9fdb48b-a68b-4f4c-8479-f39ceda9b82c	c7941644cbf28bd48c77f2212ab63e255876980205be0c34d29039436345d679	2026-11-18 05:53:22.999788+00	20261115100000_manufacturing_sessions_ratings	\N	\N	2026-11-18 05:53:22.979489+00	1
71d937f1-70c6-4391-b994-08f1512f6ab4	0a28b49ea9822935565d7a48be1f37672516b2a150de6d699acdb8a6de903899	2026-11-18 05:53:23.020121+00	20261117100000_modifier_is_active	\N	\N	2026-11-18 05:53:23.018936+00	1
13cd8684-2bce-4d22-b73f-06f83e3ada01	3a6fbf70825ab27f0d93c1c39ca2288a8e3ce671f87efa830930aedb4622d5cf	2026-11-18 05:53:23.001494+00	20261116000000_session_revocation	\N	\N	2026-11-18 05:53:23.000161+00	1
547481f5-d003-416a-96f9-d9180d82c5ee	7a35ceb439d2fd82a430a9c5c458c0a87cb76b85f36ab14abbf4e1a495cd53d6	2026-11-18 05:53:23.003139+00	20261116100000_batch_quality_and_price_snapshot	\N	\N	2026-11-18 05:53:23.001837+00	1
60da33c2-35eb-47d6-8af0-a0193cc78a90	ac2c883f5feafd8a909fc0e176406a215e9a9120c721bf390a3efbf9f43bc1c0	2026-11-18 06:17:28.598979+00	20261122000000_licenses_and_superadmin	\N	\N	2026-11-18 06:17:28.588037+00	1
93f1d122-26c9-4d4d-aa62-002d8a2b4cd3	2b624fa598608bba456bc4371e4136984e200e44ffb437292354d9e182473b14	2026-11-18 05:53:23.030693+00	20261118000000_manufacturing_journal_v2	\N	\N	2026-11-18 05:53:23.020436+00	1
38740647-1432-4b9d-b2d7-3b05b41e9ea2	f3eb4a5032c6f73fdefb9bae1e8c8419ae3b88ae003c57d61e83f0e32f58db50	2026-11-18 05:53:23.057836+00	20261121000000_phone_books_sync	\N	\N	2026-11-18 05:53:23.050395+00	1
248bf9d0-f44e-4fc0-936d-750a69f3261c	89131b17e09bf5c36060a1eb5752da5ab74b7ad796dfe3889d34472d9a3738b6	2026-11-18 05:53:23.038474+00	20261119100000_table_session_join_secret	\N	\N	2026-11-18 05:53:23.037334+00	1
ed23cfcf-2217-440d-8012-a219160ac4c9	7c3ca2243e2ba425327035431b869d94471b051213fa44808d97e388e6f556af	2026-11-18 05:53:23.050017+00	20261120000000_stock_journal_entries	\N	\N	2026-11-18 05:53:23.038845+00	1
\.


--
-- Data for Name: attendance; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.attendance (id, "branchId", "userId", "clockInAt", "clockOutAt", note, "breakMinutes", "clockInKey", "clockOutKey") FROM stdin;
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.audit_logs (id, "userId", action, entity, "entityId", metadata, "createdAt") FROM stdin;
\.


--
-- Data for Name: backup_config; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.backup_config (id, endpoint, bucket, "accessKeyId", "secretAccessKey", region, "intervalDays", "retainCount", "updatedById", "updatedAt") FROM stdin;
\.


--
-- Data for Name: backups; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.backups (id, status, "sizeBytes", "s3KeyDb", "s3KeyUploads", sha256, "triggeredById", "failureReason", "createdAt", "verifiedAt") FROM stdin;
\.


--
-- Data for Name: bank_transactions; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.bank_transactions (id, "branchId", "postedOn", description, reference, amount, status, "expenseId", "createdAt") FROM stdin;
\.


--
-- Data for Name: branches; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.branches (id, "restaurantId", name, address, phone, "gstNumber", "isActive", "createdAt", "updatedAt", country, "taxRegime", "taxMode", "taxLabel", "taxId", "autoConfirmOrders", "autoConfirmReservations", "kioskToken", "kioskDineInEnabled", "kioskTakeawayEnabled", "printerCodepage", "printerColumns", "printerPaperWidthMm", "printerConnection", "printerHost", "printerPort") FROM stdin;
cmwlph928002xnw0112sak74j	cmwlph925002vnw01igutco9z	Main Branch	\N	\N	\N	t	2026-11-18 05:53:49.856	2026-11-18 05:53:49.856	IN	INDIA_GST	INCLUSIVE	\N	\N	f	f	\N	t	t	CP858	\N	80	USB	\N	9100
demo-branch	demo-restaurant	Main Branch	123 Demo Street	\N	\N	t	2026-11-18 06:17:36.653	2026-11-18 06:17:36.653	IN	INDIA_GST	INCLUSIVE	\N	\N	f	f	\N	t	t	CP858	\N	80	USB	\N	9100
\.


--
-- Data for Name: budgets; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.budgets (id, "branchId", month, category, amount, "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: buzzer_calls; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.buzzer_calls (id, "buzzerId", "orderId", "tableId", state, error, "createdById", "createdAt", "sentAt", "ackedAt", "expiresAt") FROM stdin;
\.


--
-- Data for Name: buzzers; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.buzzers (id, "branchId", name, number, "tableId", driver, "webhookUrl", "webhookSecret", "deviceToken", "isActive", "lastSeenAt", "createdAt") FROM stdin;
\.


--
-- Data for Name: campaigns; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.campaigns (id, "branchId", name, channel, segment, message, "createdAt", "lastSentAt", "lastSentCount") FROM stdin;
\.


--
-- Data for Name: cash_closings; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.cash_closings (id, "branchId", "businessDate", "openingFloat", "cashSales", "cashExpenses", "expectedCash", "countedCash", variance, note, "closedById", "createdAt") FROM stdin;
\.


--
-- Data for Name: combo_components; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.combo_components (id, "comboItemId", "componentItemId", quantity) FROM stdin;
\.


--
-- Data for Name: coupons; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.coupons (id, "branchId", code, kind, value, "minOrderAmount", "maxDiscount", "validFrom", "validUntil", "usageLimit", "usedCount", "isActive", "createdAt") FROM stdin;
\.


--
-- Data for Name: customer_addresses; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.customer_addresses (id, "customerId", label, line1, street, landmark, city, state, pincode, instructions, "isDefault", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: customers; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.customers (id, "branchId", name, phone, email, "createdAt", address, allergies, anniversary, birthday, "loyaltyPoints", notes, "walletBalance", "marketingOptOut", "referralCode") FROM stdin;
\.


--
-- Data for Name: delivery_assignments; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.delivery_assignments (id, "orderId", "branchId", "fromDriverId", "toDriverId", reason, "assignedById", "createdAt") FROM stdin;
\.


--
-- Data for Name: delivery_zones; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.delivery_zones (id, "branchId", name, fee, "minOrderAmount", "etaMinutes", pincodes, "isActive", "createdAt") FROM stdin;
\.


--
-- Data for Name: departments; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.departments (id, "restaurantId", name, "createdAt") FROM stdin;
\.


--
-- Data for Name: device_tokens; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.device_tokens (id, "userId", token, platform, "appVersion", "createdAt", "lastSeenAt") FROM stdin;
\.


--
-- Data for Name: display_ads; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.display_ads (id, "branchId", "terminalId", kind, url, title, "durationSec", "sortOrder", "isActive", "startsOn", "endsOn", "createdAt") FROM stdin;
\.


--
-- Data for Name: display_terminals; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.display_terminals (id, "branchId", name, token, "idleSeconds", "thankYouSeconds", "adSlideSeconds", "adFit", "isActive", state, "stateAt", "lastSeenAt", "createdAt") FROM stdin;
\.


--
-- Data for Name: document_files; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.document_files (id, "documentId", "fileName", "mimeType", size, data, "createdAt") FROM stdin;
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.documents (id, "branchId", title, category, body, "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: download_stats; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.download_stats (channel, count) FROM stdin;
\.


--
-- Data for Name: equipment; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.equipment (id, "branchId", name, location, "serviceIntervalDays", "lastServicedAt", "nextDueAt", notes, "isActive", "createdAt") FROM stdin;
\.


--
-- Data for Name: expenses; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.expenses (id, "branchId", "spentOn", category, amount, note, "createdById", "createdAt", "paidFromCash", "clientRequestId") FROM stdin;
\.


--
-- Data for Name: floor_layouts; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.floor_layouts (id, "floorId", name, "isActive", "sortOrder", tables, "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: floors; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.floors (id, "branchId", name, "sortOrder", "isActive") FROM stdin;
demo-floor	demo-branch	Ground Floor	0	t
\.


--
-- Data for Name: gateway_payments; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.gateway_payments (id, "restaurantId", "branchId", "orderId", provider, mode, "amountMinor", currency, status, "providerRef", "providerPaymentId", "checkoutUrl", note, "createdById", "appliedAt", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: gateway_refunds; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.gateway_refunds (id, "restaurantId", "gatewayPaymentId", "orderId", provider, "amountMinor", currency, status, "providerRefundId", "refundId", reason, note, "createdById", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: gateway_webhook_events; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.gateway_webhook_events (id, provider, mode, "eventId", "receivedAt") FROM stdin;
\.


--
-- Data for Name: gift_card_redemptions; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.gift_card_redemptions (id, "giftCardId", "orderId", amount, "createdAt") FROM stdin;
\.


--
-- Data for Name: gift_cards; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.gift_cards (id, "branchId", code, "initialValue", balance, "customerId", "isActive", "createdAt") FROM stdin;
\.


--
-- Data for Name: goods_receipt_items; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.goods_receipt_items (id, "goodsReceiptId", "ingredientId", "purchaseOrderItemId", quantity, "unitCost", "batchNumber", "expiryDate", "createdAt") FROM stdin;
\.


--
-- Data for Name: goods_receipts; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.goods_receipts (id, "branchId", "purchaseOrderId", "supplierId", "grnNumber", notes, "receivedById", "receivedAt", "createdAt") FROM stdin;
\.


--
-- Data for Name: ingredients; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.ingredients (id, "branchId", name, sku, unit, "reorderLevel", "currentStock", "costPerUnit", "isActive", "createdAt", "updatedAt", conversions, "costMethod", kind, "purchasePrice", "purchaseQuantity", "purchaseUnit", version, "yieldPercent", category, "storageLocation", "wasteApprovalQty", "parLevel") FROM stdin;
\.


--
-- Data for Name: integration_api_keys; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.integration_api_keys (id, "restaurantId", "branchId", name, "tokenHash", "lastFour", scopes, "createdById", "lastUsedAt", "revokedAt", "createdAt", "expiresAt") FROM stdin;
\.


--
-- Data for Name: integration_connections; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.integration_connections (id, "restaurantId", provider, enabled, status, "externalAccountId", "credentialsEnc", config, "lastSyncAt", "lastSuccessAt", "lastError", "createdById", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: integration_logs; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.integration_logs (id, "connectionId", level, event, message, "createdAt") FROM stdin;
\.


--
-- Data for Name: kitchen_stations; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.kitchen_stations (id, "branchId", name, "printerName") FROM stdin;
demo-station-main	demo-branch	Main Kitchen	\N
demo-station-bar	demo-branch	Bar	\N
\.


--
-- Data for Name: kot_items; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.kot_items (id, "kotId", "orderItemId", status) FROM stdin;
demo-order-takeaway-1-kot-1-demo-order-takeaway-1-item-0	demo-order-takeaway-1-kot-1	demo-order-takeaway-1-item-0	NEW
demo-order-takeaway-1-kot-2-demo-order-takeaway-1-item-1	demo-order-takeaway-1-kot-2	demo-order-takeaway-1-item-1	NEW
demo-order-takeaway-2-kot-1-demo-order-takeaway-2-item-0	demo-order-takeaway-2-kot-1	demo-order-takeaway-2-item-0	SERVED
demo-order-takeaway-2-kot-2-demo-order-takeaway-2-item-1	demo-order-takeaway-2-kot-2	demo-order-takeaway-2-item-1	SERVED
\.


--
-- Data for Name: kots; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.kots (id, "orderId", "stationId", "ticketNumber", status, "isPriority", "printedCount", "createdAt", "acceptedAt", "readyAt", "servedAt", "printedAt", "lastPrintError", "acceptedById", "rejectedAt", "rejectedById", "rejectReason") FROM stdin;
demo-order-takeaway-1-kot-1	demo-order-takeaway-1	demo-station-main	TA-DEMO-0001-1	NEW	f	0	2026-11-18 06:17:37.933	\N	\N	\N	\N	\N	\N	\N	\N	\N
demo-order-takeaway-1-kot-2	demo-order-takeaway-1	demo-station-bar	TA-DEMO-0001-2	NEW	f	0	2026-11-18 06:17:37.94	\N	\N	\N	\N	\N	\N	\N	\N	\N
demo-order-takeaway-2-kot-1	demo-order-takeaway-2	demo-station-main	TA-DEMO-0002-1	SERVED	f	0	2026-11-18 06:17:37.955	2026-11-18 06:17:37.954	2026-11-18 06:17:37.954	2026-11-18 06:17:37.954	\N	\N	\N	\N	\N	\N
demo-order-takeaway-2-kot-2	demo-order-takeaway-2	demo-station-bar	TA-DEMO-0002-2	SERVED	f	0	2026-11-18 06:17:37.959	2026-11-18 06:17:37.958	2026-11-18 06:17:37.958	2026-11-18 06:17:37.958	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: leave_requests; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.leave_requests (id, "branchId", "userId", type, "startDate", "endDate", reason, status, "decidedById", "decidedAt", "createdAt") FROM stdin;
\.


--
-- Data for Name: licenses; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.licenses (id, "restaurantId", status, "validFrom", "validUntil", "gracePeriodDays", "maxBranches", "maxUsers", "enabledModules", notes, "createdAt", "updatedAt") FROM stdin;
cmwlqbuwz001zs05fydrqbutq	demo-restaurant	ACTIVE	2026-11-18 06:17:37.859	2027-11-18 06:17:37.858	3	5	50	{POS,ORDERS,TABLES,RESERVATIONS,MENU,KDS,CUSTOMERS,INVENTORY,DELIVERY,TEAM,ACCOUNTING,REPORTS,MARKETING,OPERATIONS,ATTENDANCE,SETTINGS,VERIFACTU,INTEGRATIONS}	\N	2026-11-18 06:17:37.859	2026-11-18 06:17:37.859
\.


--
-- Data for Name: location_transfers; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.location_transfers (id, "branchId", "ingredientId", "fromLocationId", "toLocationId", quantity, note, "idempotencyKey", "createdById", "createdAt") FROM stdin;
\.


--
-- Data for Name: menu_categories; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.menu_categories (id, "branchId", name, "sortOrder", "isActive", "showOnWebsite") FROM stdin;
demo-cat-starters	demo-branch	Starters	0	t	t
demo-cat-mains	demo-branch	Main Course	1	t	t
demo-cat-drinks	demo-branch	Drinks	2	t	t
\.


--
-- Data for Name: menu_item_costings; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.menu_item_costings (id, "branchId", "menuItemId", "batchOutputQty", overheads, "halfPortionRatio", "targetMarginPercent", "targetMarkupPercent", "alertDropPoints", "baselineCost", "baselineAt", version, "updatedById", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: menu_item_modifier_groups; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.menu_item_modifier_groups ("menuItemId", "modifierGroupId", "sortOrder") FROM stdin;
demo-item-margherita	demo-mg-crust	0
\.


--
-- Data for Name: menu_items; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.menu_items (id, "branchId", "categoryId", "stationId", name, sku, description, "imageUrl", price, "taxRatePercent", "costPrice", "prepTimeMinutes", calories, "isVeg", "isVegan", "isJain", "isHalal", "isGlutenFree", "spiceLevel", allergens, "availableFrom", "availableTo", "isSeasonal", "seasonStart", "seasonEnd", barcode, "isActive", "isCombo", "sortOrder", "createdAt", "updatedAt", "inventoryTracking", "stockIngredientId", "stockQuantityPerSale", "halfPrice") FROM stdin;
demo-item-paneer-tikka	demo-branch	demo-cat-starters	demo-station-main	Paneer Tikka	\N	\N	\N	280.00	5.00	\N	\N	\N	t	f	f	f	f	NONE	{}	\N	\N	f	\N	\N	\N	t	f	0	2026-11-18 06:17:37.903	2026-11-18 06:17:37.903	NONE	\N	1.000	\N
demo-item-chicken-65	demo-branch	demo-cat-starters	demo-station-main	Chicken 65	\N	\N	\N	320.00	5.00	\N	\N	\N	f	f	f	f	f	NONE	{}	\N	\N	f	\N	\N	\N	t	f	0	2026-11-18 06:17:37.908	2026-11-18 06:17:37.908	NONE	\N	1.000	\N
demo-item-margherita	demo-branch	demo-cat-mains	demo-station-main	Margherita Pizza	\N	\N	\N	420.00	5.00	\N	\N	\N	t	f	f	f	f	NONE	{}	\N	\N	f	\N	\N	\N	t	f	0	2026-11-18 06:17:37.91	2026-11-18 06:17:37.91	NONE	\N	1.000	\N
demo-item-butter-chicken	demo-branch	demo-cat-mains	demo-station-main	Butter Chicken	\N	\N	\N	480.00	5.00	\N	\N	\N	f	f	f	f	f	NONE	{}	\N	\N	f	\N	\N	\N	t	f	0	2026-11-18 06:17:37.914	2026-11-18 06:17:37.914	NONE	\N	1.000	\N
demo-item-mojito	demo-branch	demo-cat-drinks	demo-station-bar	Virgin Mojito	\N	\N	\N	220.00	18.00	\N	\N	\N	t	f	f	f	f	NONE	{}	\N	\N	f	\N	\N	\N	t	f	0	2026-11-18 06:17:37.916	2026-11-18 06:17:37.916	NONE	\N	1.000	\N
demo-item-cola	demo-branch	demo-cat-drinks	demo-station-bar	Coca-Cola	\N	\N	\N	90.00	18.00	\N	\N	\N	t	f	f	f	f	NONE	{}	\N	\N	f	\N	\N	\N	t	f	0	2026-11-18 06:17:37.919	2026-11-18 06:17:37.919	NONE	\N	1.000	\N
\.


--
-- Data for Name: menu_price_changes; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.menu_price_changes (id, "branchId", "menuItemId", "oldPrice", "newPrice", "changedById", "changedAt", source, "productionEntryId", "unitCostAtChange") FROM stdin;
\.


--
-- Data for Name: modifier_groups; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.modifier_groups (id, name, "minSelect", "maxSelect", "isRequired", "branchId") FROM stdin;
demo-mg-crust	Crust Type	1	1	t	demo-branch
\.


--
-- Data for Name: modifier_ingredients; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.modifier_ingredients (id, "modifierId", "ingredientId", quantity, unit) FROM stdin;
\.


--
-- Data for Name: modifiers; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.modifiers (id, "groupId", name, "priceAdjustment", "taxRatePercent", "kitchenNote", "isDefault", "sortOrder", "isActive") FROM stdin;
demo-mod-thin	demo-mg-crust	Thin Crust	0.00	\N	\N	t	0	t
demo-mod-thick	demo-mg-crust	Thick Crust	0.00	\N	\N	f	0	t
demo-mod-cheese	demo-mg-crust	Extra Cheese	60.00	\N	\N	f	0	t
\.


--
-- Data for Name: nfc_tags; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.nfc_tags (id, "publicRef", "branchId", "tableId", label, mode, status, uid, "keyVersion", "metaKeySealed", "fileKeySealed", "lastCounter", "lastAuthAt", "disabledAt", "disabledReason", "replacesId", "createdById", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: nfc_taps; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.nfc_taps (id, "tagId", "branchId", counter, result, "createdAt") FROM stdin;
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.notifications (id, "branchId", "recipientUserId", type, title, body, entity, "entityId", "readAt", "createdAt") FROM stdin;
\.


--
-- Data for Name: order_item_costs; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.order_item_costs ("orderItemId", "unitCost", "createdAt") FROM stdin;
\.


--
-- Data for Name: order_item_modifiers; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.order_item_modifiers (id, "orderItemId", "modifierId", "nameSnapshot", "priceAdjSnapshot") FROM stdin;
\.


--
-- Data for Name: order_item_stock_returns; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.order_item_stock_returns (id, "orderItemId", "refundId", quantity, "createdAt") FROM stdin;
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.order_items (id, "orderId", "menuItemId", "nameSnapshot", "unitPriceSnapshot", "taxRateSnapshot", quantity, "lineTotal", "kitchenNote", status, portion, "portionRatio") FROM stdin;
demo-order-takeaway-1-item-0	demo-order-takeaway-1	demo-item-chicken-65	Chicken 65	320.00	5.00	1	320.00	\N	NEW	\N	1.000
demo-order-takeaway-1-item-1	demo-order-takeaway-1	demo-item-cola	Coca-Cola	90.00	18.00	2	180.00	\N	NEW	\N	1.000
demo-order-takeaway-2-item-0	demo-order-takeaway-2	demo-item-butter-chicken	Butter Chicken	480.00	5.00	1	480.00	\N	SERVED	\N	1.000
demo-order-takeaway-2-item-1	demo-order-takeaway-2	demo-item-cola	Coca-Cola	90.00	18.00	1	90.00	\N	SERVED	\N	1.000
\.


--
-- Data for Name: order_ratings; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.order_ratings (id, "branchId", "orderId", stars, comment, "createdAt") FROM stdin;
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.orders (id, "branchId", "orderNumber", type, status, "tableId", "guestCount", "customerId", "createdById", subtotal, "discountAmount", "taxAmount", "totalAmount", notes, "createdAt", "updatedAt", "billedAt", "loyaltyDiscountAmount", "loyaltyPointsRedeemed", "tipAmount", "guestName", channel, acceptance, "deliveryZoneId", "deliveryFee", "deliveryAddress", "deliveryPincode", "deliveryPhone", "deliveryStatus", "driverId", "deliveryEtaAt", "deliveredAt", "scheduledFor", "couponCode", "promotionName", "clientRequestId", "cancelReason", "cancelledAt", "cancelledById", "cancelSource", "acceptedAt", "acceptedById", "discountType", "discountValue", "integrationKeyId", "clientRequestHash", "discountReason", "externalSource", "externalOrderId", "externalCustomerRef", "requestedRedeemPoints", "assignedAt", "deliveryFailedReason", "pickedUpAt", "deliveryLat", "deliveryLng", "deliveryPlace", "heldForPayment", "payIntent") FROM stdin;
demo-order-takeaway-1	demo-branch	TA-DEMO-0001	TAKEAWAY	OPEN	\N	\N	\N	cmwlqbuwn001vs05fpv8oagb7	500.00	0.00	42.70	500.00	\N	2026-11-18 06:17:37.922	2026-11-18 06:17:37.922	\N	0.00	0	0.00	\N	STAFF	NOT_REQUIRED	\N	0.00	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	0	\N	\N	\N	\N	\N	\N	f	\N
demo-order-takeaway-2	demo-branch	TA-DEMO-0002	TAKEAWAY	PAID	\N	\N	\N	cmwlqbuwn001vs05fpv8oagb7	570.00	0.00	36.59	570.00	\N	2026-11-18 06:17:37.945	2026-11-18 06:17:37.945	2026-11-18 06:17:37.944	0.00	0	0.00	\N	STAFF	NOT_REQUIRED	\N	0.00	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	0	\N	\N	\N	\N	\N	\N	f	\N
\.


--
-- Data for Name: payment_gateway_catalog; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.payment_gateway_catalog (id, "restaurantId", key, name, countries, integration, "docsUrl", adapter, notes, sources, "researchedAt", active, "updatedAt") FROM stdin;
cmwlpgp740000nw01c11ubz6i	\N	razorpay	Razorpay	{IN}	Hosted Payment Link	https://razorpay.com/docs/api/payments/payment-links/create-standard	razorpay	\N	{https://razorpay.com/docs/api/payments/payment-links/create-standard,https://razorpay.com/docs/webhooks/validate-test/}	2026-11-05	t	2026-11-18 06:17:29.727
cmwlpgp770001nw01yf1d3898	\N	cashfree	Cashfree Payments	{IN}	Hosted Payment Link	https://www.cashfree.com/docs/api-reference/payments/latest/payment-links/create-payment-link	cashfree	Needs the payer phone number for each link.	{https://www.cashfree.com/docs/api-reference/payments/latest/payment-links/create-payment-link}	2026-11-05	t	2026-11-18 06:17:29.731
cmwlpgp790002nw01fbi0jvif	\N	payu	PayU	{IN}	Hosted checkout	https://docs.payu.in/	\N	No OrderRestro integration yet: listed for reference only.	{https://www.business-standard.com/finance/news/payu-secures-final-rbi-approval-as-online-payment-aggregator-125051301470_1.html}	2026-11-05	t	2026-11-18 06:17:29.733
cmwlpgp7b0003nw01sc9lhw7h	\N	ccavenue	CCAvenue	{IN}	Hosted checkout	https://www.ccavenue.com/	\N	No OrderRestro integration yet: listed for reference only.	{https://www.ccavenue.com/pr/infibeam-avenues-receives-rbis-final-authorisation-for-payment-aggregator-licence}	2026-11-05	t	2026-11-18 06:17:29.735
cmwlpgp7d0004nw012x6f7kln	\N	billdesk	BillDesk	{IN}	Hosted checkout	https://www.billdesk.com/	\N	No OrderRestro integration yet: listed for reference only. RBI authorisation date was not confirmed from a primary source.	{https://www.medianama.com/2023/02/223-full-list-who-is-and-isnt-allowed-to-operate-as-a-payment-aggregator-in-india/}	2026-11-05	t	2026-11-18 06:17:29.736
cmwlpgp7e0005nw01je185rgy	\N	phonepe	PhonePe Payment Gateway	{IN}	Hosted checkout / payment links	https://developer.phonepe.com/payment-gateway	\N	No OrderRestro integration yet: listed for reference only. Off by default: onboarding requirements were not confirmed.	{https://developer.phonepe.com/payment-gateway}	2026-11-05	f	2026-11-18 06:17:29.738
cmwlpgp7f0006nw010iyyjn7w	\N	stripe	Stripe	{US,GB,ES}	Hosted Checkout page	https://docs.stripe.com/payments/checkout	stripe	Not listed for India: Stripe availability there was limited/invite-only in the sources checked.	{https://docs.stripe.com/api/checkout/sessions/create,https://docs.stripe.com/webhooks,https://wise.com/us/blog/stripe-international}	2026-11-05	t	2026-11-18 06:17:29.74
cmwlpgp7h0007nw017ddyq3wq	\N	paypal-braintree	PayPal / Braintree	{US,GB}	Hosted checkout / Drop-in	https://developer.paypal.com/braintree/docs	\N	No OrderRestro integration yet: listed for reference only.	{https://support.wix.com/en/article/setting-up-braintree-as-a-payment-gateway}	2026-11-05	t	2026-11-18 06:17:29.741
cmwlpgp7i0008nw01tbuw8sp3	\N	paypal	PayPal	{ES}	Hosted checkout	https://developer.paypal.com/docs/checkout/	\N	No OrderRestro integration yet: listed for reference only.	{https://developer.paypal.com/docs/checkout/advanced/eligibility}	2026-11-05	t	2026-11-18 06:17:29.743
cmwlpgp7j0009nw01q0o5351g	\N	square	Square	{US}	Hosted payment links	https://developer.squareup.com/docs	\N	No OrderRestro integration yet: listed for reference only. Country availability was not re-verified in this pass.	{}	2026-11-05	t	2026-11-18 06:17:29.744
cmwlpgp7k000anw013xmo5do4	\N	adyen	Adyen	{US,GB,ES}	Pay by Link / hosted checkout	https://docs.adyen.com/	\N	No OrderRestro integration yet: listed for reference only. Country availability was not re-verified in this pass.	{}	2026-11-05	t	2026-11-18 06:17:29.746
cmwlpgp7l000bnw016u6tn3ot	\N	worldpay	Worldpay	{US,GB}	Hosted payment pages	https://developer.worldpay.com/	\N	No OrderRestro integration yet: listed for reference only. Country availability was not re-verified in this pass.	{}	2026-11-05	t	2026-11-18 06:17:29.747
cmwlpgp7m000cnw01mg3y2f3o	\N	checkout-com	Checkout.com	{GB}	Hosted payment links	https://www.checkout.com/docs	\N	No OrderRestro integration yet: listed for reference only. UK headquartered; no merchant-country list was found.	{}	2026-11-05	t	2026-11-18 06:17:29.748
cmwlpgp7n000dnw016vsmv9tu	\N	redsys	Redsys	{ES}	TPV Virtual (redirect)	https://pagosonline.redsys.es/	\N	No OrderRestro integration yet: listed for reference only. Needs a contract with a Spanish acquiring bank.	{https://docs.monei.com/onboarding/connect-redsys-tpv-virtual/}	2026-11-05	t	2026-11-18 06:17:29.75
cmwlpgp7o000enw0149musrgh	\N	paycomet	PAYCOMET	{ES}	Hosted payment page	https://docs.paycomet.com/	\N	No OrderRestro integration yet: listed for reference only. Authorised by the Bank of Spain per its own site.	{https://paycomet.com/en/payment-methods/spain}	2026-11-05	t	2026-11-18 06:17:29.751
\.


--
-- Data for Name: payment_gateway_connections; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.payment_gateway_connections (id, "restaurantId", provider, country, enabled, mode, "liveConfirmedAt", "liveConfirmedById", "testCredentialsEnc", "liveCredentialsEnc", "testKeys", "liveKeys", "lastError", "lastTestedAt", "lastTestOk", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.payments (id, "orderId", method, amount, reference, "createdAt", tendered, "changeGiven", "createdById", "clientRequestId") FROM stdin;
cmwlqbuzd002gs05frh7wcqgb	demo-order-takeaway-2	CASH	570.00	\N	2026-11-18 06:17:37.945	\N	\N	\N	\N
\.


--
-- Data for Name: payroll_lines; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.payroll_lines (id, "runId", "userId", "hoursWorked", "basePay", "tipShare", "unpaidLeaveDeduction", "netPay", allowances, bonus, "advanceRecovery", "otherDeductions", "adjustmentNote", "calcInputs", "overtimeHours", "overtimePay", "absenceDeduction", "absentDays", "lateDeduction", "lateMinutes") FROM stdin;
\.


--
-- Data for Name: payroll_runs; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.payroll_runs (id, "branchId", "periodStart", "periodEnd", status, "tipPool", "totalNet", "createdAt", "finalizedAt", "paidAt", "paidById", "paymentMethod", "paymentRef") FROM stdin;
\.


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.permissions (id, key, label, category) FROM stdin;
cmwlpgp8k0019nw01n0errkru	staff.manage	Manage Staff Schedules, Leave & Payroll	Staff
cmwlpgp8l001anw01ke0joioe	accounting.manage	Manage Accounting	Accounting
cmwlpgp8l001bnw01sh5z5uq3	marketing.manage	Manage Coupons, Promotions & Campaigns	Marketing
cmwlpgp8m001cnw01du2ns7dr	operations.manage	Manage Equipment & Documents	Operations
cmwlpgp84000jnw018z15uscq	orders.cancel	Cancel Orders	Orders
perm_orders_accept	orders.accept	Accept / Decline Incoming Orders	Orders
cmwlpgp85000lnw017lplbc56	discounts.apply	Apply Discounts	Orders
cmwlpgp86000mnw01253w6qlu	discounts.unlimited	Discount Above the Cashier Limit	Orders
cmwlpgp8m001dnw01fduhr9ev	system.update	Manage App Updates	Admin
cmwlpgp8n001enw01ob9efzll	production.record	Record Daily Production & Food Waste	Inventory
cmwlpgp8o001fnw01huwy005t	production.void	Reverse Production & Approve Food Waste	Inventory
cmwlpgp8p001gnw01me1sc38x	production.post	Post Production Batches (drafting needs only Record)	Inventory
cmwlpgp8q001hnw01qmzujrc9	production.report	View Manufacturing Reports	Inventory
cmwlpgp8r001inw01dto0zep1	production.quality	Record Batch Quality Inspection Results	Inventory
cmwlpgp8s001jnw01fvamodnh	menu.price	Change Menu Selling Prices from the Stock Journal	Menu
cmwlpgp8t001knw01qrkaey5m	nfc.manage	Manage NFC Table Tags & Table Ordering Mode	Tables
cmwlpgp8u001lnw013g3lun2y	table.session	Open & Close Table Sessions (guest ordering codes)	Tables
cmwlpgp8v001mnw01lvz3ljhs	ratings.view	View Customer Ratings	CRM
cmwlpgp81000fnw01d68blnyn	sales.view	View Sales	Sales
perm_dashboard_sales_view	dashboard.sales.view	View Dashboard Revenue & Sales Reports	Sales
cmwlpgp83000hnw014qggaxax	orders.create	Create Orders	Orders
cmwlpgp83000inw01s4sz0tlj	orders.edit	Edit Orders	Orders
cmwlpgp86000nnw01ru3cnc5a	refunds.process	Process Refunds	Orders
cmwlpgp87000onw01x0bqc2mf	orders.delete	Delete Past Transactions (admin password)	Orders
cmwlpgp87000pnw01ugbnrir8	bills.print	Print Bills	Orders
perm_tables_view	tables.view	View Floors & Tables (read-only)	Tables
cmwlpgp88000rnw01s0jhi9p5	tables.manage	Manage Tables	Tables
perm_menu_view	menu.view	View Menu (read-only)	Menu
cmwlpgp8a000tnw01yldwmgz7	menu.manage	Manage Menu	Menu
cmwlpgp8a000unw017r8nbiao	inventory.manage	Manage Inventory	Inventory
cmwlpgp8b000vnw01f2rfo6ai	reports.access	Access Reports	Reports
cmwlpgp8b000wnw01oakgphbj	users.manage	Manage Users	Admin
cmwlpgp8c000xnw01qddxpzly	reports.financial.view	View Financial Reports	Reports
cmwlpgp8c000ynw01q07q4i6a	data.export	Export Data	Reports
cmwlpgp8d000znw01s4ljwknf	kds.manage	Manage Kitchen Display	Kitchen
cmwlpgp8d0010nw01vn3altdv	reservations.manage	Manage Reservations	Reservations
cmwlpgp8e0011nw013937knsz	settings.manage	Manage Settings	Admin
cmwlpgp8f0012nw01hdma2b3d	customers.manage	Manage Customers & Loyalty	CRM
cmwlpgp8f0013nw016c067doc	audit_log.view	View Audit Log	Admin
cmwlpgp8g0014nw01n16s3o2c	roles.manage	Manage Roles	Admin
cmwlpgp8g0015nw017ffb9fnf	backup.manage	Manage Backups	Admin
cmwlpgp8h0016nw01pc3vry44	attendance.manage	Manage Staff Attendance	Staff
cmwlpgp8h0017nw01tvei4p27	delivery.manage	Manage Deliveries	Delivery
cmwlpgp8i0018nw01rog8prxd	delivery.rider	Use the Rider App (own deliveries)	Delivery
\.


--
-- Data for Name: phone_till_closings; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.phone_till_closings (id, "branchId", "deviceId", "deviceName", "businessDate", "openingFloat", "cashSales", "cashRefunds", "cashExpenses", "expectedCash", "countedCash", variance, "netSales", "closedByName", "closedAt", "syncedById", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: points_ledger; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.points_ledger (id, "branchId", "customerId", delta, reason, "referralId", "orderId", "idempotencyKey", "createdAt") FROM stdin;
\.


--
-- Data for Name: pos_devices; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.pos_devices (id, "restaurantId", "userId", "deviceId", name, platform, "appVersion", "enrolledAt", "lastSeenAt", "lastSyncAt", "pendingCount", "failedCount", "lastError", "revokedAt", "revokedById") FROM stdin;
\.


--
-- Data for Name: preparation_lines; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.preparation_lines (id, "preparationId", "ingredientId", quantity, unit) FROM stdin;
\.


--
-- Data for Name: preparations; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.preparations (id, "branchId", "outputIngredientId", "batchOutputQty", overheads, version, "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: product_recipe_lines; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.product_recipe_lines (id, "recipeId", "ingredientId", quantity, unit) FROM stdin;
\.


--
-- Data for Name: product_recipes; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.product_recipes (id, "branchId", "outputIngredientId", name, "baseOutputQty", version, "isActive", notes, "createdById", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: production_costs; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.production_costs (id, "entryId", category, description, amount, included) FROM stdin;
\.


--
-- Data for Name: production_entries; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.production_entries (id, "branchId", "entryNo", status, "producedAt", shift, location, "batchRef", notes, "responsibleId", "idempotencyKey", "deviceId", "correctsEntryId", "createdById", "createdAt", "postedById", "postedAt", "voidedById", "voidedAt", "voidReason", "additionalCost", costed, "expectedPrice", "expiryDate", "ingredientCost", "manufacturedOn", "priceChangeId", "priceMenuItemId", "proposedPrice", "totalCost", "unitCost", "menuItemId", "sellingPriceAtPost", "qualityResult", "qualityGrade", "qualityNotes", "qualityById", "qualityAt", "allocationMethod", "recipeId", "recipeKind", "recipeName", "recipeSnapshot", "sourcePoId", "sourcePoNumber", "sourceSupplier") FROM stdin;
\.


--
-- Data for Name: production_lines; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.production_lines (id, "entryId", role, "ingredientId", "enteredQuantity", "enteredUnit", quantity, "lineCost", "unitRate", "allocatedCost", "allocationPercent", "directToIngredientId", "expectedQuantity", "goodUnitCost", "locationId", "locationName", "lotNumber", "rejectedQuantity") FROM stdin;
\.


--
-- Data for Name: production_runs; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.production_runs (id, "branchId", "preparationId", "idempotencyKey", batches, "outputQty", "ingredientCost", "overheadCost", "totalCost", "unitCost", note, "createdById", "createdAt") FROM stdin;
\.


--
-- Data for Name: promotions; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.promotions (id, "branchId", name, kind, value, "daysOfWeek", "startMinute", "endMinute", "isActive", "createdAt") FROM stdin;
\.


--
-- Data for Name: public_order_keys; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.public_order_keys (id, "branchId", key, "orderId", "createdAt") FROM stdin;
\.


--
-- Data for Name: purchase_order_items; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.purchase_order_items (id, "purchaseOrderId", "ingredientId", "quantityOrdered", "unitCost", "quantityReceived") FROM stdin;
\.


--
-- Data for Name: purchase_orders; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.purchase_orders (id, "branchId", "supplierId", "poNumber", status, "expectedDate", notes, "totalAmount", "createdById", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: purchase_request_items; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.purchase_request_items (id, "purchaseRequestId", "ingredientId", "quantityRequested", notes) FROM stdin;
\.


--
-- Data for Name: purchase_requests; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.purchase_requests (id, "branchId", "requestNumber", status, notes, "requestedById", "approvedById", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: recipe_ingredients; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.recipe_ingredients (id, "menuItemId", "ingredientId", quantity, "createdAt", "updatedAt", unit) FROM stdin;
\.


--
-- Data for Name: referrals; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.referrals (id, "branchId", code, "referrerId", "referredId", "sharedItemId", status, "referrerPoints", "referredPoints", "qualifyingOrderId", "rewardedAt", "createdAt") FROM stdin;
\.


--
-- Data for Name: refunds; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.refunds (id, "orderId", amount, reason, method, "createdById", "createdAt", "clientRequestId") FROM stdin;
\.


--
-- Data for Name: report_schedules; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.report_schedules (id, "branchId", "reportKey", frequency, format, recipients, "isActive", "lastSentAt", "lastError", "createdAt") FROM stdin;
\.


--
-- Data for Name: reservations; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.reservations (id, "branchId", "customerName", phone, email, "guestCount", "reservedAt", "durationMinutes", "tableId", "specialRequests", deposit, status, "reminderSentAt", "createdAt", "updatedAt", channel) FROM stdin;
\.


--
-- Data for Name: restaurants; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.restaurants (id, name, "legalName", currency, timezone, "createdAt", "updatedAt", "loyaltyEarnPerCurrency", "loyaltyPointValue", "logoUrl", "upiVpa", "upiPayeeName", "maxManualDiscountPercent", "requireDiscountReason", "referralEnabled", "referralReferredPoints", "referralSharerPoints", "onlineMinOrderAmount", "referralMinPurchase", "onlinePriceAdjustKind", "onlinePriceAdjustValue", "manufacturingEnabled", "requireTableSession", "autoTableSessions", "nfcTablesEnabled") FROM stdin;
cmwlph925002vnw01igutco9z	Hello	\N	INR	Asia/Kolkata	2026-11-18 05:53:49.854	2026-11-18 05:53:49.854	100	1.00	\N	\N	\N	100.00	f	f	10	15	0.00	200.00	PERCENT	0.00	f	t	f	f
demo-restaurant	Nodedr Bistro (Demo)	\N	INR	Asia/Kolkata	2026-11-18 06:17:36.649	2026-11-18 06:17:36.649	100	1.00	\N	\N	\N	100.00	f	f	10	15	0.00	200.00	PERCENT	0.00	f	t	f	f
\.


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.role_permissions ("roleId", "permissionId") FROM stdin;
cmwlph92a002znw01i06m723i	cmwlpgp81000fnw01d68blnyn
cmwlph92a002znw01i06m723i	perm_dashboard_sales_view
cmwlph92a002znw01i06m723i	cmwlpgp83000hnw014qggaxax
cmwlph92a002znw01i06m723i	cmwlpgp83000inw01s4sz0tlj
cmwlph92a002znw01i06m723i	cmwlpgp84000jnw018z15uscq
cmwlph92a002znw01i06m723i	perm_orders_accept
cmwlph92a002znw01i06m723i	cmwlpgp85000lnw017lplbc56
cmwlph92a002znw01i06m723i	cmwlpgp86000mnw01253w6qlu
cmwlph92a002znw01i06m723i	cmwlpgp86000nnw01ru3cnc5a
cmwlph92a002znw01i06m723i	cmwlpgp87000onw01x0bqc2mf
cmwlph92a002znw01i06m723i	cmwlpgp87000pnw01ugbnrir8
cmwlph92a002znw01i06m723i	perm_tables_view
cmwlph92a002znw01i06m723i	cmwlpgp88000rnw01s0jhi9p5
cmwlph92a002znw01i06m723i	perm_menu_view
cmwlph92a002znw01i06m723i	cmwlpgp8a000tnw01yldwmgz7
cmwlph92a002znw01i06m723i	cmwlpgp8a000unw017r8nbiao
cmwlph92a002znw01i06m723i	cmwlpgp8b000vnw01f2rfo6ai
cmwlph92a002znw01i06m723i	cmwlpgp8b000wnw01oakgphbj
cmwlph92a002znw01i06m723i	cmwlpgp8c000xnw01qddxpzly
cmwlph92a002znw01i06m723i	cmwlpgp8c000ynw01q07q4i6a
cmwlph92a002znw01i06m723i	cmwlpgp8d000znw01s4ljwknf
cmwlph92a002znw01i06m723i	cmwlpgp8d0010nw01vn3altdv
cmwlph92a002znw01i06m723i	cmwlpgp8e0011nw013937knsz
cmwlph92a002znw01i06m723i	cmwlpgp8f0012nw01hdma2b3d
cmwlph92a002znw01i06m723i	cmwlpgp8f0013nw016c067doc
cmwlph92a002znw01i06m723i	cmwlpgp8g0014nw01n16s3o2c
cmwlph92a002znw01i06m723i	cmwlpgp8g0015nw017ffb9fnf
cmwlph92a002znw01i06m723i	cmwlpgp8h0016nw01pc3vry44
cmwlph92a002znw01i06m723i	cmwlpgp8h0017nw01tvei4p27
cmwlph92a002znw01i06m723i	cmwlpgp8i0018nw01rog8prxd
cmwlph92a002znw01i06m723i	cmwlpgp8k0019nw01n0errkru
cmwlph92a002znw01i06m723i	cmwlpgp8l001anw01ke0joioe
cmwlph92a002znw01i06m723i	cmwlpgp8l001bnw01sh5z5uq3
cmwlph92a002znw01i06m723i	cmwlpgp8m001cnw01du2ns7dr
cmwlph92a002znw01i06m723i	cmwlpgp8m001dnw01fduhr9ev
cmwlph92a002znw01i06m723i	cmwlpgp8n001enw01ob9efzll
cmwlph92a002znw01i06m723i	cmwlpgp8o001fnw01huwy005t
cmwlph92a002znw01i06m723i	cmwlpgp8p001gnw01me1sc38x
cmwlph92a002znw01i06m723i	cmwlpgp8q001hnw01qmzujrc9
cmwlph92a002znw01i06m723i	cmwlpgp8r001inw01dto0zep1
cmwlph92a002znw01i06m723i	cmwlpgp8s001jnw01fvamodnh
cmwlph92a002znw01i06m723i	cmwlpgp8t001knw01qrkaey5m
cmwlph92a002znw01i06m723i	cmwlpgp8u001lnw013g3lun2y
cmwlph92a002znw01i06m723i	cmwlpgp8v001mnw01lvz3ljhs
cmwlph92d0031nw01k4amxtgo	cmwlpgp81000fnw01d68blnyn
cmwlph92d0031nw01k4amxtgo	perm_dashboard_sales_view
cmwlph92d0031nw01k4amxtgo	cmwlpgp83000hnw014qggaxax
cmwlph92d0031nw01k4amxtgo	cmwlpgp83000inw01s4sz0tlj
cmwlph92d0031nw01k4amxtgo	cmwlpgp84000jnw018z15uscq
cmwlph92d0031nw01k4amxtgo	perm_orders_accept
cmwlph92d0031nw01k4amxtgo	cmwlpgp85000lnw017lplbc56
cmwlph92d0031nw01k4amxtgo	cmwlpgp86000mnw01253w6qlu
cmwlph92d0031nw01k4amxtgo	cmwlpgp86000nnw01ru3cnc5a
cmwlph92d0031nw01k4amxtgo	cmwlpgp87000onw01x0bqc2mf
cmwlph92d0031nw01k4amxtgo	cmwlpgp87000pnw01ugbnrir8
cmwlph92d0031nw01k4amxtgo	perm_tables_view
cmwlph92d0031nw01k4amxtgo	cmwlpgp88000rnw01s0jhi9p5
cmwlph92d0031nw01k4amxtgo	perm_menu_view
cmwlph92d0031nw01k4amxtgo	cmwlpgp8a000tnw01yldwmgz7
cmwlph92d0031nw01k4amxtgo	cmwlpgp8a000unw017r8nbiao
cmwlph92d0031nw01k4amxtgo	cmwlpgp8b000vnw01f2rfo6ai
cmwlph92d0031nw01k4amxtgo	cmwlpgp8b000wnw01oakgphbj
cmwlph92d0031nw01k4amxtgo	cmwlpgp8c000xnw01qddxpzly
cmwlph92d0031nw01k4amxtgo	cmwlpgp8c000ynw01q07q4i6a
cmwlph92d0031nw01k4amxtgo	cmwlpgp8d000znw01s4ljwknf
cmwlph92d0031nw01k4amxtgo	cmwlpgp8d0010nw01vn3altdv
cmwlph92d0031nw01k4amxtgo	cmwlpgp8e0011nw013937knsz
cmwlph92d0031nw01k4amxtgo	cmwlpgp8f0012nw01hdma2b3d
cmwlph92d0031nw01k4amxtgo	cmwlpgp8f0013nw016c067doc
cmwlph92d0031nw01k4amxtgo	cmwlpgp8g0014nw01n16s3o2c
cmwlph92d0031nw01k4amxtgo	cmwlpgp8g0015nw017ffb9fnf
cmwlph92d0031nw01k4amxtgo	cmwlpgp8h0016nw01pc3vry44
cmwlph92d0031nw01k4amxtgo	cmwlpgp8h0017nw01tvei4p27
cmwlph92d0031nw01k4amxtgo	cmwlpgp8i0018nw01rog8prxd
cmwlph92d0031nw01k4amxtgo	cmwlpgp8k0019nw01n0errkru
cmwlph92d0031nw01k4amxtgo	cmwlpgp8l001anw01ke0joioe
cmwlph92d0031nw01k4amxtgo	cmwlpgp8l001bnw01sh5z5uq3
cmwlph92d0031nw01k4amxtgo	cmwlpgp8m001cnw01du2ns7dr
cmwlph92d0031nw01k4amxtgo	cmwlpgp8m001dnw01fduhr9ev
cmwlph92d0031nw01k4amxtgo	cmwlpgp8n001enw01ob9efzll
cmwlph92d0031nw01k4amxtgo	cmwlpgp8o001fnw01huwy005t
cmwlph92d0031nw01k4amxtgo	cmwlpgp8p001gnw01me1sc38x
cmwlph92d0031nw01k4amxtgo	cmwlpgp8q001hnw01qmzujrc9
cmwlph92d0031nw01k4amxtgo	cmwlpgp8r001inw01dto0zep1
cmwlph92d0031nw01k4amxtgo	cmwlpgp8s001jnw01fvamodnh
cmwlph92d0031nw01k4amxtgo	cmwlpgp8t001knw01qrkaey5m
cmwlph92d0031nw01k4amxtgo	cmwlpgp8u001lnw013g3lun2y
cmwlph92d0031nw01k4amxtgo	cmwlpgp8v001mnw01lvz3ljhs
cmwlph92f0033nw015cp3msu1	cmwlpgp81000fnw01d68blnyn
cmwlph92f0033nw015cp3msu1	cmwlpgp83000hnw014qggaxax
cmwlph92f0033nw015cp3msu1	cmwlpgp83000inw01s4sz0tlj
cmwlph92f0033nw015cp3msu1	cmwlpgp84000jnw018z15uscq
cmwlph92f0033nw015cp3msu1	perm_orders_accept
cmwlph92f0033nw015cp3msu1	cmwlpgp85000lnw017lplbc56
cmwlph92f0033nw015cp3msu1	cmwlpgp86000mnw01253w6qlu
cmwlph92f0033nw015cp3msu1	cmwlpgp87000pnw01ugbnrir8
cmwlph92f0033nw015cp3msu1	cmwlpgp88000rnw01s0jhi9p5
cmwlph92f0033nw015cp3msu1	perm_tables_view
cmwlph92f0033nw015cp3msu1	cmwlpgp8a000tnw01yldwmgz7
cmwlph92f0033nw015cp3msu1	perm_menu_view
cmwlph92f0033nw015cp3msu1	cmwlpgp8a000unw017r8nbiao
cmwlph92f0033nw015cp3msu1	cmwlpgp8b000vnw01f2rfo6ai
cmwlph92f0033nw015cp3msu1	cmwlpgp8d000znw01s4ljwknf
cmwlph92f0033nw015cp3msu1	cmwlpgp8d0010nw01vn3altdv
cmwlph92f0033nw015cp3msu1	cmwlpgp8f0012nw01hdma2b3d
cmwlph92f0033nw015cp3msu1	cmwlpgp86000nnw01ru3cnc5a
cmwlph92f0033nw015cp3msu1	cmwlpgp8h0016nw01pc3vry44
cmwlph92f0033nw015cp3msu1	cmwlpgp8h0017nw01tvei4p27
cmwlph92f0033nw015cp3msu1	cmwlpgp8k0019nw01n0errkru
cmwlph92f0033nw015cp3msu1	cmwlpgp8l001anw01ke0joioe
cmwlph92f0033nw015cp3msu1	cmwlpgp8l001bnw01sh5z5uq3
cmwlph92f0033nw015cp3msu1	cmwlpgp8m001cnw01du2ns7dr
cmwlph92f0033nw015cp3msu1	cmwlpgp8s001jnw01fvamodnh
cmwlph92f0033nw015cp3msu1	cmwlpgp8u001lnw013g3lun2y
cmwlph92f0033nw015cp3msu1	cmwlpgp8v001mnw01lvz3ljhs
cmwlph92f0033nw015cp3msu1	cmwlpgp8t001knw01qrkaey5m
cmwlph92h0035nw01bp7xom9h	cmwlpgp8u001lnw013g3lun2y
cmwlph92h0035nw01bp7xom9h	cmwlpgp83000hnw014qggaxax
cmwlph92h0035nw01bp7xom9h	cmwlpgp83000inw01s4sz0tlj
cmwlph92h0035nw01bp7xom9h	perm_orders_accept
cmwlph92h0035nw01bp7xom9h	cmwlpgp87000pnw01ugbnrir8
cmwlph92h0035nw01bp7xom9h	cmwlpgp85000lnw017lplbc56
cmwlph92h0035nw01bp7xom9h	cmwlpgp81000fnw01d68blnyn
cmwlph92h0035nw01bp7xom9h	cmwlpgp8f0012nw01hdma2b3d
cmwlph92h0035nw01bp7xom9h	perm_dashboard_sales_view
cmwlph92h0035nw01bp7xom9h	perm_menu_view
cmwlph92h0035nw01bp7xom9h	perm_tables_view
cmwlph92i0037nw017ap3nsfv	cmwlpgp8u001lnw013g3lun2y
cmwlph92i0037nw017ap3nsfv	cmwlpgp83000hnw014qggaxax
cmwlph92i0037nw017ap3nsfv	cmwlpgp83000inw01s4sz0tlj
cmwlph92i0037nw017ap3nsfv	perm_orders_accept
cmwlph92i0037nw017ap3nsfv	perm_tables_view
cmwlph92i0037nw017ap3nsfv	perm_menu_view
cmwlph92i0037nw017ap3nsfv	cmwlpgp87000pnw01ugbnrir8
cmwlph92j0039nw019l8g62ok	cmwlpgp8d000znw01s4ljwknf
cmwlph92j0039nw019l8g62ok	perm_orders_accept
cmwlph92j0039nw019l8g62ok	cmwlpgp8n001enw01ob9efzll
cmwlph92j0039nw019l8g62ok	cmwlpgp8p001gnw01me1sc38x
cmwlph92k003bnw01nc7c37j7	cmwlpgp8d000znw01s4ljwknf
cmwlph92k003bnw01nc7c37j7	perm_orders_accept
cmwlph92k003bnw01nc7c37j7	cmwlpgp8a000tnw01yldwmgz7
cmwlph92k003bnw01nc7c37j7	perm_menu_view
cmwlph92k003bnw01nc7c37j7	cmwlpgp8n001enw01ob9efzll
cmwlph92k003bnw01nc7c37j7	cmwlpgp8p001gnw01me1sc38x
cmwlph92k003bnw01nc7c37j7	cmwlpgp8r001inw01dto0zep1
cmwlph92l003dnw01iefrwkf5	cmwlpgp83000hnw014qggaxax
cmwlph92l003dnw01iefrwkf5	perm_orders_accept
cmwlph92l003dnw01iefrwkf5	cmwlpgp8d000znw01s4ljwknf
cmwlph92l003dnw01iefrwkf5	perm_menu_view
cmwlph92l003dnw01iefrwkf5	perm_tables_view
cmwlph92m003fnw01zg9i2j58	cmwlpgp83000inw01s4sz0tlj
cmwlph92m003fnw01zg9i2j58	cmwlpgp8h0017nw01tvei4p27
cmwlph92m003fnw01zg9i2j58	cmwlpgp8i0018nw01rog8prxd
cmwlph92n003hnw01z0u7n446	cmwlpgp81000fnw01d68blnyn
cmwlph92n003hnw01z0u7n446	perm_dashboard_sales_view
cmwlph92n003hnw01z0u7n446	cmwlpgp8b000vnw01f2rfo6ai
cmwlph92n003hnw01z0u7n446	cmwlpgp8c000xnw01qddxpzly
cmwlph92n003hnw01z0u7n446	cmwlpgp8c000ynw01q07q4i6a
cmwlph92n003hnw01z0u7n446	cmwlpgp8l001anw01ke0joioe
cmwlph92o003jnw018e4k4ptp	cmwlpgp8a000unw017r8nbiao
cmwlph92o003jnw018e4k4ptp	cmwlpgp8b000vnw01f2rfo6ai
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp81000fnw01d68blnyn
cmwlqbtzm0019s05fvve3rcpv	perm_dashboard_sales_view
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp83000hnw014qggaxax
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp83000inw01s4sz0tlj
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp84000jnw018z15uscq
cmwlqbtzm0019s05fvve3rcpv	perm_orders_accept
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp85000lnw017lplbc56
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp86000mnw01253w6qlu
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp86000nnw01ru3cnc5a
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp87000onw01x0bqc2mf
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp87000pnw01ugbnrir8
cmwlqbtzm0019s05fvve3rcpv	perm_tables_view
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp88000rnw01s0jhi9p5
cmwlqbtzm0019s05fvve3rcpv	perm_menu_view
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8a000tnw01yldwmgz7
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8a000unw017r8nbiao
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8b000vnw01f2rfo6ai
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8b000wnw01oakgphbj
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8c000xnw01qddxpzly
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8c000ynw01q07q4i6a
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8d000znw01s4ljwknf
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8d0010nw01vn3altdv
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8e0011nw013937knsz
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8f0012nw01hdma2b3d
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8f0013nw016c067doc
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8g0014nw01n16s3o2c
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8g0015nw017ffb9fnf
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8h0016nw01pc3vry44
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8h0017nw01tvei4p27
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8i0018nw01rog8prxd
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8k0019nw01n0errkru
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8l001anw01ke0joioe
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8l001bnw01sh5z5uq3
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8m001cnw01du2ns7dr
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8m001dnw01fduhr9ev
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8n001enw01ob9efzll
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8o001fnw01huwy005t
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8p001gnw01me1sc38x
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8q001hnw01qmzujrc9
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8r001inw01dto0zep1
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8s001jnw01fvamodnh
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8t001knw01qrkaey5m
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8u001lnw013g3lun2y
cmwlqbtzm0019s05fvve3rcpv	cmwlpgp8v001mnw01lvz3ljhs
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp81000fnw01d68blnyn
cmwlqbtzw001bs05fmbbf9zzq	perm_dashboard_sales_view
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp83000hnw014qggaxax
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp83000inw01s4sz0tlj
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp84000jnw018z15uscq
cmwlqbtzw001bs05fmbbf9zzq	perm_orders_accept
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp85000lnw017lplbc56
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp86000mnw01253w6qlu
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp86000nnw01ru3cnc5a
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp87000onw01x0bqc2mf
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp87000pnw01ugbnrir8
cmwlqbtzw001bs05fmbbf9zzq	perm_tables_view
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp88000rnw01s0jhi9p5
cmwlqbtzw001bs05fmbbf9zzq	perm_menu_view
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8a000tnw01yldwmgz7
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8a000unw017r8nbiao
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8b000vnw01f2rfo6ai
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8b000wnw01oakgphbj
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8c000xnw01qddxpzly
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8c000ynw01q07q4i6a
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8d000znw01s4ljwknf
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8d0010nw01vn3altdv
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8e0011nw013937knsz
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8f0012nw01hdma2b3d
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8f0013nw016c067doc
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8g0014nw01n16s3o2c
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8g0015nw017ffb9fnf
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8h0016nw01pc3vry44
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8h0017nw01tvei4p27
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8i0018nw01rog8prxd
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8k0019nw01n0errkru
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8l001anw01ke0joioe
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8l001bnw01sh5z5uq3
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8m001cnw01du2ns7dr
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8m001dnw01fduhr9ev
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8n001enw01ob9efzll
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8o001fnw01huwy005t
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8p001gnw01me1sc38x
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8q001hnw01qmzujrc9
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8r001inw01dto0zep1
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8s001jnw01fvamodnh
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8t001knw01qrkaey5m
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8u001lnw013g3lun2y
cmwlqbtzw001bs05fmbbf9zzq	cmwlpgp8v001mnw01lvz3ljhs
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp81000fnw01d68blnyn
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp83000hnw014qggaxax
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp83000inw01s4sz0tlj
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp84000jnw018z15uscq
cmwlqbu04001ds05fr8lvx8wt	perm_orders_accept
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp85000lnw017lplbc56
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp86000mnw01253w6qlu
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp87000pnw01ugbnrir8
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp88000rnw01s0jhi9p5
cmwlqbu04001ds05fr8lvx8wt	perm_tables_view
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8a000tnw01yldwmgz7
cmwlqbu04001ds05fr8lvx8wt	perm_menu_view
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8a000unw017r8nbiao
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8b000vnw01f2rfo6ai
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8d000znw01s4ljwknf
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8d0010nw01vn3altdv
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8f0012nw01hdma2b3d
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp86000nnw01ru3cnc5a
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8h0016nw01pc3vry44
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8h0017nw01tvei4p27
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8k0019nw01n0errkru
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8l001anw01ke0joioe
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8l001bnw01sh5z5uq3
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8m001cnw01du2ns7dr
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8s001jnw01fvamodnh
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8u001lnw013g3lun2y
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8v001mnw01lvz3ljhs
cmwlqbu04001ds05fr8lvx8wt	cmwlpgp8t001knw01qrkaey5m
cmwlqbu0b001fs05fynn5hkhe	cmwlpgp8u001lnw013g3lun2y
cmwlqbu0b001fs05fynn5hkhe	cmwlpgp83000hnw014qggaxax
cmwlqbu0b001fs05fynn5hkhe	cmwlpgp83000inw01s4sz0tlj
cmwlqbu0b001fs05fynn5hkhe	perm_orders_accept
cmwlqbu0b001fs05fynn5hkhe	cmwlpgp87000pnw01ugbnrir8
cmwlqbu0b001fs05fynn5hkhe	cmwlpgp85000lnw017lplbc56
cmwlqbu0b001fs05fynn5hkhe	cmwlpgp81000fnw01d68blnyn
cmwlqbu0b001fs05fynn5hkhe	cmwlpgp8f0012nw01hdma2b3d
cmwlqbu0b001fs05fynn5hkhe	perm_dashboard_sales_view
cmwlqbu0b001fs05fynn5hkhe	perm_menu_view
cmwlqbu0b001fs05fynn5hkhe	perm_tables_view
cmwlqbu0g001hs05fxvmrf6nc	cmwlpgp8u001lnw013g3lun2y
cmwlqbu0g001hs05fxvmrf6nc	cmwlpgp83000hnw014qggaxax
cmwlqbu0g001hs05fxvmrf6nc	cmwlpgp83000inw01s4sz0tlj
cmwlqbu0g001hs05fxvmrf6nc	perm_orders_accept
cmwlqbu0g001hs05fxvmrf6nc	perm_tables_view
cmwlqbu0g001hs05fxvmrf6nc	perm_menu_view
cmwlqbu0g001hs05fxvmrf6nc	cmwlpgp87000pnw01ugbnrir8
cmwlqbu0l001js05f8k83kvv8	cmwlpgp8d000znw01s4ljwknf
cmwlqbu0l001js05f8k83kvv8	perm_orders_accept
cmwlqbu0l001js05f8k83kvv8	cmwlpgp8n001enw01ob9efzll
cmwlqbu0l001js05f8k83kvv8	cmwlpgp8p001gnw01me1sc38x
cmwlqbu0q001ls05fm4fizzoh	cmwlpgp8d000znw01s4ljwknf
cmwlqbu0q001ls05fm4fizzoh	perm_orders_accept
cmwlqbu0q001ls05fm4fizzoh	cmwlpgp8a000tnw01yldwmgz7
cmwlqbu0q001ls05fm4fizzoh	perm_menu_view
cmwlqbu0q001ls05fm4fizzoh	cmwlpgp8n001enw01ob9efzll
cmwlqbu0q001ls05fm4fizzoh	cmwlpgp8p001gnw01me1sc38x
cmwlqbu0q001ls05fm4fizzoh	cmwlpgp8r001inw01dto0zep1
cmwlqbu0u001ns05f8vpxy307	cmwlpgp83000hnw014qggaxax
cmwlqbu0u001ns05f8vpxy307	perm_orders_accept
cmwlqbu0u001ns05f8vpxy307	cmwlpgp8d000znw01s4ljwknf
cmwlqbu0u001ns05f8vpxy307	perm_menu_view
cmwlqbu0u001ns05f8vpxy307	perm_tables_view
cmwlqbu0y001ps05ftpcn7zxz	cmwlpgp83000inw01s4sz0tlj
cmwlqbu0y001ps05ftpcn7zxz	cmwlpgp8h0017nw01tvei4p27
cmwlqbu0y001ps05ftpcn7zxz	cmwlpgp8i0018nw01rog8prxd
cmwlqbu12001rs05fbsj8oopm	cmwlpgp81000fnw01d68blnyn
cmwlqbu12001rs05fbsj8oopm	perm_dashboard_sales_view
cmwlqbu12001rs05fbsj8oopm	cmwlpgp8b000vnw01f2rfo6ai
cmwlqbu12001rs05fbsj8oopm	cmwlpgp8c000xnw01qddxpzly
cmwlqbu12001rs05fbsj8oopm	cmwlpgp8c000ynw01q07q4i6a
cmwlqbu12001rs05fbsj8oopm	cmwlpgp8l001anw01ke0joioe
cmwlqbu17001ts05fj3cixm9y	cmwlpgp8a000unw017r8nbiao
cmwlqbu17001ts05fj3cixm9y	cmwlpgp8b000vnw01f2rfo6ai
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.roles (id, "restaurantId", name, label, "isSystem", "createdAt") FROM stdin;
cmwlph92a002znw01i06m723i	cmwlph925002vnw01igutco9z	OWNER	OWNER	t	2026-11-18 05:53:49.858
cmwlph92d0031nw01k4amxtgo	cmwlph925002vnw01igutco9z	ADMINISTRATOR	ADMINISTRATOR	t	2026-11-18 05:53:49.862
cmwlph92f0033nw015cp3msu1	cmwlph925002vnw01igutco9z	RESTAURANT_MANAGER	RESTAURANT MANAGER	t	2026-11-18 05:53:49.864
cmwlph92h0035nw01bp7xom9h	cmwlph925002vnw01igutco9z	CASHIER	CASHIER	t	2026-11-18 05:53:49.866
cmwlph92i0037nw017ap3nsfv	cmwlph925002vnw01igutco9z	WAITER	WAITER	t	2026-11-18 05:53:49.867
cmwlph92j0039nw019l8g62ok	cmwlph925002vnw01igutco9z	KITCHEN_STAFF	KITCHEN STAFF	t	2026-11-18 05:53:49.868
cmwlph92k003bnw01nc7c37j7	cmwlph925002vnw01igutco9z	CHEF	CHEF	t	2026-11-18 05:53:49.869
cmwlph92l003dnw01iefrwkf5	cmwlph925002vnw01igutco9z	BARTENDER	BARTENDER	t	2026-11-18 05:53:49.87
cmwlph92m003fnw01zg9i2j58	cmwlph925002vnw01igutco9z	DELIVERY_STAFF	DELIVERY STAFF	t	2026-11-18 05:53:49.871
cmwlph92n003hnw01z0u7n446	cmwlph925002vnw01igutco9z	ACCOUNTANT	ACCOUNTANT	t	2026-11-18 05:53:49.871
cmwlph92o003jnw018e4k4ptp	cmwlph925002vnw01igutco9z	INVENTORY_MANAGER	INVENTORY MANAGER	t	2026-11-18 05:53:49.872
cmwlqbtzm0019s05fvve3rcpv	demo-restaurant	OWNER	OWNER	t	2026-11-18 06:17:36.658
cmwlqbtzw001bs05fmbbf9zzq	demo-restaurant	ADMINISTRATOR	ADMINISTRATOR	t	2026-11-18 06:17:36.669
cmwlqbu04001ds05fr8lvx8wt	demo-restaurant	RESTAURANT_MANAGER	RESTAURANT MANAGER	t	2026-11-18 06:17:36.676
cmwlqbu0b001fs05fynn5hkhe	demo-restaurant	CASHIER	CASHIER	t	2026-11-18 06:17:36.683
cmwlqbu0g001hs05fxvmrf6nc	demo-restaurant	WAITER	WAITER	t	2026-11-18 06:17:36.689
cmwlqbu0l001js05f8k83kvv8	demo-restaurant	KITCHEN_STAFF	KITCHEN STAFF	t	2026-11-18 06:17:36.693
cmwlqbu0q001ls05fm4fizzoh	demo-restaurant	CHEF	CHEF	t	2026-11-18 06:17:36.698
cmwlqbu0u001ns05f8vpxy307	demo-restaurant	BARTENDER	BARTENDER	t	2026-11-18 06:17:36.702
cmwlqbu0y001ps05ftpcn7zxz	demo-restaurant	DELIVERY_STAFF	DELIVERY STAFF	t	2026-11-18 06:17:36.707
cmwlqbu12001rs05fbsj8oopm	demo-restaurant	ACCOUNTANT	ACCOUNTANT	t	2026-11-18 06:17:36.711
cmwlqbu17001ts05fj3cixm9y	demo-restaurant	INVENTORY_MANAGER	INVENTORY MANAGER	t	2026-11-18 06:17:36.715
\.


--
-- Data for Name: service_logs; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.service_logs (id, "equipmentId", "servicedAt", cost, note, "createdAt") FROM stdin;
\.


--
-- Data for Name: shifts; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.shifts (id, "branchId", "userId", "startsAt", "endsAt", note) FROM stdin;
\.


--
-- Data for Name: staff_api_keys; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.staff_api_keys (id, "userId", name, "tokenHash", "lastFour", "lastUsedAt", "revokedAt", "createdAt") FROM stdin;
\.


--
-- Data for Name: staff_pay; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.staff_pay ("userId", "payType", rate, "overtimeAfterHours", "overtimeMultiplier", "deductAbsence", "lateGraceMinutes") FROM stdin;
\.


--
-- Data for Name: stock_batches; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.stock_batches (id, "branchId", "ingredientId", "goodsReceiptItemId", "batchNumber", "quantityReceived", "quantityRemaining", "unitCost", "expiryDate", "receivedAt") FROM stdin;
\.


--
-- Data for Name: stock_journal_entries; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.stock_journal_entries (id, "branchId", "entryNo", type, status, "occurredAt", reason, notes, "idempotencyKey", "createdById", "createdAt", "updatedAt", "postedById", "postedAt", "voidedById", "voidedAt", "voidReason") FROM stdin;
\.


--
-- Data for Name: stock_journal_lines; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.stock_journal_lines (id, "entryId", "ingredientId", "sortOrder", direction, "enteredQuantity", "enteredUnit", quantity, "fromLocationId", "fromLocationName", "toLocationId", "toLocationName", "wasteReason", note, "unitCost", "wasteEntryId") FROM stdin;
\.


--
-- Data for Name: stock_levels; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.stock_levels (id, "ingredientId", "locationId", quantity, "updatedAt") FROM stdin;
\.


--
-- Data for Name: stock_locations; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.stock_locations (id, "branchId", name, "sortOrder", "isActive", "createdAt") FROM stdin;
\.


--
-- Data for Name: stock_movements; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.stock_movements (id, "branchId", "ingredientId", "batchId", type, quantity, note, "createdById", "createdAt", "orderId", "deviceId", "productionEntryId", "wasteEntryId", "locationId", "journalEntryId") FROM stdin;
\.


--
-- Data for Name: stock_takes; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.stock_takes (id, "branchId", "takenAt", area, note, "idempotencyKey", "deviceId", "createdById", "createdAt", lines) FROM stdin;
\.


--
-- Data for Name: stock_transfers; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.stock_transfers (id, "restaurantId", "fromBranchId", "toBranchId", "fromBranchName", "toBranchName", "ingredientName", unit, quantity, "unitCost", note, "createdById", "createdAt") FROM stdin;
\.


--
-- Data for Name: supplier_invoices; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.supplier_invoices (id, "branchId", "supplierId", "purchaseOrderId", "goodsReceiptId", "invoiceNumber", "invoiceDate", "dueDate", "totalAmount", "amountPaid", status, notes, "recordedById", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: supplier_payments; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.supplier_payments (id, "branchId", "supplierInvoiceId", amount, "paymentMethod", reference, "paidAt", "recordedById", "createdAt") FROM stdin;
\.


--
-- Data for Name: supplier_quotation_items; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.supplier_quotation_items (id, "supplierQuotationId", "ingredientId", "quantityQuoted", "unitPrice") FROM stdin;
\.


--
-- Data for Name: supplier_quotations; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.supplier_quotations (id, "branchId", "supplierId", "quotationNumber", status, "validUntil", notes, "createdById", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: suppliers; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.suppliers (id, "branchId", name, "contactName", phone, email, address, "gstNumber", notes, "isActive", "createdAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: sync_changes; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.sync_changes (seq, tbl, pk, "pkKey", op, "row", ts, origin) FROM stdin;
\.


--
-- Data for Name: sync_state; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.sync_state (id, enabled, role, "deviceId", "serverUrl", "apiKey", seeded, "lastPullSeq", "lastPushSeq", "lastSyncAt", "lastError", conflicts) FROM stdin;
1	f	client	a026e9f654e3b0865caca24d18d8255f	\N	\N	f	0	0	\N	\N	[]
\.


--
-- Data for Name: table_accesses; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.table_accesses (id, "tableId", "tagId", "tokenHash", "expiresAt", "lastUsedAt", "createdAt") FROM stdin;
\.


--
-- Data for Name: table_requests; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.table_requests (id, "branchId", "tableId", type, "createdAt", "resolvedAt") FROM stdin;
\.


--
-- Data for Name: table_session_grants; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.table_session_grants (id, "sessionId", "tokenHash", "createdAt") FROM stdin;
\.


--
-- Data for Name: table_sessions; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.table_sessions (id, "branchId", "tableId", status, "codeHash", "openedById", "openedAt", "expiresAt", "closedAt", "closedReason", "failedTries", "lockedUntil", "openedVia", "joinSecret") FROM stdin;
\.


--
-- Data for Name: tables; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.tables (id, "floorId", number, name, capacity, status, "posX", "posY", width, height, rotation, shape, color, "assignedWaiterId", notes, "qrToken", "createdAt", "updatedAt", "statusSince", hidden) FROM stdin;
cmwlqbux80021s05ft4ye88ee	demo-floor	1	Table 1	4	AVAILABLE	20	20	80	80	0	square	\N	\N	\N	\N	2026-11-18 06:17:37.869	2026-11-18 06:17:37.869	2026-11-18 06:17:37.869	f
cmwlqbuxc0023s05f0ey6f99j	demo-floor	2	Table 2	4	AVAILABLE	140	20	80	80	0	square	\N	\N	\N	\N	2026-11-18 06:17:37.872	2026-11-18 06:17:37.872	2026-11-18 06:17:37.872	f
cmwlqbuxe0025s05fenfaeclz	demo-floor	3	Table 3	6	AVAILABLE	260	20	80	80	0	square	\N	\N	\N	\N	2026-11-18 06:17:37.874	2026-11-18 06:17:37.874	2026-11-18 06:17:37.874	f
cmwlqbuxg0027s05fgh92cql5	demo-floor	4	Table 4	4	AVAILABLE	380	20	80	80	0	square	\N	\N	\N	\N	2026-11-18 06:17:37.877	2026-11-18 06:17:37.877	2026-11-18 06:17:37.877	f
cmwlqbuxi0029s05frkpt7njl	demo-floor	5	Table 5	4	AVAILABLE	20	140	80	80	0	square	\N	\N	\N	\N	2026-11-18 06:17:37.879	2026-11-18 06:17:37.879	2026-11-18 06:17:37.879	f
cmwlqbuxl002bs05fgg5qw8c8	demo-floor	6	Table 6	6	AVAILABLE	140	140	80	80	0	square	\N	\N	\N	\N	2026-11-18 06:17:37.881	2026-11-18 06:17:37.881	2026-11-18 06:17:37.881	f
cmwlqbuxn002ds05fevt3ptiw	demo-floor	7	Table 7	4	AVAILABLE	260	140	80	80	0	square	\N	\N	\N	\N	2026-11-18 06:17:37.884	2026-11-18 06:17:37.884	2026-11-18 06:17:37.884	f
cmwlqbuxp002fs05f9hr7jdb0	demo-floor	8	Table 8	4	AVAILABLE	380	140	80	80	0	square	\N	\N	\N	\N	2026-11-18 06:17:37.886	2026-11-18 06:17:37.886	2026-11-18 06:17:37.886	f
\.


--
-- Data for Name: user_branches; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.user_branches ("userId", "branchId") FROM stdin;
cmwlph92p003lnw01vzd35f50	cmwlph928002xnw0112sak74j
cmwlqbuws001xs05fga0dytq7	demo-branch
cmwlqbuwn001vs05fpv8oagb7	demo-branch
\.


--
-- Data for Name: user_permission_overrides; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.user_permission_overrides ("userId", "permissionId", effect, reason, "expiresAt", "createdAt") FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.users (id, "restaurantId", "roleId", name, email, phone, "passwordHash", "pinHash", "isActive", "twoFactorSecret", "createdAt", "updatedAt", "twoFactorEnabled", "twoFactorLastStep", "twoFactorRecoveryHashes", "dashboardPrefs", "riderLat", "riderLng", "riderLocationAt", "riderOnline", "departmentId", "sessionsValidFrom", "isSuperAdmin") FROM stdin;
cmwlph92p003lnw01vzd35f50	cmwlph925002vnw01igutco9z	cmwlph92a002znw01i06m723i	Himanshu	himanshupm18@gmail.com	\N	$2b$12$rg5rv5cHiuklmqU3FH064.mXKgfud/FhMbggf6NcuX8XG9Fkfdx3K	\N	t	\N	2026-11-18 05:53:49.873	2026-11-18 05:53:49.873	f	\N	{}	\N	\N	\N	\N	f	\N	\N	f
cmwlqbuwn001vs05fpv8oagb7	demo-restaurant	cmwlqbtzm0019s05fvve3rcpv	Demo Owner	owner@demo.local	\N	$2b$12$GLg.4P1X0Ixi3PwqjXWJo.0jJ7oRtnRiHOsPh/iOk5KFFSfOsB3DC	$2b$12$v2VjkuZHTTtXvaM1v7Gxv.oyoRLJtIuUkM2Gte2IaxThX.0KOd50.	t	\N	2026-11-18 06:17:37.847	2026-11-18 06:17:37.847	f	\N	{}	\N	\N	\N	\N	f	\N	\N	f
cmwlqbuws001xs05fga0dytq7	demo-restaurant	cmwlqbtzm0019s05fvve3rcpv	Super Admin	superadmin@orderrestro.local	\N	$2b$12$pOstTJSoab8bMm1Qmcq70ecRPhukhZ9pFWfD/ItVMWnozbLthCZ1W	9999	t	\N	2026-11-18 06:17:37.852	2026-11-18 06:17:37.852	f	\N	{}	\N	\N	\N	\N	f	\N	\N	t
\.


--
-- Data for Name: verifactu_records; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.verifactu_records (id, "restaurantId", "branchId", "issuerNif", seq, type, "invoiceType", "invoiceNumber", "issueDate", "taxTotalCents", "totalCents", "generatedAt", "previousHash", hash, xml, "qrUrl", environment, "orderId", "refundId", status, attempts, "nextAttemptAt", csv, "errorCode", "errorText", "responseXml", "submittedAt", "createdAt") FROM stdin;
\.


--
-- Data for Name: verifactu_settings; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.verifactu_settings (id, "branchId", enabled, environment, "seriesPrefix", "nextNumber", "nextRefundNumber", "installationNumber", "certEncrypted", "certPasswordEncrypted", "certSubject", "certExpiresAt", "updatedAt") FROM stdin;
\.


--
-- Data for Name: waitlist_entries; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.waitlist_entries (id, "branchId", "customerName", phone, "partySize", "quotedWaitMinutes", notes, status, "tableId", "createdAt", "seatedAt") FROM stdin;
\.


--
-- Data for Name: waste_entries; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.waste_entries (id, "branchId", kind, "ingredientId", "enteredQuantity", "enteredUnit", quantity, reason, shift, location, note, "occurredAt", "includedInProduction", "productionEntryId", status, "idempotencyKey", "deviceId", "createdById", "createdAt", "approvedById", "approvedAt", "decisionNote", "reversedById", "reversedAt", "reverseReason", "photoUrl") FROM stdin;
\.


--
-- Data for Name: waste_logs; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.waste_logs (id, "branchId", "ingredientId", "batchId", quantity, reason, "unitCostAtWaste", notes, "createdById", "createdAt", "entryId") FROM stdin;
\.


--
-- Data for Name: webhook_deliveries; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.webhook_deliveries (id, "endpointId", event, payload, status, attempts, "lastStatusCode", "lastError", "nextAttemptAt", "createdAt", "deliveredAt") FROM stdin;
\.


--
-- Data for Name: webhook_endpoints; Type: TABLE DATA; Schema: public; Owner: nodedr
--

COPY public.webhook_endpoints (id, "restaurantId", url, secret, events, description, "isActive", "createdAt") FROM stdin;
\.


--
-- Name: sync_changes_seq_seq; Type: SEQUENCE SET; Schema: public; Owner: nodedr
--

SELECT pg_catalog.setval('public.sync_changes_seq_seq', 1, false);


--
-- Name: _prisma_migrations _prisma_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public._prisma_migrations
    ADD CONSTRAINT _prisma_migrations_pkey PRIMARY KEY (id);


--
-- Name: attendance attendance_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.attendance
    ADD CONSTRAINT attendance_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: backup_config backup_config_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.backup_config
    ADD CONSTRAINT backup_config_pkey PRIMARY KEY (id);


--
-- Name: backups backups_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.backups
    ADD CONSTRAINT backups_pkey PRIMARY KEY (id);


--
-- Name: bank_transactions bank_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.bank_transactions
    ADD CONSTRAINT bank_transactions_pkey PRIMARY KEY (id);


--
-- Name: branches branches_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.branches
    ADD CONSTRAINT branches_pkey PRIMARY KEY (id);


--
-- Name: budgets budgets_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.budgets
    ADD CONSTRAINT budgets_pkey PRIMARY KEY (id);


--
-- Name: buzzer_calls buzzer_calls_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.buzzer_calls
    ADD CONSTRAINT buzzer_calls_pkey PRIMARY KEY (id);


--
-- Name: buzzers buzzers_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.buzzers
    ADD CONSTRAINT buzzers_pkey PRIMARY KEY (id);


--
-- Name: campaigns campaigns_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.campaigns
    ADD CONSTRAINT campaigns_pkey PRIMARY KEY (id);


--
-- Name: cash_closings cash_closings_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.cash_closings
    ADD CONSTRAINT cash_closings_pkey PRIMARY KEY (id);


--
-- Name: combo_components combo_components_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.combo_components
    ADD CONSTRAINT combo_components_pkey PRIMARY KEY (id);


--
-- Name: coupons coupons_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.coupons
    ADD CONSTRAINT coupons_pkey PRIMARY KEY (id);


--
-- Name: customer_addresses customer_addresses_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.customer_addresses
    ADD CONSTRAINT customer_addresses_pkey PRIMARY KEY (id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: delivery_assignments delivery_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.delivery_assignments
    ADD CONSTRAINT delivery_assignments_pkey PRIMARY KEY (id);


--
-- Name: delivery_zones delivery_zones_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.delivery_zones
    ADD CONSTRAINT delivery_zones_pkey PRIMARY KEY (id);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (id);


--
-- Name: device_tokens device_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.device_tokens
    ADD CONSTRAINT device_tokens_pkey PRIMARY KEY (id);


--
-- Name: display_ads display_ads_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.display_ads
    ADD CONSTRAINT display_ads_pkey PRIMARY KEY (id);


--
-- Name: display_terminals display_terminals_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.display_terminals
    ADD CONSTRAINT display_terminals_pkey PRIMARY KEY (id);


--
-- Name: document_files document_files_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.document_files
    ADD CONSTRAINT document_files_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: download_stats download_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.download_stats
    ADD CONSTRAINT download_stats_pkey PRIMARY KEY (channel);


--
-- Name: equipment equipment_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.equipment
    ADD CONSTRAINT equipment_pkey PRIMARY KEY (id);


--
-- Name: expenses expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (id);


--
-- Name: floor_layouts floor_layouts_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.floor_layouts
    ADD CONSTRAINT floor_layouts_pkey PRIMARY KEY (id);


--
-- Name: floors floors_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.floors
    ADD CONSTRAINT floors_pkey PRIMARY KEY (id);


--
-- Name: gateway_payments gateway_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.gateway_payments
    ADD CONSTRAINT gateway_payments_pkey PRIMARY KEY (id);


--
-- Name: gateway_refunds gateway_refunds_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.gateway_refunds
    ADD CONSTRAINT gateway_refunds_pkey PRIMARY KEY (id);


--
-- Name: gateway_webhook_events gateway_webhook_events_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.gateway_webhook_events
    ADD CONSTRAINT gateway_webhook_events_pkey PRIMARY KEY (id);


--
-- Name: gift_card_redemptions gift_card_redemptions_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.gift_card_redemptions
    ADD CONSTRAINT gift_card_redemptions_pkey PRIMARY KEY (id);


--
-- Name: gift_cards gift_cards_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.gift_cards
    ADD CONSTRAINT gift_cards_pkey PRIMARY KEY (id);


--
-- Name: goods_receipt_items goods_receipt_items_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.goods_receipt_items
    ADD CONSTRAINT goods_receipt_items_pkey PRIMARY KEY (id);


--
-- Name: goods_receipts goods_receipts_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.goods_receipts
    ADD CONSTRAINT goods_receipts_pkey PRIMARY KEY (id);


--
-- Name: ingredients ingredients_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.ingredients
    ADD CONSTRAINT ingredients_pkey PRIMARY KEY (id);


--
-- Name: integration_api_keys integration_api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.integration_api_keys
    ADD CONSTRAINT integration_api_keys_pkey PRIMARY KEY (id);


--
-- Name: integration_connections integration_connections_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.integration_connections
    ADD CONSTRAINT integration_connections_pkey PRIMARY KEY (id);


--
-- Name: integration_logs integration_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.integration_logs
    ADD CONSTRAINT integration_logs_pkey PRIMARY KEY (id);


--
-- Name: kitchen_stations kitchen_stations_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.kitchen_stations
    ADD CONSTRAINT kitchen_stations_pkey PRIMARY KEY (id);


--
-- Name: kot_items kot_items_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.kot_items
    ADD CONSTRAINT kot_items_pkey PRIMARY KEY (id);


--
-- Name: kots kots_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.kots
    ADD CONSTRAINT kots_pkey PRIMARY KEY (id);


--
-- Name: leave_requests leave_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.leave_requests
    ADD CONSTRAINT leave_requests_pkey PRIMARY KEY (id);


--
-- Name: licenses licenses_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.licenses
    ADD CONSTRAINT licenses_pkey PRIMARY KEY (id);


--
-- Name: location_transfers location_transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.location_transfers
    ADD CONSTRAINT location_transfers_pkey PRIMARY KEY (id);


--
-- Name: menu_categories menu_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_categories
    ADD CONSTRAINT menu_categories_pkey PRIMARY KEY (id);


--
-- Name: menu_item_costings menu_item_costings_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_item_costings
    ADD CONSTRAINT menu_item_costings_pkey PRIMARY KEY (id);


--
-- Name: menu_item_modifier_groups menu_item_modifier_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_item_modifier_groups
    ADD CONSTRAINT menu_item_modifier_groups_pkey PRIMARY KEY ("menuItemId", "modifierGroupId");


--
-- Name: menu_items menu_items_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT menu_items_pkey PRIMARY KEY (id);


--
-- Name: menu_price_changes menu_price_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_price_changes
    ADD CONSTRAINT menu_price_changes_pkey PRIMARY KEY (id);


--
-- Name: modifier_groups modifier_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.modifier_groups
    ADD CONSTRAINT modifier_groups_pkey PRIMARY KEY (id);


--
-- Name: modifier_ingredients modifier_ingredients_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.modifier_ingredients
    ADD CONSTRAINT modifier_ingredients_pkey PRIMARY KEY (id);


--
-- Name: modifiers modifiers_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.modifiers
    ADD CONSTRAINT modifiers_pkey PRIMARY KEY (id);


--
-- Name: nfc_tags nfc_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.nfc_tags
    ADD CONSTRAINT nfc_tags_pkey PRIMARY KEY (id);


--
-- Name: nfc_taps nfc_taps_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.nfc_taps
    ADD CONSTRAINT nfc_taps_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: order_item_costs order_item_costs_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.order_item_costs
    ADD CONSTRAINT order_item_costs_pkey PRIMARY KEY ("orderItemId");


--
-- Name: order_item_modifiers order_item_modifiers_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.order_item_modifiers
    ADD CONSTRAINT order_item_modifiers_pkey PRIMARY KEY (id);


--
-- Name: order_item_stock_returns order_item_stock_returns_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.order_item_stock_returns
    ADD CONSTRAINT order_item_stock_returns_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: order_ratings order_ratings_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.order_ratings
    ADD CONSTRAINT order_ratings_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: payment_gateway_catalog payment_gateway_catalog_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.payment_gateway_catalog
    ADD CONSTRAINT payment_gateway_catalog_pkey PRIMARY KEY (id);


--
-- Name: payment_gateway_connections payment_gateway_connections_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.payment_gateway_connections
    ADD CONSTRAINT payment_gateway_connections_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: payroll_lines payroll_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.payroll_lines
    ADD CONSTRAINT payroll_lines_pkey PRIMARY KEY (id);


--
-- Name: payroll_runs payroll_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.payroll_runs
    ADD CONSTRAINT payroll_runs_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: phone_till_closings phone_till_closings_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.phone_till_closings
    ADD CONSTRAINT phone_till_closings_pkey PRIMARY KEY (id);


--
-- Name: points_ledger points_ledger_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.points_ledger
    ADD CONSTRAINT points_ledger_pkey PRIMARY KEY (id);


--
-- Name: pos_devices pos_devices_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.pos_devices
    ADD CONSTRAINT pos_devices_pkey PRIMARY KEY (id);


--
-- Name: preparation_lines preparation_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.preparation_lines
    ADD CONSTRAINT preparation_lines_pkey PRIMARY KEY (id);


--
-- Name: preparations preparations_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.preparations
    ADD CONSTRAINT preparations_pkey PRIMARY KEY (id);


--
-- Name: product_recipe_lines product_recipe_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.product_recipe_lines
    ADD CONSTRAINT product_recipe_lines_pkey PRIMARY KEY (id);


--
-- Name: product_recipes product_recipes_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.product_recipes
    ADD CONSTRAINT product_recipes_pkey PRIMARY KEY (id);


--
-- Name: production_costs production_costs_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.production_costs
    ADD CONSTRAINT production_costs_pkey PRIMARY KEY (id);


--
-- Name: production_entries production_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.production_entries
    ADD CONSTRAINT production_entries_pkey PRIMARY KEY (id);


--
-- Name: production_lines production_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.production_lines
    ADD CONSTRAINT production_lines_pkey PRIMARY KEY (id);


--
-- Name: production_runs production_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.production_runs
    ADD CONSTRAINT production_runs_pkey PRIMARY KEY (id);


--
-- Name: promotions promotions_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.promotions
    ADD CONSTRAINT promotions_pkey PRIMARY KEY (id);


--
-- Name: public_order_keys public_order_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.public_order_keys
    ADD CONSTRAINT public_order_keys_pkey PRIMARY KEY (id);


--
-- Name: purchase_order_items purchase_order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_order_items
    ADD CONSTRAINT purchase_order_items_pkey PRIMARY KEY (id);


--
-- Name: purchase_orders purchase_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_pkey PRIMARY KEY (id);


--
-- Name: purchase_request_items purchase_request_items_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_request_items
    ADD CONSTRAINT purchase_request_items_pkey PRIMARY KEY (id);


--
-- Name: purchase_requests purchase_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_requests
    ADD CONSTRAINT purchase_requests_pkey PRIMARY KEY (id);


--
-- Name: recipe_ingredients recipe_ingredients_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.recipe_ingredients
    ADD CONSTRAINT recipe_ingredients_pkey PRIMARY KEY (id);


--
-- Name: referrals referrals_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_pkey PRIMARY KEY (id);


--
-- Name: refunds refunds_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.refunds
    ADD CONSTRAINT refunds_pkey PRIMARY KEY (id);


--
-- Name: report_schedules report_schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.report_schedules
    ADD CONSTRAINT report_schedules_pkey PRIMARY KEY (id);


--
-- Name: reservations reservations_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.reservations
    ADD CONSTRAINT reservations_pkey PRIMARY KEY (id);


--
-- Name: restaurants restaurants_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.restaurants
    ADD CONSTRAINT restaurants_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY ("roleId", "permissionId");


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: service_logs service_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.service_logs
    ADD CONSTRAINT service_logs_pkey PRIMARY KEY (id);


--
-- Name: shifts shifts_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.shifts
    ADD CONSTRAINT shifts_pkey PRIMARY KEY (id);


--
-- Name: staff_api_keys staff_api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.staff_api_keys
    ADD CONSTRAINT staff_api_keys_pkey PRIMARY KEY (id);


--
-- Name: staff_pay staff_pay_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.staff_pay
    ADD CONSTRAINT staff_pay_pkey PRIMARY KEY ("userId");


--
-- Name: stock_batches stock_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_batches
    ADD CONSTRAINT stock_batches_pkey PRIMARY KEY (id);


--
-- Name: stock_journal_entries stock_journal_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_journal_entries
    ADD CONSTRAINT stock_journal_entries_pkey PRIMARY KEY (id);


--
-- Name: stock_journal_lines stock_journal_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_journal_lines
    ADD CONSTRAINT stock_journal_lines_pkey PRIMARY KEY (id);


--
-- Name: stock_levels stock_levels_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_levels
    ADD CONSTRAINT stock_levels_pkey PRIMARY KEY (id);


--
-- Name: stock_locations stock_locations_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_locations
    ADD CONSTRAINT stock_locations_pkey PRIMARY KEY (id);


--
-- Name: stock_movements stock_movements_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_pkey PRIMARY KEY (id);


--
-- Name: stock_takes stock_takes_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_takes
    ADD CONSTRAINT stock_takes_pkey PRIMARY KEY (id);


--
-- Name: stock_transfers stock_transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_transfers
    ADD CONSTRAINT stock_transfers_pkey PRIMARY KEY (id);


--
-- Name: supplier_invoices supplier_invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_invoices
    ADD CONSTRAINT supplier_invoices_pkey PRIMARY KEY (id);


--
-- Name: supplier_payments supplier_payments_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_payments
    ADD CONSTRAINT supplier_payments_pkey PRIMARY KEY (id);


--
-- Name: supplier_quotation_items supplier_quotation_items_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_quotation_items
    ADD CONSTRAINT supplier_quotation_items_pkey PRIMARY KEY (id);


--
-- Name: supplier_quotations supplier_quotations_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_quotations
    ADD CONSTRAINT supplier_quotations_pkey PRIMARY KEY (id);


--
-- Name: suppliers suppliers_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (id);


--
-- Name: sync_changes sync_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.sync_changes
    ADD CONSTRAINT sync_changes_pkey PRIMARY KEY (seq);


--
-- Name: sync_state sync_state_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.sync_state
    ADD CONSTRAINT sync_state_pkey PRIMARY KEY (id);


--
-- Name: table_accesses table_accesses_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.table_accesses
    ADD CONSTRAINT table_accesses_pkey PRIMARY KEY (id);


--
-- Name: table_requests table_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.table_requests
    ADD CONSTRAINT table_requests_pkey PRIMARY KEY (id);


--
-- Name: table_session_grants table_session_grants_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.table_session_grants
    ADD CONSTRAINT table_session_grants_pkey PRIMARY KEY (id);


--
-- Name: table_sessions table_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.table_sessions
    ADD CONSTRAINT table_sessions_pkey PRIMARY KEY (id);


--
-- Name: tables tables_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.tables
    ADD CONSTRAINT tables_pkey PRIMARY KEY (id);


--
-- Name: user_branches user_branches_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.user_branches
    ADD CONSTRAINT user_branches_pkey PRIMARY KEY ("userId", "branchId");


--
-- Name: user_permission_overrides user_permission_overrides_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.user_permission_overrides
    ADD CONSTRAINT user_permission_overrides_pkey PRIMARY KEY ("userId", "permissionId");


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: verifactu_records verifactu_records_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.verifactu_records
    ADD CONSTRAINT verifactu_records_pkey PRIMARY KEY (id);


--
-- Name: verifactu_settings verifactu_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.verifactu_settings
    ADD CONSTRAINT verifactu_settings_pkey PRIMARY KEY (id);


--
-- Name: waitlist_entries waitlist_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.waitlist_entries
    ADD CONSTRAINT waitlist_entries_pkey PRIMARY KEY (id);


--
-- Name: waste_entries waste_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.waste_entries
    ADD CONSTRAINT waste_entries_pkey PRIMARY KEY (id);


--
-- Name: waste_logs waste_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.waste_logs
    ADD CONSTRAINT waste_logs_pkey PRIMARY KEY (id);


--
-- Name: webhook_deliveries webhook_deliveries_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.webhook_deliveries
    ADD CONSTRAINT webhook_deliveries_pkey PRIMARY KEY (id);


--
-- Name: webhook_endpoints webhook_endpoints_pkey; Type: CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.webhook_endpoints
    ADD CONSTRAINT webhook_endpoints_pkey PRIMARY KEY (id);


--
-- Name: attendance_branchId_clockInAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "attendance_branchId_clockInAt_idx" ON public.attendance USING btree ("branchId", "clockInAt");


--
-- Name: attendance_userId_clockInKey_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "attendance_userId_clockInKey_key" ON public.attendance USING btree ("userId", "clockInKey");


--
-- Name: attendance_userId_clockOutAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "attendance_userId_clockOutAt_idx" ON public.attendance USING btree ("userId", "clockOutAt");


--
-- Name: attendance_userId_clockOutKey_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "attendance_userId_clockOutKey_key" ON public.attendance USING btree ("userId", "clockOutKey");


--
-- Name: audit_logs_entity_entityId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "audit_logs_entity_entityId_idx" ON public.audit_logs USING btree (entity, "entityId");


--
-- Name: backups_status_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "backups_status_createdAt_idx" ON public.backups USING btree (status, "createdAt");


--
-- Name: bank_transactions_branchId_postedOn_description_amount_refe_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "bank_transactions_branchId_postedOn_description_amount_refe_key" ON public.bank_transactions USING btree ("branchId", "postedOn", description, amount, reference);


--
-- Name: bank_transactions_branchId_postedOn_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "bank_transactions_branchId_postedOn_idx" ON public.bank_transactions USING btree ("branchId", "postedOn");


--
-- Name: branches_kioskToken_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "branches_kioskToken_key" ON public.branches USING btree ("kioskToken");


--
-- Name: branches_restaurantId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "branches_restaurantId_idx" ON public.branches USING btree ("restaurantId");


--
-- Name: budgets_branchId_month_category_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "budgets_branchId_month_category_key" ON public.budgets USING btree ("branchId", month, category);


--
-- Name: buzzer_calls_buzzerId_state_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "buzzer_calls_buzzerId_state_idx" ON public.buzzer_calls USING btree ("buzzerId", state);


--
-- Name: buzzer_calls_orderId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "buzzer_calls_orderId_idx" ON public.buzzer_calls USING btree ("orderId");


--
-- Name: buzzers_branchId_name_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "buzzers_branchId_name_key" ON public.buzzers USING btree ("branchId", name);


--
-- Name: buzzers_deviceToken_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "buzzers_deviceToken_key" ON public.buzzers USING btree ("deviceToken");


--
-- Name: buzzers_tableId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "buzzers_tableId_key" ON public.buzzers USING btree ("tableId");


--
-- Name: campaigns_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "campaigns_branchId_idx" ON public.campaigns USING btree ("branchId");


--
-- Name: cash_closings_branchId_businessDate_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "cash_closings_branchId_businessDate_key" ON public.cash_closings USING btree ("branchId", "businessDate");


--
-- Name: combo_components_comboItemId_componentItemId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "combo_components_comboItemId_componentItemId_key" ON public.combo_components USING btree ("comboItemId", "componentItemId");


--
-- Name: coupons_branchId_code_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "coupons_branchId_code_key" ON public.coupons USING btree ("branchId", code);


--
-- Name: customer_addresses_customerId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "customer_addresses_customerId_idx" ON public.customer_addresses USING btree ("customerId");


--
-- Name: customers_branchId_phone_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "customers_branchId_phone_idx" ON public.customers USING btree ("branchId", phone);


--
-- Name: customers_referralCode_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "customers_referralCode_key" ON public.customers USING btree ("referralCode");


--
-- Name: delivery_assignments_branchId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "delivery_assignments_branchId_createdAt_idx" ON public.delivery_assignments USING btree ("branchId", "createdAt");


--
-- Name: delivery_assignments_orderId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "delivery_assignments_orderId_createdAt_idx" ON public.delivery_assignments USING btree ("orderId", "createdAt");


--
-- Name: delivery_zones_branchId_isActive_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "delivery_zones_branchId_isActive_idx" ON public.delivery_zones USING btree ("branchId", "isActive");


--
-- Name: departments_restaurantId_name_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "departments_restaurantId_name_key" ON public.departments USING btree ("restaurantId", name);


--
-- Name: device_tokens_token_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX device_tokens_token_key ON public.device_tokens USING btree (token);


--
-- Name: device_tokens_userId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "device_tokens_userId_idx" ON public.device_tokens USING btree ("userId");


--
-- Name: display_ads_branchId_isActive_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "display_ads_branchId_isActive_idx" ON public.display_ads USING btree ("branchId", "isActive");


--
-- Name: display_terminals_branchId_name_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "display_terminals_branchId_name_key" ON public.display_terminals USING btree ("branchId", name);


--
-- Name: display_terminals_token_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX display_terminals_token_key ON public.display_terminals USING btree (token);


--
-- Name: document_files_documentId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "document_files_documentId_idx" ON public.document_files USING btree ("documentId");


--
-- Name: documents_branchId_category_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "documents_branchId_category_idx" ON public.documents USING btree ("branchId", category);


--
-- Name: equipment_branchId_nextDueAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "equipment_branchId_nextDueAt_idx" ON public.equipment USING btree ("branchId", "nextDueAt");


--
-- Name: expenses_branchId_spentOn_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "expenses_branchId_spentOn_idx" ON public.expenses USING btree ("branchId", "spentOn");


--
-- Name: expenses_clientRequestId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "expenses_clientRequestId_key" ON public.expenses USING btree ("clientRequestId");


--
-- Name: floor_layouts_floorId_name_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "floor_layouts_floorId_name_key" ON public.floor_layouts USING btree ("floorId", name);


--
-- Name: floors_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "floors_branchId_idx" ON public.floors USING btree ("branchId");


--
-- Name: gateway_payments_orderId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "gateway_payments_orderId_idx" ON public.gateway_payments USING btree ("orderId");


--
-- Name: gateway_payments_provider_mode_providerRef_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "gateway_payments_provider_mode_providerRef_key" ON public.gateway_payments USING btree (provider, mode, "providerRef");


--
-- Name: gateway_payments_restaurantId_status_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "gateway_payments_restaurantId_status_idx" ON public.gateway_payments USING btree ("restaurantId", status);


--
-- Name: gateway_refunds_gatewayPaymentId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "gateway_refunds_gatewayPaymentId_idx" ON public.gateway_refunds USING btree ("gatewayPaymentId");


--
-- Name: gateway_refunds_orderId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "gateway_refunds_orderId_idx" ON public.gateway_refunds USING btree ("orderId");


--
-- Name: gateway_webhook_events_provider_mode_eventId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "gateway_webhook_events_provider_mode_eventId_key" ON public.gateway_webhook_events USING btree (provider, mode, "eventId");


--
-- Name: gift_cards_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "gift_cards_branchId_idx" ON public.gift_cards USING btree ("branchId");


--
-- Name: gift_cards_code_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX gift_cards_code_key ON public.gift_cards USING btree (code);


--
-- Name: goods_receipt_items_goodsReceiptId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "goods_receipt_items_goodsReceiptId_idx" ON public.goods_receipt_items USING btree ("goodsReceiptId");


--
-- Name: goods_receipts_branchId_grnNumber_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "goods_receipts_branchId_grnNumber_key" ON public.goods_receipts USING btree ("branchId", "grnNumber");


--
-- Name: goods_receipts_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "goods_receipts_branchId_idx" ON public.goods_receipts USING btree ("branchId");


--
-- Name: ingredients_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "ingredients_branchId_idx" ON public.ingredients USING btree ("branchId");


--
-- Name: ingredients_branchId_name_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "ingredients_branchId_name_key" ON public.ingredients USING btree ("branchId", name);


--
-- Name: integration_api_keys_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "integration_api_keys_branchId_idx" ON public.integration_api_keys USING btree ("branchId");


--
-- Name: integration_api_keys_restaurantId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "integration_api_keys_restaurantId_idx" ON public.integration_api_keys USING btree ("restaurantId");


--
-- Name: integration_api_keys_tokenHash_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "integration_api_keys_tokenHash_key" ON public.integration_api_keys USING btree ("tokenHash");


--
-- Name: integration_connections_restaurantId_provider_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "integration_connections_restaurantId_provider_key" ON public.integration_connections USING btree ("restaurantId", provider);


--
-- Name: integration_logs_connectionId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "integration_logs_connectionId_createdAt_idx" ON public.integration_logs USING btree ("connectionId", "createdAt");


--
-- Name: kitchen_stations_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "kitchen_stations_branchId_idx" ON public.kitchen_stations USING btree ("branchId");


--
-- Name: kot_items_kotId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "kot_items_kotId_idx" ON public.kot_items USING btree ("kotId");


--
-- Name: kots_orderId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "kots_orderId_idx" ON public.kots USING btree ("orderId");


--
-- Name: kots_stationId_status_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "kots_stationId_status_idx" ON public.kots USING btree ("stationId", status);


--
-- Name: leave_requests_branchId_status_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "leave_requests_branchId_status_idx" ON public.leave_requests USING btree ("branchId", status);


--
-- Name: leave_requests_userId_startDate_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "leave_requests_userId_startDate_idx" ON public.leave_requests USING btree ("userId", "startDate");


--
-- Name: licenses_restaurantId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "licenses_restaurantId_key" ON public.licenses USING btree ("restaurantId");


--
-- Name: location_transfers_branchId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "location_transfers_branchId_createdAt_idx" ON public.location_transfers USING btree ("branchId", "createdAt");


--
-- Name: location_transfers_branchId_idempotencyKey_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "location_transfers_branchId_idempotencyKey_key" ON public.location_transfers USING btree ("branchId", "idempotencyKey");


--
-- Name: menu_categories_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "menu_categories_branchId_idx" ON public.menu_categories USING btree ("branchId");


--
-- Name: menu_item_costings_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "menu_item_costings_branchId_idx" ON public.menu_item_costings USING btree ("branchId");


--
-- Name: menu_item_costings_menuItemId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "menu_item_costings_menuItemId_key" ON public.menu_item_costings USING btree ("menuItemId");


--
-- Name: menu_items_branchId_categoryId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "menu_items_branchId_categoryId_idx" ON public.menu_items USING btree ("branchId", "categoryId");


--
-- Name: menu_price_changes_branchId_changedAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "menu_price_changes_branchId_changedAt_idx" ON public.menu_price_changes USING btree ("branchId", "changedAt");


--
-- Name: menu_price_changes_menuItemId_changedAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "menu_price_changes_menuItemId_changedAt_idx" ON public.menu_price_changes USING btree ("menuItemId", "changedAt");


--
-- Name: modifier_groups_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "modifier_groups_branchId_idx" ON public.modifier_groups USING btree ("branchId");


--
-- Name: modifier_ingredients_modifierId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "modifier_ingredients_modifierId_idx" ON public.modifier_ingredients USING btree ("modifierId");


--
-- Name: modifier_ingredients_modifierId_ingredientId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "modifier_ingredients_modifierId_ingredientId_key" ON public.modifier_ingredients USING btree ("modifierId", "ingredientId");


--
-- Name: modifiers_groupId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "modifiers_groupId_idx" ON public.modifiers USING btree ("groupId");


--
-- Name: nfc_tags_branchId_uid_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "nfc_tags_branchId_uid_key" ON public.nfc_tags USING btree ("branchId", uid);


--
-- Name: nfc_tags_publicRef_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "nfc_tags_publicRef_key" ON public.nfc_tags USING btree ("publicRef");


--
-- Name: nfc_tags_tableId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "nfc_tags_tableId_idx" ON public.nfc_tags USING btree ("tableId");


--
-- Name: nfc_taps_branchId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "nfc_taps_branchId_createdAt_idx" ON public.nfc_taps USING btree ("branchId", "createdAt");


--
-- Name: nfc_taps_tagId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "nfc_taps_tagId_createdAt_idx" ON public.nfc_taps USING btree ("tagId", "createdAt");


--
-- Name: notifications_branchId_recipientUserId_readAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "notifications_branchId_recipientUserId_readAt_idx" ON public.notifications USING btree ("branchId", "recipientUserId", "readAt");


--
-- Name: order_item_modifiers_orderItemId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "order_item_modifiers_orderItemId_idx" ON public.order_item_modifiers USING btree ("orderItemId");


--
-- Name: order_item_stock_returns_orderItemId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "order_item_stock_returns_orderItemId_idx" ON public.order_item_stock_returns USING btree ("orderItemId");


--
-- Name: order_item_stock_returns_refundId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "order_item_stock_returns_refundId_idx" ON public.order_item_stock_returns USING btree ("refundId");


--
-- Name: order_items_orderId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "order_items_orderId_idx" ON public.order_items USING btree ("orderId");


--
-- Name: order_ratings_branchId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "order_ratings_branchId_createdAt_idx" ON public.order_ratings USING btree ("branchId", "createdAt");


--
-- Name: order_ratings_orderId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "order_ratings_orderId_key" ON public.order_ratings USING btree ("orderId");


--
-- Name: orders_branchId_clientRequestId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "orders_branchId_clientRequestId_key" ON public.orders USING btree ("branchId", "clientRequestId");


--
-- Name: orders_branchId_deliveryStatus_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "orders_branchId_deliveryStatus_idx" ON public.orders USING btree ("branchId", "deliveryStatus");


--
-- Name: orders_branchId_externalSource_externalOrderId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "orders_branchId_externalSource_externalOrderId_key" ON public.orders USING btree ("branchId", "externalSource", "externalOrderId");


--
-- Name: orders_branchId_orderNumber_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "orders_branchId_orderNumber_key" ON public.orders USING btree ("branchId", "orderNumber");


--
-- Name: orders_branchId_status_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "orders_branchId_status_idx" ON public.orders USING btree ("branchId", status);


--
-- Name: orders_integrationKeyId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "orders_integrationKeyId_idx" ON public.orders USING btree ("integrationKeyId");


--
-- Name: payment_gateway_catalog_restaurantId_key_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "payment_gateway_catalog_restaurantId_key_key" ON public.payment_gateway_catalog USING btree ("restaurantId", key);


--
-- Name: payment_gateway_connections_restaurantId_provider_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "payment_gateway_connections_restaurantId_provider_key" ON public.payment_gateway_connections USING btree ("restaurantId", provider);


--
-- Name: payments_orderId_clientRequestId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "payments_orderId_clientRequestId_key" ON public.payments USING btree ("orderId", "clientRequestId");


--
-- Name: payments_orderId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "payments_orderId_idx" ON public.payments USING btree ("orderId");


--
-- Name: payroll_lines_runId_userId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "payroll_lines_runId_userId_key" ON public.payroll_lines USING btree ("runId", "userId");


--
-- Name: payroll_runs_branchId_periodStart_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "payroll_runs_branchId_periodStart_idx" ON public.payroll_runs USING btree ("branchId", "periodStart");


--
-- Name: permissions_key_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX permissions_key_key ON public.permissions USING btree (key);


--
-- Name: phone_till_closings_branchId_businessDate_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "phone_till_closings_branchId_businessDate_idx" ON public.phone_till_closings USING btree ("branchId", "businessDate");


--
-- Name: phone_till_closings_branchId_deviceId_businessDate_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "phone_till_closings_branchId_deviceId_businessDate_key" ON public.phone_till_closings USING btree ("branchId", "deviceId", "businessDate");


--
-- Name: points_ledger_customerId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "points_ledger_customerId_createdAt_idx" ON public.points_ledger USING btree ("customerId", "createdAt");


--
-- Name: points_ledger_idempotencyKey_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "points_ledger_idempotencyKey_key" ON public.points_ledger USING btree ("idempotencyKey");


--
-- Name: pos_devices_deviceId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "pos_devices_deviceId_idx" ON public.pos_devices USING btree ("deviceId");


--
-- Name: pos_devices_restaurantId_deviceId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "pos_devices_restaurantId_deviceId_key" ON public.pos_devices USING btree ("restaurantId", "deviceId");


--
-- Name: pos_devices_userId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "pos_devices_userId_idx" ON public.pos_devices USING btree ("userId");


--
-- Name: preparation_lines_preparationId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "preparation_lines_preparationId_idx" ON public.preparation_lines USING btree ("preparationId");


--
-- Name: preparation_lines_preparationId_ingredientId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "preparation_lines_preparationId_ingredientId_key" ON public.preparation_lines USING btree ("preparationId", "ingredientId");


--
-- Name: preparations_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "preparations_branchId_idx" ON public.preparations USING btree ("branchId");


--
-- Name: preparations_outputIngredientId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "preparations_outputIngredientId_key" ON public.preparations USING btree ("outputIngredientId");


--
-- Name: product_recipe_lines_recipeId_ingredientId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "product_recipe_lines_recipeId_ingredientId_key" ON public.product_recipe_lines USING btree ("recipeId", "ingredientId");


--
-- Name: product_recipes_branchId_outputIngredientId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "product_recipes_branchId_outputIngredientId_idx" ON public.product_recipes USING btree ("branchId", "outputIngredientId");


--
-- Name: product_recipes_branchId_outputIngredientId_name_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "product_recipes_branchId_outputIngredientId_name_key" ON public.product_recipes USING btree ("branchId", "outputIngredientId", name);


--
-- Name: production_costs_entryId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "production_costs_entryId_idx" ON public.production_costs USING btree ("entryId");


--
-- Name: production_entries_branchId_entryNo_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "production_entries_branchId_entryNo_key" ON public.production_entries USING btree ("branchId", "entryNo");


--
-- Name: production_entries_branchId_idempotencyKey_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "production_entries_branchId_idempotencyKey_key" ON public.production_entries USING btree ("branchId", "idempotencyKey");


--
-- Name: production_entries_branchId_producedAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "production_entries_branchId_producedAt_idx" ON public.production_entries USING btree ("branchId", "producedAt");


--
-- Name: production_lines_entryId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "production_lines_entryId_idx" ON public.production_lines USING btree ("entryId");


--
-- Name: production_lines_ingredientId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "production_lines_ingredientId_idx" ON public.production_lines USING btree ("ingredientId");


--
-- Name: production_runs_branchId_idempotencyKey_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "production_runs_branchId_idempotencyKey_key" ON public.production_runs USING btree ("branchId", "idempotencyKey");


--
-- Name: production_runs_preparationId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "production_runs_preparationId_createdAt_idx" ON public.production_runs USING btree ("preparationId", "createdAt");


--
-- Name: promotions_branchId_isActive_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "promotions_branchId_isActive_idx" ON public.promotions USING btree ("branchId", "isActive");


--
-- Name: public_order_keys_branchId_key_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "public_order_keys_branchId_key_key" ON public.public_order_keys USING btree ("branchId", key);


--
-- Name: purchase_order_items_purchaseOrderId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "purchase_order_items_purchaseOrderId_idx" ON public.purchase_order_items USING btree ("purchaseOrderId");


--
-- Name: purchase_orders_branchId_poNumber_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "purchase_orders_branchId_poNumber_key" ON public.purchase_orders USING btree ("branchId", "poNumber");


--
-- Name: purchase_orders_branchId_status_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "purchase_orders_branchId_status_idx" ON public.purchase_orders USING btree ("branchId", status);


--
-- Name: purchase_request_items_purchaseRequestId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "purchase_request_items_purchaseRequestId_idx" ON public.purchase_request_items USING btree ("purchaseRequestId");


--
-- Name: purchase_requests_branchId_requestNumber_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "purchase_requests_branchId_requestNumber_key" ON public.purchase_requests USING btree ("branchId", "requestNumber");


--
-- Name: purchase_requests_branchId_status_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "purchase_requests_branchId_status_idx" ON public.purchase_requests USING btree ("branchId", status);


--
-- Name: recipe_ingredients_menuItemId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "recipe_ingredients_menuItemId_idx" ON public.recipe_ingredients USING btree ("menuItemId");


--
-- Name: recipe_ingredients_menuItemId_ingredientId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "recipe_ingredients_menuItemId_ingredientId_key" ON public.recipe_ingredients USING btree ("menuItemId", "ingredientId");


--
-- Name: referrals_branchId_status_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "referrals_branchId_status_idx" ON public.referrals USING btree ("branchId", status);


--
-- Name: referrals_referredId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "referrals_referredId_key" ON public.referrals USING btree ("referredId");


--
-- Name: referrals_referrerId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "referrals_referrerId_idx" ON public.referrals USING btree ("referrerId");


--
-- Name: refunds_clientRequestId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "refunds_clientRequestId_key" ON public.refunds USING btree ("clientRequestId");


--
-- Name: refunds_orderId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "refunds_orderId_idx" ON public.refunds USING btree ("orderId");


--
-- Name: report_schedules_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "report_schedules_branchId_idx" ON public.report_schedules USING btree ("branchId");


--
-- Name: reservations_branchId_reservedAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "reservations_branchId_reservedAt_idx" ON public.reservations USING btree ("branchId", "reservedAt");


--
-- Name: roles_restaurantId_name_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "roles_restaurantId_name_key" ON public.roles USING btree ("restaurantId", name);


--
-- Name: service_logs_equipmentId_servicedAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "service_logs_equipmentId_servicedAt_idx" ON public.service_logs USING btree ("equipmentId", "servicedAt");


--
-- Name: shifts_branchId_startsAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "shifts_branchId_startsAt_idx" ON public.shifts USING btree ("branchId", "startsAt");


--
-- Name: shifts_userId_startsAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "shifts_userId_startsAt_idx" ON public.shifts USING btree ("userId", "startsAt");


--
-- Name: staff_api_keys_tokenHash_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "staff_api_keys_tokenHash_key" ON public.staff_api_keys USING btree ("tokenHash");


--
-- Name: staff_api_keys_userId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "staff_api_keys_userId_idx" ON public.staff_api_keys USING btree ("userId");


--
-- Name: stock_batches_branchId_ingredientId_receivedAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_batches_branchId_ingredientId_receivedAt_idx" ON public.stock_batches USING btree ("branchId", "ingredientId", "receivedAt");


--
-- Name: stock_batches_goodsReceiptItemId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "stock_batches_goodsReceiptItemId_key" ON public.stock_batches USING btree ("goodsReceiptItemId");


--
-- Name: stock_journal_entries_branchId_entryNo_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "stock_journal_entries_branchId_entryNo_key" ON public.stock_journal_entries USING btree ("branchId", "entryNo");


--
-- Name: stock_journal_entries_branchId_idempotencyKey_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "stock_journal_entries_branchId_idempotencyKey_key" ON public.stock_journal_entries USING btree ("branchId", "idempotencyKey");


--
-- Name: stock_journal_entries_branchId_occurredAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_journal_entries_branchId_occurredAt_idx" ON public.stock_journal_entries USING btree ("branchId", "occurredAt");


--
-- Name: stock_journal_lines_entryId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_journal_lines_entryId_idx" ON public.stock_journal_lines USING btree ("entryId");


--
-- Name: stock_journal_lines_ingredientId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_journal_lines_ingredientId_idx" ON public.stock_journal_lines USING btree ("ingredientId");


--
-- Name: stock_levels_ingredientId_locationId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "stock_levels_ingredientId_locationId_key" ON public.stock_levels USING btree ("ingredientId", "locationId");


--
-- Name: stock_levels_locationId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_levels_locationId_idx" ON public.stock_levels USING btree ("locationId");


--
-- Name: stock_locations_branchId_name_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "stock_locations_branchId_name_key" ON public.stock_locations USING btree ("branchId", name);


--
-- Name: stock_movements_branchId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_movements_branchId_createdAt_idx" ON public.stock_movements USING btree ("branchId", "createdAt");


--
-- Name: stock_movements_branchId_ingredientId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_movements_branchId_ingredientId_createdAt_idx" ON public.stock_movements USING btree ("branchId", "ingredientId", "createdAt");


--
-- Name: stock_movements_journalEntryId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_movements_journalEntryId_idx" ON public.stock_movements USING btree ("journalEntryId");


--
-- Name: stock_movements_orderId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_movements_orderId_idx" ON public.stock_movements USING btree ("orderId");


--
-- Name: stock_movements_productionEntryId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_movements_productionEntryId_idx" ON public.stock_movements USING btree ("productionEntryId");


--
-- Name: stock_movements_wasteEntryId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_movements_wasteEntryId_idx" ON public.stock_movements USING btree ("wasteEntryId");


--
-- Name: stock_takes_branchId_idempotencyKey_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "stock_takes_branchId_idempotencyKey_key" ON public.stock_takes USING btree ("branchId", "idempotencyKey");


--
-- Name: stock_takes_branchId_takenAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_takes_branchId_takenAt_idx" ON public.stock_takes USING btree ("branchId", "takenAt");


--
-- Name: stock_transfers_restaurantId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "stock_transfers_restaurantId_createdAt_idx" ON public.stock_transfers USING btree ("restaurantId", "createdAt");


--
-- Name: supplier_invoices_branchId_invoiceNumber_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "supplier_invoices_branchId_invoiceNumber_key" ON public.supplier_invoices USING btree ("branchId", "invoiceNumber");


--
-- Name: supplier_invoices_branchId_supplierId_status_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "supplier_invoices_branchId_supplierId_status_idx" ON public.supplier_invoices USING btree ("branchId", "supplierId", status);


--
-- Name: supplier_payments_branchId_supplierInvoiceId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "supplier_payments_branchId_supplierInvoiceId_idx" ON public.supplier_payments USING btree ("branchId", "supplierInvoiceId");


--
-- Name: supplier_quotation_items_supplierQuotationId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "supplier_quotation_items_supplierQuotationId_idx" ON public.supplier_quotation_items USING btree ("supplierQuotationId");


--
-- Name: supplier_quotations_branchId_quotationNumber_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "supplier_quotations_branchId_quotationNumber_key" ON public.supplier_quotations USING btree ("branchId", "quotationNumber");


--
-- Name: supplier_quotations_branchId_supplierId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "supplier_quotations_branchId_supplierId_idx" ON public.supplier_quotations USING btree ("branchId", "supplierId");


--
-- Name: suppliers_branchId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "suppliers_branchId_idx" ON public.suppliers USING btree ("branchId");


--
-- Name: sync_changes_row_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX sync_changes_row_idx ON public.sync_changes USING btree (tbl, "pkKey");


--
-- Name: table_accesses_tableId_expiresAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "table_accesses_tableId_expiresAt_idx" ON public.table_accesses USING btree ("tableId", "expiresAt");


--
-- Name: table_accesses_tokenHash_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "table_accesses_tokenHash_key" ON public.table_accesses USING btree ("tokenHash");


--
-- Name: table_requests_branchId_resolvedAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "table_requests_branchId_resolvedAt_idx" ON public.table_requests USING btree ("branchId", "resolvedAt");


--
-- Name: table_requests_tableId_type_resolvedAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "table_requests_tableId_type_resolvedAt_idx" ON public.table_requests USING btree ("tableId", type, "resolvedAt");


--
-- Name: table_session_grants_sessionId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "table_session_grants_sessionId_idx" ON public.table_session_grants USING btree ("sessionId");


--
-- Name: table_session_grants_tokenHash_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "table_session_grants_tokenHash_key" ON public.table_session_grants USING btree ("tokenHash");


--
-- Name: table_sessions_tableId_status_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "table_sessions_tableId_status_idx" ON public.table_sessions USING btree ("tableId", status);


--
-- Name: tables_floorId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "tables_floorId_idx" ON public.tables USING btree ("floorId");


--
-- Name: tables_floorId_number_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "tables_floorId_number_key" ON public.tables USING btree ("floorId", number);


--
-- Name: tables_qrToken_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "tables_qrToken_key" ON public.tables USING btree ("qrToken");


--
-- Name: users_restaurantId_email_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "users_restaurantId_email_key" ON public.users USING btree ("restaurantId", email);


--
-- Name: users_restaurantId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "users_restaurantId_idx" ON public.users USING btree ("restaurantId");


--
-- Name: verifactu_records_branchId_status_nextAttemptAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "verifactu_records_branchId_status_nextAttemptAt_idx" ON public.verifactu_records USING btree ("branchId", status, "nextAttemptAt");


--
-- Name: verifactu_records_orderId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "verifactu_records_orderId_idx" ON public.verifactu_records USING btree ("orderId");


--
-- Name: verifactu_records_restaurantId_issuerNif_environment_invoic_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "verifactu_records_restaurantId_issuerNif_environment_invoic_key" ON public.verifactu_records USING btree ("restaurantId", "issuerNif", environment, "invoiceNumber", type);


--
-- Name: verifactu_records_restaurantId_issuerNif_environment_seq_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "verifactu_records_restaurantId_issuerNif_environment_seq_key" ON public.verifactu_records USING btree ("restaurantId", "issuerNif", environment, seq);


--
-- Name: verifactu_settings_branchId_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "verifactu_settings_branchId_key" ON public.verifactu_settings USING btree ("branchId");


--
-- Name: waitlist_entries_branchId_status_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "waitlist_entries_branchId_status_idx" ON public.waitlist_entries USING btree ("branchId", status);


--
-- Name: waste_entries_branchId_idempotencyKey_key; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE UNIQUE INDEX "waste_entries_branchId_idempotencyKey_key" ON public.waste_entries USING btree ("branchId", "idempotencyKey");


--
-- Name: waste_entries_branchId_occurredAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "waste_entries_branchId_occurredAt_idx" ON public.waste_entries USING btree ("branchId", "occurredAt");


--
-- Name: waste_entries_ingredientId_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "waste_entries_ingredientId_idx" ON public.waste_entries USING btree ("ingredientId");


--
-- Name: waste_logs_branchId_ingredientId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "waste_logs_branchId_ingredientId_createdAt_idx" ON public.waste_logs USING btree ("branchId", "ingredientId", "createdAt");


--
-- Name: webhook_deliveries_endpointId_createdAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "webhook_deliveries_endpointId_createdAt_idx" ON public.webhook_deliveries USING btree ("endpointId", "createdAt");


--
-- Name: webhook_deliveries_status_nextAttemptAt_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "webhook_deliveries_status_nextAttemptAt_idx" ON public.webhook_deliveries USING btree (status, "nextAttemptAt");


--
-- Name: webhook_endpoints_restaurantId_isActive_idx; Type: INDEX; Schema: public; Owner: nodedr
--

CREATE INDEX "webhook_endpoints_restaurantId_isActive_idx" ON public.webhook_endpoints USING btree ("restaurantId", "isActive");


--
-- Name: attendance sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.attendance FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: audit_logs sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.audit_logs FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: bank_transactions sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.bank_transactions FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: branches sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.branches FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: budgets sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.budgets FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: buzzer_calls sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.buzzer_calls FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: buzzers sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.buzzers FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: campaigns sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.campaigns FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: cash_closings sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.cash_closings FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: combo_components sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.combo_components FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: coupons sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.coupons FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: customer_addresses sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.customer_addresses FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: customers sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.customers FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: delivery_assignments sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.delivery_assignments FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: delivery_zones sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.delivery_zones FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: departments sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.departments FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: device_tokens sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.device_tokens FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: display_ads sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.display_ads FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: display_terminals sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.display_terminals FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: document_files sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.document_files FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: documents sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.documents FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: equipment sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.equipment FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: expenses sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.expenses FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: floor_layouts sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.floor_layouts FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: floors sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.floors FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: gateway_payments sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.gateway_payments FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: gateway_refunds sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.gateway_refunds FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: gateway_webhook_events sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.gateway_webhook_events FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: gift_card_redemptions sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.gift_card_redemptions FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: gift_cards sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.gift_cards FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: goods_receipt_items sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.goods_receipt_items FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: goods_receipts sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.goods_receipts FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: ingredients sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.ingredients FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: integration_api_keys sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.integration_api_keys FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: integration_connections sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.integration_connections FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: integration_logs sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.integration_logs FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: kitchen_stations sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.kitchen_stations FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: kot_items sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.kot_items FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: kots sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.kots FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: leave_requests sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.leave_requests FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: licenses sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.licenses FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: location_transfers sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.location_transfers FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: menu_categories sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.menu_categories FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: menu_item_costings sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.menu_item_costings FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: menu_item_modifier_groups sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.menu_item_modifier_groups FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('menuItemId', 'modifierGroupId');


--
-- Name: menu_items sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.menu_items FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: menu_price_changes sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.menu_price_changes FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: modifier_groups sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.modifier_groups FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: modifier_ingredients sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.modifier_ingredients FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: modifiers sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.modifiers FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: nfc_tags sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.nfc_tags FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: nfc_taps sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.nfc_taps FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: notifications sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.notifications FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: order_item_costs sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.order_item_costs FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('orderItemId');


--
-- Name: order_item_modifiers sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.order_item_modifiers FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: order_item_stock_returns sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.order_item_stock_returns FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: order_items sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.order_items FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: order_ratings sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.order_ratings FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: orders sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.orders FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: payment_gateway_catalog sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.payment_gateway_catalog FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: payment_gateway_connections sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.payment_gateway_connections FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: payments sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.payments FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: payroll_lines sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.payroll_lines FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: payroll_runs sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.payroll_runs FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: permissions sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.permissions FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: phone_till_closings sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.phone_till_closings FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: points_ledger sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.points_ledger FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: pos_devices sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.pos_devices FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: preparation_lines sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.preparation_lines FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: preparations sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.preparations FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: product_recipe_lines sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.product_recipe_lines FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: product_recipes sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.product_recipes FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: production_costs sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.production_costs FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: production_entries sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.production_entries FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: production_lines sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.production_lines FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: production_runs sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.production_runs FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: promotions sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.promotions FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: public_order_keys sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.public_order_keys FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: purchase_order_items sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.purchase_order_items FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: purchase_orders sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.purchase_orders FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: purchase_request_items sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.purchase_request_items FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: purchase_requests sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.purchase_requests FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: recipe_ingredients sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.recipe_ingredients FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: referrals sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.referrals FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: refunds sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.refunds FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: report_schedules sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.report_schedules FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: reservations sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.reservations FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: restaurants sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.restaurants FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: role_permissions sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.role_permissions FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('roleId', 'permissionId');


--
-- Name: roles sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.roles FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: service_logs sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.service_logs FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: shifts sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.shifts FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: staff_api_keys sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.staff_api_keys FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: staff_pay sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.staff_pay FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('userId');


--
-- Name: stock_batches sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.stock_batches FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: stock_journal_entries sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.stock_journal_entries FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: stock_journal_lines sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.stock_journal_lines FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: stock_levels sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.stock_levels FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: stock_locations sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.stock_locations FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: stock_movements sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.stock_movements FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: stock_takes sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.stock_takes FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: stock_transfers sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.stock_transfers FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: supplier_invoices sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.supplier_invoices FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: supplier_payments sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.supplier_payments FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: supplier_quotation_items sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.supplier_quotation_items FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: supplier_quotations sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.supplier_quotations FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: suppliers sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.suppliers FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: table_accesses sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.table_accesses FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: table_requests sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.table_requests FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: table_session_grants sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.table_session_grants FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: table_sessions sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.table_sessions FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: tables sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.tables FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: user_branches sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.user_branches FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('userId', 'branchId');


--
-- Name: user_permission_overrides sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.user_permission_overrides FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('userId', 'permissionId');


--
-- Name: users sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: verifactu_settings sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.verifactu_settings FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: waitlist_entries sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.waitlist_entries FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: waste_entries sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.waste_entries FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: waste_logs sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.waste_logs FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: webhook_endpoints sync_log; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER sync_log AFTER INSERT OR DELETE OR UPDATE ON public.webhook_endpoints FOR EACH ROW EXECUTE FUNCTION public.sync_log_change('id');


--
-- Name: verifactu_records verifactu_records_guard; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER verifactu_records_guard BEFORE INSERT OR DELETE OR UPDATE ON public.verifactu_records FOR EACH ROW EXECUTE FUNCTION public.verifactu_records_guard();


--
-- Name: verifactu_records verifactu_records_no_truncate; Type: TRIGGER; Schema: public; Owner: nodedr
--

CREATE TRIGGER verifactu_records_no_truncate BEFORE TRUNCATE ON public.verifactu_records FOR EACH STATEMENT EXECUTE FUNCTION public.verifactu_records_no_truncate();


--
-- Name: attendance attendance_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.attendance
    ADD CONSTRAINT "attendance_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: attendance attendance_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.attendance
    ADD CONSTRAINT "attendance_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: audit_logs audit_logs_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT "audit_logs_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: backups backups_triggeredById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.backups
    ADD CONSTRAINT "backups_triggeredById_fkey" FOREIGN KEY ("triggeredById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: bank_transactions bank_transactions_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.bank_transactions
    ADD CONSTRAINT "bank_transactions_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: branches branches_restaurantId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.branches
    ADD CONSTRAINT "branches_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES public.restaurants(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: budgets budgets_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.budgets
    ADD CONSTRAINT "budgets_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: buzzer_calls buzzer_calls_buzzerId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.buzzer_calls
    ADD CONSTRAINT "buzzer_calls_buzzerId_fkey" FOREIGN KEY ("buzzerId") REFERENCES public.buzzers(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: buzzers buzzers_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.buzzers
    ADD CONSTRAINT "buzzers_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: campaigns campaigns_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.campaigns
    ADD CONSTRAINT "campaigns_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: cash_closings cash_closings_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.cash_closings
    ADD CONSTRAINT "cash_closings_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: combo_components combo_components_comboItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.combo_components
    ADD CONSTRAINT "combo_components_comboItemId_fkey" FOREIGN KEY ("comboItemId") REFERENCES public.menu_items(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: combo_components combo_components_componentItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.combo_components
    ADD CONSTRAINT "combo_components_componentItemId_fkey" FOREIGN KEY ("componentItemId") REFERENCES public.menu_items(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: coupons coupons_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.coupons
    ADD CONSTRAINT "coupons_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: customer_addresses customer_addresses_customerId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.customer_addresses
    ADD CONSTRAINT "customer_addresses_customerId_fkey" FOREIGN KEY ("customerId") REFERENCES public.customers(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: customers customers_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT "customers_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: delivery_assignments delivery_assignments_assignedById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.delivery_assignments
    ADD CONSTRAINT "delivery_assignments_assignedById_fkey" FOREIGN KEY ("assignedById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: delivery_assignments delivery_assignments_orderId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.delivery_assignments
    ADD CONSTRAINT "delivery_assignments_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES public.orders(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: delivery_zones delivery_zones_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.delivery_zones
    ADD CONSTRAINT "delivery_zones_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: departments departments_restaurantId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT "departments_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES public.restaurants(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: device_tokens device_tokens_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.device_tokens
    ADD CONSTRAINT "device_tokens_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: display_ads display_ads_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.display_ads
    ADD CONSTRAINT "display_ads_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: display_terminals display_terminals_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.display_terminals
    ADD CONSTRAINT "display_terminals_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: document_files document_files_documentId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.document_files
    ADD CONSTRAINT "document_files_documentId_fkey" FOREIGN KEY ("documentId") REFERENCES public.documents(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: documents documents_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT "documents_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: equipment equipment_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.equipment
    ADD CONSTRAINT "equipment_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: expenses expenses_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT "expenses_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: expenses expenses_createdById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT "expenses_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: floor_layouts floor_layouts_floorId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.floor_layouts
    ADD CONSTRAINT "floor_layouts_floorId_fkey" FOREIGN KEY ("floorId") REFERENCES public.floors(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: floors floors_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.floors
    ADD CONSTRAINT "floors_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: gateway_payments gateway_payments_restaurantId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.gateway_payments
    ADD CONSTRAINT "gateway_payments_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES public.restaurants(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: gateway_refunds gateway_refunds_restaurantId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.gateway_refunds
    ADD CONSTRAINT "gateway_refunds_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES public.restaurants(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: gift_card_redemptions gift_card_redemptions_giftCardId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.gift_card_redemptions
    ADD CONSTRAINT "gift_card_redemptions_giftCardId_fkey" FOREIGN KEY ("giftCardId") REFERENCES public.gift_cards(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: gift_card_redemptions gift_card_redemptions_orderId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.gift_card_redemptions
    ADD CONSTRAINT "gift_card_redemptions_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES public.orders(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: gift_cards gift_cards_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.gift_cards
    ADD CONSTRAINT "gift_cards_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: gift_cards gift_cards_customerId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.gift_cards
    ADD CONSTRAINT "gift_cards_customerId_fkey" FOREIGN KEY ("customerId") REFERENCES public.customers(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: goods_receipt_items goods_receipt_items_goodsReceiptId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.goods_receipt_items
    ADD CONSTRAINT "goods_receipt_items_goodsReceiptId_fkey" FOREIGN KEY ("goodsReceiptId") REFERENCES public.goods_receipts(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: goods_receipt_items goods_receipt_items_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.goods_receipt_items
    ADD CONSTRAINT "goods_receipt_items_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: goods_receipt_items goods_receipt_items_purchaseOrderItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.goods_receipt_items
    ADD CONSTRAINT "goods_receipt_items_purchaseOrderItemId_fkey" FOREIGN KEY ("purchaseOrderItemId") REFERENCES public.purchase_order_items(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: goods_receipts goods_receipts_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.goods_receipts
    ADD CONSTRAINT "goods_receipts_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: goods_receipts goods_receipts_purchaseOrderId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.goods_receipts
    ADD CONSTRAINT "goods_receipts_purchaseOrderId_fkey" FOREIGN KEY ("purchaseOrderId") REFERENCES public.purchase_orders(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: goods_receipts goods_receipts_receivedById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.goods_receipts
    ADD CONSTRAINT "goods_receipts_receivedById_fkey" FOREIGN KEY ("receivedById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: goods_receipts goods_receipts_supplierId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.goods_receipts
    ADD CONSTRAINT "goods_receipts_supplierId_fkey" FOREIGN KEY ("supplierId") REFERENCES public.suppliers(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: ingredients ingredients_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.ingredients
    ADD CONSTRAINT "ingredients_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: integration_api_keys integration_api_keys_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.integration_api_keys
    ADD CONSTRAINT "integration_api_keys_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: integration_api_keys integration_api_keys_createdById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.integration_api_keys
    ADD CONSTRAINT "integration_api_keys_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: integration_api_keys integration_api_keys_restaurantId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.integration_api_keys
    ADD CONSTRAINT "integration_api_keys_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES public.restaurants(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: integration_connections integration_connections_restaurantId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.integration_connections
    ADD CONSTRAINT "integration_connections_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES public.restaurants(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: integration_logs integration_logs_connectionId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.integration_logs
    ADD CONSTRAINT "integration_logs_connectionId_fkey" FOREIGN KEY ("connectionId") REFERENCES public.integration_connections(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: kitchen_stations kitchen_stations_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.kitchen_stations
    ADD CONSTRAINT "kitchen_stations_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: kot_items kot_items_kotId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.kot_items
    ADD CONSTRAINT "kot_items_kotId_fkey" FOREIGN KEY ("kotId") REFERENCES public.kots(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: kot_items kot_items_orderItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.kot_items
    ADD CONSTRAINT "kot_items_orderItemId_fkey" FOREIGN KEY ("orderItemId") REFERENCES public.order_items(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: kots kots_orderId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.kots
    ADD CONSTRAINT "kots_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES public.orders(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: kots kots_stationId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.kots
    ADD CONSTRAINT "kots_stationId_fkey" FOREIGN KEY ("stationId") REFERENCES public.kitchen_stations(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: leave_requests leave_requests_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.leave_requests
    ADD CONSTRAINT "leave_requests_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: leave_requests leave_requests_decidedById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.leave_requests
    ADD CONSTRAINT "leave_requests_decidedById_fkey" FOREIGN KEY ("decidedById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: leave_requests leave_requests_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.leave_requests
    ADD CONSTRAINT "leave_requests_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: licenses licenses_restaurantId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.licenses
    ADD CONSTRAINT "licenses_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES public.restaurants(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: menu_categories menu_categories_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_categories
    ADD CONSTRAINT "menu_categories_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: menu_item_costings menu_item_costings_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_item_costings
    ADD CONSTRAINT "menu_item_costings_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: menu_item_costings menu_item_costings_menuItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_item_costings
    ADD CONSTRAINT "menu_item_costings_menuItemId_fkey" FOREIGN KEY ("menuItemId") REFERENCES public.menu_items(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: menu_item_modifier_groups menu_item_modifier_groups_menuItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_item_modifier_groups
    ADD CONSTRAINT "menu_item_modifier_groups_menuItemId_fkey" FOREIGN KEY ("menuItemId") REFERENCES public.menu_items(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: menu_item_modifier_groups menu_item_modifier_groups_modifierGroupId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_item_modifier_groups
    ADD CONSTRAINT "menu_item_modifier_groups_modifierGroupId_fkey" FOREIGN KEY ("modifierGroupId") REFERENCES public.modifier_groups(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: menu_items menu_items_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT "menu_items_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: menu_items menu_items_categoryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT "menu_items_categoryId_fkey" FOREIGN KEY ("categoryId") REFERENCES public.menu_categories(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: menu_items menu_items_stationId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT "menu_items_stationId_fkey" FOREIGN KEY ("stationId") REFERENCES public.kitchen_stations(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: menu_items menu_items_stockIngredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.menu_items
    ADD CONSTRAINT "menu_items_stockIngredientId_fkey" FOREIGN KEY ("stockIngredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: modifier_groups modifier_groups_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.modifier_groups
    ADD CONSTRAINT "modifier_groups_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: modifier_ingredients modifier_ingredients_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.modifier_ingredients
    ADD CONSTRAINT "modifier_ingredients_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: modifier_ingredients modifier_ingredients_modifierId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.modifier_ingredients
    ADD CONSTRAINT "modifier_ingredients_modifierId_fkey" FOREIGN KEY ("modifierId") REFERENCES public.modifiers(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: modifiers modifiers_groupId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.modifiers
    ADD CONSTRAINT "modifiers_groupId_fkey" FOREIGN KEY ("groupId") REFERENCES public.modifier_groups(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: nfc_tags nfc_tags_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.nfc_tags
    ADD CONSTRAINT "nfc_tags_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: nfc_tags nfc_tags_tableId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.nfc_tags
    ADD CONSTRAINT "nfc_tags_tableId_fkey" FOREIGN KEY ("tableId") REFERENCES public.tables(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: nfc_taps nfc_taps_tagId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.nfc_taps
    ADD CONSTRAINT "nfc_taps_tagId_fkey" FOREIGN KEY ("tagId") REFERENCES public.nfc_tags(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: notifications notifications_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT "notifications_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: notifications notifications_recipientUserId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT "notifications_recipientUserId_fkey" FOREIGN KEY ("recipientUserId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: order_item_costs order_item_costs_orderItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.order_item_costs
    ADD CONSTRAINT "order_item_costs_orderItemId_fkey" FOREIGN KEY ("orderItemId") REFERENCES public.order_items(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: order_item_modifiers order_item_modifiers_modifierId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.order_item_modifiers
    ADD CONSTRAINT "order_item_modifiers_modifierId_fkey" FOREIGN KEY ("modifierId") REFERENCES public.modifiers(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: order_item_modifiers order_item_modifiers_orderItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.order_item_modifiers
    ADD CONSTRAINT "order_item_modifiers_orderItemId_fkey" FOREIGN KEY ("orderItemId") REFERENCES public.order_items(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: order_item_stock_returns order_item_stock_returns_orderItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.order_item_stock_returns
    ADD CONSTRAINT "order_item_stock_returns_orderItemId_fkey" FOREIGN KEY ("orderItemId") REFERENCES public.order_items(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: order_item_stock_returns order_item_stock_returns_refundId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.order_item_stock_returns
    ADD CONSTRAINT "order_item_stock_returns_refundId_fkey" FOREIGN KEY ("refundId") REFERENCES public.refunds(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: order_items order_items_menuItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT "order_items_menuItemId_fkey" FOREIGN KEY ("menuItemId") REFERENCES public.menu_items(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: order_items order_items_orderId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT "order_items_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES public.orders(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: orders orders_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT "orders_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: orders orders_createdById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT "orders_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: orders orders_customerId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT "orders_customerId_fkey" FOREIGN KEY ("customerId") REFERENCES public.customers(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: orders orders_deliveryZoneId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT "orders_deliveryZoneId_fkey" FOREIGN KEY ("deliveryZoneId") REFERENCES public.delivery_zones(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: orders orders_driverId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT "orders_driverId_fkey" FOREIGN KEY ("driverId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: orders orders_integrationKeyId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT "orders_integrationKeyId_fkey" FOREIGN KEY ("integrationKeyId") REFERENCES public.integration_api_keys(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: orders orders_tableId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT "orders_tableId_fkey" FOREIGN KEY ("tableId") REFERENCES public.tables(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: payment_gateway_catalog payment_gateway_catalog_restaurantId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.payment_gateway_catalog
    ADD CONSTRAINT "payment_gateway_catalog_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES public.restaurants(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: payment_gateway_connections payment_gateway_connections_restaurantId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.payment_gateway_connections
    ADD CONSTRAINT "payment_gateway_connections_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES public.restaurants(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: payments payments_orderId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT "payments_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES public.orders(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: payroll_lines payroll_lines_runId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.payroll_lines
    ADD CONSTRAINT "payroll_lines_runId_fkey" FOREIGN KEY ("runId") REFERENCES public.payroll_runs(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: payroll_lines payroll_lines_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.payroll_lines
    ADD CONSTRAINT "payroll_lines_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: payroll_runs payroll_runs_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.payroll_runs
    ADD CONSTRAINT "payroll_runs_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: phone_till_closings phone_till_closings_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.phone_till_closings
    ADD CONSTRAINT "phone_till_closings_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: points_ledger points_ledger_customerId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.points_ledger
    ADD CONSTRAINT "points_ledger_customerId_fkey" FOREIGN KEY ("customerId") REFERENCES public.customers(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: pos_devices pos_devices_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.pos_devices
    ADD CONSTRAINT "pos_devices_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: preparation_lines preparation_lines_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.preparation_lines
    ADD CONSTRAINT "preparation_lines_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: preparation_lines preparation_lines_preparationId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.preparation_lines
    ADD CONSTRAINT "preparation_lines_preparationId_fkey" FOREIGN KEY ("preparationId") REFERENCES public.preparations(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: preparations preparations_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.preparations
    ADD CONSTRAINT "preparations_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: preparations preparations_outputIngredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.preparations
    ADD CONSTRAINT "preparations_outputIngredientId_fkey" FOREIGN KEY ("outputIngredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: product_recipe_lines product_recipe_lines_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.product_recipe_lines
    ADD CONSTRAINT "product_recipe_lines_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: product_recipe_lines product_recipe_lines_recipeId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.product_recipe_lines
    ADD CONSTRAINT "product_recipe_lines_recipeId_fkey" FOREIGN KEY ("recipeId") REFERENCES public.product_recipes(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: product_recipes product_recipes_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.product_recipes
    ADD CONSTRAINT "product_recipes_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: product_recipes product_recipes_outputIngredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.product_recipes
    ADD CONSTRAINT "product_recipes_outputIngredientId_fkey" FOREIGN KEY ("outputIngredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: production_costs production_costs_entryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.production_costs
    ADD CONSTRAINT "production_costs_entryId_fkey" FOREIGN KEY ("entryId") REFERENCES public.production_entries(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: production_entries production_entries_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.production_entries
    ADD CONSTRAINT "production_entries_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: production_entries production_entries_correctsEntryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.production_entries
    ADD CONSTRAINT "production_entries_correctsEntryId_fkey" FOREIGN KEY ("correctsEntryId") REFERENCES public.production_entries(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: production_lines production_lines_entryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.production_lines
    ADD CONSTRAINT "production_lines_entryId_fkey" FOREIGN KEY ("entryId") REFERENCES public.production_entries(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: production_lines production_lines_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.production_lines
    ADD CONSTRAINT "production_lines_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: production_runs production_runs_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.production_runs
    ADD CONSTRAINT "production_runs_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: production_runs production_runs_preparationId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.production_runs
    ADD CONSTRAINT "production_runs_preparationId_fkey" FOREIGN KEY ("preparationId") REFERENCES public.preparations(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: promotions promotions_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.promotions
    ADD CONSTRAINT "promotions_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: purchase_order_items purchase_order_items_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_order_items
    ADD CONSTRAINT "purchase_order_items_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: purchase_order_items purchase_order_items_purchaseOrderId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_order_items
    ADD CONSTRAINT "purchase_order_items_purchaseOrderId_fkey" FOREIGN KEY ("purchaseOrderId") REFERENCES public.purchase_orders(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: purchase_orders purchase_orders_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT "purchase_orders_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: purchase_orders purchase_orders_createdById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT "purchase_orders_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: purchase_orders purchase_orders_supplierId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT "purchase_orders_supplierId_fkey" FOREIGN KEY ("supplierId") REFERENCES public.suppliers(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: purchase_request_items purchase_request_items_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_request_items
    ADD CONSTRAINT "purchase_request_items_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: purchase_request_items purchase_request_items_purchaseRequestId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_request_items
    ADD CONSTRAINT "purchase_request_items_purchaseRequestId_fkey" FOREIGN KEY ("purchaseRequestId") REFERENCES public.purchase_requests(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: purchase_requests purchase_requests_approvedById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_requests
    ADD CONSTRAINT "purchase_requests_approvedById_fkey" FOREIGN KEY ("approvedById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: purchase_requests purchase_requests_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_requests
    ADD CONSTRAINT "purchase_requests_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: purchase_requests purchase_requests_requestedById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.purchase_requests
    ADD CONSTRAINT "purchase_requests_requestedById_fkey" FOREIGN KEY ("requestedById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: recipe_ingredients recipe_ingredients_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.recipe_ingredients
    ADD CONSTRAINT "recipe_ingredients_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: recipe_ingredients recipe_ingredients_menuItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.recipe_ingredients
    ADD CONSTRAINT "recipe_ingredients_menuItemId_fkey" FOREIGN KEY ("menuItemId") REFERENCES public.menu_items(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: referrals referrals_referredId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT "referrals_referredId_fkey" FOREIGN KEY ("referredId") REFERENCES public.customers(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: referrals referrals_referrerId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT "referrals_referrerId_fkey" FOREIGN KEY ("referrerId") REFERENCES public.customers(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: refunds refunds_createdById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.refunds
    ADD CONSTRAINT "refunds_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: refunds refunds_orderId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.refunds
    ADD CONSTRAINT "refunds_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES public.orders(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: report_schedules report_schedules_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.report_schedules
    ADD CONSTRAINT "report_schedules_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: reservations reservations_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.reservations
    ADD CONSTRAINT "reservations_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: reservations reservations_tableId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.reservations
    ADD CONSTRAINT "reservations_tableId_fkey" FOREIGN KEY ("tableId") REFERENCES public.tables(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: role_permissions role_permissions_permissionId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT "role_permissions_permissionId_fkey" FOREIGN KEY ("permissionId") REFERENCES public.permissions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_roleId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT "role_permissions_roleId_fkey" FOREIGN KEY ("roleId") REFERENCES public.roles(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: roles roles_restaurantId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT "roles_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES public.restaurants(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: service_logs service_logs_equipmentId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.service_logs
    ADD CONSTRAINT "service_logs_equipmentId_fkey" FOREIGN KEY ("equipmentId") REFERENCES public.equipment(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: shifts shifts_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.shifts
    ADD CONSTRAINT "shifts_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: shifts shifts_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.shifts
    ADD CONSTRAINT "shifts_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: staff_api_keys staff_api_keys_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.staff_api_keys
    ADD CONSTRAINT "staff_api_keys_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: staff_pay staff_pay_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.staff_pay
    ADD CONSTRAINT "staff_pay_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: stock_batches stock_batches_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_batches
    ADD CONSTRAINT "stock_batches_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: stock_batches stock_batches_goodsReceiptItemId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_batches
    ADD CONSTRAINT "stock_batches_goodsReceiptItemId_fkey" FOREIGN KEY ("goodsReceiptItemId") REFERENCES public.goods_receipt_items(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: stock_batches stock_batches_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_batches
    ADD CONSTRAINT "stock_batches_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: stock_journal_entries stock_journal_entries_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_journal_entries
    ADD CONSTRAINT "stock_journal_entries_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: stock_journal_lines stock_journal_lines_entryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_journal_lines
    ADD CONSTRAINT "stock_journal_lines_entryId_fkey" FOREIGN KEY ("entryId") REFERENCES public.stock_journal_entries(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: stock_journal_lines stock_journal_lines_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_journal_lines
    ADD CONSTRAINT "stock_journal_lines_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: stock_levels stock_levels_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_levels
    ADD CONSTRAINT "stock_levels_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: stock_levels stock_levels_locationId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_levels
    ADD CONSTRAINT "stock_levels_locationId_fkey" FOREIGN KEY ("locationId") REFERENCES public.stock_locations(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: stock_locations stock_locations_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_locations
    ADD CONSTRAINT "stock_locations_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: stock_movements stock_movements_batchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT "stock_movements_batchId_fkey" FOREIGN KEY ("batchId") REFERENCES public.stock_batches(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: stock_movements stock_movements_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT "stock_movements_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: stock_movements stock_movements_createdById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT "stock_movements_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: stock_movements stock_movements_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT "stock_movements_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: stock_takes stock_takes_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.stock_takes
    ADD CONSTRAINT "stock_takes_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: supplier_invoices supplier_invoices_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_invoices
    ADD CONSTRAINT "supplier_invoices_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: supplier_invoices supplier_invoices_goodsReceiptId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_invoices
    ADD CONSTRAINT "supplier_invoices_goodsReceiptId_fkey" FOREIGN KEY ("goodsReceiptId") REFERENCES public.goods_receipts(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: supplier_invoices supplier_invoices_purchaseOrderId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_invoices
    ADD CONSTRAINT "supplier_invoices_purchaseOrderId_fkey" FOREIGN KEY ("purchaseOrderId") REFERENCES public.purchase_orders(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: supplier_invoices supplier_invoices_recordedById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_invoices
    ADD CONSTRAINT "supplier_invoices_recordedById_fkey" FOREIGN KEY ("recordedById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: supplier_invoices supplier_invoices_supplierId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_invoices
    ADD CONSTRAINT "supplier_invoices_supplierId_fkey" FOREIGN KEY ("supplierId") REFERENCES public.suppliers(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: supplier_payments supplier_payments_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_payments
    ADD CONSTRAINT "supplier_payments_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: supplier_payments supplier_payments_recordedById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_payments
    ADD CONSTRAINT "supplier_payments_recordedById_fkey" FOREIGN KEY ("recordedById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: supplier_payments supplier_payments_supplierInvoiceId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_payments
    ADD CONSTRAINT "supplier_payments_supplierInvoiceId_fkey" FOREIGN KEY ("supplierInvoiceId") REFERENCES public.supplier_invoices(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: supplier_quotation_items supplier_quotation_items_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_quotation_items
    ADD CONSTRAINT "supplier_quotation_items_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: supplier_quotation_items supplier_quotation_items_supplierQuotationId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_quotation_items
    ADD CONSTRAINT "supplier_quotation_items_supplierQuotationId_fkey" FOREIGN KEY ("supplierQuotationId") REFERENCES public.supplier_quotations(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: supplier_quotations supplier_quotations_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_quotations
    ADD CONSTRAINT "supplier_quotations_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: supplier_quotations supplier_quotations_createdById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_quotations
    ADD CONSTRAINT "supplier_quotations_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: supplier_quotations supplier_quotations_supplierId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.supplier_quotations
    ADD CONSTRAINT "supplier_quotations_supplierId_fkey" FOREIGN KEY ("supplierId") REFERENCES public.suppliers(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: suppliers suppliers_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT "suppliers_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: table_accesses table_accesses_tableId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.table_accesses
    ADD CONSTRAINT "table_accesses_tableId_fkey" FOREIGN KEY ("tableId") REFERENCES public.tables(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: table_requests table_requests_tableId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.table_requests
    ADD CONSTRAINT "table_requests_tableId_fkey" FOREIGN KEY ("tableId") REFERENCES public.tables(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: table_session_grants table_session_grants_sessionId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.table_session_grants
    ADD CONSTRAINT "table_session_grants_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES public.table_sessions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: tables tables_assignedWaiterId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.tables
    ADD CONSTRAINT "tables_assignedWaiterId_fkey" FOREIGN KEY ("assignedWaiterId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: tables tables_floorId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.tables
    ADD CONSTRAINT "tables_floorId_fkey" FOREIGN KEY ("floorId") REFERENCES public.floors(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_branches user_branches_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.user_branches
    ADD CONSTRAINT "user_branches_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_branches user_branches_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.user_branches
    ADD CONSTRAINT "user_branches_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_permission_overrides user_permission_overrides_permissionId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.user_permission_overrides
    ADD CONSTRAINT "user_permission_overrides_permissionId_fkey" FOREIGN KEY ("permissionId") REFERENCES public.permissions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: user_permission_overrides user_permission_overrides_userId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.user_permission_overrides
    ADD CONSTRAINT "user_permission_overrides_userId_fkey" FOREIGN KEY ("userId") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: users users_departmentId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT "users_departmentId_fkey" FOREIGN KEY ("departmentId") REFERENCES public.departments(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: users users_restaurantId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT "users_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES public.restaurants(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: users users_roleId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT "users_roleId_fkey" FOREIGN KEY ("roleId") REFERENCES public.roles(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: verifactu_records verifactu_records_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.verifactu_records
    ADD CONSTRAINT "verifactu_records_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: verifactu_settings verifactu_settings_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.verifactu_settings
    ADD CONSTRAINT "verifactu_settings_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: waitlist_entries waitlist_entries_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.waitlist_entries
    ADD CONSTRAINT "waitlist_entries_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: waitlist_entries waitlist_entries_tableId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.waitlist_entries
    ADD CONSTRAINT "waitlist_entries_tableId_fkey" FOREIGN KEY ("tableId") REFERENCES public.tables(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: waste_entries waste_entries_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.waste_entries
    ADD CONSTRAINT "waste_entries_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: waste_entries waste_entries_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.waste_entries
    ADD CONSTRAINT "waste_entries_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: waste_logs waste_logs_batchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.waste_logs
    ADD CONSTRAINT "waste_logs_batchId_fkey" FOREIGN KEY ("batchId") REFERENCES public.stock_batches(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: waste_logs waste_logs_branchId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.waste_logs
    ADD CONSTRAINT "waste_logs_branchId_fkey" FOREIGN KEY ("branchId") REFERENCES public.branches(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: waste_logs waste_logs_createdById_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.waste_logs
    ADD CONSTRAINT "waste_logs_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: waste_logs waste_logs_entryId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.waste_logs
    ADD CONSTRAINT "waste_logs_entryId_fkey" FOREIGN KEY ("entryId") REFERENCES public.waste_entries(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: waste_logs waste_logs_ingredientId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.waste_logs
    ADD CONSTRAINT "waste_logs_ingredientId_fkey" FOREIGN KEY ("ingredientId") REFERENCES public.ingredients(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: webhook_deliveries webhook_deliveries_endpointId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.webhook_deliveries
    ADD CONSTRAINT "webhook_deliveries_endpointId_fkey" FOREIGN KEY ("endpointId") REFERENCES public.webhook_endpoints(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: webhook_endpoints webhook_endpoints_restaurantId_fkey; Type: FK CONSTRAINT; Schema: public; Owner: nodedr
--

ALTER TABLE ONLY public.webhook_endpoints
    ADD CONSTRAINT "webhook_endpoints_restaurantId_fkey" FOREIGN KEY ("restaurantId") REFERENCES public.restaurants(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 07dLQt0aCP10Ac7ZYuSovyibD3J3X4Ksil4DlwdMX7nbQgaonhAimrqazWrpCo6

