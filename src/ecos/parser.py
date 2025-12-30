"""
ecos-reader 응답 파서

ECOS API 응답을 pandas DataFrame으로 변환합니다.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

# ECOS API 컬럼명 -> 정규화된 컬럼명 매핑
COLUMN_MAP: dict[str, str] = {
    "STAT_CODE": "stat_code",
    "STAT_NAME": "stat_name",
    "ITEM_CODE1": "item_code1",
    "ITEM_NAME1": "item_name1",
    "ITEM_CODE2": "item_code2",
    "ITEM_NAME2": "item_name2",
    "ITEM_CODE3": "item_code3",
    "ITEM_NAME3": "item_name3",
    "ITEM_CODE4": "item_code4",
    "ITEM_NAME4": "item_name4",
    "UNIT_NAME": "unit",
    "TIME": "time",
    "DATA_VALUE": "value",
    "GRP_CODE": "grp_code",
    "GRP_NAME": "grp_name",
    "ITEM_CODE": "item_code",
    "ITEM_NAME": "item_name",
    "P_ITEM_CODE": "p_item_code",
    "P_ITEM_NAME": "p_item_name",
    "CYCLE": "cycle",
    "START_TIME": "start_time",
    "END_TIME": "end_time",
    "DATA_CNT": "data_cnt",
    "WEIGHT": "weight",
    # StatisticTableList 추가 필드
    "P_STAT_CODE": "p_stat_code",
    "SRCH_YN": "srch_yn",
    "ORG_NAME": "org_name",
    # StatisticWord 추가 필드
    "WORD": "word",
    "CONTENT": "content",
    # KeyStatisticList 추가 필드
    "CLASS_NAME": "class_name",
    "KEYSTAT_NAME": "keystat_name",
    # StatisticMeta 추가 필드
    "LVL": "lvl",
    "P_CONT_CODE": "p_cont_code",
    "CONT_CODE": "cont_code",
    "CONT_NAME": "cont_name",
    "META_DATA": "meta_data",
}


def parse_response(response: dict[str, Any]) -> pd.DataFrame:
    """
    ECOS API 응답을 pandas DataFrame으로 변환합니다.

    Parameters
    ----------
    response : dict
        ECOS API JSON 응답

    Returns
    -------
    pd.DataFrame
        정규화된 DataFrame

    Notes
    -----
    - 컬럼명은 snake_case로 정규화됩니다.
    - 빈 응답은 빈 DataFrame을 반환합니다.
    - 수치 컬럼은 자동으로 float으로 변환됩니다.
    """
    # 응답 데이터 추출
    # StatisticSearch -> row, StatisticItemList -> row 등
    data = None

    # 여러 서비스 응답 형식 지원
    for key in [
        "StatisticSearch",
        "StatisticItemList",
        "StatisticTableList",
        "KeyStatisticList",
        "StatisticWord",
        "StatisticMeta",
    ]:
        if key in response:
            data = response[key].get("row", [])
            break

    if not data:
        return pd.DataFrame()

    # DataFrame 생성
    df = pd.DataFrame(data)

    # 컬럼명 정규화
    df = df.rename(columns=COLUMN_MAP)

    # 수치 컬럼 변환
    if "value" in df.columns:
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    if "data_cnt" in df.columns:
        df["data_cnt"] = pd.to_numeric(df["data_cnt"], errors="coerce")

    if "weight" in df.columns:
        df["weight"] = pd.to_numeric(df["weight"], errors="coerce")

    return df


def parse_time_column(df: pd.DataFrame, time_col: str = "time") -> pd.DataFrame:
    """
    시간 컬럼을 datetime으로 변환합니다.

    Parameters
    ----------
    df : pd.DataFrame
        변환할 DataFrame
    time_col : str
        시간 컬럼명, 기본값 'time'

    Returns
    -------
    pd.DataFrame
        날짜 컬럼이 추가된 DataFrame

    Notes
    -----
    ECOS 시간 형식:
    - 연간: YYYY (예: 2024)
    - 반년: YYYYSN (예: 2024S1)
    - 분기: YYYYQN (예: 2024Q1)
    - 월간: YYYYMM (예: 202401)
    - 반월: YYYYMMSMN (예: 202401SM1)
    - 일간: YYYYMMDD (예: 20240101)
    """
    if time_col not in df.columns or df.empty:
        return df

    df = df.copy()

    def convert_time(time_str: str) -> pd.Timestamp | None:
        if not time_str:
            return None

        time_str = str(time_str)

        # 연간: YYYY
        if len(time_str) == 4 and time_str.isdigit():
            return pd.Timestamp(f"{time_str}-01-01")

        # 반년: YYYYSN
        if len(time_str) == 6 and "S" in time_str and "SM" not in time_str:
            year = time_str[:4]
            half = int(time_str[5])
            month = (half - 1) * 6 + 1
            return pd.Timestamp(f"{year}-{month:02d}-01")

        # 분기: YYYYQN
        if len(time_str) == 6 and "Q" in time_str:
            year = time_str[:4]
            quarter = int(time_str[5])
            month = (quarter - 1) * 3 + 1
            return pd.Timestamp(f"{year}-{month:02d}-01")

        # 월간: YYYYMM
        if len(time_str) == 6 and time_str.isdigit():
            return pd.Timestamp(f"{time_str[:4]}-{time_str[4:6]}-01")

        # 반월: YYYYMMSMN
        if len(time_str) == 10 and "SM" in time_str:
            year = time_str[:4]
            month_str = time_str[4:6]
            half = int(time_str[9])
            day = 1 if half == 1 else 16
            return pd.Timestamp(f"{year}-{month_str}-{day:02d}")

        # 일간: YYYYMMDD
        if len(time_str) == 8 and time_str.isdigit():
            return pd.Timestamp(f"{time_str[:4]}-{time_str[4:6]}-{time_str[6:8]}")

        return None

    df["date"] = df[time_col].apply(convert_time)

    return df


def normalize_stat_result(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    date_col: str = "time",
) -> pd.DataFrame:
    """
    통계 조회 결과를 정규화합니다.

    Parameters
    ----------
    df : pd.DataFrame
        원본 DataFrame
    columns : list[str], optional
        선택할 컬럼 목록, 기본값은 ['date', 'value', 'unit']
    date_col : str
        날짜로 변환할 원본 컬럼명

    Returns
    -------
    pd.DataFrame
        정규화된 DataFrame
    """
    if df.empty:
        return df

    # 날짜 변환
    df = parse_time_column(df, date_col)

    # 기본 컬럼 선택
    if columns is None:
        columns = ["date", "value", "unit"]

    # 존재하는 컬럼만 선택
    available_columns = [col for col in columns if col in df.columns]

    if available_columns:
        df = df[available_columns]

    # 날짜 기준 정렬
    if "date" in df.columns:
        df = df.sort_values("date").reset_index(drop=True)

    return df
