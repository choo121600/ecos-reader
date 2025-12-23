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
