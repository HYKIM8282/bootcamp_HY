# BOOTCAMP_HY 작업 지침

이 파일은 Claude가 매 대화마다 자동으로 읽는 프로젝트 규칙이다.

---

## 작업 원칙 (Claude가 코드를 다룰 때)

### 1. 한 번에 하나만
한 번에 한 파일, 한 가지 목적만 수정한다.
여러 파일이 필요하면 먼저 사용자에게 순서를 알린 뒤 차례로 진행한다.

### 2. 변경 전 한 줄 예고
파일을 수정하기 전에 "무엇을 / 왜"를 한 줄로 먼저 말한 후 수정한다.
예시: "community/views.py의 list_posts에 페이지네이션 추가. 이유: 게시글이 많아지면 한번에 다 불러오면 느려져서."

### 3. 변경 후 한 줄 요약
파일 수정 후에는 변경 내용을 1~2줄로 요약한다. 길게 쓰지 않는다.
예시: "수정 완료. list_posts에 ?page=1 쿼리 파라미터 추가, 페이지당 20개씩 반환."

### 4. 초보자 친화 설명
사용자는 초보 개발자다.
전문 용어는 처음 사용 시 1줄로 풀어서 설명한다.
모든 답변은 한국어로 작성한다.

### 5. 큰 작업은 계획 먼저
3개 이상의 파일을 수정하거나 새 기능을 추가하는 경우, 코드 작성 전에 계획만 먼저 제시하고 사용자 승인을 받은 뒤 진행한다.

---

## API 응답 표준 형식

모든 API 응답은 아래 구조를 따른다.

**성공:**
```json
{
  "success": true,
  "data": {...} 또는 [...],
  "meta": {
    "total": 100,
    "page": 1
  }
}
```

**실패:**
```json
{
  "success": false,
  "error": {
    "code": "BROKER_NOT_FOUND",
    "message": "해당 중개사를 찾을 수 없습니다"
  }
}
```

---

## 기술 스택 (변경 시 ADR 작성)

- Backend: Django + DRF (ViewSet 기반 — ADR-0001)
- Frontend: JavaScript + axios
- DB: SQLite (개발) / PostgreSQL (배포 예정)
- Maps: Kakao Maps SDK
- External APIs: V-World 외

기술 스택 변경 시 `docs/adr/` 에 새 ADR을 작성한다.
