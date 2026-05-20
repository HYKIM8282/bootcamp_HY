"""
한국어 감정분석 터미널 테스트 스크립트 (서버 불필요)

모델: Copycats/koelectra-base-v3-generalized-sentiment-analysis
  - 2-class (0 = negative, 1 = positive)
  - 한국어 일반 텍스트(리뷰/커뮤니티 글)에 강함
  - 약 420MB, 첫 실행 시 자동 다운로드

점수 환산: (P_positive - P_negative) × 10  →  -10 ~ +10 사이 연속 점수
  - 강한 긍정  → +10 근처
  - 강한 부정  → -10 근처
  - 애매한 글  →  0 근처
  - 통계 집계(평균/합산)에 그대로 사용 가능

사용법:
  # 1) 대화형 모드 — 계속 문장을 입력받음 (가장 추천)
  python cli_test.py

  # 2) 한 문장만 분석하고 종료
  python cli_test.py "이 중개사 정말 친절하고 빠르게 처리해줬어요"

  # 3) 미리 준비된 샘플 일괄 분석
  python cli_test.py --samples
"""

import sys

import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_NAME = "Copycats/koelectra-base-v3-generalized-sentiment-analysis"

# 이 모델의 라벨 인덱스 → 사람이 읽을 수 있는 이름.
# (모델 config의 id2label이 'LABEL_0' 같은 식으로 들어있을 수 있어 직접 매핑)
LABEL_MAP = {0: "negative", 1: "positive"}

# 환산 점수 범위: -SCORE_SCALE ~ +SCORE_SCALE
SCORE_SCALE = 10

# 부동산 커뮤니티 도메인 샘플 (긍정/부정/애매 섞임)
SAMPLES = [
    "이 중개사 정말 친절하고 매물도 빠르게 찾아주셨어요. 강추합니다.",
    "전화도 안 받고 약속도 자주 어기네요. 다시는 안 갈 듯.",
    "그냥 평범한 거래였어요. 특별히 좋지도 나쁘지도 않음.",
    "허위 매물 올려놓고 가니까 다른 거 보여주네요. 사기꾼 같음.",
    "처음 집 사는 거였는데 친절하게 설명해주셔서 안심하고 계약했어요.",
    "수수료만 챙기고 끝. 사후 관리 0점.",
]


def load_model():
    """모델과 토크나이저를 메모리에 로드. 첫 실행 시 자동 다운로드(약 420MB)."""
    print(f"[load] {MODEL_NAME} 로딩 중... (첫 실행 시 다운로드로 1~2분 소요)")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()  # 추론 모드 (드롭아웃 끔)
    print(f"[load] 완료. 라벨 매핑: {LABEL_MAP}\n")
    return tokenizer, model


def analyze(text: str, tokenizer, model) -> dict:
    """한 문장 → 감정분석 결과 (라벨, 확신도, all_scores, 환산 점수)."""
    # 1) 토큰화
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)

    # 2) 추론 (학습 안 하므로 no_grad)
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = F.softmax(logits, dim=-1).squeeze().tolist()

    # 3) 결과 가공
    all_scores = {LABEL_MAP[i]: float(p) for i, p in enumerate(probs)}
    top_idx = int(torch.tensor(probs).argmax().item())

    # 4) 점수 환산: (P_pos - P_neg) × 10  →  -10 ~ +10 연속 점수
    sentiment_score = (all_scores["positive"] - all_scores["negative"]) * SCORE_SCALE

    return {
        "label": LABEL_MAP[top_idx],
        "confidence": float(probs[top_idx]),
        "all_scores": all_scores,
        "sentiment_score": round(sentiment_score, 2),  # -10.00 ~ +10.00
    }


def print_result(text: str, result: dict) -> None:
    """결과를 보기 좋게 출력. 환산 점수를 가장 강조해서 보여줌."""
    score = result["sentiment_score"]
    # 점수 부호에 따라 시각적 표시
    if score > 0:
        sign_icon = "🟢"
        sign_str = f"+{score:.2f}"
    elif score < 0:
        sign_icon = "🔴"
        sign_str = f"{score:.2f}"
    else:
        sign_icon = "⚪"
        sign_str = " 0.00"

    print(f"\n📝 입력: {text}")
    print(f"   ➜ 라벨: [{result['label']}]  (확신도 {result['confidence']:.4f})")
    print(f"   ➜ 환산 점수: {sign_icon} {sign_str}  (범위 -{SCORE_SCALE} ~ +{SCORE_SCALE})")
    bar_len = 30
    for label, prob in result["all_scores"].items():
        bar = "█" * int(prob * bar_len)
        print(f"   {label:10s} {bar:<{bar_len}} {prob:.4f}")


def run_interactive(tokenizer, model) -> None:
    """대화형 모드: quit 입력 또는 Ctrl+C 까지 반복."""
    print("=" * 60)
    print(" 대화형 모드 — 분석할 문장을 입력하세요")
    print(" (종료: 'quit' / 'exit' / 'q' 입력 또는 Ctrl+C)")
    print("=" * 60)
    while True:
        try:
            text = input("\n>>> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n종료합니다.")
            return
        if not text:
            continue
        if text.lower() in ("quit", "exit", "q"):
            print("종료합니다.")
            return
        try:
            result = analyze(text, tokenizer, model)
            print_result(text, result)
        except Exception as e:
            print(f"[ERROR] 분석 실패: {e}")


def main() -> None:
    args = sys.argv[1:]
    tokenizer, model = load_model()

    if not args:
        run_interactive(tokenizer, model)
    elif args[0] == "--samples":
        print(f"미리 준비된 샘플 {len(SAMPLES)}개를 분석합니다.\n")
        total = 0.0
        for s in SAMPLES:
            result = analyze(s, tokenizer, model)
            print_result(s, result)
            total += result["sentiment_score"]
        avg = total / len(SAMPLES)
        print("\n" + "=" * 60)
        print(f" 📊 평균 환산 점수: {avg:+.2f}  (합계 {total:+.2f} / {len(SAMPLES)}건)")
        print("=" * 60)
    else:
        text = " ".join(args)
        print_result(text, analyze(text, tokenizer, model))


if __name__ == "__main__":
    main()
