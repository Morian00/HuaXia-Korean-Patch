from __future__ import annotations

import argparse
import csv
import shutil
from datetime import datetime
from pathlib import Path


FIELDS = ["language_table", "sid", "zh", "ko_new", "owner", "notes"]


def kit_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def escape_tsv_value(value: str) -> str:
    return (value or "").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n").replace("\t", "\\t")


def escape_tsv_row(row: dict[str, str], fields: list[str]) -> dict[str, str]:
    return {field: escape_tsv_value(row.get(field, "")) for field in fields}


def write_tsv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(escape_tsv_row(row, fields) for row in rows)


def sid_sort_key(row: dict[str, str]) -> tuple[str, int, int | str]:
    table = row.get("language_table", "")
    sid = row.get("sid", "")
    return (table, 0, int(sid)) if sid.isdigit() else (table, 1, sid)


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply reviewed Needs_Translation.tsv rows to Full_Translation.tsv.")
    parser.add_argument("--full", type=Path, default=kit_root() / "input" / "Full_Translation.tsv")
    parser.add_argument("--review", type=Path, default=kit_root() / "output" / "Needs_Translation.tsv")
    parser.add_argument("--log", type=Path, default=kit_root() / "output" / "Apply_Log.tsv")
    parser.add_argument("--owner", default="UpdateMaintenance")
    parser.add_argument("--notes", default="applied_from_update_report")
    args = parser.parse_args()

    if not args.full.exists():
        raise FileNotFoundError(args.full)
    if not args.review.exists():
        raise FileNotFoundError(args.review)

    full_rows = load_tsv(args.full)
    full_by_key = {(row["language_table"], row["sid"]): row for row in full_rows}
    review_rows = load_tsv(args.review)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = args.full.with_name(f"{args.full.stem}.before_apply_{stamp}{args.full.suffix}")
    shutil.copy2(args.full, backup)

    logs: list[dict[str, str]] = []
    applied = 0
    skipped = 0

    for row in review_rows:
        ko_new = row.get("ko_new", "").strip()
        if not ko_new:
            skipped += 1
            continue

        key = (row["language_table"], row["sid"])
        if key in full_by_key:
            target = full_by_key[key]
            old_zh = target.get("zh", "")
            old_ko = target.get("ko_new", "")
            target["zh"] = row.get("zh", target.get("zh", ""))
            target["ko_new"] = ko_new
            target["owner"] = merge_note(target.get("owner", ""), args.owner)
            target["notes"] = merge_note(target.get("notes", ""), args.notes)
            status = "updated"
        else:
            target = {
                "language_table": row["language_table"],
                "sid": row["sid"],
                "zh": row.get("zh", ""),
                "ko_new": ko_new,
                "owner": args.owner,
                "notes": args.notes,
            }
            full_rows.append(target)
            full_by_key[key] = target
            old_zh = ""
            old_ko = ""
            status = "added"

        logs.append(
            {
                "status": status,
                "language_table": row["language_table"],
                "sid": row["sid"],
                "old_zh": old_zh,
                "new_zh": target.get("zh", ""),
                "old_ko": old_ko,
                "new_ko": target.get("ko_new", ""),
            }
        )
        applied += 1

    full_rows.sort(key=sid_sort_key)
    write_tsv(args.full, [{field: row.get(field, "") for field in FIELDS} for row in full_rows], FIELDS)
    write_tsv(args.log, logs, ["status", "language_table", "sid", "old_zh", "new_zh", "old_ko", "new_ko"])

    print(f"backup={backup}")
    print(f"applied={applied} skipped_empty_ko_new={skipped}")
    return 0


def merge_note(existing: str, addition: str) -> str:
    parts = [part for part in existing.split("; ") if part]
    if addition and addition not in parts:
        parts.append(addition)
    return "; ".join(parts)


if __name__ == "__main__":
    raise SystemExit(main())
