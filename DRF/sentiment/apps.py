from django.apps import AppConfig


class SentimentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sentiment"
    verbose_name = "감정분석"

    def ready(self):
        """앱 로드 완료 시 시그널 연결 (Review.post_save 자동 분석)."""
        from . import signals  # noqa: F401
