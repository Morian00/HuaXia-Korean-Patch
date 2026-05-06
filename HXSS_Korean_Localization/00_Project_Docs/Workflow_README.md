# Huaxia: Warring States Korean Localization Workflow

## 목적

Huaxia: Warring States 한국어 완역을 위한 번역 데이터 관리, Lua 언어 테이블 생성, BepInEx 보조 적용 워크플로를 정의한다.

## 기본 구조

```text
HXSS_Korean_Localization/
  00_Project_Docs/
  01_XML_Localization/
    XmlWork/
      SourceSnapshot/
      WorkingXml/
      SlimTranslationXml/
      Review/
      Reports/
  02_Tools/
  03_Font_Work/
  MaintenanceKit/
  99_Cleanup_Archive/
```

## 번역 대상

- 실제 번역 대상은 2개 언어 테이블.
  - `t_language.xml`
  - `t_tasklanguage.xml`
- 최종 반영 위치:
  - `XmlWork/WorkingXml/t_language.xml`
  - `XmlWork/WorkingXml/t_tasklanguage.xml`
- 작업용 기준 파일:
  - `MaintenanceKit/input/Full_Translation.tsv`
  - `XmlWork/SlimTranslationXml/t_language.slim.xml`
  - `XmlWork/SlimTranslationXml/t_tasklanguage.slim.xml`

## 경량 파일 원칙

- 최종 게임 적용용 XML은 원본 속성 구조를 유지한다.
- AI 번역 작업용 파일은 토큰 절감을 위해 `sid`, `zh`, `ko` 또는 `ko_new`만 유지한다.
- 다른 언어 컬럼(`tw`, `en`, `ja` 등)은 작업용 파일에서 제거한다.
- 경량 파일은 최종 암호화 대상이 아니다.

경량 파일 생성:

```powershell
python HXSS_Korean_Localization\02_Tools\create_slim_translation_files.py
```

## 번역 파일 형식

`Full_Translation.tsv` 기본 컬럼:

```text
language_table	sid	zh	ko_new	owner	notes
```

- `language_table`: `t_language.xml` 또는 `t_tasklanguage.xml`.
- `sid`: 언어 행 ID. 수정 금지.
- `zh`: 중국어 원문. 수정 금지.
- `ko_new`: 한국어 번역문.
- `owner`: 담당자 기록. 필요 시 사용.
- `notes`: 보류 사유, 문맥 메모.
- 원문에 없는 괄호 한자 병기나 해설을 추가하지 않는다.

## 현재 적용 방식

현재 배포 구조는 원본 게임 파일 직접 교체보다 BepInEx 보조 플러그인 적용을 우선한다.

### 1순위: Lua 언어 테이블 우선 로드

플러그인은 게임이 언어 Lua를 읽는 시점에 패치 폴더의 파일을 우선 반환한다.
원본 게임 파일은 수정하지 않는다.

```text
BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/
  t_language.lua
  t_taskLanguage.lua
```

TSV 런타임 오버라이드 방식은 제거한다.
정상 적용이 불안정했고, 메인 메뉴와 설정처럼 다른 로드 경로를 타는 UI가 누락되었기 때문이다.

패치 Lua는 매번 새 구조로 생성하지 않는다.
정상 작동이 확인된 Lua 구조를 기준으로 필요한 경우에만 최소 수정한다.

### 2순위: 화면 텍스트 오버라이드

언어 테이블에 없는 하드코드 UI는 별도 후보 목록으로 관리한다.

```text
HXSS_Korean_Localization/01_XML_Localization/XmlWork/Review/Hardcoded_UI_Bundle_Replacement_Candidates.tsv
```

확정된 문구만 플러그인 오버라이드에 반영한다.

## 초벌 번역 원본

대량 초벌 번역 원본은 다음 폴더에 보관한다.

```text
HXSS_Korean_Localization/01_XML_Localization/XmlWork/Review/Archive_Raw/
  chinese_extracted.txt
  huax_translated.txt
```

이 파일들은 비교와 복구용 원본이며, 게임 적용 파일이 아니다.

## 담당 기준

### Codex

- XML 추출, 검증, 병합, 반영 스크립트 관리.
- 작업 파일 구조화와 분할 기준 정리.
- 사전, 톤 가이드, 금지 표현 관리.
- 태그, 변수, 숫자, 줄바꿈 보존 검증.
- 중국어 잔존, 원문에 없는 괄호 한자 병기, 용어 불일치 검사.

### Local Qwen

- `Full_Translation.tsv` 기준 대량 번역.
- 기본 모델은 `qwen3.5:9b` 또는 동급 Qwen 9B 전후 모델.
- UI, 시스템, 도움말, 스탯, 아이템, 스킬, 내러티브 전반의 1차 번역.
- 사전과 톤 가이드를 프롬프트에 포함해 일관성 유지.
- 원문에 없는 괄호 한자 병기나 해설 추가 금지.

### Human Review

- 인게임 표시 확인.
- 고유명사 최종 결정.
- 직역투, 어색한 문장, UI 폭 문제 수정.
- 보류 이슈를 `TASK.md`에 기록.

### Antigravity

- 대량 번역 담당에서 제외.
- 필요 시 내러티브나 고유명사 후보 보조 검수에 한정 사용.

## 작업 순서

1. `Full_Translation.tsv` 또는 slim XML 기준으로 번역.
2. 담당자별 결과 병합.
3. 검증.
   - 빈 번역.
   - 중국어 잔존.
   - 태그/변수/숫자 보존.
   - `language_table + sid` 중복.
4. `WorkingXml`의 `ko` 속성에 반영.
5. 평문 XML 재암호화.
6. 게임 실행 테스트.

## 기타 XML 처리

- 기타 XML 대부분은 언어 `sid` 참조 또는 코드 데이터.
- `remark`는 대체로 개발자 메모이며 번역 대상이 아니다.
- 감사표:
  - `XmlWork/Reports/Xml_Direct_Text_Audit.tsv`
- 현재 직접 출력 문자열 의심:
  - `t_sounds.xml`의 `content` 22개.

## 적용 방식

`hxss_Data/StreamingAssets/XmlConfig_Decrypted/Decrypted_README.md` 기준:

- 게임은 평문 XML을 직접 읽지 않는다.
- 평문 XML 수정 후 DES-CBC-PKCS7 방식으로 재암호화 필요.
- 단, 2026-05-04 기준 인게임 표시 확인 결과 `XmlConfig` XML만으로는 언어가 반영되지 않음.
- 실제 런타임 언어 표시는 다음 Lua config를 우선 참조하는 것으로 판단.
  - `hxss_Data/StreamingAssets/lua/game/config/t_language.lua`
  - `hxss_Data/StreamingAssets/lua/game/config/t_taskLanguage.lua`
- Lua 언어 파일은 DES 암호화 상태이며, 복호화 후 Lua 5.4 바이트코드 구조.

기존 직접 교체 적용 흐름:

1. `Full_Translation.tsv` 기준 `WorkingXml`의 `ko` 속성 유지.
2. XML은 기준 데이터와 백업용으로 관리.
3. `MaintenanceKit/build_patch_lua.bat`로 Lua 언어 테이블 생성.
4. Lua 파일을 DES 암호화.
5. `lua/game/config`의 `t_language.lua`, `t_taskLanguage.lua` 교체.

이 방식은 인게임 적용이 가능하나, 원본 파일을 직접 교체하므로 다음 문제가 있다.

- 게임 업데이트 시 원본 파일 복구 또는 충돌 가능.
- 잘못된 Lua 바이트코드/암호화 처리 시 무한 로딩 발생 가능.
- 한글 패치 삭제만으로 원복되지 않음.

따라서 장기 배포 구조는 원본 파일 직접 교체가 아니라 BepInEx 보조 플러그인 기반 우선 로드 방식으로 전환한다.

## 신규 적용 방향

목표는 원본 게임 파일을 직접 수정하지 않고, 게임이 언어 파일과 폰트를 읽는 시점에 한글 패치 파일을 우선 사용하게 만드는 것이다.

현재 런타임 구조:

```text
BepInEx/plugins/HXSS.HuiWenFontReplacer/
  HXSS.HuiWenFontReplacer.dll
  Shilla_HuiWen_CN_KR_Strict.ttf
  hardcoded_text.tsv
  KoreanPatch/
    lua/game/config/
      t_language.lua
      t_taskLanguage.lua
```

우선순위:

1. Lua/config 파일 로드 경로 후킹.
   - 게임이 `t_language.lua`, `t_taskLanguage.lua`를 읽을 때 패치 폴더의 파일을 대신 반환.
   - 원본 파일 수정 없음.
   - 패치 폴더 제거 시 원복.
2. 폰트 자동 교체.
   - 기존 후이웬+신라 통합 폰트를 런타임에 적용.
   - 원본 폰트 번들 수정 없음.
3. 하드코딩 UI 텍스트 런타임 치환.
   - `血亲关系`, `人际关系`, `查看志向`처럼 언어 테이블에 없는 프리팹 문자열 보정.
   - 같은 길이 문자열 제약 없음.
4. 미번역 중국어 수집.
   - 한국어가 포함된 문자열은 수집 제외.
   - 중국어 잔존 문자열만 수집.
   - 필요 시 자동 번역 또는 후속 수동 번역 대상으로 분류.

## 런타임 우선순위

표시 문구 적용 우선순위:

1. 패치 Lua 언어 테이블.
2. 수동 하드코딩 오버라이드.
3. 미번역 중국어 수집.

XML 백업/검증 흐름:

  1. XML 복호화.
  2. `ko` 속성 수정.
  3. XML 재암호화.
  4. 게임 경로에 배치.

패치 Lua 생성:

```powershell
HXSS_Korean_Localization\MaintenanceKit\build_patch_lua.bat
```

생성된 Lua는 플러그인 패치 폴더에 배치한다.
직접 설치 방식은 배포 대상에서 제외한다.

## 금지 사항

- `sid` 수정 금지.
- `zh` 수정 금지.
- 최종 XML에서 `ko` 외 언어 컬럼 수정 금지.
- `WorkingXml` 구조 훼손 금지.
- 검증 전 암호화/배포 금지.
- 원본 Lua 직접 교체 방식 재도입 금지.
- TSV 런타임 오버라이드 방식 재도입 금지.
- 번들 직접 문자열 치환은 최후 수단으로만 사용.
