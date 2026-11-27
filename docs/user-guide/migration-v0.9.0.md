# v0.9.0 마이그레이션 가이드

v0.9.0은 1.0.0을 앞두고 공개 지표 함수의 호출 방식을 정리한 릴리스입니다.
**기존 코드는 그대로 동작합니다.** 바뀐 호출 방식을 쓰면
[`EcosDeprecationWarning`](../api-reference/exceptions.md)이 표시되며,
해당 경로는 **1.0.0에서 제거**됩니다
([하위호환 정책](../development/deprecation-policy.md)).

## 무엇이 바뀌었나

### 1. 키워드 전용 인자

모든 지표 함수의 인자가 키워드 전용이 되었습니다. 위치로 전달하면 경고가 나고,
1.0.0부터는 `TypeError`가 됩니다. 인자 순서를 착각해 `start_date` 자리에
다른 값이 들어가는 실수를 막기 위한 변경입니다.

```python
import ecos

# 이전 — deprecated (1.0.0에서 TypeError)
df = ecos.get_trade("export", "202301", "202312")

# 이후
df = ecos.get_trade(flow="export", start_date="202301", end_date="202312")
```

`get_indicator()`의 첫 인자 `name`만 예외로 위치 전달을 계속 허용합니다.

```python
df = ecos.get_indicator("cpi", start_date="202301", end_date="202312")
```

### 2. 선택값을 영문으로 통일

한글로 받던 선택값을 영문으로 통일했습니다. 한글 값은 경고와 함께 영문 값으로
변환되며 1.0.0에서 제거됩니다. (`get_cpi_monthly(sub_category=...)`처럼 ECOS 분류명을
그대로 받는 `sub_category` 인자는 바뀌지 않습니다.)

| 함수 | 인자 | 이전 (deprecated) | 이후 |
| :--- | :--- | :--- | :--- |
| `get_investor_trading` | `action` | `"순매수"` / `"매수"` / `"매도"` | `"net_buy"` / `"buy"` / `"sell"` |
| `get_investor_trading` | `metric` | `"거래대금"` / `"거래량"` | `"value"` / `"volume"` |
| `get_bond_market` | `bond_type` | `"종류별"` / `"시장별"` | `"by_type"` / `"by_market"` |
| `get_bond_market` | `measure` | `"거래대금"` / `"거래량"` / `"상장잔액"` / `"상장종목수"` | `"value"` / `"volume"` / `"listed_balance"` / `"listed_count"` |
| `get_bank_deposit_rate`, `get_bank_lending_rate` | `basis` | `"신규취급액"` / `"잔액"` | `"new"` / `"outstanding"` |
| `get_m1_variants`, `get_m2_variants`, `get_m2_by_holder` | `variant` | `"평잔_계절조정"` / `"평잔_원계열"` / `"말잔_계절조정"` / `"말잔_원계열"` | `"average_sa"` / `"average_nsa"` / `"end_sa"` / `"end_nsa"` (함수별 지원 범위는 기존과 동일) |
| `get_household_credit` | `category` | `"업권별"` / `"용도별"` | `"by_lender"` / `"by_purpose"` |
| `get_borrower_loan` | `loan_type` | `"신규"` / `"잔액"` | `"new"` / `"outstanding"` |
| `get_borrower_loan` | `category` | `"전체"` / `"업권별"` / `"성별"` / `"연령별"` / `"지역별"` / `"담보유형별"` / `"다중대출별"` | `"all"` / `"by_lender"` / `"by_gender"` / `"by_age"` / `"by_region"` / `"by_collateral"` / `"by_loan_count"` |
| `get_cpi_by_category` | `category` | `"전체"` / `"상품"` / `"서비스"` / `"식품_에너지제외"` / `"농산물_석유제외"` / `"식료품_비주류음료"` / `"주거_수도_전기"` / `"교통"` | `"all"` / `"goods"` / `"services"` / `"ex_food_energy"` / `"ex_agri_oil"` / `"food_beverages"` / `"housing_utilities"` / `"transport"` |

```python
# 이전 — deprecated
df = ecos.get_investor_trading(action="순매수", metric="거래대금")

# 이후
df = ecos.get_investor_trading(action="net_buy", metric="value")
```

반환 DataFrame의 `category_value`처럼 ECOS 원천 라벨을 담은 **데이터 값**은
바뀌지 않습니다. 바뀐 것은 함수 **인자**의 선택값뿐입니다.

### 3. `seasonal` → `seasonal_adj`

계절조정 여부 인자 이름을 `seasonal_adj`로 통일했습니다.

```python
# 이전 — deprecated
df = ecos.get_industrial_production(seasonal=True)

# 이후
df = ecos.get_industrial_production(seasonal_adj=True)
```

대상: `get_industrial_production`, `get_facility_investment`.

## 미리 점검하기

경고를 오류로 바꿔 실행하면 1.0.0에서 깨질 호출을 모두 찾을 수 있습니다.

```bash
python -W error::FutureWarning your_script.py
pytest -W error::ecos.exceptions.EcosDeprecationWarning
```
