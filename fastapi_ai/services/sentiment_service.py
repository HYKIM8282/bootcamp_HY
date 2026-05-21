"""감정분석 비즈니스 로직.

원칙: Fat service. 분석·전처리·점수환산 모두 여기.
모델 인스턴스는 main.py의 lifespan에서 1회 로드 → 전역 dict 공유.

모델: Copycats/koelectra-base-v3-generalized-sentiment-analysis
  - 2-class: 0=negative, 1=positive
  - 한국어 일반 텍스트(리뷰/커뮤니티)에 강함
  - 약 420MB, 첫 실행 시 자동 다운로드

점수 환산:
  score = P_positive - P_negative      # 범위 -1 ~ +1
  label = neutral if |score| < THRESHOLD else (positive/negative)
"""
from typing import Dict

import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from core import config
from schemas.sentiment import AnalyzeRequest, AnalyzeResponse

# 점수 절댓값이 이 임계값보다 작으면 neutral 라벨
NEUTRAL_THRESHOLD = 0.3

# 모델 버전 식별자 (DB의 model_version 필드에 저장됨)
MODEL_VERSION = config.MODEL_NAME.split("/")[-1]

# 전역 모델 저장소 — main.py의 lifespan에서 채워짐 (1회 로드)
ml_models: Dict = {}


def load_model() -> None:
    """앱 시작 시 1회 호출. 모델·토크나이저 메모리에 적재.

    매 요청마다 로드하면 응답 5~30초 + OOM 위험.
    이 함수는 main.py의 lifespan에서만 호출됨.
    """
    print(f"[load] {config.MODEL_NAME} 로딩 중... (첫 실행 시 다운로드, ~420MB)")
    tokenizer = AutoTokenizer.from_pretrained(config.MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(config.MODEL_NAME)
    model.eval()  # Dropout/BatchNorm 끔 (추론 모드)
    ml_models["tokenizer"] = tokenizer
    ml_models["model"] = model
    print(f"[load] 완료. (version: {MODEL_VERSION})")


def analyze_text(req: AnalyzeRequest) -> AnalyzeResponse:
    """텍스트 → 감정 점수.

    USE_DUMMY_ANALYZER=true 면 별점 기반 더미 응답 (테스트용).
    아니면 실제 KoElectra 모델로 추론.
    """
    if config.USE_DUMMY_ANALYZER:
        return _dummy_analyze(req)
    return _ai_analyze(req)


def _ai_analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """실제 KoElectra 모델 추론."""
    tokenizer = ml_models["tokenizer"]
    model = ml_models["model"]

    # 토큰화 (최대 길이 자르기 — BERT 계열 512 토큰 제한)
    inputs = tokenizer(
        req.text,
        return_tensors="pt",
        truncation=True,
        max_length=config.MAX_INPUT_LENGTH,
    )

    # 추론 (gradient 계산 안 함 → 메모리·속도 절반)
    with torch.inference_mode():
        logits = model(**inputs).logits
        probs = F.softmax(logits, dim=-1).squeeze().tolist()

    # 모델 출력 구조: [P_negative, P_positive]
    p_negative, p_positive = probs[0], probs[1]

    # 점수: 확률 차이 (-1 ~ +1)
    score = p_positive - p_negative

    # 라벨: 임계값으로 neutral 처리 (2-class 모델을 3-class처럼 사용)
    if abs(score) < NEUTRAL_THRESHOLD:
        label = "neutral"
    elif score > 0:
        label = "positive"
    else:
        label = "negative"

    return AnalyzeResponse(
        score=round(score, 4),
        label=label,
        ai_probability=round(p_positive, 4),
        model_version=MODEL_VERSION,
    )


def _dummy_analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """별점 기반 더미 응답 (USE_DUMMY=true 일 때만).

    모델 안 띄우고 빠르게 흐름 검증할 때 사용.
    """
    if req.star >= 4:
        return AnalyzeResponse(
            score=0.7, label="positive", ai_probability=0.85, model_version="dummy-v0"
        )
    if req.star == 3:
        return AnalyzeResponse(
            score=0.0, label="neutral", ai_probability=0.5, model_version="dummy-v0"
        )
    return AnalyzeResponse(
        score=-0.7, label="negative", ai_probability=0.15, model_version="dummy-v0"
    )
