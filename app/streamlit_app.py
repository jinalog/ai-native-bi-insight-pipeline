import os
import duckdb
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# Streamlit KPI Dashboard
# - DuckDB에 생성된 mart_daily_campaign_kpi를 읽어와
#   핵심 KPI를 테이블/차트로 보여준다.
# ---------------------------------------------------------

st.set_page_config(page_title="AI Native KPI Dashboard", layout="wide")

st.title("광고·결제 KPI 대시보드 (Daily Campaign KPI)")
st.caption("DuckDB Mart(mart_daily_campaign_kpi) 기반 — 로컬 재현 가능한 BI")

# DuckDB 경로 (.env의 DUCKDB_PATH 사용, 없으면 기본값)
DB_PATH = os.getenv("DUCKDB_PATH", "portfolio.duckdb")

@st.cache_data
def load_kpi() -> pd.DataFrame:
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("""
        select
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
        from mart_daily_campaign_kpi
        order by date, campaign_id
    """).df()
    con.close()

    # Streamlit 편의: 날짜 타입 정리
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_kpi()

if df.empty:
    st.error("mart_daily_campaign_kpi가 비어 있습니다. 먼저 `python scripts/build_duckdb.py`를 실행하세요.")
    st.stop()

# ---------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------
st.sidebar.header("필터")

min_d, max_d = df["date"].min(), df["date"].max()
date_range = st.sidebar.date_input(
    "기간 선택",
    value=(min_d.date(), max_d.date()),
    min_value=min_d.date(),
    max_value=max_d.date(),
)

channels = ["(ALL)"] + sorted(df["channel"].dropna().unique().tolist())
sel_channel = st.sidebar.selectbox("채널", channels, index=0)

campaigns = ["(ALL)"] + sorted(df["campaign_id"].dropna().unique().tolist())
sel_campaign = st.sidebar.selectbox("캠페인", campaigns, index=0)

countries = ["(ALL)"] + sorted(df["country"].dropna().unique().tolist())
sel_country = st.sidebar.selectbox("국가", countries, index=0)

# 적용
start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

f = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()

if sel_channel != "(ALL)":
    f = f[f["channel"] == sel_channel]
if sel_campaign != "(ALL)":
    f = f[f["campaign_id"] == sel_campaign]
if sel_country != "(ALL)":
    f = f[f["country"] == sel_country]

# ---------------------------------------------------------
# KPI Cards
# ---------------------------------------------------------
st.subheader("요약 KPI")

col1, col2, col3, col4, col5 = st.columns(5)

total_impr = int(f["impressions"].sum())
total_clicks = int(f["clicks"].sum())
total_rev = float(f["revenue"].sum())
total_cost = float(f["cost"].sum())
roas = (total_rev / total_cost) if total_cost > 0 else 0.0

col1.metric("Impressions", f"{total_impr:,}")
col2.metric("Clicks", f"{total_clicks:,}")
col3.metric("Revenue", f"{total_rev:,.2f}")
col4.metric("Cost", f"{total_cost:,.4f}")
col5.metric("ROAS", f"{roas:,.2f}")

st.divider()

# ---------------------------------------------------------
# Chart + Table
# ---------------------------------------------------------
st.subheader("일별 추이")

# 일별로 다시 집계해서 차트 구성 (필터 적용된 f 기준)
daily = (
    f.groupby("date", as_index=False)
     .agg(
        revenue=("revenue", "sum"),
        cost=("cost", "sum"),
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        conversions=("conversions", "sum"),
     )
)
daily["roas"] = daily.apply(lambda r: (r["revenue"] / r["cost"]) if r["cost"] > 0 else 0.0, axis=1)
daily["ctr"] = daily.apply(lambda r: (r["clicks"] / r["impressions"]) if r["impressions"] > 0 else 0.0, axis=1)
daily["cvr"] = daily.apply(lambda r: (r["conversions"] / r["clicks"]) if r["clicks"] > 0 else 0.0, axis=1)

c1, c2 = st.columns(2)

with c1:
    st.line_chart(daily.set_index("date")[["revenue", "cost"]])

with c2:
    st.line_chart(daily.set_index("date")[["roas", "ctr", "cvr"]])

st.subheader("상세 테이블")
st.dataframe(f, use_container_width=True)

st.divider()
st.subheader("Text2SQL (자연어 질문 → SQL → 결과)")

from text2sql import generate_sql

q = st.text_input(
    "질문을 입력하세요 (예: 2026-01-01에 캠페인별 ROAS 상위 10개 보여줘)",
    value="2026-01-01에 캠페인별 ROAS 상위 10개 보여줘"
)

run = st.button("SQL 생성 & 실행")

if run:
    try:
        sql = generate_sql(q)
        st.markdown("**생성된 SQL**")
        st.code(sql, language="sql")

        con = duckdb.connect(DB_PATH, read_only=True)
        out = con.execute(sql).df()
        con.close()

        st.markdown("**쿼리 결과**")
        st.dataframe(out, use_container_width=True)

    except Exception as e:
        st.error(str(e))
