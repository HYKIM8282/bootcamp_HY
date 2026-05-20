# ─────────────────────────────────────────────────────────
# base.py: 감정분석기 추상 인터페이스 (계약)
# ─────────────────────────────────────────────────────────
# 역할: 모든 분석기가 공통으로 따라야 할 입출력 형태 정의
# 영향: 바뀌면 analyzers/keyword.py, (향후) ai.py, hybrid.py 모두 영향
# 주의: 이 파일은 자주 바뀌면 안 됨 — 변경 시 모든 분석기 점검 필요
# ─────────────────────────────────────────────────────────

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────
# 분석 결과 표준 형식
# ─────────────────────────────────────────────────────────
# 역할: 모든 분석기의 출력은 이 형태여야 함
# 영향: SentimentResult 모델, API 응답, 점수 환산 함수 모두 이걸 받음
# 주의: 새 필드 추가 시 기본값 필수 (하위 호환 보장)
@dataclass
class AnalyzerResult:
    score: float                                  # 종합 점수 (음수 부정 / 양수 긍정)
    is_dangerous: bool = False                    # 위험 신호 발견 여부
    positive_hits: list[str] = field(default_factory=list)   # 매칭된 긍정 키워드
    negative_hits: list[str] = field(default_factory=list)   # 매칭된 부정 키워드
    danger_hits: list[str] = field(default_factory=list)     # 매칭된 위험 키워드
    ai_probability: float | None = None           # AI 모델 확률 (없으면 None)
    confidence: float = 0.0                       # 0.0 ~ 1.0, 결과 확신도
    method: str = ""                              # "keyword" | "ai" | "hybrid"


# ─────────────────────────────────────────────────────────
# 분석기 추상 클래스
# ─────────────────────────────────────────────────────────
# 역할: 새 분석기는 이걸 상속하고 analyze() 만 구현
# 영향: 구현체(keyword/ai/hybrid)가 다 따름
# 주의: analyze() 의 입출력 시그니처 절대 변경 X
class BaseAnalyzer(ABC):
    name: str = "base"                            # 분석기 이름 (subclass 가 override)

    @abstractmethod
    def analyze(self, text: str) -> AnalyzerResult:
        """원본 텍스트를 받아 AnalyzerResult 반환."""
        raise NotImplementedError
