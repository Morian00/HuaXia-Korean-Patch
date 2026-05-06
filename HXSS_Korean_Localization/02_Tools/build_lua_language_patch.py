from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET


LANG_ATTRS = [
    "zh",
    "tw",
    "en",
    "ru",
    "de",
    "fr",
    "ko",
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
]

TABLES = {
    "t_language.xml": ("t_language", "t_language.lua"),
    "t_tasklanguage.xml": ("t_taskLanguage", "t_taskLanguage.lua"),
}


def normalize_runtime_text(value: str) -> str:
    for _ in range(3):
        unescaped = html.unescape(value)
        if unescaped == value:
            break
        value = unescaped
    value = (
        value.replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
    )
    return re.sub(r"<([^<>]*?)\s+>", r"<\1>", value)


def lua_quote(value: str) -> str:
    value = normalize_runtime_text(value)
    escaped = (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace('"', '\\"')
    )
    return f'"{escaped}"'


def lua_scalar(value: str, force_string: bool = False) -> str:
    if not force_string:
        try:
            if value.strip() and str(int(value)) == value.strip():
                return str(int(value))
        except ValueError:
            pass
    return lua_quote(value)


def write_lua_source(xml_path: Path, table_name: str, out_path: Path) -> tuple[int, int]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    rows = []
    ko_nonempty = 0

    for elem in root:
        sid = elem.get("sid")
        if not sid:
            continue
        fields = [f"sid = {lua_scalar(sid)}"]
        for attr in LANG_ATTRS:
            value = elem.get(attr)
            if value is None:
                continue
            if attr == "ko" and value:
                ko_nonempty += 1
            fields.append(f"{attr} = {lua_quote(value)}")
        if table_name == "t_taskLanguage":
            fields.extend(
                [
                    "VoiceGroupZH = 0",
                    "VoiceGroupTW = 0",
                    "VoiceGroupEN = 0",
                ]
            )
        rows.append((sid, fields))

    with out_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(f"{table_name} = {{}}\n")
        f.write(f"{table_name}.config = {{\n")
        for sid, fields in rows:
            f.write(f"  [{lua_scalar(sid)}] = {{ {', '.join(fields)} }},\n")
        f.write("}\n")
        f.write(f"function {table_name}.getConfigById(id)\n")
        f.write(f"  if {table_name}.config[id] == nil then\n")
        f.write("    return nil\n")
        f.write("  end\n")
        f.write(f"  return {table_name}.config[id]\n")
        f.write("end\n")
        f.write(f"function {table_name}.getAllConfig()\n")
        f.write(f"  return {table_name}.config\n")
        f.write("end\n")
        f.write(f"return {table_name}\n")

    return len(rows), ko_nonempty


def compile_lua_sources(release_dir: Path, luac_path: str) -> Path:
    compiled_dir = release_dir / "CompiledLua"
    compiled_dir.mkdir(parents=True, exist_ok=True)
    for _, (_, lua_name) in TABLES.items():
        source_lua = release_dir / "SourceLua" / lua_name
        compiled_lua = compiled_dir / lua_name
        subprocess.run(
            [luac_path, "-o", str(compiled_lua), str(source_lua)],
            check=True,
        )
    return compiled_dir


def encrypt_lua_sources(release_dir: Path, crypto_script: Path, input_dir: Path) -> None:
    work_encrypt = release_dir / "_encrypt_work"
    work_encrypt.mkdir(parents=True, exist_ok=True)
    shutil.copy2(crypto_script, work_encrypt / "XmlConfigCrypto.ps1")

    for _, (_, lua_name) in TABLES.items():
        source_lua = input_dir / lua_name
        # The existing crypto script only processes .xml files. Use a temporary
        # .xml name, then rename the encrypted output back to .lua.
        shutil.copy2(source_lua, work_encrypt / lua_name.replace(".lua", ".xml"))

    subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            ".\\XmlConfigCrypto.ps1",
            "-Mode",
            "Encrypt",
        ],
        cwd=work_encrypt,
        check=True,
    )

    encrypted_dir = release_dir / "EncryptedLua"
    encrypted_dir.mkdir(parents=True, exist_ok=True)
    for _, (_, lua_name) in TABLES.items():
        encrypted_xml = work_encrypt / "__encrypted" / lua_name.replace(".lua", ".xml")
        shutil.copy2(encrypted_xml, encrypted_dir / lua_name)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build encrypted Lua language config files from WorkingXml."
    )
    parser.add_argument(
        "--work-xml",
        default="HXSS_Korean_Localization/01_XML_Localization/XmlWork/WorkingXml",
    )
    parser.add_argument(
        "--release-root",
        default="HXSS_Korean_Localization/01_XML_Localization/XmlWork/Release",
    )
    parser.add_argument(
        "--crypto-script",
        default="hxss_Data/StreamingAssets/XmlConfig_Decrypted/XmlConfigCrypto.ps1",
    )
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Compile generated Lua source with luac before DES encryption.",
    )
    parser.add_argument(
        "--luac",
        default="luac",
        help="Path to luac executable when --compile is used.",
    )
    args = parser.parse_args()

    work_xml = Path(args.work_xml)
    release_root = Path(args.release_root)
    crypto_script = Path(args.crypto_script)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    release_kind = "BytecodePatch" if args.compile else "SourcePatch"
    release_dir = release_root / f"LuaConfig_KO_{release_kind}_{stamp}"
    source_dir = release_dir / "SourceLua"
    source_dir.mkdir(parents=True, exist_ok=True)

    report = []
    for xml_name, (table_name, lua_name) in TABLES.items():
        xml_path = work_xml / xml_name
        if not xml_path.exists():
            raise FileNotFoundError(xml_path)
        rows, ko_nonempty = write_lua_source(xml_path, table_name, source_dir / lua_name)
        report.append((lua_name, rows, ko_nonempty))

    input_dir = source_dir
    if args.compile:
        input_dir = compile_lua_sources(release_dir, args.luac)

    encrypt_lua_sources(release_dir, crypto_script, input_dir)

    report_path = release_dir / "Lua_Build_Report.tsv"
    with report_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("lua_file\trows\tko_nonempty\n")
        for row in report:
            f.write("\t".join(map(str, row)) + "\n")

    print(release_dir)
    for row in report:
        print("\t".join(map(str, row)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
