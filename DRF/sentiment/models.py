# ─────────────────────────────────────────────────────────
# sentiment/models.py: 감정분석 결과 캐싱
# ─────────────────────────────────────────────────────────
# 역할: 분석 결과를 DB에 저장 (재계산 방지 + 학습 데이터 축적)
# 영향: 바뀌면 migrations/, admin.py, (향후) serializers.py 영향
# 주의: GFK(GenericForeignKey)로 Review/Post 어디든 연결 가능
#       — interactions.Image 와 동일한 패턴 (DRY)
# ─────────────────────────────────────────────────────────

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


# ─────────────────────────────────────────────────────────
# SentimentResult: 텍스트 1건의 감정분석 결과
# ─────────────────────────────────────────────────────────
# 역할: 분석기 출력(AnalyzerResult)을 DB에 영구 저장
# 영향: 신뢰 점수 계산(향후 trust_score 앱)이 이걸 읽음
# 주의: target_type/target_id 로 Review/Post 등을 동시에 가리킴
#       동일 대상 재분석 시 새 row 추가 (히스토리 유지)
class SentimentResult(models.Model):
    # 분석 대상 (GFK — Review/Post/기타)
    target_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="대상 모델 종류",
    )
    target_id = models.PositiveIntegerField(verbose_name="대상 ID")
    target = GenericForeignKey("target_type", "target_id")

    # 분석기 종류
    METHOD_CHOICES = [
        ("keyword", "키워드 사전"),
        ("ai", "AI 모델"),
        ("hybrid", "하이브리드"),
    ]
    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        default="keyword",
        verbose_name="분석 방식",
    )

    # 점수 결과
    score = models.FloatField(verbose_name="종합 점수")
    is_dangerous = models.BooleanField(default=False, verbose_name="위험 신호")
    ai_probability = models.FloatField(
        null=True, blank=True, verbose_name="AI 긍정 확률(0~1)"
    )
    confidence = models.FloatField(default=0.0, verbose_name="결과 확신도(0~1)")

    # AI 응답 (FastAPI 연동) ─────────────────────────────
    LABEL_CHOICES = [
        ("positive", "긍정"),
        ("neutral", "중립"),
        ("negative", "부정"),
        ("error", "분석 실패"),
    ]
    label = models.CharField(
        max_length=20,
        choices=LABEL_CHOICES,
        default="neutral",
        verbose_name="감정 라벨",
    )
    model_version = models.CharField(
        max_length=50,
        default="",
        blank=True,
        verbose_name="모델 버전",
        help_text="어느 분석기로 만든 결과인지 추적용 (예: dummy-v0, klue-bert-v1)",
    )
    raw_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="원본 응답",
        help_text="FastAPI 원본 JSON 응답 백업 (디버깅·재현용)",
    )

    # 매칭 근거 (디버깅/투명성용)
    positive_hits = models.JSONField(default=list, blank=True, verbose_name="긍정 매칭")
    negative_hits = models.JSONField(default=list, blank=True, verbose_name="부정 매칭")
    danger_hits = models.JSONField(default=list, blank=True, verbose_name="위험 매칭")

    # 검수 큐
    needs_review = models.BooleanField(default=False, verbose_name="사람 검수 필요")
    reviewed = models.BooleanField(default=False, verbose_name="검수 완료")

    # 공통 필드 (명명 규칙 준수)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="분석 시각")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정 시각")

    class Meta:
        db_table = "sentiment_result"
        verbose_name = "감정분석 결과"
        verbose_name_plural = "감정분석 결과 목록"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["target_type", "target_id"], name="idx_sentiment_target"),
            models.Index(fields=["is_dangerous", "needs_review"], name="idx_sentiment_flag"),
        ]

    def __str__(self) -> str:
        flag = " [DANGER]" if self.is_dangerous else ""
        return f"[{self.get_method_display()}] {self.score:+.1f}{flag}"
