# 명령어 치트시트 — BOOTCAMP_HY

자주 헷갈리는 명령어를 "언제 쓰는지" 기준으로 정리.

---

## 🐍 1. 가상환경 (venv)

가상환경 = 프로젝트별 파이썬 패키지 격리 공간.

| 상황 | 명령어 |
|---|---|
| 가상환경 활성화 | `source .venv/bin/activate` |
| 활성화 확인 | `which python` (`.venv` 가 보이면 OK) |
| 패키지 설치 | `pip install celery redis` |
| 설치된 패키지 보기 | `pip list` |
| requirements.txt 한 번에 설치 | `pip install -r requirements.txt` |
| 가상환경 끄기 | `deactivate` |

> **트러블슈팅**: 활성화 안 됐는데 `pip install` 하면 시스템 파이썬에 깔림 → 항상 `(.venv)` 확인.
> 안 되면 절대경로로: `.venv/bin/pip install ...`

---

## 🐙 2. Git (로컬)

Git = 코드 변경사항을 시간순으로 기록.

### 상태 확인
| 상황 | 명령어 |
|---|---|
| 뭐가 바뀌었나? | `git status` |
| 짧게 보기 | `git status --short` |
| 실제 변경 내용 | `git diff` |
| 변경 통계만 | `git diff --stat` |
| 커밋 이력 | `git log --oneline -5` |
| 현재 브랜치 | `git branch --show-current` |

### 커밋 만들기 (3단계)
```bash
git add 파일이름.py              # 1. staging
git commit -m "feat: ..."        # 2. 커밋
git push origin main             # 3. GitHub로
```

### 되돌리기
| 상황 | 명령어 |
|---|---|
| add 취소 | `git reset HEAD 파일이름` |
| 변경 자체를 버림 ⚠️ | `git restore 파일이름` |

### 브랜치
| 상황 | 명령어 |
|---|---|
| 새 브랜치 만들고 이동 | `git checkout -b feat/celery-비동기` |
| 브랜치 이동 | `git checkout main` |
| 브랜치 목록 | `git branch` |

---

## ☁️ 3. GitHub (원격)

| 상황 | 명령어 |
|---|---|
| 내 커밋을 GitHub로 | `git push origin main` |
| GitHub에서 최신 가져오기 | `git pull origin main` |
| 원격 주소 확인 | `git remote -v` |
| 푸시됐는지 확인 (비어 있으면 OK) | `git log origin/main..HEAD` |

> **헷갈림 정리**: `commit` = 내 컴퓨터 저장 / `push` = GitHub 업로드.

---

## 🐳 4. Docker

Docker = 프로그램을 격리 상자(컨테이너)에 담아 실행 (Redis 등).

| 상황 | 명령어 |
|---|---|
| 컨테이너 백그라운드 실행 | `docker compose up -d redis` |
| 상태 보기 | `docker compose ps` |
| 로그 실시간 보기 | `docker compose logs -f redis` |
| 컨테이너 안에서 명령 실행 | `docker exec -it bootcamp_redis redis-cli ping` |
| 멈추기 | `docker compose down` |
| 멈추고 데이터까지 삭제 ⚠️ | `docker compose down -v` |

> **`-d`** = detached (백그라운드) / **`-it`** = 컨테이너 안 대화형 셸

---

## 🎯 5. Django (manage.py)

| 상황 | 명령어 |
|---|---|
| 개발 서버 실행 | `python manage.py runserver` |
| 마이그레이션 생성 | `python manage.py makemigrations` |
| DB에 적용 | `python manage.py migrate` |
| 관리자 계정 만들기 | `python manage.py createsuperuser` |
| Django 쉘 | `python manage.py shell` |
| 설정 점검 | `python manage.py check` |

---

## ⚡ 6. Celery

| 상황 | 명령어 |
|---|---|
| Worker 실행 | `celery -A config worker -l info` |
| Worker 종료 | Ctrl+C |
| Django shell 에서 task 호출 | `analyze_review_task.delay(review_id)` |

> **`-A config`** = config/celery.py 가 진입점 / **`-l info`** = 로그 레벨

---

## 🗂️ 7. 옵시디언 vault

vault 는 **별도 Git 저장소** (`my-vault`) — bootcamp_HY 와 분리.

```bash
cd /mnt/d/obsidian_claude/my_vault
git status
git add .
git commit -m "vault backup 2026-05-21"
git push origin main
```

> **편의 스킬**: `/sync` 호출 시 bootcamp_HY + vault 양쪽 동시 백업.

---

## 🌳 자주 쓰는 흐름 (시나리오별)

### 시나리오 A. 작업 시작
```bash
source .venv/bin/activate         # ① 가상환경
docker compose up -d redis        # ② Redis
python manage.py runserver        # ③ Django
# 다른 터미널에서:
celery -A config worker -l info   # ④ Celery worker
```

### 시나리오 B. 작업 후 백업
```bash
git status                        # ① 뭐 바뀌었나
git add 바뀐파일                   # ② staging
git commit -m "feat: ..."         # ③ 커밋
git push origin main              # ④ GitHub
# 옵시디언도 정리했다면:
/sync                             # ⑤ vault 백업 (스킬)
```

### 시나리오 C. 다음날 작업 재개
```bash
git pull origin main              # ① 변경분 받기
source .venv/bin/activate         # ② 가상환경
pip install -r requirements.txt   # ③ 새 패키지 동기화
docker compose up -d redis        # ④ Redis 다시 띄우기
```

---

## 🆘 자주 헷갈리는 3가지

### ❓ "방금 작업한 게 GitHub에 올라갔나?"
```bash
git log origin/main..HEAD --oneline
```
**비어 있으면** = 푸시 완료.

### ❓ "가상환경이 켜져 있나?"
```bash
which python
```
경로에 `.venv` 가 보이면 OK.

### ❓ "Redis 가 떠 있나?"
```bash
docker compose ps
```
`STATUS` 가 `Up (healthy)` 이면 OK.

---

## 🔗 관련 문서
- [docs/principles.md](principles.md) — 신뢰 7원칙
- [docs/dry_guide.md](dry_guide.md) — DRY 가이드
- [docs/adr/](adr/) — 아키텍처 결정 기록
