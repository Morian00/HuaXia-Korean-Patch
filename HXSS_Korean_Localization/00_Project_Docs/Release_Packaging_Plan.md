# HXSS Korean Patch Release Packaging Plan

## 목적

한국어 패치를 단일 공개 패키지로 배포한다.

패키지는 일반 사용자가 바로 설치해 플레이할 수 있어야 하며, 동시에 다른 작업자가 게임 업데이트 대응과 번역 수정을 이어받을 수 있어야 한다.

현재 배포물은 GitHub Releases용 수동 설치 ZIP을 기준으로 한다.
최종 사용자는 ZIP 내부 파일을 게임 설치 폴더에 복사해 설치한다.
다음 작업자는 동일 패키지 안의 번역 원본, 업데이트 검출 도구, Lua 재생성 도구, 플러그인 소스를 통해 유지보수를 이어갈 수 있다.

## 현재 적용 방식

- BepInEx IL2CPP 기반 플러그인 사용.
- 게임 원본 파일 직접 수정 없음.
- 플러그인이 언어 Lua 로드 시점에 패치 Lua를 우선 반환.
- 대상 Lua:
  - `t_language.lua`
  - `t_taskLanguage.lua`
- 한국어 번역 기준 파일:
  - `MaintenanceKit/input/Full_Translation.tsv`
- `Full_Translation.tsv`를 기준으로 패치 Lua를 생성.
- HuiWenZhengKai 계열 특수 폰트는 런타임에서 한중 통합 폰트로 교체.
- 언어 Lua에 없는 일부 하드코드 UI는 `hardcoded_text.tsv`로 보정.
- 미번역 중국어 수집 기능은 기본 비활성화.
- TSV 런타임 오버라이드 방식은 폐기.

## 배포 패키지 성격

파일명 예시:

```text
HXSS_KoreanPatch_v0.1.3_YYYYMMDD_HHMMSS.zip
```

패키지 성격:

- 수동 설치형 한국어 패치
- GitHub Releases 배포용 ZIP 패키지
- 유지보수 인수인계 패키지
- 번역 원본 공개 패키지
- 업데이트 대응 도구 포함 패키지

따라서 배포 파일에는 단순 실행에 필요한 파일뿐 아니라, 다음 작업자가 이어받기 위한 원본과 도구도 포함한다.
배포 ZIP 안에는 게임 설치 폴더에 복사할 파일, 유지보수용 파일, 문서가 포함된다.
단일 실행 설치기와 설치기 manifest는 포함하지 않는다.

## 패키지 포함 대상

### 게임 적용 파일

```text
BepInEx/
  config/
    hxss.huiwen-font-replacer.cfg
  plugins/
    HXSS.HuiWenFontReplacer/
      HXSS.HuiWenFontReplacer.dll
      Shilla_HuiWen_CN_KR_Strict.ttf
      hardcoded_text.tsv
      KoreanPatch/
        lua/
          game/
            config/
              t_language.lua
              t_taskLanguage.lua
```

### BepInEx 기반 파일

```text
BepInEx/
dotnet/
winhttp.dll
doorstop_config.ini
.doorstop_version
changelog.txt
```

기준 폴더:

```text
HXSS_Korean_Localization/BepInEx-Unity.IL2CPP-win-x64-6.0.0-be.755+3fab71a
```

BepInEx 자체는 개조하지 않는다.
패키징 시 원본 BepInEx 폴더를 복사한 뒤 한국어 패치 플러그인과 설정 파일을 주입한다.

### 유지보수 키트

```text
HXSS_Korean_Localization/
  MaintenanceKit/
    update_audit.bat
    apply_report.bat
    build_patch_lua.bat
    package_release.bat
    README.md
    input/
      Full_Translation.tsv
    output/
      README.md
    tools/
      update_audit.py
      apply_report.py
      build_patch_lua.py
      package_release.py
      XmlConfigCrypto.ps1
      lua54.exe
      lua54.dll
      luac54.exe
```

유지보수 키트는 게임 업데이트 후 원본 Lua와 현재 번역 원본을 비교하고, 새 번역을 반영하며, 패치 Lua와 배포 ZIP을 다시 생성하기 위한 도구 모음이다.

### 문서

```text
README_KO.md
CHANGELOG_KO.md
HXSS_Korean_Localization/
  00_Project_Docs/
    Glossary.md
    Translation_Tone_Guide.md
    Workflow_README.md
    Release_Packaging_Plan.md
```

문서 포함 목적:

- 용어 일관성 유지.
- `Glossary.md` 기준 용어 확인 및 후속 번역 수정 지원.
- 번역 톤 기준 공유.
- 이후 작업자 인수인계.
- 업데이트 대응 절차 명시.

### 플러그인 소스

```text
HXSS_Korean_Localization/
  03_Font_Work/
    Font/
      HuiWenFontReplacer/
        Plugin.cs
        HuiWenFontReplacer.csproj
```

포함 목적:

- 폰트 교체 로직 수정 가능.
- 하드코드 UI 보정 로직 수정 가능.
- 미번역 중국어 수집 조건 수정 가능.
- 이후 BepInEx 또는 게임 구조 변경 대응 가능.

`bin`, `obj`, `.vs` 등 빌드 산출물은 제외한다.

### 설치기 소스

```text
HXSS_Korean_Localization/
  Installer/
    HXSSKoreanPatchInstaller/
      HXSSKoreanPatchInstaller.csproj
      Program.cs
      app.manifest
```

보관 목적:

- Steam 설치 위치 자동 탐색 로직 수정 가능.
- 설치/제거 및 백업 정책 수정 가능.
- 사용자 지정 설치 위치 선택 UI 수정 가능.
- 이후 설치기 배포 재검토 시 참고 가능.

현재 GitHub Releases 배포 ZIP에는 설치기 실행 파일을 포함하지 않는다.
설치기 소스는 저장소 또는 유지보수 인수인계 자료로만 보관한다.
수동 설치 ZIP의 필수 포함 대상은 아니다.

`bin`, `obj`, 임시 `Resources/payload.zip`는 소스 보관 대상에서 제외한다.

## 패키지 제외 대상

다음 파일은 배포물에 포함하지 않는다.

- `collected_chinese.tsv`
- `lua_loader_trace.tsv`
- `language_call_trace.tsv`
- `MaintenanceKit/cache`
- `__pycache__`
- `*.pyc`
- 과거 리뷰 리포트 전체
- 과거 스크린샷 정리 폴더
- 실패한 Lua 빌드 산출물
- 중복 백업본
- 단일 실행 설치기
- 설치기 페이로드 ZIP
- 설치기 manifest
- 이전 XML 직접 적용 워크플로 산출물
- 이전 TSV 런타임 오버라이드 산출물

단, `MaintenanceKit/output/README.md`는 출력 폴더의 용도를 설명하기 위해 포함한다.

## 사용자 설치 및 제거 절차

### 설치

1. 배포 ZIP 압축 해제.
2. Steam 라이브러리에서 `Huaxia: Warring States` 설치 폴더 열기.
3. ZIP 내부의 파일과 폴더를 게임 설치 폴더 최상위에 복사.
4. 같은 파일명이 있으면 덮어쓰기.
5. 게임 실행.
6. 언어 설정에서 한국어 선택.
7. 게임 재시작.
8. 메인 메뉴, 공지, 설정, 캐릭터 생성 화면 확인.

Steam 설치 폴더 접근 예시:

```text
Steam 라이브러리 > Huaxia: Warring States 우클릭 > 관리 > 로컬 파일 보기
```

설치 폴더 검증 기준:

- `hxss.exe` 존재.
- `hxss_Data` 폴더 존재.
- ZIP 내부 파일을 `hxss.exe`가 있는 폴더에 복사.

### 제거

1. 게임 설치 폴더 열기.
2. 다음 폴더와 설정 파일 삭제.

```text
BepInEx/plugins/HXSS.HuiWenFontReplacer/
BepInEx/config/hxss.huiwen-font-replacer.cfg
```

3. 다른 BepInEx 플러그인을 사용하지 않는 경우에만 BepInEx 기반 파일 전체 삭제.
4. 필요 시 Steam에서 게임 파일 무결성 검사 실행.

BepInEx 기반 파일 전체 삭제 대상:

```text
BepInEx/
dotnet/
winhttp.dll
doorstop_config.ini
.doorstop_version
changelog.txt
```

다른 모드 또는 BepInEx 플러그인을 함께 사용하는 경우 BepInEx 기반 파일 전체 삭제는 권장하지 않는다.

## 플러그인 설정

설정 파일:

```text
BepInEx/config/hxss.huiwen-font-replacer.cfg
```

배포 기본값:

- `EnableFontReplacement = true`
- `EnableTextOverrides = true`
- `EnableChineseCollector = false`
- `EnableLuaLoadTrace = false`
- `UiScanIntervalSeconds = 2`

설정 의미:

- `EnableFontReplacement`: HuiWenZhengKai 특수 폰트를 한중 통합 폰트로 교체.
- `EnableTextOverrides`: `hardcoded_text.tsv` 기반 하드코드 UI 보정.
- `EnableChineseCollector`: 패치 Lua와 하드코드 사전에 없는 중국어 UI 수집.
- `EnableLuaLoadTrace`: Lua 우선 로드 여부 디버깅용 추적 파일 생성.
- `UiScanIntervalSeconds`: UI 스캔 주기.

일반 배포에서는 수집과 추적 기능을 꺼둔다.
유지보수자가 미번역 UI를 찾을 때만 켠다.

## 유지보수 절차

### 1. 게임 업데이트 후 변경점 검출

실행:

```text
HXSS_Korean_Localization/MaintenanceKit/update_audit.bat
```

입력:

- 현재 게임 폴더의 원본 `t_language.lua`
- 현재 게임 폴더의 원본 `t_taskLanguage.lua`
- `MaintenanceKit/input/Full_Translation.tsv`

출력:

```text
MaintenanceKit/output/Update_Summary.tsv
MaintenanceKit/output/Action_Summary.tsv
MaintenanceKit/output/Action_Items.tsv
MaintenanceKit/output/Needs_Translation.tsv
MaintenanceKit/output/Added_Rows.tsv
MaintenanceKit/output/Changed_TextOnly.tsv
MaintenanceKit/output/Changed_FormatOnly.tsv
MaintenanceKit/output/Removed_Rows.tsv
```

우선 확인 파일:

1. `Update_Summary.tsv`
2. `Needs_Translation.tsv`
3. `Changed_TextOnly.tsv`
4. `Added_Rows.tsv`

### 2. 신규 또는 변경 번역 작성

`Needs_Translation.tsv`의 `ko_new` 칸만 작성한다.

수정 금지 컬럼:

- `action`
- `language_table`
- `sid`
- `zh`
- `en`
- `current_ko`
- `previous_ko`
- `note`

주의:

- 태그 삭제 금지.
- 변수 삭제 금지.
- 줄바꿈 의미 보존.
- 원문에 없는 한자 괄호 병기 추가 금지.
- 콘솔에서 깨져 보이는 문자를 그대로 복사하지 않음.

### 3. 번역 원본 병합

실행:

```text
HXSS_Korean_Localization/MaintenanceKit/apply_report.bat
```

역할:

- `Needs_Translation.tsv`의 `ko_new`가 채워진 행만 병합.
- 기존 sid는 갱신.
- 신규 sid는 추가.
- 실행 전 `Full_Translation.tsv` 자동 백업.

`Full_Translation.tsv`를 직접 수정한 경우 이 단계는 생략 가능.

### 4. 패치 Lua 재생성

실행:

```text
HXSS_Korean_Localization/MaintenanceKit/build_patch_lua.bat
```

역할:

- `Full_Translation.tsv` 기준으로 패치 Lua 생성.
- Lua 컴파일.
- 게임용 암호화.
- 플러그인 패치 폴더에 설치.

최종 설치 위치:

```text
BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_language.lua
BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_taskLanguage.lua
```

원본 게임 Lua 경로에는 직접 덮어쓰지 않는다.

### 5. 인게임 검증

확인 우선순위:

- 메인 메뉴.
- 공지.
- 설정 메뉴.
- 새 게임 시작.
- 캐릭터 생성.
- 족군 선택.
- 업데이트 신규 문구.
- `Needs_Translation.tsv`에서 처리한 항목.

### 6. 배포 ZIP 재생성

실행:

```text
HXSS_Korean_Localization/MaintenanceKit/package_release.bat
```

출력:

```text
HXSS_Korean_Localization/ReleasePackages/
```

생성 파일:

- 수동 설치용 배포 ZIP.
- 파일 목록 manifest.
- stage 폴더.

## 패키징 자동화 기준

현재 패키징 스크립트:

```text
HXSS_Korean_Localization/MaintenanceKit/tools/package_release.py
```

처리 순서:

1. BepInEx 원본 템플릿 복사.
2. 최신 플러그인 DLL 복사.
3. 통합 폰트 복사.
4. `hardcoded_text.tsv` 복사.
5. 최신 `KoreanPatch` Lua 복사.
6. 기본 config 생성.
7. README/CHANGELOG 생성.
8. 유지보수 키트 복사.
9. 공개 문서 복사. `Glossary.md`는 필수 포함.
10. 플러그인 소스 복사.
11. trace/cache/수집 파일 제외.
12. stage 기준 수동 설치 ZIP 생성.
13. manifest 생성.
14. SHA-256 검증값 생성.

현재 `package_release.py`는 설치기 포함 패키징 흐름으로 작성되어 있다.
GitHub Releases 수동 설치 ZIP 배포 기준에 맞게 설치기 빌드 단계를 제거하거나 옵션화해야 한다.

## 배포 전 체크리스트

- 최신 `Full_Translation.tsv` 수정분 반영 완료.
- `build_patch_lua.bat` 실행 완료.
- `KoreanPatch/lua/game/config/`에 최신 Lua 2개 존재.
- `hardcoded_text.tsv` 최신화.
- `HXSS.HuiWenFontReplacer.dll` 최신 빌드 반영.
- 수집 파일 제외 확인.
- trace 파일 제외 확인.
- 유지보수 키트 포함 확인.
- `Full_Translation.tsv` 포함 확인.
- `00_Project_Docs/Glossary.md` 포함 확인.
- `00_Project_Docs/Translation_Tone_Guide.md` 포함 확인.
- `update_audit.bat`, `apply_report.bat`, `build_patch_lua.bat`, `package_release.bat` 포함 확인.
- `lua54.exe`, `luac54.exe`, `XmlConfigCrypto.ps1` 포함 확인.
- README_KO 유지보수 절차 포함 확인.
- README_KO 설치/제거 절차 포함 확인.
- 수동 설치 ZIP manifest 확인.
- ZIP 최상위에 게임 폴더 복사 대상 파일 배치 확인.
- ZIP 내부에 단일 실행 설치기 없음.
- SHA-256 해시 생성 및 Release notes 반영.

## 인코딩 주의

모든 TSV와 문서는 UTF-8 또는 UTF-8 with BOM을 사용한다.

PowerShell 콘솔에서 한글 또는 중국어가 물음표로 보일 수 있다.
콘솔 표시가 깨지는 것과 파일 내용이 깨지는 것은 다르다.
단, 깨진 콘솔 출력을 번역 파일에 복사하면 실제 파일도 손상될 수 있다.

파일 수정은 VS Code 또는 유지보수 키트의 Python 도구를 우선 사용한다.

## 현재 남은 개선점

- 유지보수 키트 실행 파일화 검토.
- Python 미설치 환경 지원 강화.
- 플러그인 빌드 자동화 추가.
- 배포 ZIP 생성 전 자동 검증 항목 확대.
- `hardcoded_text.tsv` 중복 검사 자동화.
- 미번역 중국어 수집 결과를 `hardcoded_text.tsv` 후보로 자동 변환하는 도구 추가.
