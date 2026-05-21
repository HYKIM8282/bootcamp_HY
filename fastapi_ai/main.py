"""FastAPI 진입점 — router 등록 + 모델 1회 로드.

원칙: Thin router / Fat service.
- 비즈니스 로직 X (routers/, services/ 로 위임)
- 모델 로드만 여기서 (lifespan으로 앱 시작 시 1회)

실행: cd fastapi_ai && .venv/bin/uvicorn main:app --port 8001
Swagger: http://localhost:8001/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core import config
from routers import sentiment
from services import sentiment_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 호출.

    USE_DUMMY_ANALYZER=true 면 모델 안 로드 (빠른 개발 모드).
    아니면 앱 시작 시 모델 1회만 로드 → 매 요청 재로드 방지.
    """
    if not config.USE_DUMMY_ANALYZER:
        sentiment_service.load_model()
    yield
    # 종료 시 cleanup
    sentiment_service.ml_models.clear()


app = FastAPI(title="bootcamp_HY AI Service", lifespan=lifespan)

app.include_router(sentiment.router)


@app.get("/")
def root():
    return {
        "message": "AI service is running",
        "status": "ok",
        "dummy_mode": config.USE_DUMMY_ANALYZER,
    }
