-- =========================================================
-- Daily Campaign KPI Mart 생성 SQL
-- 목적:
--   광고 이벤트 로그(ad_event_log)와
--   결제 로그(payment_log)를 기반으로
--   "일자 × 캠페인 × 채널 × 국가" 단위 KPI 마트를 생성한다.
--
-- 특징:
--   - Raw 테이블은 그대로 두고
--   - 집계/비율 계산 확인
--   - BI / Text2SQL 조회용 단일 Mart 제공
-- =========================================================


-- 기존 마트 데이터 초기화
-- (재빌드 시 중복 적재 방지 목적)
delete from mart_daily_campaign_kpi;


-- =========================================================
-- 1. 광고 로그 일별 집계 (CTE: ad_daily)
-- =========================================================
-- ad_event_log:
--   - impression / click 이벤트가 row 단위로 존재
--   - 비용(cost)은 이벤트 단위로 누적
--
-- 여기서는:
--   - impression 수
--   - click 수
--   - 총 광고비(cost)
-- 를 일자/캠페인/채널/국가 단위로 집계
with ad_daily as (
  select
    date,                 -- 기준 일자
    campaign_id,          -- 캠페인 ID
    channel,              -- 유입 채널 (search, social 등)
    country,              -- 국가 코드

    -- 노출 수
    sum(
      case when event_type = 'impression' then 1 else 0 end
    ) as impressions,

    -- 클릭 수
    sum(
      case when event_type = 'click' then 1 else 0 end
    ) as clicks,

    -- 광고 비용 합계
    sum(cost) as cost

  from ad_event_log
  group by 1,2,3,4
),


-- =========================================================
-- 2. 결제 로그 일별 집계 (CTE: pay_daily)
-- =========================================================
-- payment_log:
--   - 결제 시도 단위 row
--   - success_yn = 'Y' 인 경우만 실제 매출 발생
--
-- 여기서는:
--   - 결제 시도 수
--   - 성공 결제 수 (전환 수)
--   - 매출(revenue)
-- 를 일자/캠페인 단위로 집계
pay_daily as (
  select
    date,
    campaign_id,

    -- 결제 시도 수
    count(*) as payment_attempts,

    -- 결제 성공 수 (전환 수)
    sum(
      case when success_yn = 'Y' then 1 else 0 end
    ) as conversions,

    -- 매출 합계 (성공 결제만)
    sum(
      case when success_yn = 'Y' then amount else 0 end
    ) as revenue

  from payment_log
  group by 1,2
)


-- =========================================================
-- 3. KPI 계산 후 Mart 테이블에 적재
-- =========================================================
insert into mart_daily_campaign_kpi (
  date,
  campaign_id,
  channel,
  country,

  impressions,
  clicks,
  ctr,

  payment_attempts,
  conversions,
  payment_success_rate,

  revenue,
  cost,
  conversion_rate,
  roas,

  updated_at
)
select
  -- 기본 키 차원
  a.date,
  a.campaign_id,
  a.channel,
  a.country,

  -- 광고 지표
  a.impressions,
  a.clicks,

  -- CTR = clicks / impressions
  case
    when a.impressions > 0
    then cast(a.clicks as double) / cast(a.impressions as double)
    else 0
  end as ctr,

  -- 결제 지표 (없을 경우 0으로 보정)
  coalesce(p.payment_attempts, 0) as payment_attempts,
  coalesce(p.conversions, 0) as conversions,

  -- 결제 성공률 = conversions / payment_attempts
  case
    when coalesce(p.payment_attempts, 0) > 0
    then cast(coalesce(p.conversions,0) as double)
         / cast(p.payment_attempts as double)
    else 0
  end as payment_success_rate,

  -- 매출 / 비용
  coalesce(p.revenue, 0) as revenue,
  a.cost,

  -- 전환율 = conversions / clicks
  case
    when a.clicks > 0
    then cast(coalesce(p.conversions,0) as double)
         / cast(a.clicks as double)
    else 0
  end as conversion_rate,

  -- ROAS = revenue / cost
  case
    when a.cost > 0
    then cast(coalesce(p.revenue,0) as double)
         / cast(a.cost as double)
    else 0
  end as roas,

  -- 적재 시각
  current_timestamp as updated_at

from ad_daily a
left join pay_daily p
  on a.date = p.date
 and a.campaign_id = p.campaign_id
;