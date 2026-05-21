"""Sentiment 비동기 task.

원칙:
- task 는 services.analyze_review() 를 감싸기만 (DRY — 로직 중복 X)
- 인자는 Review 인스턴스 X → review_id O (직렬화 가능한 PK만)
- FastAPI 일시 다운 등 외부 의존 실패 시 자동 재시도

호출:
    signals.py 에서 analyze_review_task.delay(review.id) 형태로 호출됨.

흐름:
    [Review 저장] → signals → .delay() → [Redis 큐]
        → [Worker가 꺼냄] → analyze_review_task(review_id)
        → Review 조회 → services.analyze_review() → SentimentResult 저장
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,                      # self 인자 받기 (재시도/요청 정보 접근용)
    autoretry_for=(Exception,),     # 예외 시 자동 재시도 (FastAPI 일시 다운 등)
    retry_backoff=True,             # 1s → 2s → 4s 점점 늘림 (지수 백오프)
    retry_backoff_max=30,           # 최대 30초까지만 늘림
    retry_jitter=True,              # 같은 시각 폭주 방지 (랜덤 가산)
    retry_kwargs={"max_retries": 3},
)
def analyze_review_task(self, review_id: int):
    """Review 한 건을 비동기로 감정분석.

    Args:
        review_id: interactions.Review 의 PK
                   (인스턴스 X — JSON 직렬화 불가)

    Returns:
        SentimentResult.id (성공 시) 또는 None (Review 없음/실패)
    """
    # 늦은 import — 앱 로딩 순서/순환 의존 방지
    from interactions.models import Review

    from .services import analyze_review

    try:
        review = Review.objects.get(pk=review_id)
    except Review.DoesNotExist:
        # 작업 등록 후 Review 가 삭제된 경우 — 재시도 의미 없음
        logger.warning("Review #%s 가 사라짐 (재시도 안 함)", review_id)
        return None

    logger.info("[Celery] Review #%s 감정분석 시작", review_id)
    result = analyze_review(review)

    if result is None:
        logger.error("[Celery] Review #%s 분석 실패 (result=None)", review_id)
        return None

    logger.info(
        "[Celery] Review #%s 분석 완료: %s (score=%.2f)",
        review_id, result.label, result.score,
    )
    return result.id