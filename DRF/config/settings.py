from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


KAKAO_JS_KEY = os.getenv("KAKAO_JS_KEY")
VWORLD_API_KEY    = os.getenv("VWORLD_API_KEY", "")
BASE_URLS = os.getenv("BASE_URLS", "https://api.vworld.kr/ned/data/getEBOfficeInfo")
BASE_URLS2= os.getenv("BASE_URLS2", "https://api.vworld.kr/ned/data/getEBBfficeInfo")
VWORLD_TIMEOUT    = int(os.getenv("VWORLD_TIMEOUT", 10))
VWORLD_DOMAIN = os.getenv("VWORLD_DOMAIN", "localhost")

# ───────────────────────────────────────────────────────
# AI 감정분석 (FastAPI 연동) — sentiment 앱에서 사용
# ───────────────────────────────────────────────────────
FASTAPI_URL        = os.getenv("FASTAPI_URL", "http://127.0.0.1:8001")
FASTAPI_TIMEOUT    = float(os.getenv("FASTAPI_TIMEOUT", 10.0))
INTERNAL_API_KEY   = os.getenv("INTERNAL_API_KEY", "dev-key-change-me")
USE_DUMMY_ANALYZER = os.getenv("USE_DUMMY", "false").lower() == "true"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'brokers',
    'accounts',
    'interactions',
    'community',
    'sentiment',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.kakao_key',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}

from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":  False,
    "AUTH_HEADER_TYPES":      ("Bearer",),
}



# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static', 
]

# settings.py — STATIC_URL 아래에 추가

MEDIA_URL  = '/media/'                          # 브라우저가 접근하는 URL 경로
MEDIA_ROOT = BASE_DIR / 'media'                 # 실제 파일이 저장되는 폴더

LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'


# 프로젝트 공용 static 폴더가 있다면
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# collectstatic이 모아둘 최종 폴더
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ───────────────────────────────────────────────────────
# Celery — 비동기 작업 큐 (sentiment.tasks 등에서 사용)
# ───────────────────────────────────────────────────────
# Broker  = 작업 큐 보관소 (Django → Worker 로 전달)
# Backend = 결과 저장소 (선택적, 결과 조회 안 하면 비활성화 가능)
#
# Redis DB 번호 분리 이유:
#   /0 = 큐, /1 = 결과 → redis-cli SELECT 로 따로 디버깅 가능
# ───────────────────────────────────────────────────────
CELERY_BROKER_URL     = os.getenv("CELERY_BROKER_URL",     "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# 직렬화: JSON 만 허용 (보안 + 호환성)
CELERY_ACCEPT_CONTENT    = ["json"]
CELERY_TASK_SERIALIZER   = "json"
CELERY_RESULT_SERIALIZER = "json"

# 시간대: Django 의 TIME_ZONE 재사용 (Asia/Seoul)
CELERY_TIMEZONE   = TIME_ZONE
CELERY_ENABLE_UTC = True

# 작업 관리
CELERY_TASK_TRACK_STARTED   = True   # "STARTED" 상태 추적 (디버깅 용이)
CELERY_TASK_TIME_LIMIT      = 60     # 한 task 최대 60초 (FastAPI 행 걸려도 워커 보호)
CELERY_TASK_SOFT_TIME_LIMIT = 50     # 50초에 SoftTimeLimitExceeded 예외 → graceful cleanup

# 개발 편의: 로컬에서 worker 안 띄우고도 즉시 실행 (테스트용)
# CELERY_TASK_ALWAYS_EAGER = True   # 필요 시 주석 해제
