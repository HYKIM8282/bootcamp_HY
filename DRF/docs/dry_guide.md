# DRY 가이드 — "끌어당기기" 원칙

> BOOTCAMP_HY 프로젝트의 핵심 설계 원칙.
> AI 데이터 추가 시 충돌 없는 깔끔한 구조 유지가 1순위 목표.

---

## 💡 DRY 한 줄 정의

> **DRY = Don't Repeat Yourself = "똑같은 코드 두 번 쓰지 마라"**

같은 코드가 여러 곳에 흩어져 있으면 → 바꿀 때 다 찾아다녀야 함 → 하나 빼먹으면 버그.
**한 곳에 한 번만** 두고, 필요한 곳에서 "끌어당겨서" 쓴다.

---

## 🚨 이 프로젝트에서 실제로 일어날 수 있는 상황

### ❌ 나쁜 예 (DRY 위반 — 복붙)

```python
# community/models.py
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # ← 반복
    updated_at = models.DateTimeField(auto_now=True)      # ← 반복
    is_deleted = models.BooleanField(default=False)       # ← 반복

class Review(models.Model):
    rating = models.IntegerField()
    comment = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # ← 또 반복
    updated_at = models.DateTimeField(auto_now=True)      # ← 또 반복
    is_deleted = models.BooleanField(default=False)       # ← 또 반복

# brokers/models.py
class Broker(models.Model):
    name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)  # ← 또또 반복
    updated_at = models.DateTimeField(auto_now=True)      # ← 또또 반복
    is_deleted = models.BooleanField(default=False)       # ← 또또 반복
```

**문제:**
- 같은 줄이 3번 반복
- 나중에 `created_at`을 `created_time`으로 바꾸고 싶으면 → 3군데 다 고쳐야 함
- AI 학습 데이터 추가하다가 새 모델 또 만들면 → 또 복붙해야 함

### ✅ 좋은 예 (DRY 적용 — 끌어당기기)

**Step 1: 공통 위치에 "추상 모델" 만들기**

```python
# config/models.py  ← 새로 만드는 공통 파일
# ─────────────────────────────────────────────────────
# TimeStampedModel: 생성/수정 시각을 공통으로 관리하는 추상 모델
# ─────────────────────────────────────────────────────
# 역할: 모든 모델이 상속받아 created_at, updated_at 자동 부여
# 영향: 이걸 바꾸면 상속받는 모든 모델 영향
# 주의: abstract = True 라서 직접 테이블 안 만들어짐
# ─────────────────────────────────────────────────────
from django.db import models

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True   # ← 이게 핵심. "테이블은 안 만들고 상속용으로만"


class AuthoredModel(TimeStampedModel):
    """작성자가 있는 모델용. TimeStampedModel도 같이 가져옴"""
    author = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='+',
    )

    class Meta:
        abstract = True
```

**Step 2: 각 앱에서 끌어당겨 쓰기**

```python
# community/models.py
from config.models import AuthoredModel   # ← 끌어당기기!

class Post(AuthoredModel):       # ← 상속만 받으면 끝
    title = models.CharField(max_length=200)
    content = models.TextField()
    # author, created_at, updated_at, is_deleted 자동으로 생김

class Review(AuthoredModel):
    rating = models.IntegerField()
    comment = models.TextField()
```

```python
# brokers/models.py
from config.models import TimeStampedModel

class Broker(TimeStampedModel):
    name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
```

**효과:**
- 반복되던 6줄 → 1번만 정의
- `created_at`을 바꾸고 싶으면 → `config/models.py` **한 곳만** 수정
- 새 모델 만들 때 → `class 새모델(AuthoredModel):` 한 줄이면 끝

---

## 🎯 이 프로젝트에서 "끌어당기기" 할 수 있는 5가지

### 1. 공통 필드 — 추상 모델
- 위치: `config/models.py` 또는 `interactions/base_models.py`
- 대상: created_at, updated_at, is_deleted, author 등

### 2. 이미지 첨부 — **이미 끌어당기기 적용됨** ✅
```python
# interactions/models.py 에 Image 모델 하나만 있음
# Post, Review, Broker 모두 GFK 로 끌어당겨서 씀
# → 이게 바로 DRY 의 모범 사례
```

### 3. 페이지네이션 응답 포맷

**나쁜 예 — 각 view 마다 복붙:**
```python
return Response({"success": True, "data": serializer.data, "meta": {...}})
```

**좋은 예 — 공통 응답 함수:**
```python
# config/responses.py  ← 새로 만들기
def paginated_success(data, total, page=1):
    """CLAUDE.md 의 표준 응답 포맷"""
    return Response({
        "success": True,
        "data": data,
        "meta": {"total": total, "page": page}
    })

def error_response(code, message):
    return Response({
        "success": False,
        "error": {"code": code, "message": message}
    })

# 각 앱에서
from config.responses import paginated_success
return paginated_success(serializer.data, total=100, page=1)
```

### 4. 권한 체크

```python
# config/permissions.py
class IsAuthorOrReadOnly(permissions.BasePermission):
    """작성자 본인만 수정/삭제 가능, 나머지는 읽기만"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
```

### 5. 신뢰점수 계산 (이 프로젝트의 핵심 기능)

```python
# brokers/services.py  ← 비즈니스 로직 전용 파일
# ─────────────────────────────────────────────────────
# calculate_trust_score: 중개사 신뢰점수 계산 함수
# ─────────────────────────────────────────────────────
# 역할: 7개 규칙으로 신뢰점수 산출
# 영향: views.py, admin.py, serializers.py 어디서든 끌어다 씀
# 주의: 공식 변경 시 docs/trust_score_formula.md 도 같이 수정
# ─────────────────────────────────────────────────────
def calculate_trust_score(broker):
    score = 0
    # ... 7개 규칙 적용
    return score
```

---

## 🗂 "끌어당기기" 위치 선정 기준

| 코드 종류 | 어디에 둘까 | 예시 |
|---------|-----------|------|
| 모든 앱이 쓰는 공통 모델 | `config/models.py` | TimeStampedModel |
| 모든 앱이 쓰는 응답/유틸 | `config/utils.py`, `config/responses.py` | paginated_success |
| 모든 앱이 쓰는 권한 | `config/permissions.py` | IsAuthorOrReadOnly |
| **여러 모델에 붙는 부가기능** | `interactions/` | Image (GFK), Like, Bookmark |
| 한 앱 안에서만 반복되는 로직 | 해당 앱의 `services.py` | calculate_trust_score |
| 한 앱 안 여러 view 가 쓰는 헬퍼 | 해당 앱의 `utils.py` | format_phone_number |

---

## ⚠️ DRY 의 함정 — 너무 일찍 빼지 마라

**3번 미만 반복은 그냥 둬도 됨.**

- 2번 반복 → 그냥 둬도 됨
- 3번 이상 반복 → 그때 공통으로 끌어당기기

너무 일찍 추상화하면 오히려 코드가 복잡해진다. "복붙 2번 → 3번째 복붙하려는 순간" 이 적정 타이밍.

---

## 🔍 끌어당기기 점검 명령어

새 코드 짜기 전에 같은 코드 있는지 찾아보는 법:

```bash
# 같은 필드 패턴 찾기
grep -rn "created_at = models.DateTimeField" --include="*.py" .

# 같은 함수 이름 찾기
grep -rn "def calculate" --include="*.py" .

# 같은 응답 포맷 찾기
grep -rn '"success": True' --include="*.py" .
```

`/blueprint` 스킬이 5단계에서 이걸 자동으로 점검한다.

---

## 📌 꼭 기억할 3가지

1. **3번 반복되면** → 공통 위치로 끌어당기기
2. **공통 위치 1순위** → `config/` (전역) 또는 `interactions/` (여러 모델 부가기능)
3. **이미 끌어당겨진 게 있는지** 먼저 확인 — grep 하는 습관

→ 이 프로젝트의 `interactions/Image` 가 좋은 모범 사례. 다른 영역에도 똑같이 적용한다.
