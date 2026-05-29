#!/usr/bin/env python3
"""선언적 레지스트리 기반 지표 문서를 자동 생성합니다 (#16).

:data:`ecos.indicators.INDICATORS` 를 단일 진실원천으로 삼아, 레지스트리에 등록된
지표 목록을 markdown 표로 출력합니다. 새 지표를 레지스트리에 한 줄 추가하면 이
스크립트를 다시 실행하는 것만으로 문서가 동기화됩니다.

범위 주의
---------
이 스크립트는 **레지스트리에 등록된 단순 지표**(날짜 외 선택 인자가 없는 단일
통계표·항목 지표)만 다룹니다. 전체 ECOS 통계 구현 현황(파라미터화/계산 지표 포함)을
사람이 큐레이션하는 ``IMPLEMENTATION_STATUS.md`` 를 대체하지 않습니다. 모든 지표가
레지스트리로 마이그레이션되면 그 문서도 이 방식으로 자동 생성될 수 있습니다.

사용법
------
    python scripts/gen_indicator_registry_doc.py            # stdout 출력
    python scripts/gen_indicator_registry_doc.py -o docs/development/indicator-registry.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# src 레이아웃을 import 경로에 추가 (설치 없이 실행 가능하도록).
_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists():
    sys.path.insert(0, str(_SRC))

from ecos.indicators import list_indicators  # noqa: E402

_DATE_FORMAT_LABEL = {"D": "일별", "M": "월별", "Q": "분기", "A": "연간"}


def render() -> str:
    """레지스트리 내용을 markdown 문자열로 렌더링합니다."""
    specs = list_indicators()

    lines = [
        "# 선언적 지표 레지스트리 (Indicator Registry)",
        "",
        "> 이 파일은 `scripts/gen_indicator_registry_doc.py` 가 "
        "`ecos.indicators.INDICATORS` 레지스트리에서 자동 생성합니다. 직접 편집하지 마세요.",
        ">",
        "> 전체 ECOS 통계 구현 현황은 `IMPLEMENTATION_STATUS.md` 를 참고하세요. "
        "이 문서는 레지스트리에 등록된 단순 지표만 다룹니다.",
        "",
        f"등록된 선언적 지표: **{len(specs)}건**",
        "",
    ]

    # 카테고리별 그룹핑 (카테고리명 정렬, 그 안에서 name 정렬).
    categories: dict[str, list] = {}
    for spec in specs:
        categories.setdefault(spec.category or "기타", []).append(spec)

    for category in sorted(categories):
        lines.append(f"## {category}")
        lines.append("")
        lines.append("| name | 통계표코드 | 항목코드 | 주기 | 단위 | 설명 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for spec in sorted(categories[category], key=lambda s: s.name):
            freq = _DATE_FORMAT_LABEL.get(spec.date_format, spec.date_format)
            unit = spec.unit or "-"
            item = spec.item_code1 or "-"
            lines.append(
                f"| `{spec.name}` | {spec.stat_code} | {item} | {freq} | {unit} "
                f"| {spec.description} |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="출력 파일 경로 (생략 시 stdout)",
    )
    args = parser.parse_args()

    content = render()
    if args.output is None:
        sys.stdout.write(content)
    else:
        args.output.write_text(content, encoding="utf-8")
        print(f"wrote {args.output} ({len(list_indicators())} indicators)")


if __name__ == "__main__":
    main()
