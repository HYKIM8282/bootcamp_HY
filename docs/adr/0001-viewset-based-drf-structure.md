# ADR-0001: ViewSet 기반 DRF 구조 채택

## Status

Accepted (2026-05-18)

## Context

## Context

BOOTCAMP_HY는 단순한 웹사이트가 아니라 **다양한 클라이언트**에서
동일한 데이터를 받아써야 하는 구조다.
현재는 웹 중심으로 개발하지만, 향후 모바일 앱(Android/iOS)과
Unity 기반 VR/실시간 임장 클라이언트, AI 분석 모듈 등의
확장이 예정되어 있다.
따라서 백엔드는 화면(HTML)을 그리는 게 아니라
**JSON 형태의 API**를 제공해야 한다.


Django REST Framework(DRF)에서 API를 만드는 방법은 크게 3가지다:

1. **APIView** — HTTP 메서드(GET/POST/PUT/DELETE)를 직접 하나씩 작성
2. **Generic View** — 자주 쓰는 패턴(목록/생성 등)을 일부 자동화
3. **ViewSet** — CRUD 5종(목록·생성·조회·수정·삭제)을 한 클래스로 자동 처리,
   Router와 결합하면 URL도 자동 생성

## Decision

**ViewSet + Router 조합**을 프로젝트의 기본 API 구조로 채택한다.

- 모델별로 `ModelViewSet`을 정의
- `DefaultRouter`로 URL 자동 등록
- 커스텀 동작이 필요한 경우에만 `@action` 데코레이터 추가

## Consequences

### 좋은 점
- CRUD 코드가 짧아져서 반복 작업이 줄어든다
- URL이 자동 생성돼서 라우팅 관리가 일관적이다
- 웹/Android/iOS 공용 JSON API라는 목표에 잘 맞는다

### 나쁜 점 / 주의할 점
- 커스텀 로직이 복잡해지면 ViewSet 안에서 메서드 오버라이드가
  많아져 가독성이 떨어질 수 있다
- ViewSet의 자동 동작을 잘 이해해야 디버깅이 쉬워진다
  (어떤 URL이 어떤 메서드로 연결되는지 등)
