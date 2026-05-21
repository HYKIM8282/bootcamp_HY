"""감정분석 라우터.

원칙: Thin router. URL 받기 + service 호출만.
- 비즈니스 로직 X (services/sentiment_service.py 로 위임)
- DB 직접 접근 X
"""
from fastapi import APIRouter

from schemas.sentiment import AnalyzeRequest, AnalyzeResponse
from services import sentiment_service

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """텍스트 + 별점 → 감정 분석 결과."""
    return sentiment_service.analyze_text(req)
