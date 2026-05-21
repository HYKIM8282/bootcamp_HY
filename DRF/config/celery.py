"""Celery 앱 정의 — Django ↔ Celery 연결의 진입점.

역할:
- Django settings 모듈을 알려주고
- settings.py 의 CELERY_* 변수를 Celery 설정으로 읽어오고
- 각 앱의 tasks.py 를 자동으로 찾는다.

호출 흐름:
    worker 실행 → celery.py 로드 → settings.py 읽음 → @shared_task 등록

원칙: 이 파일은 "연결" 만 담당. 실제 task 로직은 각 앱의 tasks.py 에.
"""
import os

from celery import Celery

# 1) Django settings 위치를 환경변수로 등록
#    (manage.py 가 하는 것과 같은 일 — Celery 도 Django 설정을 알아야 함)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# 2) Celery 앱 인스턴스 생성
#    이름 "config" 은 메인 프로젝트 이름 (실행 시 -A config 와 일치해야 함)
app = Celery("config")

# 3) settings.py 에서 CELERY_ 로 시작하는 모든 변수를 Celery 설정으로 흡수
#    namespace="CELERY" → settings.CELERY_BROKER_URL 같은 것만 인식
app.config_from_object("django.conf:settings", namespace="CELERY")

# 4) INSTALLED_APPS 의 각 앱에서 tasks.py 를 자동 탐색 + 등록
#    (sentiment/tasks.py 의 @shared_task 자동 발견)
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """동작 확인용 더미 task. shell 에서 debug_task.delay() 로 호출."""
    print(f"Request: {self.request!r}")
