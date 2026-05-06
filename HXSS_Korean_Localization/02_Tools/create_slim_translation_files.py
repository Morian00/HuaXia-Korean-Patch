#!/usr/bin/env python3
"""
Create slim translation work files from t_language.xml and t_tasklanguage.xml.

The game-facing XML must keep its original structure for re-encryption.
These slim files are for AI/human translation work only.
"""

from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
XML_WORK = PROJECT_ROOT / "01_XML_Localization" / "XmlWork"
WORKING_XML = XML_WORK / "WorkingXml"
SLIM_XML = XML_WORK / "SlimTranslationXml"
REVIEW = XML_WORK / "Review"
LANGUAGE_FILES = ("t_language.xml", "t_tasklanguage.xml")


def write_slim_xml(source: Path, target: Path) -> int:
    tree = ET.parse(source)
    root = tree.getroot()
    slim_root = ET.Element(root.tag)
    count = 0

    for elem in root.findall("sample"):
        sid = elem.attrib.get("sid", "").strip()
        zh = elem.attrib.get("zh", "")
        ko = elem.attrib.get("ko", "")
        if not sid or not zh:
            continue
        ET.SubElement(slim_root, "sample", {"sid": sid, "zh": zh, "ko": ko})
        count += 1

    target.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(slim_root, space="\t")
    ET.ElementTree(slim_root).write(target, encoding="utf-8", xml_declaration=True)
    return count


def write_full_tsv(target: Path) -> int:
    rows: list[dict[str, str]] = []
    for filename in LANGUAGE_FILES:
        root = ET.parse(WORKING_XML / filename).getroot()
        for elem in root.findall("sample"):
            sid = elem.attrib.get("sid", "").strip()
            zh = elem.attrib.get("zh", "")
            if not sid or not zh:
                continue
            rows.append(
                {
                    "language_table": filename,
                    "sid": sid,
                    "zh": zh,
                    "ko_new": "",
                    "owner": "",
                    "notes": "",
                }
            )

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            delimiter="\t",
            fieldnames=["language_table", "sid", "zh", "ko_new", "owner", "notes"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    total = 0
    for filename in LANGUAGE_FILES:
        source = WORKING_XML / filename
        target = SLIM_XML / filename.replace(".xml", ".slim.xml")
        count = write_slim_xml(source, target)
        print(f"{target}: {count} rows")
        total += count

    tsv_count = write_full_tsv(REVIEW / "Full_Translation.tsv")
    print(f"{REVIEW / 'Full_Translation.tsv'}: {tsv_count} rows")
    print(f"total slim xml rows: {total}")


if __name__ == "__main__":
    main()
