#!/usr/bin/env python3
"""Copy Korean localization text into every non-Chinese language column.

The game can fall back to other language columns in some UI paths. For a
Korean-only patch, mirroring ko into every non-Chinese column prevents mixed
English/Chinese output when the language index or fallback path is inconsistent.
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


LANGUAGE_FILES = ("t_language.xml", "t_tasklanguage.xml")
TARGET_COLUMNS = (
    "en",
    "ru",
    "de",
    "fr",
    "ja",
    "th",
    "pl",
    "tr",
    "uk",
    "it",
    "cs",
    "hu",
    "nl",
    "es",
    "la",
    "pt",
    "br",
    "sv",
    "da",
)


def force_file(path: Path) -> tuple[int, int]:
    tree = ET.parse(path)
    root = tree.getroot()
    rows = 0
    writes = 0

    for sample in root.findall("sample"):
        ko = sample.get("ko", "")
        if not ko:
            continue
        rows += 1
        for column in TARGET_COLUMNS:
            if sample.get(column) != ko:
                sample.set(column, ko)
                writes += 1

    tree.write(path, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    return rows, writes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--xml-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "01_XML_Localization" / "XmlWork" / "WorkingXml",
    )
    args = parser.parse_args()

    total_rows = 0
    total_writes = 0
    for filename in LANGUAGE_FILES:
        rows, writes = force_file(args.xml_dir / filename)
        total_rows += rows
        total_writes += writes
        print(f"{filename}: rows_with_ko={rows} copied_cells={writes}")

    print(f"total_rows_with_ko={total_rows}")
    print(f"total_copied_cells={total_writes}")


if __name__ == "__main__":
    main()
