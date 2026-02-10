-- =========================
-- Raw tables
-- =========================

create table if not exists ad_event_log (
  event_time      timestamp,
  date            date,
  user_id         varchar(64),
  campaign_id     varchar(64),
  channel         varchar(32),
  country         varchar(8),
  event_type      varchar(16),   -- impression | click
  cost            numeric(12,4),
  device          varchar(16)    -- mobile | desktop
);

create table if not exists payment_log (
  payment_time    timestamp,
  date            date,
  user_id         varchar(64),
  order_id        varchar(64),
  campaign_id     varchar(64),
  amount          numeric(12,2),
  success_yn      char(1),       -- Y | N
  fail_reason     varchar(32)
);

-- =========================
-- Mart table
-- =========================

create table if not exists mart_daily_campaign_kpi (
  date                 date,
  campaign_id          varchar(64),
  channel              varchar(32),
  country              varchar(8),

  impressions          bigint,
  clicks               bigint,
  ctr                  numeric(12,6),

  payment_attempts     bigint,
  conversions          bigint,
  payment_success_rate numeric(12,6),

  revenue              numeric(18,2),
  cost                 numeric(18,4),
  conversion_rate      numeric(12,6),
  roas                 numeric(12,6),

  updated_at           timestamp default current_timestamp
);
