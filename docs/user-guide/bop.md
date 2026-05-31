# 국제수지 지표

경상수지, 자본수지, 금융계정 등 국제수지 관련 지표를 조회하는 방법을 설명합니다.

## 국제수지

국제수지(통계표 `301Y013`)를 조회합니다. 단위는 백만달러이며, 월·분기·연 주기를 지원합니다. `value` 는 흑자일 때 양수, 적자일 때 음수입니다.

### 기본 사용법

```python
import ecos

# 경상수지, 월별 (기본값)
df = ecos.get_balance_of_payments()
print(df.tail())
```

### 옵션 지정

```python
# 자본수지
df = ecos.get_balance_of_payments(account="capital")

# 금융계정, 연 주기
df = ecos.get_balance_of_payments(account="financial", frequency="annual")

# 분기 주기, 기간 지정
df = ecos.get_balance_of_payments(
    account="current",
    frequency="quarterly",
    start_date="2020Q1",
    end_date="2024Q4",
)
```

`get_balance_of_payments(account="current", start_date=None, end_date=None, frequency="monthly")` 의 인자는 다음과 같습니다.

| `account` | 설명 |
|-----------|------|
| `"current"` | 경상수지 (기본값) |
| `"capital"` | 자본수지 |
| `"financial"` | 금융계정 |

| `frequency` | 날짜 형식 |
|-------------|-----------|
| `"monthly"` | `YYYYMM` (기본값) |
| `"quarterly"` | `YYYYQn` (예: `2024Q1`) |
| `"annual"` | `YYYY` |

!!! info "날짜 형식"
    `start_date` / `end_date` 형식은 `frequency` 설정에 따라 달라집니다. 기간을 생략하면 주기별 기본 범위가 적용됩니다.

!!! info "부호 규칙"
    `value` 는 흑자일 때 양수, 적자일 때 음수로 표현됩니다.

### 반환 데이터 구조

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `date` | datetime | 조회 시점 |
| `value` | float | 국제수지 (백만달러, 흑자 양수 / 적자 음수) |
| `unit` | str | 단위 |

## 실전 활용 예제

### 경상수지 추이 시각화

```python
import ecos
import matplotlib.pyplot as plt

df = ecos.get_balance_of_payments(account="current", start_date="202001")

df.set_index("date")["value"].plot(
    kind="bar",
    title="경상수지 추이",
    ylabel="경상수지 (백만달러)",
    figsize=(14, 6),
    grid=True,
    color=["red" if x < 0 else "blue" for x in df["value"]],
)
plt.axhline(y=0, color="black", linestyle="-", linewidth=1)
plt.tight_layout()
plt.show()
```

### 흑자·적자 개월 집계

```python
import ecos

df = ecos.get_balance_of_payments(account="current", start_date="202001")

surplus = (df["value"] > 0).sum()
deficit = (df["value"] < 0).sum()

print(f"흑자 개월: {surplus}")
print(f"적자 개월: {deficit}")
print(f"누적 경상수지: {df['value'].sum():.0f} 백만달러")
```

## 다음 단계

- [환율 지표](forex.md) - 원/외화 매매기준율
- [무역(수출입) 지표](trade.md) - 통관기준 수출입금액
- [성장 지표](growth.md) - GDP 등 경제성장 지표
