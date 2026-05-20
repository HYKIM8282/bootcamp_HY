# ─────────────────────────────────────────────────────────
# sentiment.analyzers: 감정분석기 패키지
# ─────────────────────────────────────────────────────────
# 역할: 분석 알고리즘 종류별로 파일 분리 (전략 패턴)
# 영향: 외부 코드는 base.AnalyzerResult / KeywordAnalyzer 만 import
# 주의: 새 분석기 추가 시 base.BaseAnalyzer 를 상속하고 analyze() 구현만 하면 됨
#       기존 파일 수정 불필요
# ─────────────────────────────────────────────────────────

from .base import AnalyzerResult, BaseAnalyzer
from .keyword import KeywordAnalyzer

__all__ = [
    "AnalyzerResult",
    "BaseAnalyzer",
    "KeywordAnalyzer",
]
