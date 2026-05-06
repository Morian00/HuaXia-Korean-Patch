# Huaxia Korean Localization Task

## 현재 목표

- 한국어 패치 v0.1.3 GitHub Releases 배포 완료 상태 유지.
- 설치기 없는 수동 설치 ZIP 기준 유지.
- 원본 게임 Lua 직접 수정 없이 BepInEx 플러그인에서 패치 Lua 우선 로드.
- 게임 업데이트 후 추가/변경 문자열을 `MaintenanceKit` 리포트로 추적.
- 사용자 제보와 게임 업데이트에 따른 후속 패치 대응.

## 현재 기준 파일

- 번역 원본: `HXSS_Korean_Localization/MaintenanceKit/input/Full_Translation.tsv`
- 패치 Lua 설치 위치:
  - `BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_language.lua`
  - `BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_taskLanguage.lua`
- 플러그인 DLL:
  - `BepInEx/plugins/HXSS.HuiWenFontReplacer/HXSS.HuiWenFontReplacer.dll`
- 하드코드 UI 보정:
  - `BepInEx/plugins/HXSS.HuiWenFontReplacer/hardcoded_text.tsv`
- 배포 config:
  - `BepInEx/config/hxss.huiwen-font-replacer.cfg`
- 유지보수 키트:
  - `HXSS_Korean_Localization/MaintenanceKit/`
- 배포 패키지:
  - `HXSS_Korean_Localization/ReleasePackages/HXSS_KoreanPatch_v0.1.3_20260507_035157.zip`

## 현재 적용 구조

1. 게임 원본 Lua는 직접 수정하지 않음.
2. `CXLuaMgr.CustomLuaFilePath` 후킹으로 언어 Lua 로드 시점에 패치 Lua 경로를 우선 반환.
3. TSV 런타임 오버라이드는 제거.
4. 폰트 대응은 TMP fallback 매핑을 기본값으로 사용.
5. 강제 폰트 치환은 `EnableFontOverride=false` 기본값으로 분리.
6. 하드코드 UI는 `hardcoded_text.tsv` 기반으로 선택적 스캔 적용.
7. `hardcoded_text.tsv` 변경 시 런타임 재로드 지원.
8. 미번역 중국어 수집은 한국어 시작 문구 감지 후에만 활성화.
9. 배포 기본값에서는 중국어 수집, Lua 로드 추적, 폰트 디버그 비활성화.

## 최근 완료

- Lua 패치 우선 로드 방식으로 플러그인 전환.
- TMP fallback 기반 폰트 대응 구조 적용.
- 하드코드 UI 보정 및 런타임 재로드 구조 적용.
- 선택적 중국어 수집, Lua 로드 추적, 폰트 디버그 옵션 분리.
- `build_patch_lua.py` / `build_patch_lua.bat` 추가.
- `update_audit.py` / `apply_report.py` 기반 업데이트 대응 흐름 구축.
- `package_release.py`를 GitHub Releases 수동 설치 ZIP 기준으로 수정.
- 설치기 프로토타입 작성 후 현 배포 기준에서 제외.
- 예전 설치기 산출물, 캐시, 과거 릴리스 산출물, 백업용 아카이브 정리.
- v0.1.3 수동 설치 ZIP 생성 완료.
  - `HXSS_KoreanPatch_v0.1.3_20260507_035157.zip`
  - SHA-256: `155695c3c6aac38c8dae4e0935121e3ededd04d399c34a5a131cd43b8370493f`
- GitHub 저장소 게시 및 v0.1.3 Release 업로드 완료.

## 최신 업데이트 감지 결과

기준 리포트 생성 시각: 2026-05-06 17:08.

출력 위치:

- `HXSS_Korean_Localization/MaintenanceKit/output/Update_Summary.tsv`
- `HXSS_Korean_Localization/MaintenanceKit/output/Action_Summary.tsv`
- `HXSS_Korean_Localization/MaintenanceKit/output/Needs_Translation.tsv`
- `HXSS_Korean_Localization/MaintenanceKit/output/Changed_TextOnly.tsv`
- `HXSS_Korean_Localization/MaintenanceKit/output/Added_Rows.tsv`

요약:

- `t_language.xml`
  - 현재 행: 31437
  - 기존 번역 행: 30944
  - 신규 행: 493
  - 실제 원문 변경: 0
  - 서식 변경: 3112
  - 삭제 행: 0
- `t_tasklanguage.xml`
  - 현재 행: 9416
  - 기존 번역 행: 9286
  - 신규 행: 130
  - 실제 원문 변경: 0
  - 서식 변경: 507
  - 삭제 행: 0

신규 행 분류:

- 빈 행: 398
- 비중문 또는 태그: 84
- 물음표 placeholder: 99
- 참조 전용: 42

현재 `Needs_Translation.tsv`와 `Changed_TextOnly.tsv`에는 즉시 번역이 필요한 행이 없음.

## 최신 패치 Lua 빌드

- 빌드/설치 시각: 2026-05-07 03:28.
- 설치 위치:
  - `BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_language.lua`
  - `BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_taskLanguage.lua`
- 기준 번역 파일:
  - `MaintenanceKit/input/Full_Translation.tsv`

## 최신 배포 패키지

- 버전: `v0.1.3`
- 패키지 형식: `HXSS_KoreanPatch_v0.1.3_YYYYMMDD_HHMMSS.zip`
- 최신 파일:
  - `HXSS_KoreanPatch_v0.1.3_20260507_035157.zip`
- 위치:
  - `HXSS_Korean_Localization/ReleasePackages/`
- 포함:
  - BepInEx IL2CPP 원본 기반 파일.
  - 한국어 패치 플러그인 DLL.
  - 한중 통합 폰트.
  - 패치 Lua 2종.
  - `hardcoded_text.tsv`.
  - 배포 기본 config.
  - `README_KO.md`, `CHANGELOG_KO.md`.
  - 유지보수 키트.
  - 공개 문서 및 플러그인 소스.
  - `manifest.tsv`.

배포 ZIP 제외 대상:

- 설치기 실행 파일.
- 원본 게임 실행 파일.
- 원본 게임 DLL.
- `hxss_Data/`.
- `collected_chinese.tsv`.
- `lua_loader_trace.tsv`.
- `font_debug.tsv`.
- 캐시, stage, `__pycache__`.

## 다음 작업

1. 사용자 제보 발생 시 이슈 정리.
2. 게임 업데이트 발생 시 `MaintenanceKit/update_audit.bat` 실행.
3. 신규 번역 필요 행이 생기면 `Needs_Translation.tsv` 검수 후 패치 Lua 재생성.
4. 필요 시 후속 버전 `v0.1.4` 배포.

## 작업 원칙

- `Full_Translation.tsv`를 단일 번역 원본으로 유지.
- 원본 Lua 파일 직접 수정 금지.
- 플러그인 TSV 오버라이드 방식 재도입 금지.
- 배포 기본값에서 `EnableChineseCollector=false` 유지.
- 배포 기본값에서 `EnableLuaLoadTrace=false` 유지.
- 배포 기본값에서 `EnableFontDebug=false` 유지.
- 유지보수자가 미번역 수집이 필요할 때만 수집 기능 활성화.
- 콘솔에서 깨진 한글/중국어를 복사해 저장 금지.
- 물음표 반복 또는 U+FFFD 대체 문자가 들어간 파일은 배포 전 반드시 검사.
- 태그, 변수, 참조 문자열 보존.
- 원문에 없는 한자 괄호 병기 추가 금지.
