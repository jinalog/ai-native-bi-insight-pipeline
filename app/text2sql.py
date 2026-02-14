import os
from dotenv import load_dotenv
from openai import OpenAI
from sql_guard import validate_sql

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
당신은 DuckDB(SQL) 생성기입니다.
사용자의 질문을 보고, DuckDB에서 실행 가능한 단 하나의 SELECT SQL만 출력하세요.

엄격 규칙:
- 반드시 SELECT로 시작하는 "단일 쿼리"만 출력
- 세미콜론(;) 금지
- INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/PRAGMA 등 변경 쿼리 금지
- 테이블은 mart_daily_campaign_kpi만 사용
- 가능한 한 명확한 필터(날짜, 캠페인, 채널, 국가)를 포함
- 질문이 모호하면 가장 일반적인 형태로 작성(예: 최근 7일, 상위 10개)
"""

SCHEMA_HINT = """
테이블: mart_daily_campaign_kpi
컬럼:
- date (DATE)
- campaign_id (VARCHAR)
- channel (VARCHAR)
- country (VARCHAR)
- impressions (BIGINT)
- clicks (BIGINT)
- ctr (DOUBLE/NUMERIC)
- payment_attempts (BIGINT)
- conversions (BIGINT)
- payment_success_rate (DOUBLE/NUMERIC)
- revenue (DOUBLE/NUMERIC)
- cost (DOUBLE/NUMERIC)
- conversion_rate (DOUBLE/NUMERIC)
- roas (DOUBLE/NUMERIC)
- updated_at (TIMESTAMP)

예시:
Q: 2026-01-01에 캠페인별 ROAS 상위 5개
A: select campaign_id, sum(revenue) as revenue, sum(cost) as cost,
          case when sum(cost)=0 then 0 else sum(revenue)/sum(cost) end as roas
   from mart_daily_campaign_kpi
   where date = '2026-01-01'
   group by campaign_id
   order by roas desc
   limit 5
"""

def _llm_to_sql(question: str, model: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + SCHEMA_HINT},
            {"role": "user", "content": question},
        ],
    )
    return resp.choices[0].message.content.strip()

def generate_sql(question: str, model: str = "gpt-4o-mini") -> str:
    sql = _llm_to_sql(question, model=model)
    validate_sql(sql)
    return sql

def recover_sql(question: str, bad_sql: str, error_msg: str, model: str = "gpt-4o-mini") -> str:
    """실행 오류가 났을 때: 에러 메시지를 반영해 SQL을 수정해서 다시 생성"""
    prompt = f"""
아래 SQL을 DuckDB에서 실행했더니 오류가 발생했습니다.
오류를 해결한 "단 하나의 SELECT SQL"만 다시 작성하세요.

[질문]
{question}

[기존 SQL]
{bad_sql}

[오류 메시지]
{error_msg}

규칙은 동일합니다:
- SELECT 단일 쿼리
- 세미콜론 금지
- mart_daily_campaign_kpi만 사용
"""
    fixed = _llm_to_sql(prompt, model=model)
    validate_sql(fixed)
    return fixed
