# HuaXia Warring States Korean Patch

Huaxia: Warring States 비공식 유저 한글 패치입니다.

본 패치는 Steam판 Huaxia: Warring States 보유자를 대상으로 합니다.
원본 게임 실행 파일은 포함하지 않으며, BepInEx 기반 플러그인을 통해 한국어 Lua 파일과 폰트를 우선 적용합니다.

## 다운로드

최신 배포 파일은 GitHub Releases에서 다운로드합니다.

1. 저장소 오른쪽의 Releases 선택
2. 최신 버전 선택
3. Assets에서 `HXSS_KoreanPatch_vX.X.X_YYYYMMDD_HHMMSS.zip` 다운로드

저장소의 Code 버튼으로 받는 압축 파일은 작업 파일 묶음입니다.
일반 사용자는 Releases의 ZIP 파일을 받아야 합니다.

## 설치 방법

1. 다운로드한 ZIP 파일 압축 해제
2. Steam 라이브러리에서 Huaxia: Warring States 우클릭
3. 관리 > 로컬 파일 보기 선택
4. ZIP 내부 파일과 폴더를 게임 설치 폴더 최상위에 복사
5. 같은 파일명이 있으면 덮어쓰기
6. 게임 실행
7. 언어 설정에서 한국어 선택
8. 게임 재시작

복사 대상 폴더는 `hxss.exe`가 있는 폴더입니다.

## 제거 방법

게임 설치 폴더에서 다음 항목을 삭제합니다.

```text
BepInEx/plugins/HXSS.HuiWenFontReplacer/
BepInEx/config/hxss.huiwen-font-replacer.cfg
```

다른 BepInEx 플러그인을 사용하지 않는 경우에만 다음 항목도 삭제할 수 있습니다.

```text
BepInEx/
dotnet/
winhttp.dll
doorstop_config.ini
.doorstop_version
changelog.txt
```

문제가 남아 있으면 Steam에서 게임 파일 무결성 검사를 실행합니다.

## 주의사항

- 본 패치는 공식 한국어 패치가 아닙니다.
- 원본 게임 파일, 수정된 게임 실행 파일, 크랙 파일을 포함하지 않습니다.
- GitHub Releases 외부에서 재업로드된 파일은 검증하지 않습니다.
- 게임 업데이트 후 일부 문구가 미번역으로 돌아가거나 적용이 깨질 수 있습니다.
- 다른 BepInEx 모드와 함께 사용하는 경우 제거 시 BepInEx 공용 파일 삭제에 주의해야 합니다.

## 문제 제보

문제 제보 시 다음 정보를 함께 남겨 주세요.

- 패치 버전
- 게임 버전 또는 업데이트 날짜
- 발생 위치
- 스크린샷
- 재현 방법

## 작업 문서

아래 문서는 번역 유지보수와 배포 작업자를 위한 자료입니다.

- 프로젝트 구조: `HXSS_Korean_Localization/README.md`
- 배포 패키징 계획: `HXSS_Korean_Localization/00_Project_Docs/Release_Packaging_Plan.md`
- GitHub 배포 절차: `HXSS_Korean_Localization/00_Project_Docs/GitHub_Release_Guide.md`

