"""환경변수·설정값 — DRF의 settings.py와 짝.

주의: INTERNAL_API_KEY는 양쪽 (DRF·FastAPI) 동일해야 인증 통과.
"""
import os

# 모델 설정 (6단계 — 한국어 일반 텍스트 감정분석, 부동산 리뷰에 적합)
# Copycats/koelectra-... : 2-class (negative/positive), 약 420MB
# cli_test.py 에서 검증된 모델
MODEL_NAME = os.getenv("MODEL_NAME", "Copycats/koelectra-base-v3-generalized-sentiment-analysis")
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "512"))

# 인증
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "dev-key-change-me")

# 개발 토글: True 면 실제 모델 안 띄우고 더미 응답 (3단계에서 활용)
USE_DUMMY_ANALYZER = os.getenv("USE_DUMMY", "false").lower() == "true"
