import os
import duckdb
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DUCKDB_PATH", "portfolio.duckdb")

DDL_SQL = open("sql/00_create_tables.sql", "r", encoding="utf-8").read()
MART_SQL = open("sql/10_build_mart_daily_campaign_kpi.sql", "r", encoding="utf-8").read()

def main():
    con = duckdb.connect(DB_PATH)

    con.execute(DDL_SQL)

    con.execute("delete from ad_event_log;")
    con.execute("delete from payment_log;")

    con.execute("""
        insert into ad_event_log
        select * from read_csv_auto('data/sample/ad_event_log.csv', header=true);
    """)

    con.execute("""
        insert into payment_log
        select * from read_csv_auto('data/sample/payment_log.csv', header=true);
    """)

    con.execute(MART_SQL)

    df = con.execute(
        "select * from mart_daily_campaign_kpi order by date, campaign_id;"
    ).df()
    print(df)

    con.close()
    print("DuckDB build completed.")

if __name__ == "__main__":
    main()
