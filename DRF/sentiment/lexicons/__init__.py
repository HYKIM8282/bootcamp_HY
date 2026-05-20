# ─────────────────────────────────────────────────────────
# sentiment.lexicons: 감정분석용 사전 패키지
# ─────────────────────────────────────────────────────────
# 역할: 부동산 도메인의 긍정/부정/위험/슬랭 사전을 한 곳에 모음
# 영향: 바뀌면 sentiment/analyzers/keyword.py, preprocessing.py 영향
# 주의: 새 사전 추가 시 이 폴더에 *.py 만 추가 (기존 파일 수정 X)
# ─────────────────────────────────────────────────────────

from .positive import POSITIVE_KEYWORDS
from .negative import NEGATIVE_KEYWORDS
from .danger import DANGER_WORDS
from .slang import SLANG_MAP, ABBREV_MAP

__all__ = [
    "POSITIVE_KEYWORDS",
    "NEGATIVE_KEYWORDS",
    "DANGER_WORDS",
    "SLANG_MAP",
    "ABBREV_MAP",
]
