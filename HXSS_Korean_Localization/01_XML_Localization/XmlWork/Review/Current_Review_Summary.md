# Current Review Summary

## 현재 상태

- 게임은 XML보다 Lua 언어 테이블을 우선 참조함.
- 현재 적용 방식은 BepInEx 플러그인의 패치 Lua 우선 로드 방식.
- 원본 게임 Lua 파일 직접 교체 없음.
- TSV 런타임 오버라이드 방식은 폐기됨.
- 실제 적용 파일:
  - `BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_language.lua`
  - `BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_taskLanguage.lua`
- 최신 생성 산출물:
  - `HXSS_Korean_Localization/01_XML_Localization/XmlWork/Release/LuaConfig_KO_PluginPatch_20260505_173734`

## 최신 수정

- 한글 패치 플러그인 정상 적용 확인.
- 플러그인 폴더에서 TSV 런타임 오버라이드 제거.
- 업데이트 대응용 `MaintenanceKit` 유지.
- 최신 번역 기준 파일:
  - `HXSS_Korean_Localization/MaintenanceKit/input/Full_Translation.tsv`
- 최신 Lua 생성 도구:
  - `HXSS_Korean_Localization/MaintenanceKit/build_patch_lua.bat`
  - `HXSS_Korean_Localization/MaintenanceKit/tools/build_patch_lua.py`
- 작업 폴더 정리 완료.
  - 과거 BepInEx 자동번역 워크플로는 `99_Cleanup_Archive`로 이동.
  - Review 폴더의 과거 감사 산출물은 보관 폴더로 이동.
  - 플러그인 폴더의 trace/log/backup 파일 제거.

## 유지보수 명령

업데이트 변경 확인:

```powershell
HXSS_Korean_Localization\MaintenanceKit\update_audit.bat
```

번역 반영 리포트 생성:

```powershell
HXSS_Korean_Localization\MaintenanceKit\apply_report.bat
```

패치 Lua 재생성:

```powershell
HXSS_Korean_Localization\MaintenanceKit\build_patch_lua.bat
```

## 다음 확인

1. 메인 메뉴, 설정, 커스터마이징 화면 한국어 출력 확인.
2. 공지 화면 태그가 문자로 노출되지 않는지 확인.
3. `{ref=...}`가 사용자 화면에 노출되는지 확인.
4. 잔여 한자와 하드코드 UI 후보 확인.
5. 배포 패키징 스크립트 작성.
