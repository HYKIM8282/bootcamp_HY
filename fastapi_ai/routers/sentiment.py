"""감정분석 라우터.

원칙: Thin router. URL 받기 + service 호출만.
- 비즈니스 로직 X (services/sentiment_service.py 로 위임)
- DB 직접 접근 X
"""
from fastapi import APIRouter

router = APIRouter(prefix="/sentiment", tags=["sentiment"])

# 3단계에서 추가 예정:
# @router.post("/analyze")
# def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
#     return sentiment_service.analyze_text(req)
