# 02. Architecture

## 1. 설계 원칙

본 프로젝트는 “분석가가 SQL로 뽑아주는 BI”가 아니라,
비기술 직군 운영자가 자연어 질문으로 바로 답을 얻는
AI Native BI 흐름을 목표로 한다.

따라서 설계는 다음 원칙을 따른다.

- LLM이 안정적으로 질의할 수 있도록 “AI 친화적” 스키마를 제공한다
- Raw 로그를 그대로 노출하지 않고, 의미 단위로 정규화/집계된 Mart를 만든다
- Airflow 파이프라인은 “재현 가능/운영 가능”한 형태로 구성한다
- BI는 지표를 보여주는 것에 그치지 않고, 인사이트(설명)까지 제공한다

---

## 2. 전체 구성요소

### 2.1 Data Sources (합성 로그)
- 광고 이벤트 로그(ad events): impression, click, cost 등
- 결제 로그(payment): 결제 성공/실패, 결제 금액 등

### 2.2 Storage / Layers
- Raw Layer: 원천 로그(일자 파티션)
- Mart Layer: 분석 및 LLM 질의를 위한 AI Native 데이터 마트

### 2.3 Orchestration
- Airflow DAG 기반 ETL/ELT
- 품질 체크, 변환, Mart 적재, 이상치 탐지, LLM 리포트 생성까지 하나의 DAG로 관리

### 2.4 BI
- Superset 대시보드로 핵심 KPI 시각화
- 대시보드 상단에 LLM 요약 카드(Insight Summary) 제공

### 2.5 LLM Layer
- Text2SQL: 운영자의 자연어 질문을 Mart SQL로 변환
- Insight Summary: KPI 변동/이상치의 원인 후보를 요약 생성

---

## 3. 데이터 플로우

1) 광고/결제 Raw 로그 적재
- 일자 기준 파티션으로 저장
- 스키마 및 필수 필드 검증

2) ETL 변환 (Airflow)
- 광고/결제 로그 정합성 검증 (null, type, range)
- 세션/캠페인/일자 단위의 기준 테이블로 정규화
- KPI 계산 (CTR, CVR, ROAS 등)

3) AI Native 데이터 마트 적재
- LLM이 질의하기 쉬운 형태로 “의미 단위” 테이블 구성
- 조인 폭발을 피하고, 질문 패턴에 맞춘 형태로 핵심 지표를 제공

4) 이상치 탐지 및 인사이트 생성
- 일자/캠페인/채널별 KPI 변화율 기반 이상치 후보 탐지
- “매출↓인데 CTR 유지 → 결제 성공률↓” 같은 패턴을 규칙/피처로 추출
- 탐지 결과를 LLM 입력 포맷으로 정리

5) 사용자 제공(대시보드 + 자연어 질의)
- Superset: KPI 모니터링
- Text2SQL: 운영자 질문 → SQL 자동 생성 → 결과 반환
- Insight: 변동 원인 후보와 근거 지표를 자연어로 요약

---

## 4. AI Native 데이터 마트 정의

본 프로젝트에서 “AI Native 데이터 마트”는 다음을 의미한다.

- 운영자가 던지는 질문을 기준으로 “질의 대상이 되는 테이블”을 설계한다
- LLM이 안정적으로 SQL을 생성할 수 있도록:
  - 컬럼명은 의미가 명확해야 한다
  - 지표는 가능한 Mart에서 사전 계산되어야 한다
  - 지나치게 복잡한 조인/서브쿼리 없이도 답을 낼 수 있어야 한다
- 결과적으로 Text2SQL은 Raw가 아닌 Mart를 대상으로 수행한다

---

## 5. Airflow DAG (Task Design)

DAG는 다음 태스크로 구성한다.

- extract_ad_log
- extract_payment_log
- validate_schema
- transform_to_mart (daily_campaign_kpi 생성)
- detect_anomaly (일자/캠페인 KPI 변화율 기반)
- build_llm_context (LLM 입력용 요약 테이블/JSON 생성)
- generate_insight_report (LLM 요약 생성)

---

## 6. 운영 시나리오 (예시)

운영자는 아래처럼 질문한다.

- “어제 매출이 왜 떨어졌어?”
- “CTR은 괜찮은데 전환이 안 나오는 이유가 뭐야?”
- “비용은 늘었는데 ROAS가 떨어진 이유가 뭐야?”

시스템은 다음 순서로 답한다.

- Text2SQL로 Mart에서 관련 KPI를 조회한다
- KPI 변동과 연관 지표(CTR, CVR, 결제 성공률 등)를 함께 비교한다
- LLM이 원인 후보를 근거 지표와 함께 자연어로 설명한다
