# GitHub Releases 배포 절차

## 목적

GitHub Desktop과 GitHub Releases를 사용해 비공식 유저 한글 패치를 배포한다.
저장소에는 작업 파일과 문서만 커밋하고, 실제 배포 ZIP은 Release Assets로만 업로드한다.

## 권장 저장소 구조

- `README.md`: 저장소 첫 화면 안내
- `.gitignore`: 원본 게임 파일, 빌드 산출물, 임시 파일 제외
- `.gitattributes`: 텍스트 파일 줄바꿈 기준
- `HXSS_Korean_Localization/README.md`: 프로젝트 내부 구조 설명
- `HXSS_Korean_Localization/00_Project_Docs/`: 작업 문서, 배포 문서, 기준표
- `HXSS_Korean_Localization/01_XML_Localization/`: 번역 데이터와 XML 작업 자료
- `HXSS_Korean_Localization/02_Tools/`: 추출, 검증, 병합 도구
- `HXSS_Korean_Localization/03_Font_Work/`: 폰트 적용 관련 작업 자료
- `HXSS_Korean_Localization/MaintenanceKit/`: 업데이트 대응 및 패키징 보조 도구
- `HXSS_Korean_Localization/ReleasePackages/`: 로컬 배포 산출물 보관 위치

`Installer/` 폴더는 설치기 프로토타입 보관용이다.
현재 GitHub Releases 배포 ZIP에는 설치기 실행 파일을 포함하지 않는다.

## Git 커밋 대상

- 번역 원본 데이터
- 검수용 TSV, XML, Lua 작업 산출물
- 패키징 스크립트
- README, 설치 안내, 변경 내역
- 배포 체크리스트
- 플러그인 소스

## Git 커밋 제외 대상

- 원본 게임 실행 파일
- 원본 게임 DLL
- 원본 게임 리소스 파일
- 빌드된 설치 EXE
- 설치기 페이로드 ZIP
- 릴리즈 ZIP
- 임시 스테이징 폴더
- 캐시, 로그, 분석 도구
- 추출한 원본 폰트 파일

## GitHub Desktop 작업 순서

1. GitHub Desktop 실행
2. File > Add local repository 선택
3. 게임 설치 폴더 선택
4. Changes 탭 확인
5. 원본 게임 파일, EXE, DLL, ZIP이 변경 목록에 없는지 확인
6. Summary에 커밋 제목 입력
7. Commit to main 선택
8. Publish repository 선택
9. Public 저장소로 생성
10. GitHub 웹에서 Releases 메뉴 진입
11. Draft a new release 선택
12. Tag 입력
13. Release title 입력
14. Release notes 작성
15. ZIP 파일을 Assets에 업로드
16. Publish release 선택

## 릴리즈 태그 규칙

- 정식 배포: `v1.0.0`
- 수정 배포: `v1.0.1`
- 테스트 배포: `v0.2.0-beta`

현재 기준 버전이 `v0.1.3`이면 태그는 `v0.1.3` 사용 권장.

## 릴리즈 제목 예시

`HuaXia Warring States Korean Patch v0.1.3`

## 릴리즈 노트 예시

```md
## HuaXia Warring States Korean Patch v0.1.3

### 대상
- Steam판 HuaXia Warring States
- 지원 게임 버전: [확인 필요]

### 변경 내역
- 한국어 번역 적용
- UI 출력 보정
- GitHub Releases 수동 설치 ZIP 배포 기준 정리

### 설치 방법
1. 아래 Assets에서 ZIP 파일 다운로드
2. ZIP 압축 해제
3. Steam 라이브러리에서 게임 설치 폴더 열기
4. ZIP 내부 파일을 게임 설치 폴더 최상위에 복사
5. 같은 파일명이 있으면 덮어쓰기
6. 게임 실행

### 제거 방법
1. 게임 설치 폴더 열기
2. `BepInEx/plugins/HXSS.HuiWenFontReplacer/` 삭제
3. `BepInEx/config/hxss.huiwen-font-replacer.cfg` 삭제
4. 다른 BepInEx 플러그인을 사용하지 않는 경우에만 BepInEx 기반 파일 전체 삭제

### 주의
- 본 패치는 비공식 유저 한글 패치입니다.
- 원본 게임 파일은 포함하지 않습니다.
- 정품 Steam판 보유자를 대상으로 합니다.
- GitHub Releases 외부에서 재업로드된 파일은 검증하지 않습니다.

### 파일 검증
파일명: HXSS_KoreanPatch_v0.1.3_YYYYMMDD_HHMMSS.zip
SHA-256: [배포 시 입력]
```

## SHA-256 생성

PowerShell에서 릴리즈 ZIP이 있는 폴더로 이동 후 실행한다.

```powershell
Get-FileHash .\HXSS_KoreanPatch_v0.1.3_YYYYMMDD_HHMMSS.zip -Algorithm SHA256
```

출력된 해시값을 Release notes와 ZIP 내부 `SHA256.txt`에 기록한다.

## 배포 전 체크리스트

- GitHub Desktop Changes 목록에 원본 게임 파일 없음
- GitHub Desktop Changes 목록에 EXE, DLL, ZIP 없음
- 릴리즈 ZIP 내부에 원본 게임 실행 파일 없음
- 릴리즈 ZIP 내부에 수정된 원본 게임 실행 파일 없음
- 릴리즈 ZIP 내부에 설치 EXE 없음
- 설치 안내 포함
- 제거 안내 포함
- 대상 게임 버전 표기
- 패치 버전 표기
- SHA-256 해시 표기
- 공식 배포처가 GitHub Releases임을 명시

## 사용자 안내 문구

```text
본 파일은 비공식 유저 한글 패치입니다.
공식 배포처는 GitHub Releases 페이지입니다.
다운로드 출처와 파일명을 확인한 뒤 설치해 주세요.
```
