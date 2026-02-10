-- Build mart_daily_campaign_kpi from raw logs
-- Notes:
-- - ad_event_log is aggregated by (date, campaign_id, channel, country)
-- - payment_log is aggregated by (date, campaign_id)
-- - join is done by (date, campaign_id)
-- - delete+insert strategy for simplicity (portfolio)

with ad_daily as (
  select
    date,
    campaign_id,
    channel,
    country,
    sum(case when event_type = 'impression' then 1 else 0 end) as impressions,
    sum(case when event_type = 'click' then 1 else 0 end) as clicks,
    sum(cost) as ad_cost
  from ad_event_log
  group by 1,2,3,4
),
pay_daily as (
  select
    date,
    campaign_id,
    count(*) as payment_attempts,
    sum(case when success_yn = 'Y' then 1 else 0 end) as conversions,
    sum(case when success_yn = 'Y' then amount else 0 end) as revenue
  from payment_log
  group by 1,2
)

-- delete target dates (simple approach)
delete from mart_daily_campaign_kpi
where date in (select distinct date from ad_event_log)
   or date in (select distinct date from payment_log);

insert into mart_daily_campaign_kpi (
  date, campaign_id, channel, country,
  impressions, clicks, ctr,
  payment_attempts, conversions, payment_success_rate,
  revenue, cost, conversion_rate, roas
)
select
  a.date,
  a.campaign_id,
  a.channel,
  a.country,

  a.impressions,
  a.clicks,
  case when a.impressions > 0 then a.clicks::numeric / a.impressions else 0 end as ctr,

  coalesce(p.payment_attempts, 0) as payment_attempts,
  coalesce(p.conversions, 0) as conversions,
  case
    when coalesce(p.payment_attempts, 0) > 0
    then coalesce(p.conversions, 0)::numeric / p.payment_attempts
    else 0
  end as payment_success_rate,

  coalesce(p.revenue, 0) as revenue,
  coalesce(a.ad_cost, 0) as cost,

  case
    when a.clicks > 0
    then coalesce(p.conversions, 0)::numeric / a.clicks
    else 0
  end as conversion_rate,

  case
    when coalesce(a.ad_cost, 0) > 0
    then coalesce(p.revenue, 0)::numeric / a.ad_cost
    else 0
  end as roas
from ad_daily a
left join pay_daily p
  on a.date = p.date and a.campaign_id = p.campaign_id;
