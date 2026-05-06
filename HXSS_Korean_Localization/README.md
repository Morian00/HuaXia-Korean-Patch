# HXSS Korean Localization Project

이 폴더는 Huaxia: Warring States 한국어화 작업 관리용 루트 폴더다.

## 구조

- `00_Project_Docs/`: TASK, 워크플로우, AI 협업 가이드, 번역 톤 기준, 용어집.
- `01_XML_Localization/`: 과거 XML/Lua 산출물과 최신 패치 Lua 릴리스 보관.
- `02_Tools/`: 번역 추출, 검증, 병합용 스크립트.
- `03_Font_Work/`: 폰트 조사, 병합, 대체 작업 자료.
- `99_Cleanup_Archive/`: 과거 작업 보관.
- `MaintenanceKit/`: 업데이트 대응, 번역 병합, 패치 Lua 생성용 현역 도구.
- `Installer/`: 설치기 프로토타입 소스. 현재 GitHub Releases 배포 ZIP에는 설치기 실행 파일을 포함하지 않음.

## 현재 기준

완역 본작업의 기준 데이터는 `Full_Translation.tsv`이다.
최종 인게임 적용은 BepInEx 플러그인이 패치 Lua 파일을 원본 Lua 대신 우선 로드하는 방식으로 진행한다.

BepInEx 폴더 안에는 패치 Lua, 폰트 교체, 확정 하드코드 보정에 필요한 파일만 남긴다.
TSV 런타임 오버라이드는 사용하지 않는다.

## 배포 계획

배포 패키징 계획은 `00_Project_Docs/Release_Packaging_Plan.md`를 기준으로 한다.
GitHub Desktop과 GitHub Releases 배포 절차는 `00_Project_Docs/GitHub_Release_Guide.md`를 기준으로 한다.
현재 배포 기준 버전은 `v0.1.3`이다.
배포물은 `HXSS_KoreanPatch_v0.1.3_YYYYMMDD_HHMMSS.zip` 형식으로 생성한다.

최종 사용자는 ZIP 내부 파일을 게임 설치 폴더 최상위에 복사해 설치한다.
GitHub Releases 배포 기준에서는 단일 실행 설치기를 포함하지 않는다.

## 암호화 적용 기준

`hxss_Data/StreamingAssets/XmlConfig_Decrypted/Decrypted_README.md` 기준, 게임은 평문 XML을 직접 읽지 않는다.

최종 적용 흐름:

1. XmlConfig 복호화
2. 평문 XML의 `ko` 속성 수정
3. DES-CBC-PKCS7 방식으로 재암호화
4. 암호화된 파일을 게임이 읽는 위치에 배치

따라서 `WorkingXml`의 원본 XML 구조는 보존한다.
AI 번역 작업은 `SlimTranslationXml` 또는 `Review/Full_Translation.tsv`를 사용한다.
