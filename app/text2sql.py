import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# OpenAI API 클라이언트
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 허용할 SQL 형태를 매우 보수적으로 제한 (SELECT만)
FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|attach|detach|copy|pragma)\b", re.IGNORECASE)

SYSTEM_PROMPT = """
당신은 DuckDB 데이터베이스를 조회하는 SQL 생성기입니다.
사용자가 묻는 질문을 '단 하나의 SQL(SELECT)'로 변환하세요.

규칙:
- 반드시 SELECT로 시작하는 단일 쿼리만 출력
- 세미콜론(;) 포함하지 말 것
- INSERT/UPDATE/DELETE/DDL/PRAGMA 등 변경 쿼리 금지
- 기본 테이블은 mart_daily_campaign_kpi
- 필요한 경우 WHERE/GROUP BY/ORDER BY/LIMIT 사용
- 컬럼:
  date, campaign_id, channel, country,
  impressions, clicks, ctr,
  payment_attempts, conversions, payment_success_rate,
  revenue, cost, conversion_rate, roas, updated_at
"""

def generate_sql(question: str, model: str = "gpt-4o-mini") -> str:
    """
    자연어 질문 -> 안전한 SELECT SQL 생성
    - openai==1.40.0 기준: chat.completions 사용
    """
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )

    sql = resp.choices[0].message.content.strip()

    # 안전장치: SELECT만 허용
    if not sql.lower().startswith("select"):
        raise ValueError("SQL은 반드시 SELECT로 시작해야 합니다.")
    if ";" in sql:
        raise ValueError("SQL에 세미콜론(;)은 허용하지 않습니다.")
    if FORBIDDEN.search(sql):
        raise ValueError("금지된 키워드가 포함되어 있습니다. (DDL/DML/PRAGMA 등)")

    return sql
