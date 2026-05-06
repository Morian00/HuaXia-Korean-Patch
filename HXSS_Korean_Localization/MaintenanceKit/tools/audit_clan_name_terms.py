import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FULL = ROOT / "MaintenanceKit" / "input" / "Full_Translation.tsv"
OUT = ROOT / "01_XML_Localization" / "XmlWork" / "Review" / "Clan_Name_Term_Audit_20260505.tsv"
SUMMARY = ROOT / "01_XML_Localization" / "XmlWork" / "Review" / "Clan_Name_Term_Audit_Summary_20260505.tsv"

ZH_TERMS = ["氏族", "氏名", "氏：", "氏", "宗族"]
KO_TERMS = ["세가", "씨족", "씨명", "성명", "성 명", "씨 명", "당신의 세가"]


def main() -> None:
    rows = []
    summary = {term: 0 for term in ZH_TERMS + KO_TERMS}

    with FULL.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            zh = row.get("zh", "")
            ko = row.get("ko_new", "")
            zh_hits = [term for term in ZH_TERMS if term in zh]
            ko_hits = [term for term in KO_TERMS if term in ko]
            if not zh_hits and not ko_hits:
                continue
            for term in zh_hits + ko_hits:
                summary[term] += 1
            rows.append([
                row.get("language_table", ""),
                row.get("sid", ""),
                "|".join(zh_hits),
                "|".join(ko_hits),
                zh,
                ko,
                row.get("notes", ""),
            ])

    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["language_table", "sid", "zh_hits", "ko_hits", "zh", "ko_new", "notes"])
        writer.writerows(rows)

    with SUMMARY.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["term", "count"])
        for term, count in summary.items():
            if count:
                writer.writerow([term, count])

    print(f"rows={len(rows)} report={OUT} summary={SUMMARY}")


if __name__ == "__main__":
    main()
