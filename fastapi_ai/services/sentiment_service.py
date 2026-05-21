"""감정분석 비즈니스 로직.

원칙: Fat service. 분석·전처리·점수환산 모두 여기.
- 3단계: 더미 응답 (USE_DUMMY_ANALYZER=true 일 때)
- 5단계: 실제 모델 (KoBERT 등) 이식
"""

# 3단계에서 추가 예정:
# def analyze_text(req: AnalyzeRequest) -> AnalyzeResponse:
#     ...
