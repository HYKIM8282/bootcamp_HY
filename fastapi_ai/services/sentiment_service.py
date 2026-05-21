"""감정분석 비즈니스 로직.

원칙: Fat service. 분석·전처리·점수환산 모두 여기.
- 3단계 (현재): 더미 — 별점 기반 단순 매핑
- 5단계: 실제 모델 (KoBERT 등) 이식
"""
from schemas.sentiment import AnalyzeRequest, AnalyzeResponse

DUMMY_MODEL_VERSION = "dummy-v0"


def analyze_text(req: AnalyzeRequest) -> AnalyzeResponse:
    """텍스트 + 별점 → 감정 점수.

    현재 구현: 별점만 보고 라벨 결정 (더미).
    5단계에서 실제 모델로 교체 예정. text 활용은 그때부터.
    """
    if req.star >= 4:
        label = "positive"
        score = 0.7
        ai_probability = 0.85
    elif req.star == 3:
        label = "neutral"
        score = 0.0
        ai_probability = 0.5
    else:
        label = "negative"
        score = -0.7
        ai_probability = 0.15

    return AnalyzeResponse(
        score=score,
        label=label,
        ai_probability=ai_probability,
        model_version=DUMMY_MODEL_VERSION,
    )
