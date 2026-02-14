import re

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|copy|pragma|call|execute)\b",
    re.IGNORECASE,
)

def validate_sql(sql: str) -> None:
    s = sql.strip()

    if not s.lower().startswith("select"):
        raise ValueError("SQL은 SELECT만 허용됩니다.")
    if ";" in s:
        raise ValueError("세미콜론(;)은 금지입니다. 단일 쿼리만 허용합니다.")
    if FORBIDDEN.search(s):
        raise ValueError("위험 키워드(DDL/DML/PRAGMA 등)가 포함되어 있습니다.")

    # 허용 테이블 제한: mart_daily_campaign_kpi만
    if "mart_daily_campaign_kpi" not in s.lower():
        raise ValueError("허용된 테이블(mart_daily_campaign_kpi)만 조회 가능합니다.")
