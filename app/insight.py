import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INSIGHT_PROMPT = """
당신은 광고/결제 KPI를 해석하는 분석가입니다.
입력된 KPI 요약과 분해 데이터(캠페인/채널/국가)를 보고 아래 형식으로 한국어 리포트를 작성하세요.

형식(반드시 준수):

## 1. 요약 : 
 - 한 줄로 기간과 핵심 성과 요약

## 2. 핵심 지표 요약:
  - Revenue: XX원
  - Cost: XX원
  - ROAS: XX
  - CTR: X.X%
  - CVR: X.X%

## 3. 원인 가설 TOP 3:
  - **[가설 제목]**: 구체적 설명. (데이터 근거: 캠페인/채널/국가명 revenue XX원, clicks X, conversions X)
  
  - **[가설 제목]**: 구체적 설명. (데이터 근거: ...)
  
  - **[가설 제목]**: 구체적 설명. (데이터 근거: ...)

## 4. 액션 TOP 3:
  - **[액션 제목]**: 실행 방법과 기대 효과.
  
  - **[액션 제목]**: 실행 방법과 기대 효과.
  
  - **[액션 제목]**: 실행 방법과 기대 효과.

규칙:
- 모든 불릿 포인트 앞에 2칸 공백
- 숫자는 천단위 쉼표 사용
- 불릿 사이 빈 줄 추가
"""

def generate_insight(payload: dict, model: str = "gpt-4o-mini") -> str:
    resp = client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[
            {"role": "system", "content": INSIGHT_PROMPT},
            {"role": "user", "content": f"데이터: {payload}"},
        ],
    )
    return resp.choices[0].message.content.strip()