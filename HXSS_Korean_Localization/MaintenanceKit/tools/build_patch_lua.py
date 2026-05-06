from __future__ import annotations

import argparse
import csv
import html
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


TABLES = {
    "t_language.xml": ("t_language.lua", "t_language"),
    "t_tasklanguage.xml": ("t_taskLanguage.lua", "t_taskLanguage"),
}


ROW_RE = re.compile(r"^\s+\[(?P<sid>[^\]]+)\]\s*=\s*\{")


def kit_root() -> Path:
    return Path(__file__).resolve().parents[1]


def game_root() -> Path:
    return kit_root().parent.parent


def release_root() -> Path:
    return game_root() / "HXSS_Korean_Localization" / "01_XML_Localization" / "XmlWork" / "Release"


def latest_source_template() -> Path:
    candidates: list[Path] = []
    for path in release_root().glob("LuaConfig_KO_*/SourceLua"):
        if (path / "t_language.lua").exists() and (path / "t_taskLanguage.lua").exists():
            candidates.append(path)
    if not candidates:
        raise FileNotFoundError("No Lua SourceLua template found under XmlWork/Release.")
    return max(candidates, key=lambda p: (p / "t_language.lua").stat().st_mtime)


def normalize_runtime_text(value: str) -> str:
    for _ in range(3):
        unescaped = html.unescape(value)
        if unescaped == value:
            break
        value = unescaped
    value = value.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"<([^<>]*?)\s+>", r"<\1>", value)


def lua_string(value: str) -> str:
    value = normalize_runtime_text(value)
    escaped = (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace('"', '\\"')
    )
    return f'"{escaped}"'


def lua_scalar(value: str, force_string: bool = False) -> str:
    stripped = value.strip()
    if not force_string and re.fullmatch(r"-?\d+(?:\.\d+)?", stripped):
        return stripped
    return lua_string(value)


def load_translations(full_path: Path) -> dict[str, dict[str, str]]:
    by_table = {table: {} for table in TABLES}
    with full_path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            table = row.get("language_table", "")
            sid = row.get("sid", "").strip()
            ko = row.get("ko_new", "")
            if table in by_table and sid and ko != "":
                by_table[table][sid] = ko
    return by_table


def load_added_rows(path: Path) -> dict[str, dict[str, dict[str, str]]]:
    by_table = {table: {} for table in TABLES}
    if not path.exists():
        return by_table
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            table = row.get("language_table", "")
            sid = row.get("sid", "").strip()
            if table in by_table and sid:
                by_table[table][sid] = row
    return by_table


def replace_lua_field(line: str, field: str, value: str) -> tuple[str, bool]:
    marker = f"{field} = "
    start = line.find(marker)
    if start < 0:
        return line, False
    quote_start = line.find('"', start + len(marker))
    if quote_start < 0:
        return line, False

    i = quote_start + 1
    escaped = False
    while i < len(line):
        char = line[i]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            return line[:quote_start] + lua_string(value) + line[i + 1 :], True
        i += 1
    return line, False


def make_minimal_row(sid: str, zh: str, en: str, ko: str) -> str:
    fields = [
        f"sid = {lua_scalar(sid)}",
        f"zh = {lua_string(zh)}",
        'tw = ""',
        f"en = {lua_string(en)}",
        'ru = ""',
        'de = ""',
        'fr = ""',
        f"ko = {lua_string(ko)}",
        'ja = ""',
        'th = ""',
        'pl = ""',
        'tr = ""',
        'uk = ""',
        'it = ""',
        'cs = ""',
        'hu = ""',
        'nl = ""',
        'es = ""',
        'la = ""',
        'pt = ""',
        'br = ""',
        'sv = ""',
        'da = ""',
    ]
    return f"  [{lua_scalar(sid)}] = {{ {', '.join(fields)} }},"


def patch_source_file(
    source: Path,
    target: Path,
    translations: dict[str, str],
    full_rows: dict[str, dict[str, str]],
    added_rows: dict[str, dict[str, str]],
) -> tuple[int, int, int, int]:
    total_rows = 0
    changed = 0
    missing_field = 0
    seen: set[str] = set()
    source_sids: set[str] = set()
    out: list[str] = []

    with source.open("r", encoding="utf-8", newline="") as f:
        for line in f.read().splitlines():
            match = ROW_RE.match(line)
            if not match:
                out.append(line)
                continue
            total_rows += 1
            sid = match.group("sid").strip().strip('"')
            source_sids.add(sid)
            if sid in translations:
                new_line, ok = replace_lua_field(line, "ko", translations[sid])
                if not ok:
                    missing_field += 1
                    out.append(line)
                else:
                    seen.add(sid)
                    if new_line != line:
                        changed += 1
                    out.append(new_line)
            else:
                out.append(line)

    append_rows: list[str] = []
    for sid in sorted(set(full_rows) - source_sids, key=sid_sort_key):
        row = full_rows[sid]
        append_rows.append(make_minimal_row(sid, row.get("zh", ""), row.get("en", ""), row.get("ko_new", "")))
    for sid in sorted(set(added_rows) - source_sids - set(full_rows), key=sid_sort_key):
        row = added_rows[sid]
        fallback = row.get("ko_current", "") or row.get("zh", "") or row.get("en", "")
        append_rows.append(make_minimal_row(sid, row.get("zh", ""), row.get("en", ""), fallback))

    if append_rows:
        insert_index = None
        for index, line in enumerate(out):
            if line == "}":
                insert_index = index
                break
        if insert_index is None:
            raise RuntimeError(f"Cannot find config table closing brace in {source}")
        out[insert_index:insert_index] = append_rows

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    missing_sid = len(set(translations) - seen)
    return total_rows, changed, missing_sid + missing_field, len(append_rows)


def sid_sort_key(sid: str) -> tuple[int, float | str]:
    if re.fullmatch(r"-?\d+(?:\.\d+)?", sid):
        return (0, float(sid))
    return (1, sid)


def compile_lua(source_dir: Path, compiled_dir: Path, luac: Path) -> None:
    compiled_dir.mkdir(parents=True, exist_ok=True)
    for lua_name, _ in TABLES.values():
        subprocess.run(
            [str(luac), "-o", str(compiled_dir / lua_name), str(source_dir / lua_name)],
            check=True,
        )


def encrypt_lua(release_dir: Path, compiled_dir: Path, crypto: Path) -> Path:
    work = release_dir / "_encrypt_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    shutil.copy2(crypto, work / "XmlConfigCrypto.ps1")

    for lua_name, _ in TABLES.values():
        shutil.copy2(compiled_dir / lua_name, work / lua_name.replace(".lua", ".xml"))

    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", ".\\XmlConfigCrypto.ps1", "-Mode", "Encrypt"],
        cwd=work,
        check=True,
    )

    encrypted_dir = release_dir / "EncryptedLua"
    encrypted_dir.mkdir(parents=True, exist_ok=True)
    for lua_name, _ in TABLES.values():
        shutil.copy2(work / "__encrypted" / lua_name.replace(".lua", ".xml"), encrypted_dir / lua_name)
    return encrypted_dir


def install_patch_lua(encrypted_dir: Path, install_dir: Path, release_dir: Path) -> None:
    install_dir.mkdir(parents=True, exist_ok=True)
    backup_dir = release_dir / "InstalledBackup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for lua_name, _ in TABLES.values():
        current = install_dir / lua_name
        if current.exists():
            shutil.copy2(current, backup_dir / lua_name)
        shutil.copy2(encrypted_dir / lua_name, current)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HXSS Korean patch Lua files from Full_Translation.tsv.")
    parser.add_argument("--full", type=Path, default=kit_root() / "input" / "Full_Translation.tsv")
    parser.add_argument("--added-rows", type=Path, default=kit_root() / "output" / "Added_Rows.tsv")
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--luac", type=Path, default=kit_root() / "tools" / "luac54.exe")
    parser.add_argument("--crypto", type=Path, default=kit_root() / "tools" / "XmlConfigCrypto.ps1")
    parser.add_argument(
        "--install-dir",
        type=Path,
        default=game_root()
        / "BepInEx"
        / "plugins"
        / "HXSS.HuiWenFontReplacer"
        / "KoreanPatch"
        / "lua"
        / "game"
        / "config",
    )
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()

    if not args.full.exists():
        raise FileNotFoundError(args.full)
    if not args.luac.exists():
        raise FileNotFoundError(args.luac)
    if not args.crypto.exists():
        raise FileNotFoundError(args.crypto)

    template = args.template or latest_source_template()
    translations = load_translations(args.full)
    full_rows_by_table = {table: {} for table in TABLES}
    with args.full.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            table = row.get("language_table", "")
            sid = row.get("sid", "").strip()
            if table in full_rows_by_table and sid:
                full_rows_by_table[table][sid] = row
    added_rows = load_added_rows(args.added_rows)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = release_root() / f"LuaConfig_KO_PluginPatch_{stamp}"
    source_dir = out_dir / "SourceLua"
    compiled_dir = out_dir / "CompiledLua"

    report_rows: list[dict[str, str]] = []
    for table, (lua_name, _) in TABLES.items():
        rows, changed, missing, appended = patch_source_file(
            template / lua_name,
            source_dir / lua_name,
            translations[table],
            full_rows_by_table[table],
            added_rows[table],
        )
        report_rows.append(
            {
                "table": table,
                "lua": lua_name,
                "template_rows": str(rows),
                "ko_changed": str(changed),
                "translation_sids_not_in_template_or_missing_ko": str(missing),
                "appended_rows": str(appended),
            }
        )

    compile_lua(source_dir, compiled_dir, args.luac)
    encrypted_dir = encrypt_lua(out_dir, compiled_dir, args.crypto)
    if args.install:
        install_patch_lua(encrypted_dir, args.install_dir, out_dir)

    report = out_dir / "Build_Patch_Lua_Report.tsv"
    with report.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "table",
                "lua",
                "template_rows",
                "ko_changed",
                "translation_sids_not_in_template_or_missing_ko",
                "appended_rows",
            ],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(report_rows)

    print(f"template={template}")
    print(f"release_dir={out_dir}")
    print(f"installed={args.install_dir if args.install else ''}")
    for row in report_rows:
        print("\t".join(row.values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
