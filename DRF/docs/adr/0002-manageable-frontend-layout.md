# ADR-0002: 관리 가능한 프론트엔드 레이아웃 구조

## Status

Proposed (2026-05-19, rev.2 — footer 고정 / 네이밍 통일 / 중복 토큰 정리 규칙 추가)

## Context

BOOTCAMP_HY는 페이지가 늘어나고 있다 (현재 brokers / accounts / community / interactions 4개 앱).
지금까지는 페이지를 만들 때마다 [templates/base.html](../../templates/base.html)에
**그 페이지의 CSS/JS link 태그를 직접 추가**해왔다.

이 방식의 문제는 다음과 같다:

1. **모든 페이지가 모든 CSS를 로드한다**
   로그인 페이지에서도 `dashboard.css`, `broker1_list.css`가 로드된다.
   페이지가 10개, 20개로 늘면 base.html은 거대해지고 CSS 규칙이 서로 충돌한다.

2. **base.css의 역할이 섞여 있다**
   [base.css:6-7](../../static/css/base.css#L6-L7)에서 `@import 'accounts/login.css'`처럼
   "전역 토큰"이어야 할 파일이 페이지별 CSS까지 끌어온다.

3. **inline `<script>`가 템플릿에 박혀 있다**
   [header.html:21-39](../../templates/header.html#L21-L39)의 `jwtLogout` 함수는
   캐시되지 않고, 보안 정책(CSP) 적용 시 깨지며, 단위 테스트도 어렵다.

4. **페이지별 분기 수단이 부족하다**
   "현재 페이지가 어떤 메뉴 영역인지" 표시하거나
   "이 페이지만 body 배경을 다르게" 같은 일을 할 통일된 방법이 없다.

5. **실제 발견된 중복/불일치 (현재 코드 기준, 2026-05-19)**
   - **단수/복수 불일치**: `static/js/account/` (단수) vs `templates/accounts/`, `static/css/accounts/` (복수) — 자동화·일괄 검색이 깨진다.
   - **토큰 중복 정의**: [base.css](../../static/css/base.css)는 `--navy-900`, `--slate-900` 등 정식 이름으로 정의하는데,
     [brokers_base.css](../../static/css/brokers/brokers_base.css)는 같은 색을 `--n900`, `--s600` 등 짧은 이름으로 또 정의한다.
     → **같은 색이 두 이름으로 존재.** 색을 바꿀 때 두 곳을 다 고쳐야 하고, 코드 리뷰 시 어느 토큰이 진짜인지 모른다.
   - **앱별 base CSS의 페이지 @import**: `brokers_base.css`가 `broker_detail.css`를 @import한다. 3계층 구조에 "앱별 base"라는 중간 계층은 존재하지 않는다.
   - **interactions 앱의 CSS 부재**: `interactions/` 템플릿 3개는 있는데 `static/css/interactions/`는 없다. 인라인 스타일 또는 다른 곳에 묻어 있을 가능성 → 추적 어려움.

이 구조를 그대로 두면 **"코드 1줄 고치면 다른 페이지가 깨진다"**는 상태가 된다.
초기 단계인 지금이 정리하기 가장 좋은 시점이다.


## Decision

프론트엔드 자산(템플릿/CSS/JS)을 **3계층 구조**로 명확히 나눈다.

### 1) 계층 정의

| 계층 | 역할 | 위치 | 누가 로드? |
|---|---|---|---|
| **Global (전역)** | 디자인 토큰, 폰트, body 리셋, 모든 페이지 공통 요소 | `static/css/base.css`<br>`static/js/common/*.js` | base.html이 **항상** 로드 |
| **Layout (레이아웃)** | 헤더/푸터/네비게이션 | `static/css/header.css`<br>`static/css/footer.css` | base.html이 **항상** 로드 |
| **Page (페이지별)** | 그 페이지에서만 쓰는 스타일/스크립트 | `static/css/<app>/<page>.css`<br>`static/js/<app>/<page>.js` | **해당 페이지 템플릿**이 로드 |

핵심 규칙:
- **base.html은 Global + Layout만 로드한다. 페이지별 자산은 절대 base.html에 적지 않는다.**
- 페이지 템플릿은 `{% block extra_css %}` / `{% block extra_js %}` 안에서 **자기 것만** 로드한다.
- **3계층 외의 중간 계층은 만들지 않는다.** 예: `brokers_base.css`처럼 "앱별 base" 파일 금지.
  앱 단위로 공통이 필요해 보이면 → 그건 사실 **전역(Global)** 으로 승격하거나, **재사용 가능한 컴포넌트 클래스**로 base.css에 추가한다.

### 1-A) Header / Footer 고정 규칙

- `{% include 'header.html' %}` 와 `{% include 'footer.html' %}` 는 [base.html](../../templates/base.html)에 **고정**한다.
- 페이지 템플릿에서 header/footer를 **끄거나, 빼거나, 다른 것으로 교체할 수 없다.**
- 페이지 템플릿은 오직 `{% block content %}` 안만 채운다. 그 외 영역(header/footer)은 base.html의 책임.
- 이유: 모든 페이지에서 동일한 네비게이션과 푸터를 보장 → 사용자 경험 일관성, 유지보수 비용 절감.
- 예외가 필요해 보이면 → ADR을 새로 써서 정당화 후 합의. 임의로 빼지 않는다.

### 2) base.html 블록 설계

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <title>{% block title %}부동산신뢰{% endblock %}</title>

  <!-- 외부 CDN (Bootstrap, Fonts) -->
  <!-- Global + Layout CSS (항상 로드) -->
  <link rel="stylesheet" href="{% static 'css/base.css' %}">
  <link rel="stylesheet" href="{% static 'css/header.css' %}">
  <link rel="stylesheet" href="{% static 'css/footer.css' %}">

  {% block extra_css %}{% endblock %}   {# ← 페이지별 CSS만 #}
</head>
<body class="{% block body_class %}{% endblock %}">

  {% include 'header.html' %}

  <main class="container mt-4">
    {% block content %}{% endblock %}
  </main>

  {% include 'footer.html' %}

  <!-- Global JS (axios, common/auth.js 등) -->
  <script src="{% static 'js/common/auth.js' %}"></script>

  {% block extra_js %}{% endblock %}   {# ← 페이지별 JS만 #}
</body>
</html>
```

추가되는 블록:
- `{% block body_class %}` — 페이지별 body 클래스 (예: `page-login`, `page-dashboard`)
- `{% block nav_active %}` — 현재 활성 메뉴 표시용 (header.html에서 사용)

### 3) base.css의 역할 제한

base.css에는 **이 3가지만** 둔다:
1. **디자인 토큰** (`:root` 안 CSS 변수)
2. **body, html 기본 reset**
3. **모든 페이지에서 쓰는 진짜 공통 컴포넌트** (예: `.section-card`, `.back-btn`)

`@import 'accounts/login.css'` 같은 페이지 CSS 끌어오기는 **전부 제거**한다.

### 4) JS 모듈 위치 규칙

```
static/js/
├── common/          ← 모든 페이지 공통 (auth, axios 설정, 유틸)
│   └── auth.js     ← jwtLogout 등 인증 관련
├── brokers/         ← brokers 앱 페이지 전용
├── accounts/        ← accounts 앱 페이지 전용
└── ...
```

header.html의 inline `<script>`는 [static/js/common/auth.js](../../static/js/common/auth.js)로 추출한다.

### 5) 네이밍 규칙

| 종류 | 규칙 | 예시 |
|---|---|---|
| 앱 폴더 이름 | **Django 앱 이름과 정확히 동일 (복수형)** | `accounts/`, `brokers/`, `community/`, `interactions/` |
| 템플릿 파일 | `<app>/<page>.html` | `brokers/broker_detail.html` |
| CSS 파일 | `<app>/<page>.css` (템플릿과 동일 이름) | `brokers/broker_detail.css` |
| JS 파일 | `<app>/<page>.js` (템플릿과 동일 이름) | `brokers/broker_detail.js` |
| body 클래스 | `page-<page>` (kebab-case) | `page-broker-detail` |
| CSS 클래스 (페이지 전용) | `<page>-<요소>` 접두어 | `.detail-hero`, `.detail-grid` |
| 파일 이름 케이스 | **snake_case** (Django 관습) | `broker_detail.html`, `pocket_menu.css` |

**원칙 1: 템플릿 = CSS = JS = body 클래스 이름이 1:1:1:1로 매칭된다.**

**원칙 2: 앱 폴더 이름은 Django settings의 `INSTALLED_APPS`에 등록된 이름을 그대로 사용한다.**
→ `accounts` 앱이라면 `templates/accounts/`, `static/css/accounts/`, `static/js/accounts/` **모두 복수 `accounts`** 로 통일.
   `static/js/account/`(단수)처럼 한 글자라도 다르면 즉시 수정한다.

### 6) 중복 토큰 / 중복 변수 금지

- **모든 디자인 토큰은 [base.css](../../static/css/base.css)의 `:root`에만 정의한다.**
- 다른 CSS 파일에서 `:root { --xxx: ... }` 추가 금지.
- 같은 색을 다른 이름으로 또 정의 금지 (예: `--navy-900` 과 `--n900` 동시 존재 → 둘 중 정식 이름만 남기고 통일).
- 페이지 CSS는 **토큰을 정의하지 않고, 참조만 한다** (`color: var(--navy-900);`).
- 토큰 이름 케이스: **kebab-case** (예: `--navy-900`, `--text-primary`). 줄임 이름(`--n9`) 금지 → 의미 없는 줄임은 가독성을 해친다.


## Consequences

### 좋은 점
- **새 페이지 추가 작업이 단순해진다**:
  템플릿 1개 + CSS 1개 + JS 1개를 같은 이름으로 만들고, base.html은 건드리지 않는다.
- **충돌 위험이 줄어든다**:
  로그인 페이지에 dashboard CSS가 안 들어가므로 셀렉터 충돌 없음.
- **로딩 속도가 빨라진다**:
  페이지마다 필요한 CSS/JS만 로드.
- **디버깅이 쉬워진다**:
  "이 페이지 스타일이 이상해" → 같은 이름의 CSS 파일 하나만 보면 됨.
- **AI 도구(Claude 포함)가 더 정확히 작업한다**:
  네이밍 규칙이 명확하면 "broker_detail 페이지에 X 추가해줘" 한 줄로 모든 파일을 찾을 수 있음.

### 나쁜 점 / 주의할 점
- **마이그레이션 비용이 든다**:
  기존 [base.html](../../templates/base.html)의 페이지별 link를 각 페이지 템플릿으로 옮기는 작업이 필요.
  → 단계별로 진행 (Migration Path 참고).
- **"이건 전역인가 페이지별인가?" 판단이 필요**:
  애매하면 일단 **페이지별로 두고**, 두 번째 페이지에서 똑같은 스타일이 필요할 때 base.css로 승격하는 규칙.
- **block 이름을 외워야 한다**:
  `extra_css`, `extra_js`, `body_class`, `nav_active` 4개 — README나 CLAUDE.md에 기록.


## Migration Path (적용 순서)

기존 코드를 한 번에 다 고치지 않는다. **단계별로 화면 깨지는지 확인하며 진행**한다.

| 단계 | 작업 | 변경 파일 | 검증 방법 |
|---|---|---|---|
| 1 | base.html에서 페이지별 CSS/JS link 제거, 각 페이지 템플릿으로 이동 | base.html + 모든 페이지 템플릿 | 각 페이지 열어보기 |
| 2 | base.css의 `@import` 제거 | base.css | 로그인/회원가입 페이지 확인 |
| 3 | `{% block body_class %}`, `{% block nav_active %}` 추가 | base.html, header.html | 메뉴 활성화 확인 |
| 4 | header.html의 inline JS → `static/js/common/auth.js` 분리 | header.html + 새 js 파일 | 로그아웃 동작 확인 |
| 5 | **`static/js/account/` → `static/js/accounts/` 폴더 이름 통일** | js 폴더 rename + 참조 경로 수정 | 로그인/회원가입 JS 동작 확인 |
| 6 | **`brokers_base.css` 제거** — 그 안의 토큰은 base.css와 중복이므로 삭제, 페이지 CSS에서 `--n900` 등 짧은 이름 → `--navy-900` 정식 이름으로 일괄 치환 | brokers_base.css 삭제 + brokers/*.css 일괄 수정 | brokers 모든 페이지 색상 확인 |
| 7 | **`interactions/` 인라인 스타일을 `static/css/interactions/<page>.css`로 분리** | interactions 템플릿 3개 + 새 CSS 3개 | review 페이지 동작 확인 |


## 신규 파일 추가 시 검증 체크리스트

새 페이지/파일을 만들거나 기존 파일을 수정할 때 아래를 점검한다:

- [ ] 앱 폴더 이름이 Django `INSTALLED_APPS`와 **정확히** 일치하는가? (단수/복수 확인)
- [ ] 파일 이름이 **snake_case** 인가?
- [ ] 템플릿/CSS/JS 이름이 **동일**한가? (`broker_detail.html` ↔ `broker_detail.css` ↔ `broker_detail.js`)
- [ ] body 클래스를 `page-<page>` 형식으로 추가했는가?
- [ ] base.html을 수정했는가? → **수정했다면 잘못된 것.** 페이지 자산은 페이지 템플릿에서만 link.
- [ ] CSS 파일 안에 `:root { --xxx }` 가 있는가? → **있다면 잘못된 것.** 토큰은 base.css에만.
- [ ] 같은 스타일을 다른 페이지에서도 쓰고 있는가? → 그렇다면 base.css의 공통 컴포넌트로 승격 검토.
- [ ] header/footer를 페이지에서 제거하거나 교체하려고 했는가? → **금지.** base.html이 항상 포함.


## 일 적용 워크플로우 (앞으로 새 페이지 만들 때)

새 페이지 `community/post_detail` 페이지를 추가한다고 가정:

```
1. templates/community/post_detail.html 생성
   ↓ base.html 상속, {% block extra_css %}에 자기 CSS 1줄만 추가
2. static/css/community/post_detail.css 생성
   ↓ base.css의 토큰(--navy-500 등) 활용
3. static/js/community/post_detail.js 생성 (필요 시)
4. urls.py / views.py 연결
```

**base.html은 절대 건드리지 않는다.** 이 규칙 하나만 지키면 페이지가 100개가 되어도 관리 가능하다.
