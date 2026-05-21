"""환경변수·설정값 — DRF의 settings.py와 짝.

주의: INTERNAL_API_KEY는 양쪽 (DRF·FastAPI) 동일해야 인증 통과.
"""
import os

# 모델 설정 (5단계에서 사용)
MODEL_NAME = os.getenv("MODEL_NAME", "klue/bert-base")
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "512"))

# 인증
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "dev-key-change-me")

# 개발 토글: True 면 실제 모델 안 띄우고 더미 응답 (3단계에서 활용)
USE_DUMMY_ANALYZER = os.getenv("USE_DUMMY", "false").lower() == "true"
