-- =========================================================
-- Raw & Mart Table DDL
--
-- 목적:
--   - 광고 이벤트 로그 / 결제 로그를 Raw 테이블로 저장
--   - BI 및 Text2SQL에서 직접 조회할 KPI Mart 테이블 정의
--
-- 설계 원칙:
--   1) Raw 테이블은 최대한 원본 형태 유지
--   2) 시간 컬럼(event_time, payment_time)은 VARCHAR로 저장
--      → CSV 파싱/타입 이슈 방지
--      → Mart 단계에서 명시적 CAST
--   3) 집계/비율 계산은 Mart에서만 수행
-- =========================================================


-- =========================================================
-- Raw Table: ad_event_log
-- =========================================================
-- 광고 이벤트 단위 로그
-- impression / click 이벤트가 row 단위로 적재됨
create table if not exists ad_event_log (
  event_time      varchar,        -- 이벤트 발생 시각 (Raw 단계에서는 문자열로 유지)
  date            date,            -- 집계 기준 일자
  user_id         varchar(64),     -- 사용자 ID
  campaign_id     varchar(64),     -- 캠페인 ID
  channel         varchar(32),     -- 유입 채널 (search, social 등)
  country         varchar(8),      -- 국가 코드
  event_type      varchar(16),     -- impression | click
  cost            numeric(12,4),   -- 이벤트 단위 비용
  device          varchar(16)      -- mobile | desktop
);


-- =========================================================
-- Raw Table: payment_log
-- =========================================================
-- 결제 시도 단위 로그
-- 성공/실패 여부 및 금액 정보 포함
create table if not exists payment_log (
  payment_time    varchar,         -- 결제 시각 (Raw 단계에서는 문자열)
  date            date,            -- 집계 기준 일자
  user_id         varchar(64),     -- 사용자 ID
  order_id        varchar(64),     -- 주문 ID
  campaign_id     varchar(64),     -- 캠페인 ID
  amount          numeric(12,2),   -- 결제 금액
  success_yn      char(1),         -- Y | N
  fail_reason     varchar(32)      -- 실패 사유 (nullable)
);


-- =========================================================
-- Mart Table: mart_daily_campaign_kpi
-- =========================================================
-- 일자 × 캠페인 × 채널 × 국가 단위 KPI Mart
-- BI 대시보드 및 Text2SQL의 단일 조회 대상
create table if not exists mart_daily_campaign_kpi (
  date                 date,            -- 기준 일자
  campaign_id          varchar(64),     -- 캠페인 ID
  channel              varchar(32),     -- 채널
  country              varchar(8),      -- 국가

  impressions          bigint,           -- 노출 수
  clicks               bigint,           -- 클릭 수
  ctr                  numeric(12,6),    -- 클릭률

  payment_attempts     bigint,           -- 결제 시도 수
  conversions          bigint,           -- 결제 성공 수
  payment_success_rate numeric(12,6),    -- 결제 성공률

  revenue              numeric(18,2),    -- 매출
  cost                 numeric(18,4),    -- 광고비
  conversion_rate      numeric(12,6),    -- 전환율
  roas                 numeric(12,6),    -- ROAS

  updated_at           timestamp default current_timestamp  -- Mart 적재 시각
);
