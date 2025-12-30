# ecos-reader 사용 가이드

**한국은행 ECOS API를 Python에서 쉽게 사용하기**

버전: 0.1.2 | 최종 업데이트: 2025-12-30

---

## 목차

1. [시작하기](#시작하기)
   - [설치하기](#설치하기)
   - [API 키 발급받기](#api-키-발급받기)
   - [첫 번째 데이터 조회하기](#첫-번째-데이터-조회하기)
2. [금리 데이터 조회하기](#금리-데이터-조회하기)
3. [물가 데이터 조회하기](#물가-데이터-조회하기)
4. [경제 성장 데이터 조회하기](#경제-성장-데이터-조회하기)
5. [통화 데이터 조회하기](#통화-데이터-조회하기)
6. [고급 기능 사용하기](#고급-기능-사용하기)
7. [실전 활용 예제](#실전-활용-예제)
8. [문제 해결](#문제-해결)
9. [빠른 참조](#빠른-참조)

---

## 시작하기

### 설치하기

**PyPI에서 설치 (추천):**
```bash
pip install ecos-reader
```

**개발 버전 설치:**
```bash
git clone https://github.com/choo121600/ecos-reader.git
cd ecos-reader
pip install -e ".[dev]"
```

**필요한 Python 버전:** 3.10 이상

---

### API 키 발급받기

1. [한국은행 ECOS Open API](https://ecos.bok.or.kr/api/) 접속
2. "인증키 신청" 클릭
3. 필수 정보 입력 (이메일, 이름 등)
4. 이메일로 API 키 수신 (즉시 발급)

**예시:** `ABC123XYZ456...` (실제로는 긴 문자열)

---

### 첫 번째 데이터 조회하기

#### 방법 1: 코드에서 API 키 설정

```python
import ecos

# API 키 설정
ecos.set_api_key("여기에_발급받은_API키_입력")

# 한국은행 기준금리 조회
df = ecos.get_base_rate()
print(df)
```

**출력 결과:**
```
         date  value unit
0  2023-12-01   3.50    %
1  2024-01-01   3.50    %
2  2024-02-01   3.50    %
3  2024-03-01   3.50    %
...
```

#### 방법 2: 환경 변수 사용 (추천)

**터미널에서:**
```bash
export ECOS_API_KEY="여기에_발급받은_API키_입력"
```

**Python 코드:**
```python
import ecos

# API 키가 환경 변수에서 자동으로 로드됨
df = ecos.get_base_rate()
print(df)
```

#### 방법 3: .env 파일 사용

**프로젝트 폴더에 `.env` 파일 생성:**
```
ECOS_API_KEY=여기에_발급받은_API키_입력
```

**Python 코드:**
```python
import ecos

# .env 파일 로드
ecos.load_env()

# 이제 API 키가 설정됨
df = ecos.get_base_rate()
print(df)
```

---

## 금리 데이터 조회하기

금리는 경제의 온도계입니다. ecos-reader로 한국은행 기준금리, 국고채 수익률, 장단기 금리차를 쉽게 조회할 수 있습니다.

---

### 1. 한국은행 기준금리 조회하기

**언제 사용하나요?**
- 통화정책 변화를 추적할 때
- 금리 인상/인하 사이클을 분석할 때
- 시중 금리 예측의 기준으로 사용할 때

**기본 사용법:**
```python
import ecos

# 최근 1년간 기준금리
df = ecos.get_base_rate()
print(df)
```

**특정 기간 조회:**
```python
# 2020년 1월부터 2024년 12월까지
df = ecos.get_base_rate(start_date="202001", end_date="202412")
print(df)
```

**날짜 형식:** YYYYMM (예: 202401 = 2024년 1월)

**실전 활용 - 금리 변화 추적:**
```python
import ecos

df = ecos.get_base_rate(start_date="202001", end_date="202412")

# 금리 변화 계산
df = df.sort_values('date')
df['change'] = df['value'].diff()

# 금리가 변경된 시점만 출력
rate_changes = df[df['change'] != 0]
print("금리 변경 이력:")
print(rate_changes[['date', 'value', 'change']])
```

**출력:**
```
금리 변경 이력:
         date  value  change
5  2020-05-01   0.50   -0.25
18 2021-08-01   0.75    0.25
21 2021-11-01   1.00    0.25
...
```

---

### 2. 국고채 수익률 조회하기

**언제 사용하나요?**
- 장기 금리 동향을 파악할 때
- 채권 투자 의사결정을 할 때
- 경기 전망을 평가할 때

**기본 사용법 - 3년물:**
```python
import ecos

# 최근 1년간 국고채 3년물 수익률
df = ecos.get_treasury_yield(maturity="3Y")
print(df.tail())
```

**10년물 조회:**
```python
# 10년물 국고채 수익률
df = ecos.get_treasury_yield(maturity="10Y")
print(df.tail())
```

**날짜 형식:** YYYYMMDD (예: 20240101 = 2024년 1월 1일)

**사용 가능한 만기:**
- `"1Y"` - 1년물
- `"3Y"` - 3년물
- `"5Y"` - 5년물
- `"10Y"` - 10년물
- `"20Y"` - 20년물
- `"30Y"` - 30년물

**특정 기간 조회:**
```python
# 2024년 전체 기간
df = ecos.get_treasury_yield(
    maturity="10Y",
    start_date="20240101",
    end_date="20241231"
)
print(df)
```

**실전 활용 - 여러 만기 비교:**
```python
import ecos
import pandas as pd

# 여러 만기 조회
y1 = ecos.get_treasury_yield(maturity="1Y", start_date="20240101")
y3 = ecos.get_treasury_yield(maturity="3Y", start_date="20240101")
y10 = ecos.get_treasury_yield(maturity="10Y", start_date="20240101")

# 병합
comparison = pd.merge(
    y1[['date', 'value']].rename(columns={'value': '1Y'}),
    y3[['date', 'value']].rename(columns={'value': '3Y'}),
    on='date'
)
comparison = pd.merge(
    comparison,
    y10[['date', 'value']].rename(columns={'value': '10Y'}),
    on='date'
)

print(comparison.tail())
```

**출력:**
```
         date     1Y     3Y    10Y
245 2024-12-23  3.10   3.25   3.45
246 2024-12-24  3.12   3.27   3.47
```

---

### 3. 장단기 금리차 계산하기

**언제 사용하나요?**
- 경기 침체 가능성을 예측할 때
- 수익률 곡선 형태를 분석할 때
- 투자 전략을 수립할 때

**기본 사용법:**
```python
import ecos

# 10년물 - 3년물 금리차
df = ecos.get_yield_spread()
print(df.tail())
```

**출력:**
```
         date  long_yield  short_yield  spread unit
245 2024-12-20        3.45         3.25    0.20   %p
246 2024-12-23        3.47         3.27    0.20   %p
```

**커스텀 조합:**
```python
# 30년물 - 1년물 금리차
df = ecos.get_yield_spread(
    long_maturity="30Y",
    short_maturity="1Y"
)
print(df.tail())
```

**실전 활용 - 금리 역전 감지:**
```python
import ecos

# 10년-3년 금리차 조회
spread = ecos.get_yield_spread(
    long_maturity="10Y",
    short_maturity="3Y",
    start_date="20200101",
    end_date="20241231"
)

# 금리 역전 구간 찾기 (spread < 0)
inversions = spread[spread['spread'] < 0]

if not inversions.empty:
    print(f"⚠️ 금리 역전 발생!")
    print(f"총 {len(inversions)}일 동안 역전")
    print(f"최근 역전일: {inversions.iloc[-1]['date']}")
    print(f"최대 역전폭: {inversions['spread'].min():.2f}%p")
else:
    print("✓ 금리 역전 없음 (정상)")
```

**경제적 의미:**
- **양수 (정상)**: 장기 금리 > 단기 금리 → 경기 확장 전망
- **음수 (역전)**: 장기 금리 < 단기 금리 → 경기 침체 신호

---

## 물가 데이터 조회하기

물가는 화폐가치의 척도입니다. 소비자물가, 근원물가, 생산자물가를 추적하여 인플레이션을 분석할 수 있습니다.

---

### 1. 소비자물가지수(CPI) 조회하기

**언제 사용하나요?**
- 인플레이션율을 확인할 때
- 실질 소득/수익률을 계산할 때
- 한국은행 물가목표(2%) 달성 여부를 평가할 때

**기본 사용법:**
```python
import ecos

# 최근 2년간 CPI (전년동월비)
df = ecos.get_cpi()
print(df.tail())
```

**출력:**
```
         date  value unit
20 2024-08-01   2.0    %
21 2024-09-01   1.6    %
22 2024-10-01   1.3    %
23 2024-11-01   1.5    %
```

**특정 기간 조회:**
```python
# 2023년 전체
df = ecos.get_cpi(start_date="202301", end_date="202312")
print(df)
```

**날짜 형식:** YYYYMM

**실전 활용 - 물가목표 달성도 분석:**
```python
import ecos

df = ecos.get_cpi(start_date="202001", end_date="202412")

# 한국은행 물가목표
TARGET = 2.0

# 분석
df['gap_from_target'] = df['value'] - TARGET
above_target = df[df['value'] > TARGET]
below_target = df[df['value'] < TARGET]

print(f"=== 물가목표 달성도 분석 ===")
print(f"평균 CPI: {df['value'].mean():.2f}%")
print(f"목표 초과: {len(above_target)}개월 ({len(above_target)/len(df)*100:.1f}%)")
print(f"목표 미달: {len(below_target)}개월 ({len(below_target)/len(df)*100:.1f}%)")
print(f"최고 CPI: {df['value'].max():.2f}% ({df.loc[df['value'].idxmax(), 'date']})")
```

**출력:**
```
=== 물가목표 달성도 분석 ===
평균 CPI: 2.85%
목표 초과: 32개월 (66.7%)
목표 미달: 16개월 (33.3%)
최고 CPI: 6.30% (2022-07-01)
```

---

### 2. 근원 소비자물가지수 조회하기

**언제 사용하나요?**
- 기조적 인플레이션을 파악할 때
- 일시적 가격 변동(유가, 농산물)을 제외하고 분석할 때
- 통화정책 방향을 예측할 때

**기본 사용법:**
```python
import ecos

# 최근 2년간 근원 CPI
df = ecos.get_core_cpi()
print(df.tail())
```

**실전 활용 - CPI와 근원 CPI 비교:**
```python
import ecos
import pandas as pd

# 데이터 조회
cpi = ecos.get_cpi(start_date="202001", end_date="202412")
core_cpi = ecos.get_core_cpi(start_date="202001", end_date="202412")

# 병합
comparison = pd.merge(
    cpi[['date', 'value']].rename(columns={'value': 'cpi'}),
    core_cpi[['date', 'value']].rename(columns={'value': 'core_cpi'}),
    on='date'
)

# 갭 계산
comparison['gap'] = comparison['cpi'] - comparison['core_cpi']

print("=== CPI vs 근원 CPI ===")
print(comparison.tail(10))
print(f"\n평균 갭: {comparison['gap'].mean():.2f}%p")
print(f"최대 갭: {comparison['gap'].max():.2f}%p (일시적 요인 강함)")
```

**경제적 의미:**
- **CPI > 근원 CPI**: 식료품/에너지 가격이 크게 상승 (일시적 요인)
- **CPI ≈ 근원 CPI**: 물가 상승이 전반적 (기조적 인플레이션)

---

### 3. 생산자물가지수(PPI) 조회하기

**언제 사용하나요?**
- 기업의 원가 부담을 파악할 때
- 향후 소비자물가 상승을 예측할 때 (선행지표)
- 제조업 수익성을 분석할 때

**기본 사용법:**
```python
import ecos

# 최근 2년간 PPI
df = ecos.get_ppi()
print(df.tail())
```

**실전 활용 - PPI의 CPI 전이 분석:**
```python
import ecos
import pandas as pd

# 데이터 조회
ppi = ecos.get_ppi(start_date="202001", end_date="202412")
cpi = ecos.get_cpi(start_date="202001", end_date="202412")

# 병합
comparison = pd.merge(
    ppi[['date', 'value']].rename(columns={'value': 'ppi'}),
    cpi[['date', 'value']].rename(columns={'value': 'cpi'}),
    on='date'
)

# 3개월 후 CPI와 현재 PPI 비교 (시차 분석)
comparison['cpi_3m_later'] = comparison['cpi'].shift(-3)
comparison['ppi_to_cpi'] = comparison['cpi_3m_later'] - comparison['ppi']

print("=== PPI → CPI 전이 분석 ===")
print(comparison[['date', 'ppi', 'cpi', 'cpi_3m_later']].dropna().tail(10))
```

**경제적 의미:**
- PPI 상승 → 3-6개월 후 CPI 상승 가능성
- PPI와 CPI 격차가 크면 기업의 가격 전가 여력 존재

---

## 경제 성장 데이터 조회하기

GDP는 경제 규모와 성장의 척도입니다. 실질GDP, 명목GDP, GDP 디플레이터를 조회할 수 있습니다.

---

### 1. GDP 조회하기

**언제 사용하나요?**
- 경기 상황을 평가할 때
- 성장률을 계산할 때
- 경제 규모를 파악할 때

**분기별 실질 GDP (기본):**
```python
import ecos

# 최근 5년간 분기별 실질 GDP
df = ecos.get_gdp()
print(df.tail())
```

**출력:**
```
         date      value unit
16 2023-01-01  2145.23   조원
17 2023-04-01  2168.45   조원
18 2023-07-01  2182.11   조원
19 2023-10-01  2195.88   조원
```

**날짜 형식:**
- 분기: YYYYQN (예: 2024Q1 = 2024년 1분기)
- 연간: YYYY (예: 2024 = 2024년)

**연간 명목 GDP:**
```python
# 최근 10년간 연간 명목 GDP
df = ecos.get_gdp(frequency="A", basis="nominal")
print(df)
```

**특정 기간 조회:**
```python
# 2020년 1분기 ~ 2024년 4분기
df = ecos.get_gdp(
    frequency="Q",
    basis="real",
    start_date="2020Q1",
    end_date="2024Q4"
)
print(df)
```

**실전 활용 - GDP 성장률 계산:**
```python
import ecos

# 분기별 실질 GDP
df = ecos.get_gdp(frequency="Q", start_date="2020Q1", end_date="2024Q4")
df = df.sort_values('date').reset_index(drop=True)

# 전년 동기 대비 성장률 (YoY)
df['yoy_growth'] = df['value'].pct_change(periods=4) * 100

# 전기 대비 성장률 (QoQ)
df['qoq_growth'] = df['value'].pct_change() * 100

print("=== GDP 성장률 ===")
print(df[['date', 'value', 'yoy_growth', 'qoq_growth']].tail(10))

# 통계
print(f"\n평균 YoY 성장률: {df['yoy_growth'].mean():.2f}%")
print(f"최고 YoY 성장률: {df['yoy_growth'].max():.2f}% ({df.loc[df['yoy_growth'].idxmax(), 'date']})")
print(f"최저 YoY 성장률: {df['yoy_growth'].min():.2f}% ({df.loc[df['yoy_growth'].idxmin(), 'date']})")
```

**출력:**
```
=== GDP 성장률 ===
         date      value  yoy_growth  qoq_growth
10 2022-04-01  2145.23        2.85        0.65
11 2022-07-01  2168.45        3.12        1.08
...

평균 YoY 성장률: 2.34%
최고 YoY 성장률: 4.21% (2021-04-01)
최저 YoY 성장률: -1.02% (2020-04-01)
```

**파라미터:**
- `frequency`: `"Q"` (분기, 기본값) 또는 `"A"` (연간)
- `basis`: `"real"` (실질, 기본값) 또는 `"nominal"` (명목)

---

### 2. GDP 디플레이터 조회하기

**언제 사용하나요?**
- 포괄적인 물가 지표를 확인할 때
- 실질 GDP와 명목 GDP의 관계를 분석할 때
- CPI와 다른 각도에서 인플레이션을 평가할 때

**기본 사용법:**
```python
import ecos

# 분기별 GDP 디플레이터
df = ecos.get_gdp_deflator()
print(df.tail())
```

**연간 조회:**
```python
df = ecos.get_gdp_deflator(frequency="A")
print(df)
```

**실전 활용 - GDP 디플레이터 상승률:**
```python
import ecos

df = ecos.get_gdp_deflator(frequency="Q", start_date="2020Q1")
df = df.sort_values('date')

# 전년 동기 대비 상승률
df['deflator_change'] = df['value'].pct_change(periods=4) * 100

print("=== GDP 디플레이터 변화율 ===")
print(df[['date', 'value', 'deflator_change']].tail(10))
```

**경제적 의미:**
- GDP 디플레이터 = (명목 GDP / 실질 GDP) × 100
- CPI보다 범위가 넓음 (수입품 제외, 국내 생산품만 포함)
- GDP 디플레이터 상승 = 전반적인 물가 상승

---

## 통화 데이터 조회하기

통화량과 대출은 유동성의 척도입니다. M1, M2, Lf 통화량과 은행 대출 데이터를 조회할 수 있습니다.

---

### 1. 통화량 조회하기

**언제 사용하나요?**
- 시중 유동성을 파악할 때
- 통화정책 효과를 분석할 때
- 자산 가격 상승 압력을 예측할 때

**M2 조회 (기본, 가장 많이 사용):**
```python
import ecos

# 최근 3년간 M2 통화량
df = ecos.get_money_supply()
print(df.tail())
```

**출력:**
```
         date      value unit
33 2024-09-01  3852.4   조원
34 2024-10-01  3868.2   조원
35 2024-11-01  3881.5   조원
```

**M1 또는 Lf 조회:**
```python
# M1 (협의통화)
df_m1 = ecos.get_money_supply(indicator="M1")

# Lf (금융기관유동성)
df_lf = ecos.get_money_supply(indicator="Lf")
```

**날짜 형식:** YYYYMM

**특정 기간 조회:**
```python
df = ecos.get_money_supply(
    indicator="M2",
    start_date="202001",
    end_date="202412"
)
```

**실전 활용 - M2 증가율 모니터링:**
```python
import ecos

# M2 조회
df = ecos.get_money_supply(indicator="M2", start_date="202001")
df = df.sort_values('date')

# 전년 동월 대비 증가율
df['yoy_growth'] = df['value'].pct_change(periods=12) * 100

# 전월 대비 증가율
df['mom_growth'] = df['value'].pct_change() * 100

print("=== M2 증가율 ===")
print(df[['date', 'value', 'yoy_growth', 'mom_growth']].tail(12))

print(f"\n평균 YoY 증가율: {df['yoy_growth'].mean():.2f}%")
print(f"최근 12개월 평균: {df['yoy_growth'].tail(12).mean():.2f}%")

# 경고: 급격한 증가
if df['yoy_growth'].iloc[-1] > 10:
    print("⚠️ M2 증가율이 10% 초과 - 인플레이션 압력 가능성")
```

**통화 지표 종류:**
- `"M1"`: 협의통화 (현금 + 요구불예금) - 거래 목적
- `"M2"`: 광의통화 (M1 + 저축성예금 + MMF 등) - 가장 일반적
- `"Lf"`: 금융기관유동성 (M2 + 생명보험 + 증권사 등)

---

### 2. 은행 대출금 조회하기

**언제 사용하나요?**
- 가계/기업의 부채 증가 추세를 파악할 때
- 부동산 시장과 대출의 관계를 분석할 때
- 금융 안정성을 평가할 때

**전체 대출 조회:**
```python
import ecos

# 최근 3년간 전체 은행 대출
df = ecos.get_bank_lending()
print(df.tail())
```

**가계 대출만 조회:**
```python
df = ecos.get_bank_lending(sector="household")
print(df.tail())
```

**기업 대출만 조회:**
```python
df = ecos.get_bank_lending(sector="corporate")
print(df.tail())
```

**실전 활용 - 가계 vs 기업 대출 비교:**
```python
import ecos
import pandas as pd

# 데이터 조회
household = ecos.get_bank_lending(sector="household", start_date="202001")
corporate = ecos.get_bank_lending(sector="corporate", start_date="202001")

# 병합
comparison = pd.merge(
    household[['date', 'value']].rename(columns={'value': 'household'}),
    corporate[['date', 'value']].rename(columns={'value': 'corporate'}),
    on='date'
)

# 비율 계산
comparison['ratio'] = comparison['household'] / comparison['corporate']
comparison['household_pct'] = comparison['household'].pct_change(periods=12) * 100
comparison['corporate_pct'] = comparison['corporate'].pct_change(periods=12) * 100

print("=== 가계 vs 기업 대출 ===")
print(comparison.tail(10))

print(f"\n최근 가계/기업 비율: {comparison['ratio'].iloc[-1]:.2f}")
print(f"가계대출 YoY: {comparison['household_pct'].iloc[-1]:.2f}%")
print(f"기업대출 YoY: {comparison['corporate_pct'].iloc[-1]:.2f}%")

# 분석
if comparison['household_pct'].iloc[-1] > comparison['corporate_pct'].iloc[-1]:
    print("📊 가계대출이 기업대출보다 빠르게 증가 중")
```

**대출 부문:**
- `"all"`: 전체 (기본값)
- `"household"`: 가계대출
- `"corporate"`: 기업대출

**경제적 의미:**
- 가계대출 급증 → 부동산 과열 가능성, 가계부채 우려
- 기업대출 증가 → 설비투자 활발, 경기 확장 신호

---

## 고급 기능 사용하기

### 캐시 활용하기

**왜 캐시를 사용하나요?**
- API 호출 횟수 절약 (Rate Limit 회피)
- 응답 속도 향상 (0.01초 이내)
- 동일한 데이터 반복 조회 시 효율적

**캐시 동작 확인:**
```python
import ecos
import time

# 첫 번째 호출 (API 요청)
start = time.time()
df1 = ecos.get_cpi(start_date="202301", end_date="202312")
time1 = time.time() - start
print(f"첫 번째 호출: {time1:.2f}초 (API 요청)")

# 두 번째 호출 (캐시에서 반환)
start = time.time()
df2 = ecos.get_cpi(start_date="202301", end_date="202312")
time2 = time.time() - start
print(f"두 번째 호출: {time2:.2f}초 (캐시)")

print(f"속도 향상: {time1/time2:.0f}배")
```

**출력:**
```
첫 번째 호출: 0.52초 (API 요청)
두 번째 호출: 0.01초 (캐시)
속도 향상: 52배
```

**캐시 비활성화 (실시간 데이터 필요 시):**
```python
import ecos

# 캐시 비활성화
ecos.disable_cache()

# 이제 매번 API 호출
df = ecos.get_cpi()

# 다시 활성화
ecos.enable_cache()
```

**캐시 초기화:**
```python
import ecos

# 캐시된 데이터 모두 삭제
ecos.clear_cache()

# 이제 다음 호출은 API 요청
df = ecos.get_cpi()
```

**캐시 설정:**
- **TTL**: 1시간 (자동 만료)
- **크기**: 최대 100개 항목
- **정책**: LRU (가장 오래된 것부터 삭제)

---

### 로깅 활성화하기

**왜 로깅을 사용하나요?**
- API 요청 과정 추적
- 에러 발생 시 디버깅
- 성능 문제 진단

**로깅 활성화:**
```python
import logging
import ecos

# 로깅 활성화
ecos.setup_logging(logging.INFO)

# 이제 API 호출 시 로그 출력
df = ecos.get_cpi()
```

**로그 출력 예시:**
```
2025-12-23 10:30:15 [INFO] API 요청 시작: StatisticSearch
2025-12-23 10:30:15 [INFO] 캐시 미스 - API 호출 필요
2025-12-23 10:30:16 [INFO] API 응답 성공: 1.2초 소요
```

**디버그 모드 (상세 로그):**
```python
import logging
import ecos

# 상세한 디버그 로그
ecos.setup_logging(logging.DEBUG)

df = ecos.get_cpi()
```

**출력:**
```
2025-12-23 10:30:15 [DEBUG] API 요청 URL: https://ecos.bok.or.kr/api/...
2025-12-23 10:30:15 [DEBUG] 요청 파라미터: stat_code=901Y009, period=M, ...
2025-12-23 10:30:16 [DEBUG] 응답 크기: 2458 바이트
2025-12-23 10:30:16 [DEBUG] DataFrame 생성 완료: 24 행
```

---

### 성능 모니터링하기

**왜 메트릭을 수집하나요?**
- API 사용 패턴 파악
- 캐시 효율성 확인
- 성능 병목 지점 발견

**메트릭 확인:**
```python
import ecos

# 여러 API 호출
df1 = ecos.get_cpi()
df2 = ecos.get_base_rate()
df3 = ecos.get_cpi()  # 캐시에서 반환

# 메트릭 요약
metrics = ecos.get_metrics_summary()

print("=== API 사용 통계 ===")
print(f"총 호출: {metrics['api_calls']['total']}")
print(f"성공: {metrics['api_calls']['success']}")
print(f"실패: {metrics['api_calls']['failed']}")
print(f"성공률: {metrics['api_calls']['success_rate']:.1f}%")

print("\n=== 응답 시간 ===")
print(f"평균: {metrics['response_time']['average']:.2f}초")
print(f"최소: {metrics['response_time']['min']:.2f}초")
print(f"최대: {metrics['response_time']['max']:.2f}초")

print("\n=== 캐시 효율 ===")
print(f"캐시 적중: {metrics['cache']['hits']}")
print(f"캐시 미스: {metrics['cache']['misses']}")
print(f"적중률: {metrics['cache']['hit_rate']:.1f}%")
```

**출력:**
```
=== API 사용 통계 ===
총 호출: 3
성공: 3
실패: 0
성공률: 100.0%

=== 응답 시간 ===
평균: 0.42초
최소: 0.01초
최대: 0.85초

=== 캐시 효율 ===
캐시 적중: 1
캐시 미스: 2
적중률: 33.3%
```

**메트릭 초기화:**
```python
import ecos

# 메트릭 리셋
ecos.reset_metrics()

# 새로운 세션 시작
df = ecos.get_cpi()
```

---

### 커스텀 클라이언트 사용하기

**언제 사용하나요?**
- 타임아웃을 조정하고 싶을 때
- 재시도 횟수를 변경하고 싶을 때
- 캐시를 완전히 끄고 싶을 때

**기본 사용법:**
```python
from ecos import EcosClient
import ecos

# 커스텀 클라이언트 생성
custom_client = EcosClient(
    api_key="your_api_key",
    timeout=60,        # 60초 타임아웃 (기본: 30초)
    max_retries=5,     # 최대 5회 재시도 (기본: 3회)
    use_cache=True,    # 캐시 사용
)

# 전역 클라이언트로 설정
ecos.set_client(custom_client)

# 이제 모든 함수가 커스텀 클라이언트 사용
df = ecos.get_cpi()
```

**직접 사용 (고급):**
```python
from ecos import EcosClient
from ecos.parser import parse_response, normalize_stat_result

client = EcosClient(api_key="your_api_key")

# ECOS API 직접 호출
response = client.get_statistic_search(
    stat_code="901Y009",  # CPI 통계코드
    period="M",
    start_date="202301",
    end_date="202312",
    item_code1="0",
)

# DataFrame으로 변환
df = parse_response(response)
df = normalize_stat_result(df)
print(df)
```

---

### 에러 처리하기

**왜 에러 처리가 필요한가요?**
- API 키 오류 대응
- 네트워크 문제 처리
- Rate Limit 초과 대응
- 안정적인 프로덕션 코드 작성

**기본 에러 처리:**
```python
import ecos
from ecos import EcosConfigError, EcosNetworkError, EcosAPIError

try:
    df = ecos.get_cpi()
    print("✓ 데이터 조회 성공")
    print(df.tail())

except EcosConfigError as e:
    print(f"❌ API 키 오류: {e}")
    print("해결: ecos.set_api_key('your_key') 또는 환경 변수 설정")

except EcosNetworkError as e:
    print(f"❌ 네트워크 오류: {e}")
    print("해결: 인터넷 연결 확인")

except EcosAPIError as e:
    print(f"❌ API 오류 [{e.code}]: {e.message}")
    print("해결: 파라미터 또는 날짜 형식 확인")
```

**빈 DataFrame 처리:**
```python
import ecos

df = ecos.get_cpi(start_date="202301", end_date="202312")

if df.empty:
    print("⚠️ 조회된 데이터가 없습니다.")
    print("- 날짜 형식을 확인하세요 (YYYYMM)")
    print("- 데이터가 존재하는 기간인지 확인하세요")
else:
    print(f"✓ {len(df)}개 데이터 조회 완료")
    print(df.tail())
```

**재시도 로직 (Rate Limit 대응):**
```python
import time
import ecos
from ecos import EcosRateLimitError

max_retries = 3

for attempt in range(max_retries):
    try:
        df = ecos.get_cpi()
        print("✓ 성공")
        break

    except EcosRateLimitError as e:
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1초, 2초, 4초
            print(f"⚠️ Rate Limit - {wait_time}초 대기 중...")
            time.sleep(wait_time)
        else:
            print("❌ 재시도 실패")
            raise
```

**여러 지표 안전하게 조회:**
```python
import ecos
from ecos import EcosError

indicators = {
    "CPI": lambda: ecos.get_cpi(),
    "기준금리": lambda: ecos.get_base_rate(),
    "GDP": lambda: ecos.get_gdp(),
    "M2": lambda: ecos.get_money_supply(),
}

results = {}

for name, func in indicators.items():
    try:
        results[name] = func()
        print(f"✓ {name}: {len(results[name])}개 데이터")
    except EcosError as e:
        print(f"✗ {name} 실패: {e}")
        results[name] = None

# 성공한 데이터만 사용
successful_data = {k: v for k, v in results.items() if v is not None}
print(f"\n총 {len(successful_data)}/{len(indicators)}개 조회 성공")
```

---

## 실전 활용 예제

### 예제 1: 거시경제 스냅샷 대시보드

**목적:** 현재 경제 상황을 한눈에 파악

```python
import ecos

print("=" * 50)
print("       한국 거시경제 스냅샷")
print("=" * 50)

try:
    # 1. 금리
    base_rate = ecos.get_base_rate()
    if not base_rate.empty:
        current_rate = base_rate.iloc[-1]['value']
        print(f"\n📊 한국은행 기준금리: {current_rate}%")

    # 2. 물가
    cpi = ecos.get_cpi()
    if not cpi.empty:
        current_cpi = cpi.iloc[-1]['value']
        target = 2.0
        gap = current_cpi - target
        print(f"💰 소비자물가(CPI): {current_cpi}% (목표 대비 {gap:+.1f}%p)")

    # 3. 성장
    gdp = ecos.get_gdp(frequency="Q")
    if len(gdp) >= 5:
        gdp = gdp.sort_values('date').reset_index(drop=True)
        gdp['yoy'] = gdp['value'].pct_change(periods=4) * 100
        latest_growth = gdp.iloc[-1]['yoy']
        print(f"📈 실질 GDP 성장률: {latest_growth:.2f}% (YoY)")

    # 4. 통화
    m2 = ecos.get_money_supply(indicator="M2")
    if len(m2) >= 13:
        m2 = m2.sort_values('date').reset_index(drop=True)
        m2['yoy'] = m2['value'].pct_change(periods=12) * 100
        m2_growth = m2.iloc[-1]['yoy']
        print(f"💵 M2 증가율: {m2_growth:.2f}% (YoY)")

    print("\n" + "=" * 50)

except Exception as e:
    print(f"❌ 오류 발생: {e}")
```

**출력:**
```
==================================================
       한국 거시경제 스냅샷
==================================================

📊 한국은행 기준금리: 3.50%
💰 소비자물가(CPI): 2.30% (목표 대비 +0.3%p)
📈 실질 GDP 성장률: 2.85% (YoY)
💵 M2 증가율: 4.12% (YoY)

==================================================
```

---

### 예제 2: 금리 인상 사이클 분석

**목적:** 금리 변화 패턴 파악 및 향후 예측

```python
import ecos
import pandas as pd

# 금리 데이터 조회
df = ecos.get_base_rate(start_date="202001", end_date="202412")
df = df.sort_values('date').reset_index(drop=True)

# 금리 변화 계산
df['change'] = df['value'].diff()

# 금리 변경 시점만 추출
changes = df[df['change'] != 0].copy()

print("=== 기준금리 변동 이력 ===\n")

for idx, row in changes.iterrows():
    date = row['date'].strftime('%Y-%m-%d')
    rate = row['value']
    change = row['change']

    if change > 0:
        direction = "인상 ⬆️"
    else:
        direction = "인하 ⬇️"

    print(f"{date}: {rate:.2f}% ({direction} {abs(change):.2f}%p)")

# 현재 사이클 분석
current_rate = df.iloc[-1]['value']
first_rate = df.iloc[0]['value']
total_change = current_rate - first_rate

print(f"\n=== 기간 총 변화 ===")
print(f"시작: {first_rate:.2f}%")
print(f"현재: {current_rate:.2f}%")
print(f"변화: {total_change:+.2f}%p")

if total_change > 1.0:
    print("💡 분석: 긴축 사이클 진행 중")
elif total_change < -1.0:
    print("💡 분석: 완화 사이클 진행 중")
else:
    print("💡 분석: 중립 금리 수준 유지")
```

---

### 예제 3: 인플레이션 종합 분석

**목적:** 다각도로 물가 상황 분석

```python
import ecos
import pandas as pd

# 데이터 조회
cpi = ecos.get_cpi(start_date="202001", end_date="202412")
core_cpi = ecos.get_core_cpi(start_date="202001", end_date="202412")
ppi = ecos.get_ppi(start_date="202001", end_date="202412")

# 병합
inflation = pd.merge(
    cpi[['date', 'value']].rename(columns={'value': 'cpi'}),
    core_cpi[['date', 'value']].rename(columns={'value': 'core_cpi'}),
    on='date'
)
inflation = pd.merge(
    inflation,
    ppi[['date', 'value']].rename(columns={'value': 'ppi'}),
    on='date'
)

# 분석
inflation['cpi_core_gap'] = inflation['cpi'] - inflation['core_cpi']
inflation['ppi_cpi_gap'] = inflation['ppi'] - inflation['cpi']

print("=== 인플레이션 종합 분석 ===\n")

# 최근 상황
latest = inflation.iloc[-1]
print(f"기준일: {latest['date'].strftime('%Y-%m')}")
print(f"CPI: {latest['cpi']:.2f}%")
print(f"근원 CPI: {latest['core_cpi']:.2f}%")
print(f"PPI: {latest['ppi']:.2f}%")

print(f"\n=== 갭 분석 ===")
print(f"CPI - 근원CPI: {latest['cpi_core_gap']:+.2f}%p")
if abs(latest['cpi_core_gap']) > 0.5:
    print("  → 일시적 요인(식료품/에너지) 영향 큼")
else:
    print("  → 기조적 인플레이션 반영")

print(f"\nPPI - CPI: {latest['ppi_cpi_gap']:+.2f}%p")
if latest['ppi_cpi_gap'] > 1.0:
    print("  → 향후 소비자물가 상승 압력 존재")
elif latest['ppi_cpi_gap'] < -1.0:
    print("  → 기업 수익성 압박 가능성")
else:
    print("  → 균형적 상황")

# 추세
avg_cpi = inflation['cpi'].tail(12).mean()
print(f"\n최근 12개월 평균 CPI: {avg_cpi:.2f}%")

if avg_cpi > 3.0:
    print("💡 평가: 인플레이션 압력 높음 - 긴축 정책 지속 가능")
elif avg_cpi > 2.0:
    print("💡 평가: 목표 수준 근처 - 정책 중립 가능")
else:
    print("💡 평가: 디플레이션 우려 - 완화 정책 검토 가능")
```

---

### 예제 4: 경기 선행지표 점검

**목적:** 금리 역전과 선행 지표로 경기 전망

```python
import ecos

print("=== 경기 선행지표 점검 ===\n")

# 1. 금리 역전 확인
spread = ecos.get_yield_spread(
    long_maturity="10Y",
    short_maturity="3Y",
    start_date="20240101"
)

if not spread.empty:
    latest_spread = spread.iloc[-1]
    print(f"📊 국고채 10Y-3Y 스프레드: {latest_spread['spread']:.2f}%p")

    if latest_spread['spread'] < 0:
        print("  ⚠️ 금리 역전 발생 - 경기 침체 신호")
        inversions = spread[spread['spread'] < 0]
        print(f"  역전 기간: {len(inversions)}일")
    elif latest_spread['spread'] < 0.5:
        print("  ⚠️ 금리차 축소 - 경기 둔화 가능성")
    else:
        print("  ✓ 정상 범위 - 경기 확장 지속")

# 2. PPI 선행성 확인
ppi = ecos.get_ppi(start_date="202301")
if not ppi.empty:
    ppi = ppi.sort_values('date')
    latest_ppi = ppi.iloc[-1]['value']
    prev_ppi = ppi.iloc[-2]['value']

    print(f"\n💰 생산자물가(PPI): {latest_ppi:.2f}%")

    if latest_ppi > prev_ppi + 0.5:
        print("  ⬆️ 급격한 상승 - 향후 CPI 상승 압력")
    elif latest_ppi < prev_ppi - 0.5:
        print("  ⬇️ 하락 추세 - 향후 CPI 안정화 기대")
    else:
        print("  ➡️ 안정적 - 물가 현 수준 유지 전망")

# 3. M2 증가율
m2 = ecos.get_money_supply(indicator="M2", start_date="202001")
if len(m2) >= 13:
    m2 = m2.sort_values('date')
    m2['yoy'] = m2['value'].pct_change(periods=12) * 100
    latest_m2_growth = m2.iloc[-1]['yoy']

    print(f"\n💵 M2 증가율: {latest_m2_growth:.2f}% (YoY)")

    if latest_m2_growth > 8:
        print("  ⚠️ 과도한 유동성 - 자산 가격 상승 압력")
    elif latest_m2_growth < 4:
        print("  ⚠️ 유동성 부족 - 성장 둔화 우려")
    else:
        print("  ✓ 적정 수준 - 안정적 성장 지원")

print("\n" + "="*40)
```

---

### 예제 5: 월간 경제 리포트 자동화

**목적:** 매월 자동으로 경제 리포트 생성

```python
import ecos
from datetime import datetime

def generate_monthly_report():
    """월간 경제 리포트 생성"""

    current_date = datetime.now().strftime("%Y년 %m월")

    print("=" * 60)
    print(f"         {current_date} 한국 경제 리포트")
    print("=" * 60)

    # 1. 금리
    print("\n[1] 금리 동향")
    print("-" * 60)
    base_rate = ecos.get_base_rate()
    if not base_rate.empty:
        current = base_rate.iloc[-1]['value']
        prev = base_rate.iloc[-2]['value'] if len(base_rate) > 1 else current
        change = current - prev

        print(f"기준금리: {current}%", end="")
        if change != 0:
            print(f" ({change:+.2f}%p 변동)")
        else:
            print(" (동결)")

    # 2. 물가
    print("\n[2] 물가 동향")
    print("-" * 60)
    cpi = ecos.get_cpi()
    if not cpi.empty:
        latest = cpi.iloc[-1]
        print(f"소비자물가: {latest['value']}% (전년동월비)")

        if latest['value'] > 3.0:
            print("평가: 높은 인플레이션 압력")
        elif latest['value'] > 2.0:
            print("평가: 목표 수준 근처")
        else:
            print("평가: 안정적 물가")

    # 3. 성장
    print("\n[3] 경제 성장")
    print("-" * 60)
    gdp = ecos.get_gdp(frequency="Q")
    if len(gdp) >= 5:
        gdp = gdp.sort_values('date')
        gdp['yoy'] = gdp['value'].pct_change(periods=4) * 100
        latest = gdp.iloc[-1]

        print(f"실질 GDP: {latest['value']:.2f}조원")
        print(f"성장률: {latest['yoy']:.2f}% (전년동기비)")

    # 4. 통화
    print("\n[4] 통화 및 신용")
    print("-" * 60)
    m2 = ecos.get_money_supply()
    if not m2.empty:
        latest = m2.iloc[-1]
        print(f"M2: {latest['value']:.2f}조원")

    household_loan = ecos.get_bank_lending(sector="household")
    if not household_loan.empty:
        latest = household_loan.iloc[-1]
        print(f"가계대출: {latest['value']:.2f}조원")

    print("\n" + "=" * 60)
    print("보고서 생성 완료")
    print("=" * 60)

# 실행
generate_monthly_report()
```

---

## 문제 해결

### 자주 발생하는 문제와 해결 방법

#### 문제 1: "API 키가 설정되지 않았습니다"

**증상:**
```
EcosConfigError: API Key가 설정되지 않았습니다.
```

**해결 방법:**
```python
import ecos

# 방법 1: 직접 설정
ecos.set_api_key("your_api_key")

# 방법 2: 환경 변수 확인
import os
print(os.environ.get('ECOS_API_KEY'))  # None이면 설정 안 됨

# 방법 3: .env 파일 로드
ecos.load_env()
```

---

#### 문제 2: "해당하는 데이터가 없습니다"

**증상:**
빈 DataFrame이 반환됨

**원인:**
- 날짜 형식이 잘못됨
- 데이터가 존재하지 않는 기간 조회

**해결 방법:**
```python
import ecos

# 날짜 형식 확인
# 월간 데이터: YYYYMM
df = ecos.get_cpi(start_date="202401", end_date="202412")  # ✓ 올바름
# df = ecos.get_cpi(start_date="2024-01", end_date="2024-12")  # ✗ 잘못됨

# 분기 데이터: YYYYQN
df = ecos.get_gdp(frequency="Q", start_date="2024Q1")  # ✓ 올바름

# 일간 데이터: YYYYMMDD
df = ecos.get_treasury_yield(maturity="10Y", start_date="20240101")  # ✓ 올바름
```

---

#### 문제 3: Rate Limit 초과

**증상:**
```
EcosRateLimitError: 과도한 OpenAPI 호출로 이용이 제한되었습니다.
```

**해결 방법:**
```python
import ecos
import time

# 방법 1: 캐시 활용
ecos.enable_cache()  # 같은 요청 반복 시 캐시 사용

# 방법 2: 요청 간격 두기
df1 = ecos.get_cpi()
time.sleep(1)  # 1초 대기
df2 = ecos.get_base_rate()

# 방법 3: 재시도 로직
from ecos import EcosRateLimitError

for attempt in range(3):
    try:
        df = ecos.get_cpi()
        break
    except EcosRateLimitError:
        if attempt < 2:
            time.sleep(5)  # 5초 대기 후 재시도
        else:
            raise
```

---

#### 문제 4: 네트워크 타임아웃

**증상:**
```
EcosNetworkError: 요청 타임아웃 (30초)
```

**해결 방법:**
```python
from ecos import EcosClient
import ecos

# 타임아웃 늘리기
custom_client = EcosClient(
    timeout=60,  # 60초로 증가
    max_retries=5,
)

ecos.set_client(custom_client)

df = ecos.get_cpi()
```

---

#### 문제 5: DataFrame이 비어있는지 확인하기

**올바른 방법:**
```python
import ecos

df = ecos.get_cpi(start_date="202301", end_date="202312")

# 방법 1: empty 속성 사용 (추천)
if df.empty:
    print("데이터가 없습니다")
else:
    print(f"{len(df)}개 데이터 조회")

# 방법 2: len() 사용
if len(df) == 0:
    print("데이터가 없습니다")

# 안전한 접근
if not df.empty:
    latest_value = df.iloc[-1]['value']
    print(f"최근 값: {latest_value}")
```

---

## 빠른 참조

### 날짜 형식 치트시트

| 주기 | 형식 | 예시 | 사용 함수 |
|------|------|------|-----------|
| 일간 (D) | YYYYMMDD | 20240101 | `get_treasury_yield()` |
| 월간 (M) | YYYYMM | 202401 | `get_base_rate()`, `get_cpi()`, `get_money_supply()` 등 |
| 분기 (Q) | YYYYQN | 2024Q1 | `get_gdp(frequency="Q")` |
| 연간 (A) | YYYY | 2024 | `get_gdp(frequency="A")` |

---

### 함수 빠른 참조

#### 금리 지표
```python
# 기준금리 (월간)
ecos.get_base_rate(start_date="202001", end_date="202412")

# 국고채 수익률 (일간)
ecos.get_treasury_yield(maturity="10Y", start_date="20240101")

# 금리차 (일간)
ecos.get_yield_spread(long_maturity="10Y", short_maturity="3Y")
```

#### 물가 지표
```python
# CPI (월간)
ecos.get_cpi(start_date="202001", end_date="202412")

# 근원 CPI (월간)
ecos.get_core_cpi(start_date="202001", end_date="202412")

# PPI (월간)
ecos.get_ppi(start_date="202001", end_date="202412")
```

#### 성장 지표
```python
# GDP (분기)
ecos.get_gdp(frequency="Q", basis="real", start_date="2020Q1")

# GDP (연간)
ecos.get_gdp(frequency="A", basis="nominal", start_date="2020")

# GDP 디플레이터 (분기)
ecos.get_gdp_deflator(frequency="Q", start_date="2020Q1")
```

#### 통화 지표
```python
# M2 통화량 (월간)
ecos.get_money_supply(indicator="M2", start_date="202001")

# M1 통화량 (월간)
ecos.get_money_supply(indicator="M1", start_date="202001")

# 가계 대출 (월간)
ecos.get_bank_lending(sector="household", start_date="202001")

# 기업 대출 (월간)
ecos.get_bank_lending(sector="corporate", start_date="202001")
```

---

### 설정 및 유틸리티

```python
# API 키 설정
ecos.set_api_key("your_api_key")
ecos.load_env()  # .env에서 로드

# 캐시 관리
ecos.clear_cache()
ecos.disable_cache()
ecos.enable_cache()

# 로깅
import logging
ecos.setup_logging(logging.INFO)

# 메트릭
metrics = ecos.get_metrics_summary()
ecos.reset_metrics()

# 클라이언트
from ecos import EcosClient
client = EcosClient(timeout=60, max_retries=5)
ecos.set_client(client)
```

---

### 에러 타입

```python
from ecos import (
    EcosError,          # 기본 에러
    EcosConfigError,    # API 키 오류
    EcosNetworkError,   # 네트워크 오류
    EcosAPIError,       # ECOS API 오류
    EcosRateLimitError, # Rate Limit 초과
)
```

---

## 추가 리소스

- **ECOS Open API 공식 문서**: [https://ecos.bok.or.kr/api/](https://ecos.bok.or.kr/api/)
- **GitHub 저장소**: [https://github.com/choo121600/ecos-reader](https://github.com/choo121600/ecos-reader)
- **이슈 리포트**: [https://github.com/choo121600/ecos-reader/issues](https://github.com/choo121600/ecos-reader/issues)
- **개발 로드맵**: 프로젝트 루트의 ROADMAP.md

---

**문서 버전**: 2.0 (사용 가이드)
**최종 업데이트**: 2025-12-23
**라이브러리 버전**: 0.1.0
