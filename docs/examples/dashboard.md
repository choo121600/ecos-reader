# 거시경제 대시보드 예제

주요 거시경제 지표를 한눈에 볼 수 있는 대시보드를 만드는 방법을 설명합니다.

## 전체 코드

```python
"""
거시경제 대시보드 예제

주요 거시경제 지표를 한눈에 볼 수 있는 대시보드를 생성합니다.
"""

from datetime import datetime

import pandas as pd

import ecos


def create_macro_summary() -> pd.DataFrame:
    """
    주요 거시경제 지표 요약 테이블을 생성합니다.

    Returns
    -------
    pd.DataFrame
        지표명, 최신값, 전월/전기 대비 변화를 포함한 요약 테이블
    """
    summary_data = []

    # 1. 기준금리
    try:
        df = ecos.get_base_rate()
        if not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else None
            change = latest["value"] - prev["value"] if prev is not None else 0
            summary_data.append(
                {
                    "지표": "한국은행 기준금리",
                    "최신값": f"{latest['value']:.2f}%",
                    "변화": f"{change:+.2f}%p",
                    "기준일": latest["date"].strftime("%Y-%m") if pd.notna(latest["date"]) else "",
                }
            )
    except Exception as e:
        print(f"기준금리 조회 실패: {e}")

    # 2. CPI
    try:
        df = ecos.get_cpi()
        if not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else None
            change = latest["value"] - prev["value"] if prev is not None else 0
            summary_data.append(
                {
                    "지표": "소비자물가 상승률",
                    "최신값": f"{latest['value']:.1f}%",
                    "변화": f"{change:+.1f}%p",
                    "기준일": latest["date"].strftime("%Y-%m") if pd.notna(latest["date"]) else "",
                }
            )
    except Exception as e:
        print(f"CPI 조회 실패: {e}")

    # 3. 국고채 3년 수익률
    try:
        df = ecos.get_treasury_yield(maturity="3Y")
        if not df.empty:
            latest = df.iloc[-1]
            summary_data.append(
                {
                    "지표": "국고채 3년 수익률",
                    "최신값": f"{latest['value']:.2f}%",
                    "변화": "-",
                    "기준일": latest["date"].strftime("%Y-%m-%d")
                    if pd.notna(latest["date"])
                    else "",
                }
            )
    except Exception as e:
        print(f"국고채 수익률 조회 실패: {e}")

    # 4. M2 통화량
    try:
        df = ecos.get_money_supply(indicator="M2")
        if not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else None
            if prev is not None and prev["value"] > 0:
                yoy = (latest["value"] - prev["value"]) / prev["value"] * 100
                change_str = f"{yoy:+.1f}%"
            else:
                change_str = "-"

            summary_data.append(
                {
                    "지표": "M2 통화량",
                    "최신값": f"{latest['value']/1000:.0f}조원",
                    "변화": change_str,
                    "기준일": latest["date"].strftime("%Y-%m") if pd.notna(latest["date"]) else "",
                }
            )
    except Exception as e:
        print(f"M2 조회 실패: {e}")

    return pd.DataFrame(summary_data)


def analyze_yield_curve() -> dict:
    """
    수익률 곡선 분석

    Returns
    -------
    dict
        장단기 금리차 및 분석 결과
    """
    try:
        df = ecos.get_yield_spread()
        if df.empty:
            return {"error": "데이터 없음"}

        latest = df.iloc[-1]
        spread = latest["spread"]

        # 역전 여부 판단
        if spread < 0:
            signal = "⚠️ 금리 역전 (경기 침체 경고)"
        elif spread < 0.5:
            signal = "⚡ 금리차 축소 (주의)"
        else:
            signal = "✅ 정상 수익률 곡선"

        return {
            "10년물": f"{latest['long_yield']:.2f}%",
            "3년물": f"{latest['short_yield']:.2f}%",
            "금리차": f"{spread:.2f}%p",
            "신호": signal,
            "기준일": latest["date"].strftime("%Y-%m-%d") if pd.notna(latest["date"]) else "",
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    """대시보드 메인 함수"""
    print("=" * 70)
    print("           📊 한국 거시경제 대시보드")
    print(f"           생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    print()

    # 주요 지표 요약
    print("📈 주요 거시경제 지표")
    print("-" * 70)
    summary = create_macro_summary()
    if not summary.empty:
        print(summary.to_string(index=False))
    else:
        print("데이터를 불러올 수 없습니다.")
    print()

    # 수익률 곡선 분석
    print("📉 수익률 곡선 분석")
    print("-" * 70)
    yield_analysis = analyze_yield_curve()
    if "error" not in yield_analysis:
        for key, value in yield_analysis.items():
            print(f"  {key}: {value}")
    else:
        print(f"  에러: {yield_analysis['error']}")
    print()

    print("=" * 70)
    print("데이터 출처: 한국은행 ECOS Open API")
    print("=" * 70)


if __name__ == "__main__":
    main()
```

## 출력 예시

```
======================================================================
           📊 한국 거시경제 대시보드
           생성일: 2024-12-30 15:30
======================================================================

📈 주요 거시경제 지표
----------------------------------------------------------------------
           지표      최신값    변화    기준일
  한국은행 기준금리  3.50%  +0.00%p  2024-12
    소비자물가 상승률  2.3%  -0.2%p  2024-12
  국고채 3년 수익률  3.25%       -  2024-12-30
        M2 통화량  3500조원  +1.2%  2024-12

📉 수익률 곡선 분석
----------------------------------------------------------------------
  10년물: 3.45%
  3년물: 3.25%
  금리차: 0.20%p
  신호: ⚡ 금리차 축소 (주의)
  기준일: 2024-12-30

======================================================================
데이터 출처: 한국은행 ECOS Open API
======================================================================
```

## 함수 설명

### create_macro_summary()

주요 거시경제 지표의 최신값과 변화를 요약한 테이블을 생성합니다.

**반환하는 지표:**

- 한국은행 기준금리
- 소비자물가 상승률
- 국고채 3년 수익률
- M2 통화량

**특징:**

- 각 지표별로 try-except로 안전하게 처리
- 전월/전기 대비 변화 계산
- 에러 발생 시 해당 지표만 제외하고 계속 진행

### analyze_yield_curve()

수익률 곡선을 분석하고 경기 전망 신호를 제공합니다.

**분석 기준:**

- 금리차 < 0: 금리 역전 (경기 침체 경고)
- 금리차 < 0.5%p: 금리차 축소 (주의)
- 금리차 >= 0.5%p: 정상 수익률 곡선

## 확장 예제

### 1. 시각화 추가

```python
import matplotlib.pyplot as plt
import ecos

def plot_key_indicators():
    """주요 지표를 그래프로 시각화"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    # 1. 기준금리
    df = ecos.get_base_rate(start_date="202001")
    ax1.plot(df['date'], df['value'], linewidth=2, color='blue')
    ax1.set_title('기준금리')
    ax1.set_ylabel('%')
    ax1.grid(True, alpha=0.3)

    # 2. CPI
    df = ecos.get_cpi(start_date="202001")
    ax2.plot(df['date'], df['value'], linewidth=2, color='red')
    ax2.axhline(y=2.0, color='gray', linestyle='--', label='목표 2%')
    ax2.set_title('소비자물가 상승률')
    ax2.set_ylabel('%')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. GDP
    df = ecos.get_gdp(frequency="Q", start_date="2020Q1")
    ax3.bar(range(len(df)), df['value'], color='green', alpha=0.7)
    ax3.set_title('GDP 성장률 (분기)')
    ax3.set_ylabel('%')
    ax3.grid(True, alpha=0.3)

    # 4. 장단기 금리차
    df = ecos.get_yield_spread(start_date="20200101")
    colors = ['red' if x < 0 else 'blue' for x in df['spread']]
    ax4.bar(range(len(df)), df['spread'], color=colors, alpha=0.7)
    ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax4.set_title('장단기 금리차')
    ax4.set_ylabel('%p')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

# 실행
plot_key_indicators()
```

### 2. HTML 리포트 생성

```python
import ecos
import pandas as pd
from datetime import datetime

def create_html_report():
    """HTML 리포트 생성"""
    # 데이터 조회
    summary = create_macro_summary()
    yield_curve = analyze_yield_curve()

    # HTML 템플릿
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>거시경제 대시보드</title>
        <style>
            body {{ font-family: 'Malgun Gothic', sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            .warning {{ color: #ff9800; }}
            .error {{ color: #f44336; }}
            .success {{ color: #4CAF50; }}
        </style>
    </head>
    <body>
        <h1>📊 한국 거시경제 대시보드</h1>
        <p>생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

        <h2>주요 거시경제 지표</h2>
        {summary.to_html(index=False)}

        <h2>수익률 곡선 분석</h2>
        <ul>
            <li>10년물: {yield_curve.get('10년물', '-')}</li>
            <li>3년물: {yield_curve.get('3년물', '-')}</li>
            <li>금리차: {yield_curve.get('금리차', '-')}</li>
            <li>신호: {yield_curve.get('신호', '-')}</li>
        </ul>

        <p><small>데이터 출처: 한국은행 ECOS Open API</small></p>
    </body>
    </html>
    """

    # 파일 저장
    with open('macro_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("✅ macro_dashboard.html 생성 완료")

# 실행
create_html_report()
```

### 3. 정기 리포트 자동화

```python
import ecos
import schedule
import time
from datetime import datetime

def send_daily_report():
    """일일 리포트 생성 및 전송"""
    print(f"[{datetime.now()}] 일일 리포트 생성 중...")

    summary = create_macro_summary()
    yield_curve = analyze_yield_curve()

    # 콘솔 출력
    print("\n" + "=" * 70)
    print("           📊 일일 거시경제 리포트")
    print("=" * 70)
    print("\n주요 지표:")
    print(summary.to_string(index=False))
    print("\n수익률 곡선:")
    for key, value in yield_curve.items():
        print(f"  {key}: {value}")
    print("=" * 70 + "\n")

    # 여기에 이메일 전송 로직 추가 가능
    # send_email(summary, yield_curve)

# 매일 오전 9시에 실행
schedule.every().day.at("09:00").do(send_daily_report)

print("일일 리포트 스케줄러 시작...")
print("매일 오전 9시에 리포트가 생성됩니다.")

# 무한 루프
while True:
    schedule.run_pending()
    time.sleep(60)
```

## 실행 방법

### 1. 기본 실행

```bash
python examples/macro_dashboard.py
```

### 2. 모듈로 사용

```python
from examples.macro_dashboard import create_macro_summary, analyze_yield_curve

# 요약 테이블
summary = create_macro_summary()
print(summary)

# 수익률 곡선 분석
analysis = analyze_yield_curve()
print(analysis)
```

## 커스터마이징

### 추가할 만한 지표

- GDP 성장률
- 가계대출
- 기업대출
- 환율
- 주가지수

### 분석 추가

- 경기 선행 지수
- 인플레이션 압력 분석
- 금융 안정성 지표

## 다음 단계

- [기본 사용법 예제](basic.md) - 기초부터 배우기
- [사용자 가이드](../user-guide/basic-usage.md) - 심화 사용법
