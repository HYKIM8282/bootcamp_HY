"""sentiment 앱 서비스 레이어 — FastAPI 호출 + 응답 저장.

역할: FastAPI 호출 + 응답 검증 + DB 저장 + 에러 처리를 한 곳에 모음.

원칙:
- DRY: 같은 호출 로직이 signal/view/배치 등 여러 곳에서 재사용
- 외부 의존(FastAPI)이 실패해도 Review 자체는 안 깨지도록 try/except
- 실패도 흔적 남김 ('error' 라벨 SentimentResult 저장)
"""
import logging
from typing import Optional

import httpx
from django.conf import settings

from .models import SentimentResult
from .serializers import SentimentRequestSerializer, SentimentResultSerializer

logger = logging.getLogger(__name__)


def analyze_review(review) -> Optional[SentimentResult]:
    """Review 한 건을 FastAPI로 보내 분석 → SentimentResult 저장 → 반환.

    실패 시:
    - 'error' 라벨로 SentimentResult 저장 (실패도 흔적 남김 — 추적 가능)
    - 호출자에게는 그 SentimentResult 인스턴스를 그대로 반환

    Args:
        review: Review 인스턴스

    Returns:
        SentimentResult 인스턴스 (성공/실패 모두)
    """
    payload = dict(SentimentRequestSerializer(review).data)

    try:
        response = httpx.post(
            f"{settings.FASTAPI_URL}/sentiment/analyze",
            json=payload,
            timeout=settings.FASTAPI_TIMEOUT,
        )
        response.raise_for_status()  # 4xx/5xx 면 raise
        result_data = response.json()

    except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
        logger.error("FastAPI 호출 실패 (Review #%s): %s", review.id, e)
        return _save_error_result(review, str(e))

    serializer = SentimentResultSerializer(data=result_data)
    if not serializer.is_valid():
        logger.error(
            "FastAPI 응답 검증 실패 (Review #%s): %s", review.id, serializer.errors
        )
        return _save_error_result(
            review, f"Invalid response: {dict(serializer.errors)}"
        )

    return serializer.save(
        target=review,
        method="ai",
        raw_response=result_data,
    )


def _save_error_result(review, error_msg: str) -> SentimentResult:
    """분석 실패 흔적을 SentimentResult에 'error' 라벨로 저장.

    실패도 row 남기는 이유:
    - "왜 이 리뷰만 점수 없지?" 디버깅 가능
    - 향후 재시도 큐(needs_review=True) 로직 연동 가능
    """
    return SentimentResult.objects.create(
        target=review,
        method="ai",
        score=0.0,
        label="error",
        ai_probability=None,
        model_version="",
        raw_response={"error": error_msg},
    )
