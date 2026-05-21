"""Django 시작 시 Celery 앱 자동 로드.

celery_app 을 여기서 임포트하면 Django 가 뜰 때 자동으로 Celery 앱이 초기화됨.
→ @shared_task 가 이 앱을 기본 앱으로 인식.
"""
from .celery import app as celery_app

__all__ = ("celery_app",)
