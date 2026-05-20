# KR-FinBert-SC FastAPI 테스트

한국어 금융 감정분석 모델 [`snunlp/KR-FinBert-SC`](https://huggingface.co/snunlp/KR-FinBert-SC) 을
FastAPI 서버로 띄워서 직접 테스트해보는 미니 프로젝트.

- **모델 입력**: 한국어 문장 (뉴스, 공시, 리포트 같은 금융 텍스트에 강함)
- **모델 출력**: `positive` / `neutral` / `negative` 3개 라벨 중 하나 + 각 라벨의 확률값

---

## 폴더 구조

```
FastAPI/
├── venv/               # 가상환경 (이 폴더 안에서만 라이브러리 격리)
├── main.py             # FastAPI 서버 + 모델 로드 + 엔드포인트
├── test_request.py     # 서버에 테스트 요청 보내는 스크립트
├── requirements.txt    # 설치할 파이썬 라이브러리 목록
└── README.md           # 지금 보고있는 파일
```

---

## 실행 순서

### 1) 가상환경 활성화

(가상환경은 자동 설치 스크립트로 이미 만들어 둠. 비어있다면 `python3 -m venv venv` 로 직접 생성.)

```bash
cd FastAPI
source venv/bin/activate
```

활성화되면 프롬프트 앞에 `(venv)` 가 붙는다.

### 2) (최초 1회만) 라이브러리 설치

```bash
pip install -r requirements.txt
```

> ⚠️ PyTorch가 약 700MB 정도라 설치에 5~15분 걸릴 수 있다. 인터넷이 느리면 더.

### 3) FastAPI 서버 실행

```bash
uvicorn main:app --reload
```

- `main` = `main.py` 파일
- `app` = 그 파일 안의 `app = FastAPI(...)` 변수
- `--reload` = 코드 수정 시 자동 재시작 (개발용)

서버가 켜지면서 모델을 자동 다운로드한다 (최초 1회만, 약 450MB).
다운받은 모델은 `~/.cache/huggingface/` 에 저장되어 두 번째 실행부터는 즉시 로딩.

### 4) 테스트

**방법 A — Swagger UI (브라우저)**
브라우저에서 http://127.0.0.1:8000/docs 접속
→ `POST /analyze` 클릭 → `Try it out` → 문장 입력 → `Execute`

**방법 B — 파이썬 스크립트**
새 터미널을 하나 더 열고:
```bash
cd FastAPI
source venv/bin/activate
python test_request.py
```
6개 샘플 문장에 대한 감정분석 결과를 출력함.

**방법 C — curl**
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "삼성전자가 사상 최대 실적을 달성했다."}'
```

---

## 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET  | `/`               | 모델 정보, 라벨 목록 |
| POST | `/analyze`        | 문장 1개 감정분석 |
| POST | `/analyze/batch`  | 문장 여러 개(최대 32) 한 번에 분석 |
| GET  | `/docs`           | Swagger UI (인터랙티브 테스트) |

### 응답 예시

```json
{
  "success": true,
  "data": {
    "text": "삼성전자가 사상 최대 실적을 달성했다.",
    "label": "positive",
    "score": 0.9712,
    "all_scores": {
      "negative": 0.0118,
      "neutral":  0.0170,
      "positive": 0.9712
    }
  }
}
```

---

## 자주 만나는 문제

| 증상 | 원인/해결 |
|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | venv 활성화 안 됨. `source venv/bin/activate` 다시 실행 |
| 서버 시작 시 모델 다운로드가 멈춤 | 네트워크 문제. 잠시 후 재시도 |
| `[ERROR] 서버에 연결할 수 없습니다` (test_request) | 서버를 켜지 않은 상태. 먼저 `uvicorn main:app --reload` 실행 |
| 첫 요청이 5~10초 걸림 | 모델이 메모리에 로딩되는 시간. 두 번째 요청부터는 빠름 |
