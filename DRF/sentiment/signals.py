"""sentiment 앱 시그널.

Review 저장 시 자동으로 감정분석 task 를 Celery 큐에 등록.

원칙:
- 비동기 호출 — Review 저장 응답 즉시 반환 (블로킹 X)
- created=True 일 때만 (수정은 재분석 안 함 — 정책)
- transaction.on_commit() 으로 트랜잭션 커밋 후 큐 등록
  → worker 가 너무 빨라서 Review 조회 못 하는 race condition 방지

이전 버전 (동기 — 폐기):
- analyze_review(instance) 동기 호출
- Review 저장이 FastAPI 추론 0.5~2초만큼 느려짐
"""
import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="interactions.Review")
def analyze_on_review_save(sender, instance, created, **kwargs):
    """Review 생성 시 자동 감정분석 task 를 Celery 큐에 등록 (비동기).

    Args:
        sender: Review 모델 클래스 (문자열로 lazy 참조 — 순환 의존 방지)
        instance: 저장된 Review 인스턴스
        created: True 면 신규 생성, False 면 수정
    """
    if not created:
        return  # 수정은 재분석 안 함

    # 늦은 import — 앱 로딩 순서 보호
    from .tasks import analyze_review_task

    def enqueue():
        try:
            analyze_review_task.delay(instance.id)
            logger.info("Review #%s 감정분석 task 큐 등록", instance.id)
        except Exception as e:
            # Redis 다운 등 매우 드문 케이스 — Review 저장 자체는 살림
            logger.error(
                "자동 감정분석 task 등록 실패 (Review #%s): %s", instance.id, e
            )

    # 트랜잭션 커밋 후 큐 등록
    # → worker 가 즉시 Review 조회해도 DB 에 이미 있음 보장
    transaction.on_commit(enqueue)