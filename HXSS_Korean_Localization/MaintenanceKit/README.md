# HXSS 한국어 패치 유지보수 키트

## 목적

게임 업데이트 후 원본 언어 Lua 파일과 한국어 패치 원본 TSV를 비교하여 변경점을 찾는 유지보수 도구 모음이다.

현재 한국어 패치의 기준 파일은 `input/Full_Translation.tsv`이다.
게임 원본 파일은 직접 수정하지 않는다.
플러그인은 런타임에서 번역 TSV를 직접 읽지 않는다.
현재 적용 방식은 패치 Lua 파일을 게임 원본 Lua 대신 우선 로드하는 구조다.

## 기본 구조

```text
MaintenanceKit/
  update_audit.bat              업데이트 차이 검사
  apply_report.bat              검수 완료 리포트 TSV를 Full_Translation.tsv에 병합
  build_patch_lua.bat           Full_Translation.tsv 기준 패치 Lua 생성 및 설치
  input/
    Full_Translation.tsv        한국어 패치 번역 원본
  output/
    Update_Summary.tsv          업데이트 요약
    Action_Summary.tsv          조치 대상 요약
    Action_Items.tsv            전체 조치 목록
    Needs_Translation.tsv       사람이 채워야 하는 번역 목록
    Added_Rows.tsv              신규 sid 목록
    Changed_TextOnly.tsv        실제 원문 변경 목록
    Changed_FormatOnly.tsv      태그/줄바꿈 등 서식 차이 목록
    Removed_Rows.tsv            현재 원본 Lua에서 사라진 sid 목록
    Apply_Log.tsv               병합 결과 로그
  tools/
    update_audit.py
    apply_report.py
    build_patch_lua.py
    XmlConfigCrypto.ps1
    lua54.exe
    lua54.dll
    luac54.exe
```

## 작업 순서

### 1. 업데이트 차이 검사

`update_audit.bat` 실행.

이 도구는 현재 게임 폴더의 원본 파일을 읽는다.

- `hxss_Data/StreamingAssets/lua/game/config/t_language.lua`
- `hxss_Data/StreamingAssets/lua/game/config/t_taskLanguage.lua`

실행 후 `output/` 폴더에 리포트가 생성된다.

### 2. 리포트 확인

먼저 `output/Update_Summary.tsv`를 확인한다.

주요 컬럼:

- `added`: 새로 추가된 sid 수
- `changed_text`: 실제 중국어 원문이 바뀐 sid 수
- `changed_format_only`: 태그, 줄바꿈, escape 방식만 달라진 sid 수
- `removed`: 현재 원본 Lua에서 사라진 sid 수

실제 작업 대상은 주로 `output/Needs_Translation.tsv`이다.

### 3. 번역 입력

`output/Needs_Translation.tsv`의 `ko_new` 칸만 채운다.

주의:

- `sid`, `language_table`, `zh`, `en` 컬럼 수정 금지.
- 태그, 변수, 줄바꿈 의미 보존.
- `%s`, `{0}`, `{ref=...}`, `<color=...>`, `<link=...>`는 임의 삭제 금지.
- 원문에 없는 한자 괄호 병기 추가 금지.

### 4. 번역 원본에 병합

`apply_report.bat` 실행.

이 도구는 `output/Needs_Translation.tsv`의 `ko_new`가 채워진 행만 `input/Full_Translation.tsv`에 반영한다.

기존 행이면 갱신한다.
신규 행이면 추가한다.
실행 전 자동 백업 파일이 생성된다.

### 5. 패치 Lua 재생성

`Full_Translation.tsv` 반영 후 패치 Lua를 재생성한다.

`build_patch_lua.bat` 실행.

최종 배치 대상:

```text
BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_language.lua
BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_taskLanguage.lua
```

주의: 게임 원본 Lua 경로에는 직접 덮어쓰지 않는다.

### 6. 인게임 확인

게임 실행 후 한국어 설정 상태에서 확인한다.

확인 우선순위:

- 메인 메뉴
- 공지
- 설정
- 새로 추가된 업데이트 문구
- 변경 원문이 있던 항목

## 리포트 분류 기준

### added_needs_translation

신규 sid이며 중국어 원문이 존재한다.
번역 필요.

### added_no_zh_has_en

중국어 원문은 비어 있고 영어 필드만 존재한다.
개발용 문구, 영문 전용 문구, 누락 데이터 가능성 존재.
필요 시 번역.

### added_placeholder_question_marks

중국어 원문은 비어 있고 영어 필드가 물음표 반복 placeholder로만 구성된 항목이다.
대부분 개발사 더미 데이터로 판단한다.
기본적으로 번역 대상에서 제외한다.

### changed_zh_needs_review

기존 sid의 중국어 원문이 실제로 바뀐 항목이다.
기존 한국어 번역을 그대로 써도 되는지 반드시 검토한다.

### added_empty_row

신규 sid지만 원문이 비어 있다.
대부분 더미 데이터일 수 있다.
기본적으로 작업 대상에서 제외.

### added_ref_only

`{ref=...}`만 있는 구조용 행이다.
대부분 번역보다 참조 구조 유지가 우선이다.

### format_only

원문 의미는 같고 태그 표기나 줄바꿈 저장 방식만 바뀐 항목이다.
일반적으로 번역 수정 불필요.

## 금지 사항

- 원본 Lua 파일 직접 수정 금지.
- `t_language.lua`, `t_taskLanguage.lua`를 한국어 Lua로 덮어쓰는 방식 금지.
- TSV 런타임 오버라이드 재도입 금지.
- TSV 로드 실패 시 Lua 번역본으로 우회하는 fallback 사용 금지.
- 콘솔 출력 결과를 복사해 번역 파일에 붙여넣기 금지.
- 물음표 반복 또는 깨진 대체 문자가 보이는 상태로 저장 금지.

## 인코딩 주의

모든 TSV와 문서는 UTF-8 with BOM 또는 UTF-8로 저장한다.

PowerShell 콘솔에서 한글/중국어가 깨져 보일 수 있다.
콘솔 표시가 깨지는 것과 파일 내용이 깨지는 것은 다르다.
파일 수정은 가능하면 VS Code 또는 본 키트의 파이썬 도구로 수행한다.

## 배포 전 확인

- `output/Needs_Translation.tsv`에 비어 있는 핵심 번역이 없는지 확인.
- `input/Full_Translation.tsv`에 물음표 반복 또는 U+FFFD 대체 문자가 없는지 확인.
- 패치 Lua가 `KoreanPatch/lua/game/config/`에 있는지 확인.
- BepInEx 플러그인이 원본 Lua 대신 패치 Lua를 읽는지 확인.
- TSV 런타임 오버라이드가 비활성 상태인지 확인.

## 향후 개선

현재 배치 파일은 로컬 Python 실행 환경을 사용한다.
최종 인수인계 패키지는 `pyinstaller` 등으로 `update_audit.exe`, `apply_report.exe`, `build_patch_lua.exe`를 생성해 Python 설치 없이 실행 가능하게 만드는 것을 권장한다.
