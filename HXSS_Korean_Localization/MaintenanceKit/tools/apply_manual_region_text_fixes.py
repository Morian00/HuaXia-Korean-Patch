import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FULL = ROOT / "MaintenanceKit" / "input" / "Full_Translation.tsv"
REPORT = ROOT / "01_XML_Localization" / "XmlWork" / "Review" / "Manual_Region_Text_Fixes_20260505.tsv"
BEFORE = ROOT / "01_XML_Localization" / "XmlWork" / "Review" / "Archive_Legacy_Audits_20260504_1800" / "Full_Translation.before_modern_tone_final_cleanup.tsv"

UPDATES = {
    "831241": "주실의 터전, 하롱의 형승\\n농목이 함께 일고 관산이 굳다",
    "831242": "두 산이 맞선 표리의 산하\\n웅장한 변새에 화이가 섞이다",
    "831243": "하삭의 땅, 요순의 근원\\n인심이 순박하고 곡식이 들판을 채우다",
    "831244": "남으론 발해, 북으론 연산\\n바람 차고 물 시린데 기마가 누비다",
    "831245": "화하의 근원, 중원 깊은 터전\\n하락이 만나 천리옥야를 이루다",
    "831246": "하제가 엇갈리고 물길이 모이니\\n뽕과 삼이 지천에 예의가 번성하다",
    "831247": "예악이 찬란하고 어염이 풍요로우니\\n시장이 줄지어 사해를 아우르다",
    "831248": "호탕한 강줄기에 운몽이 아득하고\\n남으로 백월을 잇는 풍요의 고장",
    "831249": "아득한 큰 못에 강회가 가로지르고\\n빛나는 문장 아래 오구가 번뜩이다",
}


def main() -> None:
    before_ko = {}
    if BEFORE.exists():
        with BEFORE.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                sid = row.get("sid", "")
                if sid in UPDATES:
                    before_ko[sid] = row.get("ko_new", "")

    with FULL.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames
        rows = list(reader)

    if not fields:
        raise RuntimeError("Full_Translation.tsv header not found")

    changed = []
    existing = set()
    for row in rows:
        sid = row.get("sid", "")
        if sid not in UPDATES:
            continue
        existing.add(sid)
        old = row.get("ko_new", "")
        new = UPDATES[sid]
        if old != new:
            row["ko_new"] = new
        changed.append([row.get("language_table", ""), sid, row.get("zh", ""), before_ko.get(sid, old), new])

    missing = sorted(set(UPDATES) - existing)
    if missing:
        raise RuntimeError(f"missing sid(s): {missing}")

    with FULL.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    with REPORT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["language_table", "sid", "zh", "old_ko", "new_ko"])
        writer.writerows(changed)

    print(f"changed={len(changed)} report={REPORT}")


if __name__ == "__main__":
    main()
