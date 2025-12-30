# 100대 통계지표 개발 명세서

## 개요

한국은행 경제통계 Open API의 주요 100대 통계지표를 조회하는 서비스입니다. 한국은행이 선정한 주요 경제지표의 최신 값을 간편하게 조회할 수 있으며, 통계그룹별로 분류되어 제공됩니다.

## 상세주소

* [https://ecos.bok.or.kr/api/](https://ecos.bok.or.kr/api/)
* HTTP와 HTTPS 모두 사용 가능합니다.

## 요청인자

| 항목명(국문) | 필수여부 | 샘플데이터 | 항목설명 |
|---------|------|--------|--------|
| 서비스명 | Y | KeyStatisticList | API 서비스명 |
| 인증키 | Y | sample | 한국은행에서 발급받은 오픈API 인증키 |
| 요청유형 | Y | xml | 결과값의 파일 형식 - xml, json |
| 언어구분 | Y | kr | 결과값의 언어 - kr(국문), en(영문) |
| 요청시작건수 | Y | 1 | 전체 결과값 중 시작 번호 |
| 요청종료건수 | Y | 10 | 전체 결과값 중 끝 번호 |

### 요청인자 설명

- **서비스명**: 고정값 `KeyStatisticList`
- **인증키**: 한국은행 Open API에서 발급받은 인증키
- **요청유형**: 응답 형식 (`xml` 또는 `json`)
- **언어구분**: 응답 언어 (`kr`: 국문, `en`: 영문)
- **요청시작건수**: 페이징을 위한 시작 번호 (1부터 시작)
- **요청종료건수**: 페이징을 위한 종료 번호

## 출력값

| 항목명(국문) | 항목명(영문) | 항목크기 | 샘플데이터 | 항목설명 |
|---------|----------|------|--------|--------|
| 통계그룹명 | CLASS_NAME | 400 | 국민소득 · 경기 · 기업경영 | 통계그룹명 |
| 통계명 | KEYSTAT_NAME | 200 | 경제성장률(전기대비) | 통계명 |
| 값 | DATA_VALUE | 23 | 1.9 | 값 |
| 시점 | CYCLE | 13 | 202003 | 통계의 최근 수록 시점 |
| 단위 | UNIT_NAME | 200 | %, 달러, 십억원 등 | 단위 |

### 출력값 설명

- **통계그룹명**: 통계가 속한 그룹명 (예: 국민소득 · 경기 · 기업경영, 물가, 금리 등)
- **통계명**: 통계지표의 이름 (예: 경제성장률(전기대비), 소비자물가지수 등)
- **값**: 해당 통계지표의 최신 값
- **시점**: 통계의 최근 수록 시점 (YYYYMM 형식)
- **단위**: 데이터의 단위 (예: %, 달러, 십억원 등)

## 샘플 URL

```
https://ecos.bok.or.kr/api/KeyStatisticList/{인증키}/xml/kr/1/10
```

### URL 구성 요소

1. 기본 URL: `https://ecos.bok.or.kr/api/`
2. 서비스명: `KeyStatisticList`
3. 인증키: `{인증키}` (실제 인증키로 대체)
4. 요청유형: `xml` 또는 `json`
5. 언어구분: `kr` 또는 `en`
6. 요청시작건수: `1`
7. 요청종료건수: `10`

## 메시지 설명

### 정보 메시지

| 코드 | 설명 |
|----|----|
| 100 | 인증키가 유효하지 않습니다. 인증키를 확인하십시오! 인증키가 없는 경우 인증키를 신청하십시오! |
| 200 | 해당하는 데이터가 없습니다. |

### 에러 메시지

| 코드 | 설명 |
|----|----|
| 100 | 필수 값이 누락되어 있습니다. 필수 값을 확인하십시오! 필수 값이 누락되어 있으면 오류를 발생합니다. 요청 변수를 참고 하십시오! |
| 101 | 주기와 다른 형식의 날짜 형식입니다. |
| 200 | 파일타입 값이 누락 혹은 유효하지 않습니다. 파일타입 값을 확인하십시오! 파일타입 값이 누락 혹은 유효하지 않으면 오류를 발생합니다. 요청 변수를 참고 하십시오! |
| 300 | 조회건수 값이 누락되어 있습니다. 조회시작건수/조회종료건수 값을 확인하십시오! 조회시작건수/조회종료건수 값이 누락되어 있으면 오류를 발생합니다. |
| 301 | 조회건수 값의 타입이 유효하지 않습니다. 조회건수 값을 확인하십시오! 조회건수 값의 타입이 유효하지 않으면 오류를 발생합니다. 정수를 입력하세요. |
| 400 | 검색범위가 적정범위를 초과하여 60초 TIMEOUT이 발생하였습니다. 요청조건 조정하여 다시 요청하시기 바랍니다. |
| 500 | 서버 오류입니다. OpenAPI 호출시 서버에서 오류가 발생하였습니다. 해당 서비스를 찾을 수 없습니다. |
| 600 | DB Connection 오류입니다. OpenAPI 호출시 서버에서 DB접속 오류가 발생했습니다. |
| 601 | SQL 오류입니다. OpenAPI 호출시 서버에서 SQL 오류가 발생했습니다. |
| 602 | 과도한 OpenAPI호출로 이용이 제한되었습니다. 잠시후 이용해주시기 바랍니다. |

## 사용 예제

### XML 형식 요청

```bash
curl "https://ecos.bok.or.kr/api/KeyStatisticList/YOUR_API_KEY/xml/kr/1/10"
```

### JSON 형식 요청

```bash
curl "https://ecos.bok.or.kr/api/KeyStatisticList/YOUR_API_KEY/json/kr/1/10"
```

### 전체 목록 조회 (100개)

```bash
curl "https://ecos.bok.or.kr/api/KeyStatisticList/YOUR_API_KEY/xml/kr/1/100"
```

### 페이징 처리

```bash
# 첫 10개 결과
curl "https://ecos.bok.or.kr/api/KeyStatisticList/YOUR_API_KEY/xml/kr/1/10"

# 다음 10개 결과
curl "https://ecos.bok.or.kr/api/KeyStatisticList/YOUR_API_KEY/xml/kr/11/20"

# 마지막 10개 결과
curl "https://ecos.bok.or.kr/api/KeyStatisticList/YOUR_API_KEY/xml/kr/91/100"
```

### Python 예제

```python
import requests

api_key = "YOUR_API_KEY"
base_url = "https://ecos.bok.or.kr/api/KeyStatisticList"

# 첫 10개 조회
url = f"{base_url}/{api_key}/xml/kr/1/10"
response = requests.get(url)
print(response.text)
```

### Python 예제 - 전체 목록 조회

```python
import requests
import xml.etree.ElementTree as ET

api_key = "YOUR_API_KEY"
base_url = "https://ecos.bok.or.kr/api/KeyStatisticList"

# 전체 100개 조회
url = f"{base_url}/{api_key}/xml/kr/1/100"
response = requests.get(url)

# XML 파싱
root = ET.fromstring(response.text)
for row in root.findall('.//row'):
    group = row.find('CLASS_NAME').text
    name = row.find('KEYSTAT_NAME').text
    value = row.find('DATA_VALUE').text
    cycle = row.find('CYCLE').text
    unit = row.find('UNIT_NAME').text
    print(f"{group} | {name}: {value} {unit} (시점: {cycle})")
```

### Python 예제 - JSON 형식

```python
import requests
import json

api_key = "YOUR_API_KEY"
base_url = "https://ecos.bok.or.kr/api/KeyStatisticList"

# JSON 형식으로 조회
url = f"{base_url}/{api_key}/json/kr/1/10"
response = requests.get(url)
data = response.json()

# 데이터 출력
for item in data.get('KeyStatisticList', {}).get('row', []):
    print(f"{item['CLASS_NAME']} | {item['KEYSTAT_NAME']}: {item['DATA_VALUE']} {item['UNIT_NAME']}")
```

## 주의사항

1. **인증키**: 모든 요청에 유효한 인증키가 필요합니다.
2. **간단한 요청**: 이 서비스는 추가 필터링 파라미터가 없어 가장 간단하게 주요 통계를 조회할 수 있습니다.
3. **최신 값만 제공**: 각 통계지표의 최신 값만 제공되며, 시계열 데이터는 제공되지 않습니다.
4. **페이징**: 요청시작건수와 요청종료건수는 필수이며, 정수값이어야 합니다.
5. **호출 제한**: 과도한 호출 시 일시적으로 이용이 제한될 수 있습니다.
6. **통계그룹**: 통계는 그룹별로 분류되어 있어 관련 통계를 함께 확인할 수 있습니다.
7. **시점 형식**: 시점은 YYYYMM 형식으로 제공됩니다.
8. **100개 제한**: 총 100개의 주요 통계지표만 제공됩니다.

## 사용 시나리오

1. **대시보드 구성**: 주요 경제지표를 한눈에 보는 대시보드를 구성할 때 사용합니다.
2. **최신 지표 확인**: 각 통계지표의 최신 값을 빠르게 확인할 때 사용합니다.
3. **통계 탐색**: 어떤 통계가 있는지 탐색하고, 필요시 상세 데이터는 [통계 조회 조건 설정](statistic-search.md) API를 사용합니다.

## 통계 그룹 예시

100대 통계지표는 다음과 같은 그룹으로 분류됩니다:

- 국민소득 · 경기 · 기업경영
- 물가
- 금리
- 통화 · 금융
- 국제수지 · 환율
- 기타

각 그룹별로 관련 통계지표들이 함께 제공됩니다.

## 관련 서비스

- [서비스 통계 목록](statistic-table-list.md) - 전체 통계표 목록 조회
- [통계 조회 조건 설정](statistic-search.md) - 시계열 통계 데이터 조회
- [통계 세부항목 목록](statistic-item-list.md) - 통계표의 세부 항목 조회
- [통계용어사전](statistic-word.md) - 통계 용어 검색
