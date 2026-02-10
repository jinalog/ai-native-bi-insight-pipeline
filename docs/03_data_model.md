# 03. Data Model

본 문서는 광고·결제 로그 기반 AI 자동 인사이트 파이프라인에서
사용되는 데이터 모델을 정의한다.

본 프로젝트의 데이터 모델은
비기술 직군(마케팅/운영자)의 질문에
자연어 질의(Text2SQL) 및 자동 인사이트 생성으로
직접 연결될 수 있도록 설계되었다.

---

## 1. 데이터 레이어 구성

본 파이프라인은 다음 두 가지 데이터 레이어로 구성된다.

### 1.1 Raw Layer
- 이벤트 단위의 원본 로그 저장
- 광고 이벤트, 결제 이벤트를 그대로 보존
- 정합성 검증 및 재처리를 위한 기준 데이터

### 1.2 Mart Layer (AI Native Data Mart)
- 운영자 질문에 직접 대응하는 분석 테이블
- 날짜/캠페인/채널 기준으로 집계
- 주요 KPI를 사전에 계산하여 제공
- Text2SQL 및 LLM 인사이트 생성의 **유일한 질의 대상**

---

## 2. Raw 테이블 정의

### 2.1 ad_event_log (광고 이벤트 로그)

광고 노출 및 클릭 이벤트를 기록하는 원본 로그 테이블이다.

| 컬럼명 | 설명 |
|------|------|
| event_time | 이벤트 발생 시각 |
| date | 파티션용 날짜 (YYYY-MM-DD) |
| user_id | 사용자 식별자 |
| campaign_id | 광고 캠페인 식별자 |
| channel | 유입 채널 (search / social / display 등) |
| country | 국가 코드 (KR, JP, US 등) |
| event_type | 이벤트 유형 (impression / click) |
| cost | 광고 비용 |
| device | 디바이스 유형 (mobile / desktop) |

본 테이블은 이벤트 단위 데이터로,
직접 분석에는 사용하지 않고 ETL을 통해 Mart로 변환된다.

---

### 2.2 payment_log (결제 로그)

결제 시도 및 성공/실패 정보를 기록하는 원본 로그 테이블이다.

| 컬럼명 | 설명 |
|------|------|
| payment_time | 결제 시도 시각 |
| date | 파티션용 날짜 (YYYY-MM-DD) |
| user_id | 사용자 식별자 |
| order_id | 주문 식별자 |
| campaign_id | 유입 캠페인 식별자 |
| amount | 결제 금액 |
| success_yn | 결제 성공 여부 (Y/N) |
| fail_reason | 결제 실패 사유 코드 |

광고 성과와 실제 매출 간의 연결을 위해
campaign_id를 기준으로 광고 로그와 연계된다.

---

## 3. Mart 테이블 정의

### 3.1 mart_daily_campaign_kpi

운영자 질문, BI 대시보드, LLM 질의를 위한
핵심 분석 테이블이다.

집계 기준:
- date
- campaign_id
- channel
- country

#### 주요 컬럼 및 KPI

| 컬럼명 | 설명 |
|------|------|
| impressions | 광고 노출 수 |
| clicks | 광고 클릭 수 |
| ctr | 클릭률 (clicks / impressions) |
| payment_attempts | 결제 시도 건수 |
| conversions | 결제 성공 건수 |
| payment_success_rate | 결제 성공률 |
| revenue | 결제 성공 금액 합 |
| cost | 광고 비용 합 |
| conversion_rate | 전환율 (conversions / clicks) |
| roas | ROAS (revenue / cost) |

본 테이블은
- Raw 로그를 직접 노출하지 않고
- 질문에 필요한 KPI를 사전에 계산하여 제공함으로써
Text2SQL 및 LLM 응답의 안정성을 확보한다.

---

## 4. 질문 ↔ KPI 매핑

Mart 설계는 실제 운영자의 질문 패턴을 기준으로 이루어졌다.

### 4.1 “어제 매출이 왜 떨어졌어?”
- revenue
- conversion_rate
- payment_success_rate
- clicks
- impressions

### 4.2 “CTR은 괜찮은데 전환이 안 나오는 이유?”
- ctr
- conversion_rate
- payment_success_rate

### 4.3 “비용은 늘었는데 ROAS가 떨어진 이유?”
- cost
- revenue
- roas
- conversion_rate

이를 통해
숫자 조회를 넘어
성과 변동의 **원인 중심 분석**이 가능하도록 설계하였다.

---

## 5. 설계 의도 요약

- Raw 데이터는 보존하되 직접 질의하지 않는다
- Mart는 질문 중심으로 최소·핵심 지표만 제공한다
- KPI를 사전에 계산하여 LLM 질의 안정성을 확보한다
- 데이터 모델 자체가 인사이트 생성을 지원하도록 설계한다
