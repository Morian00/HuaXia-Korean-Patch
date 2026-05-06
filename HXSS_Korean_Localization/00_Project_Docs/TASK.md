# Huaxia Korean Localization Task

## 현재 목표

- 한국어 패치 1차 배포 안정화.
- 게임 업데이트 대응 절차 정리.
- 원본 Lua 직접 수정 대신 BepInEx 플러그인에서 패치 Lua를 우선 로드.
- 업데이트 후 추가/변경 문자열을 자동 리포트로 추적.

## 현재 기준 파일

- 번역 원본: `HXSS_Korean_Localization/MaintenanceKit/input/Full_Translation.tsv`
- 플러그인 적용 Lua:
  - `BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_language.lua`
  - `BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_taskLanguage.lua`
- 유지보수 키트: `HXSS_Korean_Localization/MaintenanceKit/`
- 배포 패키지: `HXSS_Korean_Localization/ReleasePackages/`

## 현재 적용 구조

1. 게임 원본 Lua는 직접 수정하지 않음.
2. BepInEx 플러그인이 언어 Lua 로드 시점에 패치 Lua를 우선 적용.
3. TSV 런타임 오버라이드는 제거.
4. 업데이트 검사는 원본 Lua를 복호화/파싱해 `Full_Translation.tsv`와 비교.
5. 번역 반영은 `Needs_Translation.tsv` 검수 후 `Full_Translation.tsv`에 병합하고, 패치 Lua를 재생성.
6. 미번역 중국어 수집은 플러그인 설정에서 선택적으로 활성화.
7. 배포 기본값에서는 중국어 수집과 Lua 로드 추적을 비활성화.

## 최근 완료

- TSV 런타임 오버라이드 제거.
- Lua 패치 우선 로드 방식으로 플러그인 전환.
- 플러그인 DLL 재빌드 및 설치 경로 배치.
- `build_patch_lua.py` / `build_patch_lua.bat` 추가.
- `MaintenanceKit/input/Full_Translation.tsv` 기준 패치 Lua 재생성 및 설치 완료.
- 작업 폴더 정리.
  - 오래된 Release 산출물 삭제.
  - MaintenanceKit 캐시 삭제.
  - 폐기된 TSV 오버라이드 산출물 삭제.
  - Legacy BepInEx 작업물 아카이브 이동.
  - 정리 내역: `Cleanup_Manifest_20260505_174650.tsv`
- 배포 패키징 계획 문서 추가.
  - `Release_Packaging_Plan.md`
- 배포 패키징 자동화 추가.
  - `MaintenanceKit/package_release.bat`
  - `MaintenanceKit/tools/package_release.py`
- 설치/제거 지원 설치기 프로토타입 추가.
  - `Installer/HXSSKoreanPatchInstaller/`
  - Steam 레지스트리와 앱 매니페스트 기반 설치 위치 자동 탐색.
  - 사용자 지정 설치 위치 선택 지원.
  - 설치 기록 기반 제거 및 기존 파일 백업 복원 지원.
- GitHub Releases 배포 기준은 설치기 제외 수동 설치 ZIP으로 전환.
- `package_release.py`를 수동 설치 ZIP 기준으로 수정.
- v0.1.3 수동 설치 ZIP 생성 완료.
  - `HXSS_KoreanPatch_v0.1.3_20260507_035157.zip`
- 플러그인 성능 구조 개선.
  - UI 스캔을 Unity UI 1회, TMP 1회로 통합.
  - 폰트 교체, 하드코드 UI 보정, 선택적 중국어 수집을 같은 스캔에서 처리.
- 플러그인 설정 파일 추가.
  - `BepInEx/config/hxss.huiwen-font-replacer.cfg`
  - 배포 기본값: 수집 꺼짐, Lua 추적 꺼짐.
- 업데이트 대응용 `MaintenanceKit` 구축.
- 원본 Lua 업데이트 감지 스크립트 작성.
- 리포트 기반 병합 스크립트 작성.
- 유지보수용 README 작성.

## 최신 업데이트 감지 결과

검사 기준: 2026-05-05 17:23 업데이트 검사 기준 현재 원본 Lua.

- `t_language.xml`
  - 현재 행: 31429
  - 기존 번역 행: 30936
  - 신규 행: 493
  - 실제 원문 변경: 0
  - 서식 변경: 3090
  - 삭제 행: 0
- `t_tasklanguage.xml`
  - 현재 행: 9416
  - 기존 번역 행: 9286
  - 신규 행: 130
  - 실제 원문 변경: 0
  - 서식 변경: 507
  - 삭제 행: 0

## 업데이트 대응 리포트

- `HXSS_Korean_Localization/MaintenanceKit/output/Update_Summary.tsv`
- `HXSS_Korean_Localization/MaintenanceKit/output/Action_Summary.tsv`
- `HXSS_Korean_Localization/MaintenanceKit/output/Needs_Translation.tsv`
- `HXSS_Korean_Localization/MaintenanceKit/output/Changed_TextOnly.tsv`
- `HXSS_Korean_Localization/MaintenanceKit/output/Added_Rows.tsv`

현재 `Needs_Translation.tsv`에는 즉시 번역이 필요한 일반 중국어 신규 행이 없다.
신규 행은 빈 행, 참조 전용, 태그/비중문, 물음표 placeholder로 분류됨.

## 최신 패치 Lua 빌드

- 빌드 시각: 2026-05-05 21:50
- 릴리스 폴더: `LuaConfig_KO_PluginPatch_20260505_215043`
- 설치 위치: `BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/`
- 기준 번역 파일: `MaintenanceKit/input/Full_Translation.tsv`
- U+FFFD 대체 문자 및 `????` 반복 저장 없음.

## 최신 배포 패키지

- 버전: `v0.1.3`
- 패키지 형식: `HXSS_KoreanPatch_v0.1.3_YYYYMMDD_HHMMSS.zip`
- 위치: `HXSS_Korean_Localization/ReleasePackages/`
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
  - 파일 목록 manifest.

설치기 실행 파일은 GitHub Releases 배포 ZIP에서 제외한다.
설치기 소스는 보관 대상이며, 현재 배포 기준의 필수 포함 대상이 아니다.

## 다음 작업

1. v0.1.3 수동 설치 ZIP을 깨끗한 게임 폴더에서 설치 테스트.
2. 인게임 기본 구간 확인.
3. 수동 제거 절차 확인.
4. 이상 없으면 GitHub Releases 1차 배포.

## 작업 원칙

- `Full_Translation.tsv`를 단일 번역 원본으로 유지.
- 원본 Lua 파일 직접 수정 금지.
- 플러그인 TSV 오버라이드 방식 재도입 금지.
- 배포 기본값에서 `EnableChineseCollector=false` 유지.
- 유지보수자가 미번역 수집이 필요할 때만 수집 기능 활성화.
- 콘솔에서 깨진 한글/중국어를 복사해 저장 금지.
- 물음표 반복 또는 U+FFFD 대체 문자가 들어간 파일은 배포 전 반드시 검사.
- 태그, 변수, 참조 문자열 보존.
- 원문에 없는 한자 괄호 병기 추가 금지.
