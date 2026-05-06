from __future__ import annotations

import argparse
import csv
import html
import re
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path


FIELD_RE = re.compile(r'; "([^"]+)" (.+)$')
FIELD_ONLY_RE = re.compile(r'\bSETFIELD\s+\S+\s+\S+\s+(\d+)\s+;\s+"([^"]+)"\s*$')
LOADK_RE = re.compile(r'\bLOADK\s+(\d+)\s+\S+\s+;\s+(.+)$')
LOADI_RE = re.compile(r'\bLOADI\s+(\d+)\s+(-?\d+)\b')
ROW_COMMIT_RE = re.compile(r"\b(?:SETI|SETTABLE)\b")
TAG_SPACE_RE = re.compile(r"<\s*([^<>]*?)\s*>")
WHITESPACE_RE = re.compile(r"\s+")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
REF_ONLY_RE = re.compile(r"(?:\{ref=\d+\})+")
PLACEHOLDER_QUESTION_RE = re.compile(r"^[\s?？!！,，.。…、;；:：()（）\[\]【】\-—_]+$")

TABLES = {
    "t_language.xml": ("t_language.lua", "t_language.xml"),
    "t_tasklanguage.xml": ("t_taskLanguage.lua", "t_taskLanguage.xml"),
}


def kit_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_game_root() -> Path:
    return kit_root().parent.parent


def decode_luac_value(raw: str) -> str:
    raw = raw.strip()
    if not raw.startswith('"'):
        return raw.split()[0]

    out = bytearray()
    i = 1
    while i < len(raw):
        ch = raw[i]
        if ch == '"':
            break
        if ch == "\\":
            j = i + 1
            digits: list[str] = []
            while j < len(raw) and len(digits) < 3 and raw[j].isdigit():
                digits.append(raw[j])
                j += 1
            if digits:
                out.append(int("".join(digits), 10) & 0xFF)
                i = j
                continue
            if j < len(raw):
                esc = raw[j]
                mapping = {"n": 10, "r": 13, "t": 9, "\\": 92, '"': 34}
                out.append(mapping.get(esc, ord(esc)))
                i = j + 1
                continue
        out.extend(ch.encode("utf-8"))
        i += 1
    return out.decode("utf-8", errors="replace")


def normalize_for_semantic_compare(value: str) -> str:
    value = html.unescape(value or "")
    value = value.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = TAG_SPACE_RE.sub(lambda m: "<" + WHITESPACE_RE.sub(" ", m.group(1).strip()) + ">", value)
    value = value.replace(" </", "</")
    return WHITESPACE_RE.sub("", value)


def parse_lua_rows(luac: Path, decrypted_path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    current: dict[str, str] = {}
    registers: dict[str, str] = {}

    proc = subprocess.Popen(
        [str(luac), "-l", "-l", str(decrypted_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        loadi = LOADI_RE.search(line)
        if loadi:
            registers[loadi.group(1)] = loadi.group(2)
            continue

        loadk = LOADK_RE.search(line)
        if loadk:
            registers[loadk.group(1)] = decode_luac_value(loadk.group(2))
            continue

        field_match = FIELD_RE.search(line)
        if field_match:
            field, value = field_match.group(1), field_match.group(2)
            if field in {"sid", "zh", "en", "ko"}:
                current[field] = decode_luac_value(value)
            continue

        field_only = FIELD_ONLY_RE.search(line)
        if field_only:
            register, field = field_only.group(1), field_only.group(2)
            if field in {"sid", "zh", "en", "ko"} and register in registers:
                current[field] = registers[register]
            continue

        if ROW_COMMIT_RE.search(line):
            sid = current.get("sid", "").strip()
            if sid:
                rows[sid] = dict(current)
            current = {}

    proc.wait()
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"luac failed: {decrypted_path} ({proc.returncode})")
    return rows


def decrypt_current_lua(game_root: Path, cache_dir: Path, crypto: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work = cache_dir / f"UpdateAudit_{stamp}"
    work.mkdir(parents=True, exist_ok=True)
    shutil.copy2(crypto, work / "XmlConfigCrypto.ps1")

    lua_dir = game_root / "hxss_Data" / "StreamingAssets" / "lua" / "game" / "config"
    for lua_name, temp_name in TABLES.values():
        src = lua_dir / lua_name
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copy2(src, work / temp_name)

    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", ".\\XmlConfigCrypto.ps1", "-Mode", "Decrypt"],
        cwd=work,
        check=True,
    )
    return work


def load_full(full_path: Path) -> dict[tuple[str, str], dict[str, str]]:
    rows: dict[tuple[str, str], dict[str, str]] = {}
    with full_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            rows[(row["language_table"], row["sid"])] = row
    return rows


def escape_tsv_value(value: str) -> str:
    return (value or "").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n").replace("\t", "\\t")


def escape_tsv_row(row: dict[str, str], fields: list[str]) -> dict[str, str]:
    return {field: escape_tsv_value(row.get(field, "")) for field in fields}


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(escape_tsv_row(row, fields) for row in rows)


def sid_sort_key(sid: str) -> tuple[int, int | str]:
    return (0, int(sid)) if sid.isdigit() else (1, sid)


def classify_added(row: dict[str, str]) -> str:
    zh = row.get("zh", "").strip()
    en = row.get("en", "").strip()
    ko = row.get("ko", "").strip()
    if not zh and not en and not ko:
        return "added_empty_row"
    if not zh and en and PLACEHOLDER_QUESTION_RE.fullmatch(en):
        return "added_placeholder_question_marks"
    if zh and REF_ONLY_RE.fullmatch(zh):
        return "added_ref_only"
    if zh and CJK_RE.search(zh):
        return "added_needs_translation"
    if zh:
        return "added_non_cjk_or_tag"
    if en:
        return "added_no_zh_has_en"
    return "added_other"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit current HXSS language lua update against Full_Translation.tsv.")
    parser.add_argument("--game-root", type=Path, default=default_game_root())
    parser.add_argument("--full", type=Path, default=kit_root() / "input" / "Full_Translation.tsv")
    parser.add_argument("--output", type=Path, default=kit_root() / "output")
    parser.add_argument("--cache", type=Path, default=kit_root() / "cache")
    parser.add_argument("--luac", type=Path, default=kit_root() / "tools" / "luac54.exe")
    parser.add_argument("--crypto", type=Path, default=kit_root() / "tools" / "XmlConfigCrypto.ps1")
    args = parser.parse_args()

    if not args.full.exists():
        raise FileNotFoundError(args.full)
    if not args.luac.exists():
        raise FileNotFoundError(args.luac)
    if not args.crypto.exists():
        raise FileNotFoundError(args.crypto)

    work = decrypt_current_lua(args.game_root, args.cache, args.crypto)
    full = load_full(args.full)

    added: list[dict[str, str]] = []
    changed: list[dict[str, str]] = []
    changed_text: list[dict[str, str]] = []
    changed_format: list[dict[str, str]] = []
    removed: list[dict[str, str]] = []
    action_items: list[dict[str, str]] = []
    summary: list[dict[str, str]] = []

    for table, (_, temp_name) in TABLES.items():
        current_rows = parse_lua_rows(args.luac, work / "__decrypted" / temp_name)
        full_sids = {sid for language_table, sid in full if language_table == table}
        current_sids = set(current_rows)

        for sid in sorted(current_sids - full_sids, key=sid_sort_key):
            row = current_rows[sid]
            report = {
                "language_table": table,
                "sid": sid,
                "zh": row.get("zh", ""),
                "en": row.get("en", ""),
                "ko_current": row.get("ko", ""),
            }
            added.append(report)
            action = classify_added(row)
            action_items.append(
                {
                    "action": action,
                    "language_table": table,
                    "sid": sid,
                    "zh": report["zh"],
                    "en": report["en"],
                    "current_ko": report["ko_current"],
                    "previous_ko": "",
                    "ko_new": "",
                    "note": "new sid in current game lua",
                }
            )

        for sid in sorted(current_sids & full_sids, key=sid_sort_key):
            key = (table, sid)
            old_zh = full[key].get("zh", "")
            new_zh = current_rows[sid].get("zh", "")
            if old_zh == new_zh:
                continue
            kind = (
                "format_only"
                if normalize_for_semantic_compare(old_zh) == normalize_for_semantic_compare(new_zh)
                else "text_changed"
            )
            report = {
                "language_table": table,
                "sid": sid,
                "change_kind": kind,
                "full_zh": old_zh,
                "current_zh": new_zh,
                "full_ko": full[key].get("ko_new", ""),
                "current_en": current_rows[sid].get("en", ""),
                "current_ko": current_rows[sid].get("ko", ""),
            }
            changed.append(report)
            if kind == "format_only":
                changed_format.append(report)
            else:
                changed_text.append(report)
                action_items.append(
                    {
                        "action": "changed_zh_needs_review",
                        "language_table": table,
                        "sid": sid,
                        "zh": new_zh,
                        "en": report["current_en"],
                        "current_ko": report["current_ko"],
                        "previous_ko": report["full_ko"],
                        "ko_new": "",
                        "note": "source zh changed; review previous Korean translation",
                    }
                )

        for sid in sorted(full_sids - current_sids, key=sid_sort_key):
            row = full[(table, sid)]
            removed.append(
                {
                    "language_table": table,
                    "sid": sid,
                    "full_zh": row.get("zh", ""),
                    "full_ko": row.get("ko_new", ""),
                }
            )
            action_items.append(
                {
                    "action": "removed_from_current_lua",
                    "language_table": table,
                    "sid": sid,
                    "zh": row.get("zh", ""),
                    "en": "",
                    "current_ko": "",
                    "previous_ko": row.get("ko_new", ""),
                    "ko_new": "",
                    "note": "sid not found in current game lua; do not delete automatically",
                }
            )

        summary.append(
            {
                "language_table": table,
                "current_rows": str(len(current_rows)),
                "full_rows": str(len(full_sids)),
                "added": str(len(current_sids - full_sids)),
                "changed_zh": str(sum(1 for r in changed if r["language_table"] == table)),
                "changed_text": str(sum(1 for r in changed_text if r["language_table"] == table)),
                "changed_format_only": str(sum(1 for r in changed_format if r["language_table"] == table)),
                "removed": str(len(full_sids - current_sids)),
            }
        )

    write_tsv(args.output / "Added_Rows.tsv", added, ["language_table", "sid", "zh", "en", "ko_current"])
    write_tsv(
        args.output / "Changed_Rows.tsv",
        changed,
        ["language_table", "sid", "change_kind", "full_zh", "current_zh", "full_ko", "current_en", "current_ko"],
    )
    write_tsv(
        args.output / "Changed_TextOnly.tsv",
        changed_text,
        ["language_table", "sid", "change_kind", "full_zh", "current_zh", "full_ko", "current_en", "current_ko"],
    )
    write_tsv(
        args.output / "Changed_FormatOnly.tsv",
        changed_format,
        ["language_table", "sid", "change_kind", "full_zh", "current_zh", "full_ko", "current_en", "current_ko"],
    )
    write_tsv(args.output / "Removed_Rows.tsv", removed, ["language_table", "sid", "full_zh", "full_ko"])
    write_tsv(
        args.output / "Needs_Translation.tsv",
        [r for r in action_items if r["action"] in {"added_needs_translation", "added_no_zh_has_en", "changed_zh_needs_review"}],
        ["action", "language_table", "sid", "zh", "en", "current_ko", "previous_ko", "ko_new", "note"],
    )
    write_tsv(
        args.output / "Action_Items.tsv",
        action_items,
        ["action", "language_table", "sid", "zh", "en", "current_ko", "previous_ko", "ko_new", "note"],
    )
    write_tsv(
        args.output / "Update_Summary.tsv",
        summary,
        ["language_table", "current_rows", "full_rows", "added", "changed_zh", "changed_text", "changed_format_only", "removed"],
    )

    counts = Counter(item["action"] for item in action_items)
    action_summary = [{"action": key, "count": str(value)} for key, value in sorted(counts.items())]
    write_tsv(args.output / "Action_Summary.tsv", action_summary, ["action", "count"])

    print(f"cache={work}")
    for row in summary:
        print("\t".join(row.values()))
    print(f"action_items={len(action_items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
