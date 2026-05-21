"""FastAPI 진입점 — router 등록만 (얇게).

원칙: Thin router / Fat service.
- 이 파일에 비즈니스 로직 넣지 말 것
- routers/ 의 라우터를 include만 하는 곳

실행: uvicorn main:app --port 8001 --reload
"""
from fastapi import FastAPI

# 3단계에서 활성화 예정
# from routers import sentiment

app = FastAPI(title="bootcamp_HY AI Service")

# 3단계에서 활성화 예정
# app.include_router(sentiment.router)


@app.get("/")
def root():
    return {"message": "AI service is running", "status": "ok"}
