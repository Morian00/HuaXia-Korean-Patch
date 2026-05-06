#!/usr/bin/env python3
"""
Huaxia: Warring States XML localization helper.

This script treats t_language.xml and t_tasklanguage.xml as the only files
where Korean translations are applied. Other XML files are scanned as context
tables that reference language sids.
"""

from __future__ import annotations

import argparse
import csv
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_ROOT = PROJECT_ROOT.parent
XML_WORK = PROJECT_ROOT / "01_XML_Localization" / "XmlWork"
WORKING_XML = XML_WORK / "WorkingXml"
REPORTS = XML_WORK / "Reports"
CANDIDATE = XML_WORK / "Candidate"
TRANSLATION_QUEUE = XML_WORK / "TranslationQueue"
REVIEW = XML_WORK / "Review"

LANGUAGE_FILES = ("t_language.xml", "t_tasklanguage.xml")

# Curated list of fields that usually contain language table sid references.
# Numeric gameplay fields are intentionally excluded to avoid false positives.
TEXT_REF_FIELDS = {
    "name",
    "describe",
    "description",
    "desc",
    "title",
    "content",
    "uiName",
    "language",
    "dislanguage",
    "timeName",
    "racename",
    "introduce",
    "peculiarity",
    "bubbleDescription",
    "placeTypeName",
    "outputResName",
    "storyDesc",
    "Scenariodescription",
}

EXCLUDED_REF_FIELDS = {
    "id",
    "type",
    "gender",
    "group",
    "showNamePlate",
    "remark",
}

SID_TOKEN_RE = re.compile(r"\d+")
SID_LIST_VALUE_RE = re.compile(r"^[\d,;\s]+$")
TAG_RE = re.compile(r"</?[^>]+>")
VARIABLE_RE = re.compile(r"\{\{[^{}]+\}\}|\{[^{}]+\}|%[sdif]")
NUMBER_RE = re.compile(r"[+-]?\d+(?:\.\d+)?%?|[+-]?\d+(?:\.\d+)?万|[+-]?\d+(?:\.\d+)?/[^\s,，;；。]*")


@dataclass(frozen=True)
class LangEntry:
    table: str
    sid: str
    zh: str
    ko: str


def parse_xml(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def load_language_entries(base: Path) -> dict[str, list[LangEntry]]:
    entries: dict[str, list[LangEntry]] = defaultdict(list)

    for filename in LANGUAGE_FILES:
        root = parse_xml(base / filename)
        for sample in root.findall("sample"):
            sid = sample.get("sid", "")
            zh = sample.get("zh", "")
            if not sid or not zh:
                continue
            entries[sid].append(
                LangEntry(
                    table=filename,
                    sid=sid,
                    zh=zh,
                    ko=sample.get("ko", ""),
                )
            )

    return entries


def load_language_entries_by_key(base: Path) -> dict[tuple[str, str], LangEntry]:
    entries_by_key: dict[tuple[str, str], LangEntry] = {}
    for entries in load_language_entries(base).values():
        for entry in entries:
            entries_by_key[(entry.table, entry.sid)] = entry
    return entries_by_key


def sid_tokens(value: str) -> list[str]:
    if not value:
        return []
    if not SID_LIST_VALUE_RE.fullmatch(value.strip()):
        return []
    return [token for token in SID_TOKEN_RE.findall(value) if token != "0"]


def owner_for_context(filename: str, field: str, entry: LangEntry | None) -> str:
    """Return translation owner recommendation.

    Codex is intentionally limited to UI/system/rule text. Names, regions,
    narrative, and any text with literary flavor go to Antigravity.
    """

    if entry and entry.table == "t_tasklanguage.xml":
        return "Antigravity"

    if filename in {
        "t_worldcity.xml",
        "t_scenes.xml",
        "t_fairyland.xml",
        "t_rolerace.xml",
        "t_rolesound.xml",
        "t_books.xml",
        "t_booksgounp.xml",
        "t_jobtemplate.xml",
    }:
        return "Antigravity"

    if filename in {"t_equipment.xml"}:
        return "Antigravity" if field in {"name", "description"} else "Codex"

    if filename in {"t_skill.xml", "t_talent.xml"}:
        return "Antigravity" if field == "name" else "Codex"

    if filename in {"t_birth.xml"}:
        return "Antigravity" if field == "name" else "Codex"

    if filename in {"t_building.xml"}:
        return "Antigravity" if field in {"name", "storyDesc"} else "Codex"

    if filename in {"t_interfaceguide.xml", "t_tips.xml"}:
        return "Codex" if field in {"title", "uiName"} else "Codex"

    if field in {"name", "title", "racename"}:
        return "Antigravity"

    return "Codex"


def category_for_context(filename: str, field: str, entry: LangEntry | None) -> str:
    if entry and entry.table == "t_tasklanguage.xml":
        return "Quest_Dialogue_Narrative"
    if filename in {"t_worldcity.xml", "t_scenes.xml", "t_fairyland.xml", "t_rolerace.xml"}:
        return "World_Region_Lore"
    if filename in {"t_equipment.xml"}:
        return "Items_Equipment"
    if filename in {"t_books.xml", "t_booksgounp.xml"}:
        return "Books_Learning"
    if filename in {"t_skill.xml", "t_talent.xml"}:
        return "Combat_Skills_Talents"
    if filename in {"t_birth.xml", "t_rolesound.xml", "t_rolepreset.xml", "t_changeclothes.xml"}:
        return "Character_Creation"
    if filename in {"t_building.xml", "t_jobtemplate.xml"}:
        return "Settlement_Job_System"
    if filename in {"t_interfaceguide.xml", "t_tips.xml"}:
        return "UI_Help_System"
    return "Misc"


def write_tsv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_index(base: Path = WORKING_XML, reports: Path = REPORTS) -> None:
    entries = load_language_entries(base)
    data_id_index = build_data_id_index(base)

    language_rows: list[dict[str, str]] = []
    untranslated_rows: list[dict[str, str]] = []
    duplicate_rows: list[dict[str, str]] = []
    for sid, sid_entries in entries.items():
        if len(sid_entries) > 1:
            duplicate_rows.append(
                {
                    "sid": sid,
                    "tables": ";".join(entry.table for entry in sid_entries),
                    "zh_values": " || ".join(entry.zh for entry in sid_entries),
                }
            )
        for entry in sid_entries:
            row = {
                "table": entry.table,
                "sid": entry.sid,
                "zh": entry.zh,
                "ko": entry.ko,
            }
            language_rows.append(row)
            if not entry.ko:
                untranslated_rows.append(row)

    context_rows: list[dict[str, str]] = []
    missing_rows: list[dict[str, str]] = []
    summary_counter: Counter[tuple[str, str]] = Counter()
    owner_counter: Counter[str] = Counter()
    category_counter: Counter[str] = Counter()
    seen_context_keys: set[tuple[str, str, str, str, str]] = set()
    parse_error_rows: list[dict[str, str]] = []

    for xml_path in sorted(base.glob("*.xml")):
        filename = xml_path.name
        if filename in LANGUAGE_FILES:
            continue

        try:
            root = parse_xml(xml_path)
        except ET.ParseError as exc:
            parse_error_rows.append({"source_file": filename, "error": str(exc)})
            continue

        for row_index, sample in enumerate(root.findall("sample"), start=1):
            row_id = sample.get("id", "")
            for field, value in sample.attrib.items():
                if field in EXCLUDED_REF_FIELDS or field not in TEXT_REF_FIELDS:
                    continue
                for sid in sid_tokens(value):
                    key = (filename, str(row_index), row_id, field, sid)
                    if key in seen_context_keys:
                        continue
                    seen_context_keys.add(key)

                    sid_entries = entries.get(sid, [])
                    summary_counter[(filename, field)] += 1

                    if not sid_entries:
                        owner = owner_for_context(filename, field, None)
                        category = category_for_context(filename, field, None)
                        owner_counter[owner] += 1
                        category_counter[category] += 1
                        missing_rows.append(
                            {
                                "sid": sid,
                                "language_table": "MISSING",
                                "zh": "",
                                "ko": "",
                                "source_file": filename,
                                "source_row": str(row_index),
                                "source_id": row_id,
                                "field": field,
                                "raw_value": value,
                                "category": category,
                                "owner": owner,
                            }
                        )
                        continue

                    for entry in sid_entries:
                        owner = owner_for_context(filename, field, entry)
                        category = category_for_context(filename, field, entry)
                        owner_counter[owner] += 1
                        category_counter[category] += 1
                        context_rows.append(
                            {
                                "sid": sid,
                                "language_table": entry.table,
                                "zh": entry.zh,
                                "ko": entry.ko,
                                "source_file": filename,
                                "source_row": str(row_index),
                                "source_id": row_id,
                                "field": field,
                                "raw_value": value,
                                "category": category,
                                "owner": owner,
                            }
                        )

    fieldnames = [
        "sid",
        "language_table",
        "zh",
        "ko",
        "source_file",
        "source_row",
        "source_id",
        "field",
        "raw_value",
        "category",
        "owner",
    ]

    write_tsv(reports / "language_table_index.tsv", language_rows, ["table", "sid", "zh", "ko"])
    write_tsv(reports / "untranslated_ko.tsv", untranslated_rows, ["table", "sid", "zh", "ko"])
    write_tsv(reports / "duplicate_language_sids.tsv", duplicate_rows, ["sid", "tables", "zh_values"])
    write_tsv(reports / "sid_context_index.tsv", context_rows, fieldnames)
    write_tsv(reports / "missing_text_sid_refs.tsv", missing_rows, fieldnames)
    missing_resolution_rows = resolve_missing_refs(missing_rows, data_id_index)
    write_tsv(
        reports / "missing_ref_resolution.tsv",
        missing_resolution_rows,
        [
            "sid",
            "source_file",
            "source_id",
            "field",
            "category",
            "owner",
            "resolution",
            "target_refs",
        ],
    )
    write_tsv(
        reports / "missing_language_sid_refs.tsv",
        [row for row in missing_resolution_rows if row["resolution"] == "language_sid_missing"],
        [
            "sid",
            "source_file",
            "source_id",
            "field",
            "category",
            "owner",
            "resolution",
            "target_refs",
        ],
    )
    missing_action_rows = build_missing_language_action_plan(
        [row for row in missing_resolution_rows if row["resolution"] == "language_sid_missing"]
    )
    write_tsv(
        reports / "missing_language_sid_action_plan.tsv",
        missing_action_rows,
        [
            "sid",
            "source_file",
            "source_ids",
            "field",
            "category",
            "owner",
            "recommended_action",
            "reason",
        ],
    )
    missing_tips_context_rows = build_missing_tips_context(base, entries, missing_action_rows)
    write_tsv(
        reports / "missing_tips_context.tsv",
        missing_tips_context_rows,
        [
            "tip_id",
            "tips_type",
            "title_sid",
            "title_status",
            "title_zh",
            "describe_sid",
            "describe_status",
            "describe_zh",
            "effect",
            "recommended_action",
            "owner",
            "note",
        ],
    )
    write_tsv(
        CANDIDATE / "Codex_Missing_Tips_Context.tsv",
        [row for row in missing_tips_context_rows if row["owner"] == "Codex"],
        [
            "tip_id",
            "tips_type",
            "title_sid",
            "title_status",
            "title_zh",
            "describe_sid",
            "describe_status",
            "describe_zh",
            "effect",
            "recommended_action",
            "owner",
            "note",
        ],
    )
    write_tsv(
        CANDIDATE / "Antigravity_Missing_Tips_Context.tsv",
        [row for row in missing_tips_context_rows if row["owner"] == "Antigravity"],
        [
            "tip_id",
            "tips_type",
            "title_sid",
            "title_status",
            "title_zh",
            "describe_sid",
            "describe_status",
            "describe_zh",
            "effect",
            "recommended_action",
            "owner",
            "note",
        ],
    )
    write_tsv(
        reports / "data_id_references_in_text_fields.tsv",
        [row for row in missing_resolution_rows if row["resolution"] == "data_id_reference"],
        [
            "sid",
            "source_file",
            "source_id",
            "field",
            "category",
            "owner",
            "resolution",
            "target_refs",
        ],
    )
    write_tsv(reports / "xml_parse_errors.tsv", parse_error_rows, ["source_file", "error"])

    summary_rows = []
    for (filename, field), count in sorted(summary_counter.items()):
        summary_rows.append({"source_file": filename, "field": field, "ref_count": str(count)})
    write_tsv(reports / "context_field_summary.tsv", summary_rows, ["source_file", "field", "ref_count"])

    owner_rows = [{"owner": key, "ref_count": str(value)} for key, value in sorted(owner_counter.items())]
    category_rows = [
        {"category": key, "ref_count": str(value)} for key, value in sorted(category_counter.items())
    ]
    write_tsv(reports / "owner_summary.tsv", owner_rows, ["owner", "ref_count"])
    write_tsv(reports / "category_summary.tsv", category_rows, ["category", "ref_count"])

    candidate_rows = build_candidate_rows(context_rows)
    codex_rows = [row for row in candidate_rows if row["owner"] == "Codex"]
    antigravity_rows = [row for row in candidate_rows if row["owner"] == "Antigravity"]
    review_rows = [row for row in candidate_rows if row["owner"] == "Review"]
    candidate_fields = [
        "owner",
        "language_table",
        "sid",
        "zh",
        "ko",
        "categories",
        "ref_count",
        "contexts",
    ]
    write_tsv(CANDIDATE / "Codex_Candidates.tsv", codex_rows, candidate_fields)
    write_tsv(CANDIDATE / "Antigravity_Candidates.tsv", antigravity_rows, candidate_fields)
    write_tsv(CANDIDATE / "Needs_Context_Review.tsv", review_rows, candidate_fields)

    print("XML index generated")
    print(f"language entries: {len(language_rows)}")
    print(f"duplicate language sids: {len(duplicate_rows)}")
    print(f"untranslated ko: {len(untranslated_rows)}")
    print(f"context refs: {len(context_rows)}")
    print(f"missing text refs: {len(missing_rows)}")
    print(
        "missing language refs: "
        + str(sum(1 for row in missing_resolution_rows if row["resolution"] == "language_sid_missing"))
    )
    print(
        "missing refs resolved as data ids: "
        + str(sum(1 for row in missing_resolution_rows if row["resolution"] == "data_id_reference"))
    )
    print(f"xml parse errors: {len(parse_error_rows)}")
    print(f"codex candidates: {len(codex_rows)}")
    print(f"antigravity candidates: {len(antigravity_rows)}")
    print(f"context review candidates: {len(review_rows)}")
    print(f"reports: {reports}")


def build_candidate_rows(context_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}

    for row in context_rows:
        key = (row["language_table"], row["sid"])
        if key not in grouped:
            grouped[key] = {
                "owners": set(),
                "categories": set(),
                "contexts": [],
                "language_table": row["language_table"],
                "sid": row["sid"],
                "zh": row["zh"],
                "ko": row["ko"],
            }

        item = grouped[key]
        item["owners"].add(row["owner"])  # type: ignore[index, union-attr]
        item["categories"].add(row["category"])  # type: ignore[index, union-attr]
        context = f'{row["source_file"]}:{row["source_id"] or row["source_row"]}:{row["field"]}'
        item["contexts"].append(context)  # type: ignore[index, union-attr]

    candidate_rows: list[dict[str, str]] = []
    for item in grouped.values():
        owners = item["owners"]  # type: ignore[assignment]
        categories = sorted(item["categories"])  # type: ignore[arg-type]
        contexts = item["contexts"]  # type: ignore[assignment]
        unique_contexts = []
        seen = set()
        for context in contexts:  # type: ignore[union-attr]
            if context in seen:
                continue
            seen.add(context)
            unique_contexts.append(context)

        category_set = set(categories)

        if owners == {"Codex"}:
            owner = "Codex"
        elif owners == {"Antigravity"}:
            owner = "Antigravity"
        elif category_set & {
            "World_Region_Lore",
            "Items_Equipment",
            "Books_Learning",
            "Character_Creation",
            "Settlement_Job_System",
            "Quest_Dialogue_Narrative",
        }:
            owner = "Antigravity"
        elif category_set <= {"Combat_Skills_Talents", "UI_Help_System", "Misc"}:
            owner = "Codex"
        else:
            owner = "Review"

        candidate_rows.append(
            {
                "owner": owner,
                "language_table": str(item["language_table"]),
                "sid": str(item["sid"]),
                "zh": str(item["zh"]),
                "ko": str(item["ko"]),
                "categories": ";".join(categories),
                "ref_count": str(len(unique_contexts)),
                "contexts": " | ".join(unique_contexts[:20]),
            }
        )

    return sorted(candidate_rows, key=lambda row: (row["owner"], row["language_table"], int(row["sid"])))


def build_data_id_index(base: Path) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for xml_path in sorted(base.glob("*.xml")):
        if xml_path.name in LANGUAGE_FILES:
            continue
        try:
            root = parse_xml(xml_path)
        except ET.ParseError:
            continue
        for row_index, sample in enumerate(root.findall("sample"), start=1):
            sample_id = sample.get("id", "")
            if not sample_id:
                continue
            index[sample_id].append(f'{xml_path.name}:{sample_id or row_index}')
    return index


def resolve_missing_refs(
    missing_rows: list[dict[str, str]], data_id_index: dict[str, list[str]]
) -> list[dict[str, str]]:
    resolved: list[dict[str, str]] = []
    for row in missing_rows:
        sid = row["sid"]
        target_refs = data_id_index.get(sid, [])
        if target_refs:
            resolution = "data_id_reference"
        else:
            resolution = "language_sid_missing"
        resolved.append(
            {
                "sid": sid,
                "source_file": row["source_file"],
                "source_id": row["source_id"],
                "field": row["field"],
                "category": row["category"],
                "owner": row["owner"],
                "resolution": resolution,
                "target_refs": " | ".join(target_refs[:20]),
            }
        )
    return resolved


def build_missing_language_action_plan(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in rows:
        key = (row["sid"], row["source_file"], row["field"])
        if key not in grouped:
            grouped[key] = {
                "sid": row["sid"],
                "source_file": row["source_file"],
                "field": row["field"],
                "category": row["category"],
                "owner": row["owner"],
                "source_ids": set(),
            }
        grouped[key]["source_ids"].add(row["source_id"])  # type: ignore[index, union-attr]

    action_rows: list[dict[str, str]] = []
    for item in grouped.values():
        source_file = str(item["source_file"])
        field = str(item["field"])
        sid = str(item["sid"])

        if source_file == "t_changeclothes.xml":
            action = "collect_source_text_before_add"
            reason = "커스터마이징 파츠명 sid가 언어 테이블에 없음. XML 안에는 숫자 참조만 있고 원문명이 없어 인게임 또는 에셋 데이터 확인 필요."
        elif source_file == "t_tips.xml":
            action = "inspect_context_before_add"
            reason = "도움말 title/describe가 언어 테이블에 없는 sid를 참조. 일부 필드는 데이터 id와 섞일 수 있어 주변 팁 문맥 확인 필요."
        elif source_file == "t_rolerace.xml":
            action = "add_after_antigravity_translation"
            reason = "종족/문화권 이름 sid가 언어 테이블에 없음. 표시명 성격이 강하므로 Antigravity 번역 후 언어 행 추가 후보."
        elif source_file == "t_jobtemplate.xml":
            action = "inspect_context_before_add"
            reason = "직책 설명 sid가 언어 테이블에 없음. 동일 desc가 여러 직책에서 재사용되어 문맥 확인 필요."
        elif source_file == "t_scenes.xml":
            action = "add_after_antigravity_translation"
            reason = "씬/장소명 sid가 언어 테이블에 없음. remark를 참고할 수 있으나 표시명 확정 전 확인 필요."
        else:
            action = "inspect_context_before_add"
            reason = "언어 테이블 누락 의심. 표시 여부와 원문 확인 필요."

        source_ids = sorted(str(x) for x in item["source_ids"])  # type: ignore[index]
        action_rows.append(
            {
                "sid": sid,
                "source_file": source_file,
                "source_ids": ";".join(source_ids),
                "field": field,
                "category": str(item["category"]),
                "owner": str(item["owner"]),
                "recommended_action": action,
                "reason": reason,
            }
        )

    return sorted(action_rows, key=lambda row: (row["source_file"], row["field"], int(row["sid"])))


def first_entry_zh(entries: dict[str, list[LangEntry]], sid: str) -> str:
    sid_entries = entries.get(sid, [])
    return sid_entries[0].zh if sid_entries else ""


def sid_status(entries: dict[str, list[LangEntry]], sid: str) -> str:
    if not sid or sid == "0":
        return "empty"
    return "exists" if sid in entries else "missing"


def build_translation_queue(queue_dir: Path = TRANSLATION_QUEUE) -> None:
    queue_dir.mkdir(parents=True, exist_ok=True)

    main_candidate_fields = [
        "owner",
        "language_table",
        "sid",
        "zh",
        "ko_new",
        "categories",
        "ref_count",
        "contexts",
        "translator_note",
    ]
    for owner, source_name, output_name in [
        ("Codex", "Codex_Candidates.tsv", "Codex_Main.tsv"),
        ("Antigravity", "Antigravity_Candidates.tsv", "Antigravity_Main.tsv"),
    ]:
        rows = []
        for row in read_tsv(CANDIDATE / source_name):
            rows.append(
                {
                    "owner": owner,
                    "language_table": row.get("language_table", ""),
                    "sid": row.get("sid", ""),
                    "zh": row.get("zh", ""),
                    "ko_new": "",
                    "categories": row.get("categories", ""),
                    "ref_count": row.get("ref_count", ""),
                    "contexts": row.get("contexts", ""),
                    "translator_note": "",
                }
            )
        write_tsv(queue_dir / output_name, rows, main_candidate_fields)

    tip_fields = [
        "owner",
        "tip_id",
        "tips_type",
        "title_sid",
        "title_status",
        "title_zh",
        "title_ko_new",
        "describe_sid",
        "describe_status",
        "describe_zh",
        "describe_ko_new",
        "effect",
        "recommended_action",
        "note",
        "translator_note",
    ]
    for owner, source_name, output_name in [
        ("Codex", "Codex_Missing_Tips_Context.tsv", "Codex_Missing_Tips.tsv"),
        ("Antigravity", "Antigravity_Missing_Tips_Context.tsv", "Antigravity_Missing_Tips.tsv"),
    ]:
        rows = []
        for row in read_tsv(CANDIDATE / source_name):
            rows.append(
                {
                    "owner": owner,
                    "tip_id": row.get("tip_id", ""),
                    "tips_type": row.get("tips_type", ""),
                    "title_sid": row.get("title_sid", ""),
                    "title_status": row.get("title_status", ""),
                    "title_zh": row.get("title_zh", ""),
                    "title_ko_new": "",
                    "describe_sid": row.get("describe_sid", ""),
                    "describe_status": row.get("describe_status", ""),
                    "describe_zh": row.get("describe_zh", ""),
                    "describe_ko_new": "",
                    "effect": row.get("effect", ""),
                    "recommended_action": row.get("recommended_action", ""),
                    "note": row.get("note", ""),
                    "translator_note": "",
                }
            )
        write_tsv(queue_dir / output_name, rows, tip_fields)

    customization_fields = [
        "owner",
        "sid",
        "row_id",
        "groupId",
        "gender",
        "category",
        "pictureNumber",
        "open",
        "zh_new",
        "ko_new",
        "note",
        "translator_note",
    ]
    customization_rows = []
    for row in read_tsv(CANDIDATE / "Antigravity_Missing_Character_Customization.tsv"):
        customization_rows.append(
            {
                "owner": "Antigravity",
                "sid": row.get("sid", ""),
                "row_id": row.get("row_id", ""),
                "groupId": row.get("groupId", ""),
                "gender": row.get("gender", ""),
                "category": row.get("category", ""),
                "pictureNumber": row.get("pictureNumber", ""),
                "open": row.get("open", ""),
                "zh_new": "",
                "ko_new": "",
                "note": row.get("note", ""),
                "translator_note": "",
            }
        )
    write_tsv(
        queue_dir / "Antigravity_Missing_Character_Customization.tsv",
        customization_rows,
        customization_fields,
    )

    blocked_fields = [
        "sid",
        "source_file",
        "source_ids",
        "field",
        "category",
        "owner",
        "recommended_action",
        "reason",
        "source_text_status",
        "translator_note",
    ]
    blocked_rows = []
    for row in read_tsv(REPORTS / "missing_language_sid_action_plan.tsv"):
        action = row.get("recommended_action", "")
        if action not in {"collect_source_text_before_add", "inspect_context_before_add"}:
            continue
        blocked_rows.append(
            {
                "sid": row.get("sid", ""),
                "source_file": row.get("source_file", ""),
                "source_ids": row.get("source_ids", ""),
                "field": row.get("field", ""),
                "category": row.get("category", ""),
                "owner": row.get("owner", ""),
                "recommended_action": action,
                "reason": row.get("reason", ""),
                "source_text_status": "needs_source_confirmation",
                "translator_note": "",
            }
        )
    write_tsv(queue_dir / "Blocked_Missing_Source.tsv", blocked_rows, blocked_fields)

    output_template_fields = [
        "language_table",
        "sid",
        "zh",
        "ko_new",
        "owner",
        "category",
        "source_context",
        "notes",
    ]
    write_tsv(queue_dir / "Translated_Output_Template.tsv", [], output_template_fields)

    write_text(queue_dir / "README.md", translation_queue_readme())

    print("Translation queue generated")
    print(f"queue: {queue_dir}")
    print(f"codex main rows: {len(read_tsv(queue_dir / 'Codex_Main.tsv'))}")
    print(f"antigravity main rows: {len(read_tsv(queue_dir / 'Antigravity_Main.tsv'))}")
    print(f"blocked rows: {len(read_tsv(queue_dir / 'Blocked_Missing_Source.tsv'))}")


def translation_queue_readme() -> str:
    return """# XML Translation Queue

## 목적

이 폴더는 XML 직접 번역을 시작하기 직전의 담당자별 작업 큐다.

실제 반영 대상은 WorkingXml 안의 `t_language.xml`, `t_tasklanguage.xml`이다.
큐 파일은 번역 작업용 중간 산출물이며, 게임이 직접 읽는 파일이 아니다.

## 파일 구성

- `Codex_Main.tsv`: Codex 담당 UI, 시스템, 규칙, 수치, 조건 번역.
- `Codex_Missing_Tips.tsv`: Codex 담당 도움말 누락 sid 검토.
- `Antigravity_Main.tsv`: Antigravity 담당 명칭, 지역, 장비, 서사, 대사성 문구 번역.
- `Antigravity_Missing_Tips.tsv`: Antigravity 담당 도움말 누락 sid 검토.
- `Antigravity_Missing_Character_Customization.tsv`: XML에 원문명이 없는 커스터마이징 파츠 확인 후보.
- `Blocked_Missing_Source.tsv`: 원문 확인 전 번역하면 안 되는 항목.
- `Translated_Output_Template.tsv`: 완료 번역을 병합용으로 넘길 때 사용할 공통 형식.

## 작업 규칙

- `language_table`, `sid`, `zh`는 수정하지 않는다.
- 번역문은 `ko_new`에만 입력한다.
- `title_ko_new`, `describe_ko_new`는 해당 sid가 missing인 경우에만 입력한다.
- 원문이 없는 항목은 `zh_new`와 `ko_new`를 함께 채운다.
- 확신이 없는 항목은 번역하지 말고 `translator_note`에 사유를 적는다.
- 태그, 변수, 숫자, 배율, 퍼센트는 보존한다.
- 같은 숫자 sid라도 `t_language.xml`과 `t_tasklanguage.xml`은 다른 항목일 수 있으므로 반드시 `language_table + sid` 기준으로 처리한다.

## 병합 규칙

- 완료 TSV를 받은 뒤 Codex가 XML 병합과 검증을 담당한다.
- 병합 시 `ko` 속성만 수정한다.
- `zh`, `tw`, `en`, `sid` 등 원본 속성은 수정하지 않는다.
- `Blocked_Missing_Source.tsv` 항목은 원문 확인 후 별도 언어 행 추가 여부를 결정한다.

## 담당 기준

- Codex: UI, 설정, 도움말, 스탯, 상태, 수치, 조건, 규칙, 검증.
- Antigravity: 이름, 지명, 인명, 세력명, 혈맥명, 장비명, 아이템명, 서적명, 스킬명, 천부명, 지역 설명, 대사, 퀘스트, 내러티브.
"""


def token_list(text: str) -> list[str]:
    tokens: list[str] = []
    tokens.extend(TAG_RE.findall(text or ""))
    tokens.extend(VARIABLE_RE.findall(text or ""))
    tokens.extend(NUMBER_RE.findall(text or ""))
    return tokens


def missing_tokens(source: str, target: str) -> list[str]:
    target_counter = Counter(token_list(target))
    missing: list[str] = []
    for token, count in Counter(token_list(source)).items():
        if target_counter[token] < count:
            missing.extend([token] * (count - target_counter[token]))
    return missing


def validate_translation_rows(rows: list[dict[str, str]], base: Path = WORKING_XML) -> list[dict[str, str]]:
    entries_by_key = load_language_entries_by_key(base)
    issues: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    required = {"language_table", "sid", "zh", "ko_new"}
    if rows:
        missing_headers = sorted(required - set(rows[0].keys()))
        for header in missing_headers:
            issues.append(
                {
                    "severity": "error",
                    "language_table": "",
                    "sid": "",
                    "issue": "missing_header",
                    "detail": header,
                }
            )
        if missing_headers:
            return issues

    for index, row in enumerate(rows, start=2):
        language_table = row.get("language_table", "").strip()
        sid = row.get("sid", "").strip()
        zh = row.get("zh", "")
        ko_new = row.get("ko_new", "")
        key = (language_table, sid)

        if not language_table or not sid:
            issues.append(
                {
                    "severity": "error",
                    "language_table": language_table,
                    "sid": sid,
                    "issue": "missing_key",
                    "detail": f"line {index}",
                }
            )
            continue

        if key in seen:
            issues.append(
                {
                    "severity": "error",
                    "language_table": language_table,
                    "sid": sid,
                    "issue": "duplicate_key",
                    "detail": f"line {index}",
                }
            )
        seen.add(key)

        entry = entries_by_key.get(key)
        if not entry:
            issues.append(
                {
                    "severity": "error",
                    "language_table": language_table,
                    "sid": sid,
                    "issue": "unknown_language_key",
                    "detail": f"line {index}",
                }
            )
            continue

        if entry.zh != zh:
            issues.append(
                {
                    "severity": "error",
                    "language_table": language_table,
                    "sid": sid,
                    "issue": "zh_mismatch",
                    "detail": f'expected="{entry.zh}" actual="{zh}"',
                }
            )

        if not ko_new.strip():
            issues.append(
                {
                    "severity": "warning",
                    "language_table": language_table,
                    "sid": sid,
                    "issue": "empty_translation",
                    "detail": f"line {index}",
                }
            )
            continue

        lost = missing_tokens(entry.zh, ko_new)
        if lost:
            issues.append(
                {
                    "severity": "error",
                    "language_table": language_table,
                    "sid": sid,
                    "issue": "missing_source_token",
                    "detail": " ".join(lost),
                }
            )

    return issues


def validate_translation_file(input_path: Path, report_path: Path = REVIEW / "Validation_Report.tsv") -> None:
    rows = read_tsv(input_path)
    issues = validate_translation_rows(rows)
    write_tsv(report_path, issues, ["severity", "language_table", "sid", "issue", "detail"])
    errors = sum(1 for row in issues if row["severity"] == "error")
    warnings = sum(1 for row in issues if row["severity"] == "warning")
    print("Translation file validated")
    print(f"input: {input_path}")
    print(f"rows: {len(rows)}")
    print(f"errors: {errors}")
    print(f"warnings: {warnings}")
    print(f"report: {report_path}")


def apply_translation_file(input_path: Path, base: Path = WORKING_XML) -> None:
    rows = [row for row in read_tsv(input_path) if row.get("ko_new", "").strip()]
    issues = validate_translation_rows(rows, base=base)
    blocking = [row for row in issues if row["severity"] == "error"]
    write_tsv(REVIEW / "Validation_Report.tsv", issues, ["severity", "language_table", "sid", "issue", "detail"])
    if blocking:
        print("Apply aborted because validation errors exist.")
        print(f"errors: {len(blocking)}")
        print(f"report: {REVIEW / 'Validation_Report.tsv'}")
        return

    by_table: dict[str, dict[str, str]] = defaultdict(dict)
    for row in rows:
        by_table[row["language_table"].strip()][row["sid"].strip()] = row["ko_new"]

    applied_rows: list[dict[str, str]] = []
    for table, translations in by_table.items():
        if table not in LANGUAGE_FILES:
            continue
        path = base / table
        tree = ET.parse(path)
        root = tree.getroot()
        applied = 0
        for sample in root.findall("sample"):
            sid = sample.get("sid", "")
            if sid not in translations:
                continue
            sample.set("ko", translations[sid])
            applied += 1
        tree.write(path, encoding="utf-8", xml_declaration=True)
        applied_rows.append({"language_table": table, "applied_count": str(applied)})

    write_tsv(REVIEW / "Apply_Report.tsv", applied_rows, ["language_table", "applied_count"])
    print("Translations applied")
    print(f"input: {input_path}")
    print(f"rows with ko_new: {len(rows)}")
    print(f"report: {REVIEW / 'Apply_Report.tsv'}")


def build_missing_tips_context(
    base: Path, entries: dict[str, list[LangEntry]], missing_action_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    missing_tip_ids = {
        row["source_ids"]
        for row in missing_action_rows
        if row["source_file"] == "t_tips.xml" and row["recommended_action"] == "inspect_context_before_add"
    }
    if not missing_tip_ids:
        return []

    root = parse_xml(base / "t_tips.xml")
    rows: list[dict[str, str]] = []
    for sample in root.findall("sample"):
        tip_id = sample.get("id", "")
        if tip_id not in missing_tip_ids:
            continue

        title_sid = sample.get("title", "")
        describe_sid = sample.get("describe", "")
        title_status = sid_status(entries, title_sid)
        describe_status = sid_status(entries, describe_sid)
        title_zh = first_entry_zh(entries, title_sid)
        describe_zh = first_entry_zh(entries, describe_sid)

        if title_status == "missing" and describe_status == "missing":
            action = "collect_tip_text_before_add"
            note = "Both title and describe are missing from language tables."
        elif title_status == "missing":
            action = "infer_title_or_collect"
            note = "Title sid is missing. Existing describe text may help infer title."
        elif describe_status == "missing":
            action = "infer_describe_or_collect"
            note = "Describe sid is missing. Existing title text may help infer describe."
        else:
            action = "review_data_id_or_script_rule"
            note = "No language sid is missing after latest index; verify field meaning."

        owner = owner_for_missing_tip(
            title_zh=title_zh,
            describe_zh=describe_zh,
            title_status=title_status,
            describe_status=describe_status,
            action=action,
            tip_id=tip_id,
        )

        rows.append(
            {
                "tip_id": tip_id,
                "tips_type": sample.get("tipsType", ""),
                "title_sid": title_sid,
                "title_status": title_status,
                "title_zh": title_zh,
                "describe_sid": describe_sid,
                "describe_status": describe_status,
                "describe_zh": describe_zh,
                "effect": sample.get("effect", ""),
                "recommended_action": action,
                "owner": owner,
                "note": note,
            }
        )

    return sorted(rows, key=lambda row: int(row["tip_id"]))


def owner_for_missing_tip(
    title_zh: str, describe_zh: str, title_status: str, describe_status: str, action: str, tip_id: str
) -> str:
    combined = title_zh + "\n" + describe_zh

    # Rows where both sides are missing need source confirmation before any AI
    # can translate safely. Keep them assigned to Antigravity because most of
    # these are naming/lore-facing records after source text is collected.
    if action == "collect_tip_text_before_add":
        return "Antigravity"

    literary_markers = [
        "宗族",
        "势力",
        "君主",
        "族人",
        "姓氏",
        "王",
        "郡",
        "城",
        "秦",
        "楚",
        "齐",
        "燕",
        "赵",
        "魏",
        "韩",
        "劝降",
    ]
    if any(marker in combined for marker in literary_markers):
        return "Antigravity"

    # Numeric, equipment durability, controls, and rule-like tooltip text stay
    # with Codex.
    rule_markers = [
        "{ref=",
        "属性",
        "耐久",
        "技艺",
        "等级",
        "%",
        "上限",
        "加成",
        "概率",
    ]
    if any(marker in combined for marker in rule_markers):
        return "Codex"

    return "Codex"


def main() -> None:
    parser = argparse.ArgumentParser(description="HXSS XML localization helper")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("index", help="generate language/context reports")
    subparsers.add_parser("queue", help="generate translator-facing queue files")
    validate_parser = subparsers.add_parser("validate-translations", help="validate completed translation TSV")
    validate_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="completed TSV with language_table, sid, zh, ko_new columns",
    )
    apply_parser = subparsers.add_parser("apply", help="validate and apply completed translation TSV to WorkingXml")
    apply_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="completed TSV with language_table, sid, zh, ko_new columns",
    )

    args = parser.parse_args()
    if args.command == "index":
        build_index()
    elif args.command == "queue":
        build_translation_queue()
    elif args.command == "validate-translations":
        validate_translation_file(args.input)
    elif args.command == "apply":
        apply_translation_file(args.input)


if __name__ == "__main__":
    main()
