# ReleasePackages

로컬에서 생성한 배포 ZIP, 설치 EXE, 페이로드 ZIP, manifest 파일을 보관하는 폴더입니다.

이 폴더의 실제 배포 산출물은 Git에 커밋하지 않습니다.
GitHub Releases의 Assets에만 업로드합니다.

## 사용 규칙

- ZIP, EXE, DLL, manifest 산출물은 커밋 제외
- 최신 배포 파일은 GitHub Release 생성 시 Assets에 첨부
- 배포 후 Release notes에 파일명과 SHA-256 해시 기록

