# ─────────────────────────────────────────────────────────
# keyword.py: 키워드 사전 기반 감정 분석기 (AI 없이 즉시 동작)
# ─────────────────────────────────────────────────────────
# 역할: lexicons/* 사전과 매칭하여 점수/위험 플래그 산정
# 영향: 외부에서 KeywordAnalyzer().analyze(text) 형태로 사용
# 주의: 단순 substring 매칭. 향후 형태소 분석기 도입 시 정확도↑ 가능
# ─────────────────────────────────────────────────────────

from ..lexicons import (
    POSITIVE_KEYWORDS,
    NEGATIVE_KEYWORDS,
    DANGER_WORDS,
)
# 키워드 매칭은 슬랭 원형(예: "초품아")이 사전에 있으므로 expand_slang 사용 X.
# 노이즈만 제거. expand_slang 은 AI 모델 분석기(향후)에서 사용.
from ..preprocessing import clean_noise
from .base import AnalyzerResult, BaseAnalyzer


class KeywordAnalyzer(BaseAnalyzer):
    """사전 매칭만으로 점수를 내는 분석기. AI 없이도 동작."""

    name = "keyword"

    # ─────────────────────────────────────────────
    # 분석 실행
    # ─────────────────────────────────────────────
    # 역할: 텍스트 → 전처리 → 사전 매칭 → 점수 산정
    # 영향: SentimentResult 모델에 저장될 결과 생성
    # 주의: 빈 문자열/None 입력 시 score=0 의 기본 결과 반환
    def analyze(self, text: str) -> AnalyzerResult:
        if not text:
            return AnalyzerResult(score=0.0, method=self.name)

        cleaned = clean_noise(text)

        positive_hits: list[str] = []
        negative_hits: list[str] = []
        danger_hits: list[str] = []
        score = 0.0

        # 긍정 키워드 매칭
        for word, weight in POSITIVE_KEYWORDS.items():
            if word in cleaned:
                positive_hits.append(word)
                score += weight

        # 부정 키워드 매칭
        for word, weight in NEGATIVE_KEYWORDS.items():
            if word in cleaned:
                negative_hits.append(word)
                score += weight  # weight 자체가 음수

        # 위험 키워드 검사 (발견 즉시 플래그)
        for word in DANGER_WORDS:
            if word in cleaned:
                danger_hits.append(word)

        is_dangerous = len(danger_hits) > 0

        # 신뢰도: 매칭된 키워드 수에 비례 (대충)
        total_hits = len(positive_hits) + len(negative_hits) + len(danger_hits)
        confidence = min(1.0, total_hits / 5.0)

        return AnalyzerResult(
            score=score,
            is_dangerous=is_dangerous,
            positive_hits=positive_hits,
            negative_hits=negative_hits,
            danger_hits=danger_hits,
            ai_probability=None,
            confidence=confidence,
            method=self.name,
        )
