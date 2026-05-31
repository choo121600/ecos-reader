# 범용 조회 & 탐색

ecos-reader는 큐레이션된 지표 함수(`get_base_rate`, `get_cpi` 등) 외에, **ECOS의
어떤 통계표든 직접 받을 수 있는** 범용 조회 API를 제공합니다. 도메인 함수가 없는
통계도 `get_series` 하나로 도달할 수 있습니다.

## 아무 ECOS 시계열이나 받기 — `get_series`

`get_series` 는 `(통계표코드, 주기)` 와 기간을 받아 정규화된 long-format tidy
DataFrame을 돌려줍니다.

```python
import ecos
ecos.set_api_key("YOUR_KEY")

# 기준금리(722Y001) 월별, 특정 항목
df = ecos.get_series(
    "722Y001", "monthly",
    start_date="202401", end_date="202412",
    item_code="0101000",
)
print(df.columns.tolist())   # ['date', 'value', 'unit', 'item_code1', 'item_name1']
```

### period 어휘

정식 어휘와 ECOS 원시 코드를 모두 받으며 대소문자를 구분하지 않습니다.

| 정식 어휘 | 원시 코드 | 의미 |
|-----------|-----------|------|
| `daily` | `D` | 일 |
| `monthly` | `M` | 월 |
| `quarterly` | `Q` | 분기 |
| `annual` | `A` | 연 |
| `semiannual` | `S` | 반기 |
| `semimonthly` | `SM` | 반월 |

### 항목코드 — 단일/다축

`item_code` 는 `None`(전체), 단일 문자열, 또는 길이 ≤ 4 리스트(다축)를 받습니다.

```python
# 다축 조회 — 항목 차원이 long-format으로 보존됩니다
df = ecos.get_series(
    "200Y001", "Q",
    start_date="2024Q1", end_date="2024Q4",
    item_code=["10101", "10102"],
)
```

### 큰 표와 페이지네이션

`get_series` 는 ECOS 요청 윈도우를 넘는 표를 자동으로 순회해 전량 수신합니다.
`max_rows`(안전 가드)와 `page_size` 로 조절합니다.

```python
# 일별 대형 표 — 자동 페이지네이션
df = ecos.get_series("817Y002", "D", start_date="20200101", end_date="20231231")
```

### 원본 컬럼이 필요할 때 — `tidy=False`

```python
raw = ecos.get_series("722Y001", "M", start_date="202401", end_date="202412", tidy=False)
# parse_response 의 snake_case 원본 컬럼을 그대로 반환
```

## 표 찾기 — 카탈로그 탐색 (오프라인)

전체 통계표 카탈로그가 패키지에 동봉되어 있어 **네트워크 없이** 탐색합니다.

```python
import ecos

# 키워드로 통계표 검색
hits = ecos.search_tables("소비자물가")
print(hits[["stat_code", "stat_name", "cycle"]])

# 카테고리(부모) 아래 직계 표 나열 — parent=None 이면 최상위
roots = ecos.list_tables()
children = ecos.list_tables(roots.iloc[0]["stat_code"])

# 전체 트리(중첩 dict)
tree = ecos.get_table_tree()

# 카탈로그 전체 DataFrame
catalog = ecos.load_catalog()
```

## 항목 찾기 — `list_items`

조회에 필요한 `item_code` 를 표에서 찾습니다.

```python
items = ecos.list_items("722Y001")
print(items[["item_code", "item_name", "cycle"]].head())

# 찾은 item_code 로 바로 조회
code = items.iloc[0]["item_code"]
df = ecos.get_series("722Y001", "monthly", start_date="202401", end_date="202412", item_code=code)
```

## 완결 흐름

검색 → 항목 해석 → 조회로 ECOS 전체에 도달합니다.

```python
import ecos
ecos.set_api_key("YOUR_KEY")

table = ecos.search_tables("소비자물가").iloc[0]["stat_code"]   # 901Y009
item = ecos.list_items(table).iloc[0]["item_code"]               # 0 (총지수)
df = ecos.get_series(table, "quarterly", start_date="2023Q1", end_date="2023Q4", item_code=item)
```

대량 수집 시의 rate limiter·디스크 캐시 설정은 [고급 기능](advanced.md)을 참고하세요.
