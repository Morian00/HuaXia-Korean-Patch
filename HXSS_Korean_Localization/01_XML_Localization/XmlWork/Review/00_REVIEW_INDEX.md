# Review Folder Index

## 최종 확인 대상

- `Current_Review_Summary.md`
  - 현재 적용 방식, 최신 패치 위치, 남은 확인 항목 요약.
- `../../../MaintenanceKit/input/Full_Translation.tsv`
  - 최종 번역 기준 파일.
- `Validation_Report.tsv`
  - 최신 구조 검증 결과.
- `Apply_Report.tsv`
  - XML 반영 결과.
- `Hardcoded_UI_Bundle_Replacement_Candidates.tsv`
  - Lua 언어 테이블 밖에 있는 하드코드 UI 후보.
- `Current_Remaining_CJK_Audit.tsv`
  - 배포 전 잔여 한자 확인용 최신 요약.

## 참고 파일

- `Archive_Raw/`
  - 초벌 번역 원문 보관.
- `Archive_Working_Audits_20260505_175900/`
  - 과거 검수 리포트와 일회성 스크립트 보관.
- `Archive_Legacy_Audits_20260504_1800/`
  - 이전 검수 산출물 보관.

## 적용 파일

- 플러그인 적용 Lua:
  - `../../../../../BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_language.lua`
  - `../../../../../BepInEx/plugins/HXSS.HuiWenFontReplacer/KoreanPatch/lua/game/config/t_taskLanguage.lua`
- 최신 생성 산출물:
  - `../Release/LuaConfig_KO_PluginPatch_20260505_173734`

## 현재 주의 사항

- 게임은 XML보다 Lua 언어 테이블을 우선 참조함.
- 현재 배포 방식은 원본 Lua 파일 직접 교체가 아니라 BepInEx 플러그인의 패치 Lua 우선 로드 방식.
- TSV 런타임 오버라이드는 폐기됨.
- 배포 전 플러그인 폴더에 trace/log/backup 파일이 남지 않았는지 확인 필요.
