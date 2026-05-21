"""Pydantic 모델 — DRF Serializer와 짝.

설계 원칙:
- AnalyzeRequest: DRF SentimentRequestSerializer와 1:1 대응
- AnalyzeResponse: DRF SentimentResultSerializer와 1:1 대응
- 응답 모양 변경 시 양쪽 같이 수정 (계약/contract)
"""

# 3단계에서 정의 예정:
# class AnalyzeRequest(BaseModel):
#     review_id: int
#     text: str
#     star: int
#     target_type: str = "review"
#
# class AnalyzeResponse(BaseModel):
#     score: float
#     label: str
#     ai_probability: float
#     model_version: str
