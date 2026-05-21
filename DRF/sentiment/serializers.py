"""sentiment 앱 시리얼라이저.

역할:
- SentimentRequestSerializer: Review → FastAPI 보낼 dict (DRF → FastAPI)
- SentimentResultSerializer:  FastAPI 응답 → SentimentResult 저장 (FastAPI → DB)

원칙:
- DRF: no Forms — 시리얼라이저가 검증 + 변환 통합
- FastAPI의 Pydantic 모델과 1:1 대응 (계약/contract)
  · SentimentRequestSerializer  ↔  fastapi_ai/schemas/sentiment.py::AnalyzeRequest
  · SentimentResultSerializer   ↔  fastapi_ai/schemas/sentiment.py::AnalyzeResponse
"""
from rest_framework import serializers

from .models import SentimentResult


class SentimentRequestSerializer(serializers.Serializer):
    """Review → FastAPI 분석 요청 형태로 변환 (DRF → FastAPI).

    Review 인스턴스를 받아 FastAPI가 받을 dict로 직렬화.
    응답이 아닌 요청 페이로드 생성 용도 (read-only).

    사용 예시 (6단계 services.py 에서):
        payload = SentimentRequestSerializer(review).data
        # {"review_id": 12, "text": "친절했어요", "star": 5, "target_type": "review"}
        httpx.post(url, json=payload, timeout=settings.FASTAPI_TIMEOUT)
    """

    review_id = serializers.IntegerField(source="id")
    text = serializers.CharField(source="content")
    star = serializers.IntegerField(source="score")
    target_type = serializers.SerializerMethodField()

    def get_target_type(self, obj) -> str:
        """대상 모델 종류. 향후 Post 등 확장 시 분기."""
        return "review"


class SentimentResultSerializer(serializers.ModelSerializer):
    """FastAPI 응답 → SentimentResult 저장 (FastAPI → DB).

    FastAPI 응답 JSON을 받아서 SentimentResult 한 row로 저장.
    GFK(target)·method·raw_response 는 save() 호출 시 외부에서 주입.

    사용 예시 (6단계 services.py 에서):
        serializer = SentimentResultSerializer(data=fastapi_response_dict)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            target=review,                       # GFK (target_type/target_id 자동 채움)
            method="ai",                         # 분석 방식
            raw_response=fastapi_response_dict,  # 원본 백업 (디버깅용)
        )
    """

    class Meta:
        model = SentimentResult
        # FastAPI 응답에 직접 매칭되는 필드만
        fields = ["score", "label", "ai_probability", "model_version"]
        # target / method / raw_response 는 save() 시 외부에서 주입
