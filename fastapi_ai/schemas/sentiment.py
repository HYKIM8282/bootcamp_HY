"""Pydantic 모델 — DRF Serializer와 짝.

설계 원칙:
- AnalyzeRequest: DRF SentimentRequestSerializer와 1:1 대응
- AnalyzeResponse: DRF SentimentResultSerializer와 1:1 대응
- 응답 모양 변경 시 양쪽 같이 수정 (계약/contract)
"""
from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    """DRF → FastAPI 분석 요청."""

    review_id: int = Field(..., description="Review ID (응답 매핑용)")
    text: str = Field(
        ..., min_length=1, max_length=2000, description="분석할 본문 (최대 2000자)"
    )
    star: int = Field(..., ge=1, le=5, description="별점 1~5")
    target_type: str = Field(default="review", description="대상 모델 타입")


class AnalyzeResponse(BaseModel):
    """FastAPI → DRF 분석 결과 (SentimentResult로 저장됨)."""

    # model_version 같이 model_* 필드를 쓰기 위해 보호 네임스페이스 해제
    model_config = ConfigDict(protected_namespaces=())

    score: float = Field(..., description="종합 점수 (-1 ~ +1)")
    label: str = Field(..., description="positive / neutral / negative")
    ai_probability: float = Field(..., ge=0.0, le=1.0, description="AI 긍정 확률")
    model_version: str = Field(..., description="분석에 쓴 모델 식별자 (추적용)")
