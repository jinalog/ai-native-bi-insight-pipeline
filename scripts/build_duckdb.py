import os
import duckdb
from dotenv import load_dotenv

# =========================================================
# DuckDB Build Script
#
# 역할:
#   - CSV → Raw 테이블 적재
#   - Raw → KPI Mart 생성
#
# 특징:
#   - DuckDB 파일 기반 (경량, 로컬 실행 가능)
#   - CSV 타입 자동 추론 오류 방지를 위해
#     read_csv_auto에 컬럼 타입 명시
# =========================================================


# .env 파일 로드 (OPENAI_API_KEY, DUCKDB_PATH 등)
load_dotenv()

# DuckDB 파일 경로 (기본값: portfolio.duckdb)
DB_PATH = os.getenv("DUCKDB_PATH", "portfolio.duckdb")

# DDL / Mart SQL 파일 로드
DDL_SQL = open("sql/00_create_tables.sql", "r", encoding="utf-8").read()
MART_SQL = open("sql/10_build_mart_daily_campaign_kpi.sql", "r", encoding="utf-8").read()


def main():
    # DuckDB 연결 (파일이 없으면 새로 생성)
    con = duckdb.connect(DB_PATH)

    # =====================================================
    # 1. 테이블 생성 (DDL)
    # =====================================================
    con.execute(DDL_SQL)

    # =====================================================
    # 2. Raw 테이블 초기화
    # (재실행 시 중복 적재 방지)
    # =====================================================
    con.execute("delete from ad_event_log;")
    con.execute("delete from payment_log;")

    # =====================================================
    # 3. 광고 이벤트 CSV 적재
    # - event_time은 VARCHAR로 강제
    # - 나머지 컬럼도 명시적으로 타입 지정
    #   → CSV auto-detect 오류 방지
    # =====================================================
    con.execute("""
        insert into ad_event_log
        select * from read_csv_auto(
            'data/sample/ad_event_log.csv',
            header=true,
            types={
              'event_time':'VARCHAR',
              'date':'DATE',
              'user_id':'VARCHAR',
              'campaign_id':'VARCHAR',
              'channel':'VARCHAR',
              'country':'VARCHAR',
              'event_type':'VARCHAR',
              'cost':'DECIMAL(12,4)',
              'device':'VARCHAR'
            }
        );
    """)

    # =====================================================
    # 4. 결제 로그 CSV 적재
    # - payment_time 역시 VARCHAR로 유지
    # =====================================================
    con.execute("""
        insert into payment_log
        select * from read_csv_auto(
            'data/sample/payment_log.csv',
            header=true,
            types={
              'payment_time':'VARCHAR',
              'date':'DATE',
              'user_id':'VARCHAR',
              'order_id':'VARCHAR',
              'campaign_id':'VARCHAR',
              'amount':'DECIMAL(12,2)',
              'success_yn':'VARCHAR',
              'fail_reason':'VARCHAR'
            }
        );
    """)

    # =====================================================
    # 5. KPI Mart 생성
    # - Raw 로그를 집계하여 mart_daily_campaign_kpi 생성
    # =====================================================
    con.execute(MART_SQL)

    # =====================================================
    # 6. 결과 확인 (샘플 출력)
    # =====================================================
    df = con.execute(
        "select * from mart_daily_campaign_kpi order by date, campaign_id;"
    ).df()
    print(df)

    con.close()
    print("DuckDB build completed.")


if __name__ == "__main__":
    main()