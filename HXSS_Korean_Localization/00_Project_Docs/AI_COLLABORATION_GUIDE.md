# AI Collaboration Guide

## 목적

Huaxia: Warring States 한국어 패치 작업에서 사람, Codex, 로컬 번역 모델의 역할을 분리한다.

현재 작업의 핵심은 대량 번역 자체보다 번역 데이터 구조화, 검수, 게임 적용 안정화다.

## 현재 결론

- 번역 마스터는 `MaintenanceKit/input/Full_Translation.tsv`로 관리한다.
- 초벌 번역 원본은 `Archive_Raw` 폴더에 보관한다.
- 게임 적용은 BepInEx 보조 플러그인을 사용한다.
- 원본 게임 파일 직접 교체는 최소화한다.
- 플러그인은 패치 Lua 언어 테이블을 원본 Lua보다 먼저 읽게 한다.
- TSV 런타임 오버라이드는 사용하지 않는다.

## 주요 파일

- 마스터 번역:
  - `HXSS_Korean_Localization/MaintenanceKit/input/Full_Translation.tsv`
- 초벌 번역 원본:
  - `HXSS_Korean_Localization/01_XML_Localization/XmlWork/Review/Archive_Raw/chinese_extracted.txt`
  - `HXSS_Korean_Localization/01_XML_Localization/XmlWork/Review/Archive_Raw/huax_translated.txt`
- 플러그인용 Lua 패치:
  - `BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_language.lua`
  - `BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_taskLanguage.lua`

## 역할 분담

### Codex

- 파일 구조 관리.
- TSV, XML, Lua, 플러그인 적용 흐름 정리.
- 용어집 기준 자동 검수.
- 잔여 한자, 태그, 변수, 줄바꿈, 조사 오류 검사.
- BepInEx 플러그인 수정 및 빌드.
- 배포 전 검수 리포트 생성.

Codex는 번역 문체의 최종 결정자보다 구조와 안정성 담당에 가깝다.

### 로컬 번역 모델

- 대량 번역 후보 생성.
- 사전과 톤 가이드 기준 준수.
- 원문에 없는 괄호 한자 병기 추가 금지.
- 태그, 변수, 숫자 보존.

### 사람 검수

- 인게임 표시 확인.
- 고유명사, 지명, 인명, 세력명 최종 결정.
- UI 폭, 줄바꿈, 폰트 출력 확인.
- 어색한 문장, 장르 톤 불일치, 과도한 직역 수정.

## 적용 방식

### 1순위: 패치 Lua 우선 로드

플러그인이 게임의 `t_language.lua`, `t_taskLanguage.lua` 로드 시점에 패치 폴더의 Lua를 먼저 반환한다.

장점:

- 원본 게임 파일 직접 수정 없음.
- 패치 폴더 삭제 시 원복 가능.
- 메인 메뉴, 설정, 커스터마이징처럼 언어 테이블을 직접 참조하는 UI까지 반영 가능.
- TSV 런타임 오버라이드보다 적용 누락이 적음.

주의:

- `Full_Translation.tsv` 수정 후 `MaintenanceKit/build_patch_lua.bat`로 패치 Lua를 재생성해야 한다.
- 게임 업데이트 후 `MaintenanceKit/update_audit.bat`로 원본 변경 여부를 확인해야 한다.

### 2순위: 화면 텍스트 오버라이드

언어 테이블에 없는 하드코드 UI는 플러그인의 텍스트 오버라이드로 처리한다.

- 중국어 잔존 문구 수집.
- 인게임 확인 후 후보 등록.
- 배포 전 검수에서 확정 문구만 반영.

## 검수 규칙

- `Full_Translation.tsv`가 기준이다.
- 원문 `zh`와 `sid`는 수정하지 않는다.
- `ko_new`만 수정한다.
- 원문에 없는 괄호 한자 병기 금지.
- 태그는 삭제하지 않는다.
- `<color>`, `<link>`, `<sprite>`, `<align>`, `<margin>` 계열 태그 보존.
- 줄바꿈 `\n` 보존.
- 변수 `{0}`, `{1}`, `%s`, `{ref=...}` 보존.
- 단순 한자 잔존은 자동 보고서로 확인하되, 출생월 `一`~`十二`처럼 의도된 항목은 예외 처리한다.

## 배포 전 확인

1. `Full_Translation.tsv` 잔여 한자 검사.
2. 물음표 깨짐 검사.
3. `build_patch_lua.bat`로 패치 Lua 재생성.
4. 플러그인 DLL 빌드 및 배치.
5. 인게임 메인 화면, 언어 설정, 공지, 설정, 커스터마이징, 튜토리얼 초반 확인.
6. 발견 이슈는 스크린샷과 함께 `TASK.md`에 기록.
