import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FULL = ROOT / "MaintenanceKit" / "input" / "Full_Translation.tsv"
REVIEW = ROOT / "01_XML_Localization" / "XmlWork" / "Review"
AUDIT = REVIEW / "Clan_Name_Term_Audit_20260505.tsv"
SUMMARY = REVIEW / "Clan_Name_Term_Audit_Summary_20260505.tsv"
FIXES = REVIEW / "Clan_Name_Term_Fixes_20260505.tsv"

SCAN_ZH_TERMS = ["世家", "氏族", "宗族", "氏名", "原氏名", "氏", "名"]
SCAN_KO_TERMS = ["세가", "씨족", "씨명", "원씨명", "성명", "성 명", "씨 명", "혈족", "가문", "성씨", "이름"]


def replace_term(text: str, old: str, new: str) -> str:
    return text.replace(old, new)


def normalize_translation(row: dict[str, str]) -> tuple[str, list[str]]:
    zh = row.get("zh", "")
    ko = row.get("ko_new", "")
    new = ko
    reasons: list[str] = []

    # 世家 is an actual game term and remains 세가.
    if "氏族" in zh:
        before = new
        for old in ["씨족", "세가", "씨족명", "세가명"]:
            new = replace_term(new, old, "혈족")
        if before != new:
            reasons.append("氏族=>혈족")

    if "宗族" in zh:
        before = new
        for old in ["종족", "씨족", "세가", "혈족"]:
            new = replace_term(new, old, "가문")
        if before != new:
            reasons.append("宗族=>가문")

    if "氏名" in zh:
        before = new
        new = replace_term(new, "원씨명", "원래 성명")
        new = replace_term(new, "씨명", "성명")
        new = replace_term(new, "씨 명", "성명")
        if before != new:
            reasons.append("氏名=>성명")

    stripped = zh.strip()
    if stripped == "氏":
        before = new
        if new.strip() not in {"성씨"}:
            new = "성씨"
        if before != new:
            reasons.append("氏=>성씨")

    if stripped == "名":
        before = new
        if new.strip() not in {"이름"}:
            new = "이름"
        if before != new:
            reasons.append("名=>이름")

    return new, reasons


def main() -> None:
    with FULL.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        rows = list(reader)

    if not fields:
        raise RuntimeError("Full_Translation.tsv header not found")

    audit_rows = []
    summary: dict[str, int] = {term: 0 for term in SCAN_ZH_TERMS + SCAN_KO_TERMS}
    fixes = []

    for row in rows:
        zh = row.get("zh", "")
        ko = row.get("ko_new", "")
        zh_hits = [term for term in SCAN_ZH_TERMS if term in zh]
        ko_hits = [term for term in SCAN_KO_TERMS if term in ko]
        for term in zh_hits + ko_hits:
            summary[term] = summary.get(term, 0) + 1
        if zh_hits or ko_hits:
            audit_rows.append([
                row.get("language_table", ""),
                row.get("sid", ""),
                "|".join(zh_hits),
                "|".join(ko_hits),
                zh,
                ko,
                row.get("notes", ""),
            ])

        new_ko, reasons = normalize_translation(row)
        if reasons and new_ko != ko:
            row["ko_new"] = new_ko
            fixes.append([
                row.get("language_table", ""),
                row.get("sid", ""),
                "|".join(reasons),
                zh,
                ko,
                new_ko,
            ])

    with FULL.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    with AUDIT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["language_table", "sid", "zh_hits", "ko_hits", "zh", "ko_new", "notes"])
        writer.writerows(audit_rows)

    with SUMMARY.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["term", "count"])
        for term, count in summary.items():
            if count:
                writer.writerow([term, count])

    with FIXES.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["language_table", "sid", "reason", "zh", "old_ko", "new_ko"])
        writer.writerows(fixes)

    print(f"audit_rows={len(audit_rows)} fixes={len(fixes)}")
    print(f"audit={AUDIT}")
    print(f"summary={SUMMARY}")
    print(f"fixes={FIXES}")


if __name__ == "__main__":
    main()
