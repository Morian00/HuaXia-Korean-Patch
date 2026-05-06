# HuaXia Warring States Korean Patch

비공식 유저 한글 패치 배포 및 작업 관리용 저장소입니다.

## 저장소 기준

- 실제 작업 루트: `HXSS_Korean_Localization/`
- 배포 방식: GitHub Releases의 Assets에 수동 설치 ZIP 업로드
- Git 커밋 대상: 문서, 번역 데이터, 패치 제작 도구, 플러그인 소스
- Git 커밋 제외 대상: 원본 게임 파일, 빌드된 EXE, 릴리즈 ZIP, 임시 산출물, 분석 도구, 캐시

## GitHub Desktop 사용 흐름

1. GitHub Desktop에서 이 폴더를 Existing Repository로 추가
2. 변경 목록에 원본 게임 파일이 보이지 않는지 확인
3. 문서, 번역 데이터, 패치 제작 도구, 플러그인 소스 변경만 커밋
4. GitHub에 Publish repository
5. GitHub 웹에서 Releases 생성
6. `HXSS_Korean_Localization/ReleasePackages/`의 수동 설치 ZIP 파일을 Release Assets에 업로드

## 배포 파일 관리

릴리즈 ZIP과 설치 EXE는 저장소에 커밋하지 않습니다.
현재 GitHub Releases 배포 기준에서는 설치 EXE를 사용하지 않습니다.
수동 설치 ZIP만 GitHub Releases의 Assets에 첨부합니다.

배포 전 확인 항목:

- 원본 게임 파일 미포함
- 수정된 게임 실행 파일 미포함
- 패치 버전 명시
- 대상 게임 버전 명시
- 설치/제거 방법 명시
- SHA-256 해시 제공

## 상세 문서

- 프로젝트 구조: `HXSS_Korean_Localization/README.md`
- 배포 패키징 계획: `HXSS_Korean_Localization/00_Project_Docs/Release_Packaging_Plan.md`
- GitHub 배포 절차: `HXSS_Korean_Localization/00_Project_Docs/GitHub_Release_Guide.md`
