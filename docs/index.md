# ecos-reader

**한국은행 ECOS Open API Python 클라이언트**

ecos-reader는 한국은행 ECOS Open API를 Python에서 쉽고 일관된 방식으로 사용할 수 있는 라이브러리입니다.

## 주요 특징

- **간편한 사용법**: 복잡한 API 요청을 간단한 함수 호출로 처리
- **타입 안전성**: 완전한 타입 힌팅 지원으로 IDE 자동완성 활용
- **pandas 통합**: 모든 데이터를 pandas DataFrame으로 반환
- **자동 캐싱**: 불필요한 API 호출을 줄여 성능 향상
- **포괄적인 지표**: 금리, 물가, 성장, 통화 등 주요 거시경제 지표 지원
- **에러 처리**: 명확한 예외 클래스로 안정적인 에러 핸들링

## 빠른 시작

### 설치

```bash
pip install ecos-reader
```

### API 키 설정

한국은행에서 발급받은 API 키를 환경 변수로 설정합니다.

```bash
export ECOS_API_KEY="your_api_key"
```

!!! info "API 키 발급"
    API 키는 [한국은행 ECOS](https://ecos.bok.or.kr/api/)에서 무료로 발급받을 수 있습니다.

### 첫 번째 코드

```python
import ecos

# 한국은행 기준금리 조회
df = ecos.get_base_rate()
print(df)
```

출력 예시:

```
        date  value unit
0 2024-01-01   3.50    %
1 2024-02-01   3.50    %
2 2024-03-01   3.50    %
...
```

## 지원 지표

### 금리 지표

- 한국은행 기준금리
- 국고채 수익률 (1Y, 3Y, 5Y, 10Y, 20Y, 30Y)
- 장단기 금리차

### 물가 지표

- 소비자물가지수 (CPI)
- 근원 CPI
- 생산자물가지수 (PPI)

### 성장 지표

- GDP (분기/연간, 실질/명목)
- GDP 디플레이터

### 통화 지표

- 통화량 (M1, M2, Lf)
- 은행 대출 (가계/기업)

## 다음 단계

- [설치 가이드](getting-started/installation.md) - 자세한 설치 방법
- [빠른 시작](getting-started/quickstart.md) - 기본 사용법 익히기
- [사용자 가이드](user-guide/basic-usage.md) - 심화 사용법
- [API 레퍼런스](api-reference/overview.md) - 전체 API 문서
- [예제](examples/basic.md) - 실전 예제 코드

## 라이센스

MIT License - 자세한 내용은 [LICENSE](https://github.com/choo121600/ecos-reader/blob/main/LICENSE) 파일을 참조하세요.
