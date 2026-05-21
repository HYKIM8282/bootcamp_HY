"""sentiment 앱 시그널.

Review 저장 시 자동으로 감정분석 트리거 (services.analyze_review 호출).

원칙:
- 분석 실패해도 Review 저장 자체는 영향 X (try/except 로 격리)
- created=True 일 때만 (수정은 재분석 안 함 — 정책)
- 함수 내부 import 로 앱 로딩 순서 보호 (sentiment.services → interactions.models)

성능 주의:
- 현재는 동기 호출 — Review 저장 응답이 FastAPI 추론 시간만큼 느려짐 (~0.5~2초)
- 향후 Celery 등으로 비동기 처리 가능 (별 단계)
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="interactions.Review")
def analyze_on_review_save(sender, instance, created, **kwargs):
    """Review 생성 시 자동 감정분석 (동기 호출).

    Args:
        sender: Review 모델 클래스
        instance: 저장된 Review 인스턴스
        created: True 면 신규 생성, False 면 수정
    """
    if not created:
        return  # 수정은 재분석 안 함

    # 늦은 import — 순환 의존·앱 로딩 순서 문제 방지
    from .services import analyze_review

    try:
        analyze_review(instance)
    except Exception as e:
        # 외부 의존 실패해도 Review 저장은 살리기 위해 swallow
        logger.error("자동 감정분석 실패 (Review #%s): %s", instance.id, e)
