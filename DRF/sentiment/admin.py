# ─────────────────────────────────────────────────────────
# sentiment/admin.py: Django Admin 등록
# ─────────────────────────────────────────────────────────
# 역할: SentimentResult 를 관리자 페이지에서 검수 가능하게 함
# 영향: /admin/sentiment/sentimentresult/
# 주의: AI 추론 결과(label, ai_probability, model_version)를
#       한눈에 볼 수 있도록 list_display 확장.
#       GFK target 은 별도 표시 메서드로 노출.
# ─────────────────────────────────────────────────────────

import json

from django.contrib import admin
from django.utils.html import format_html

from .models import SentimentResult


@admin.register(SentimentResult)
class SentimentResultAdmin(admin.ModelAdmin):
    # ── 목록 화면 ───────────────────────────────────────
    list_display = (
        "id",
        "target_display",      # 어느 Review/Post 인지
        "method",              # keyword / ai / hybrid
        "label_badge",         # positive / neutral / negative (색깔)
        "score",               # -10 ~ +10
        "ai_probability",      # AI 긍정 확률
        "confidence",          # 확신도
        "model_version",       # 어떤 모델로 추론?
        "is_dangerous",
        "needs_review",
        "reviewed",
        "created_at",
    )
    list_filter = (
        "method",
        "label",
        "is_dangerous",
        "needs_review",
        "reviewed",
        "model_version",
    )
    search_fields = (
        "target_id",
        "model_version",
        "positive_hits",
        "negative_hits",
        "danger_hits",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "raw_response_pretty",   # JSON 보기 좋게
    )
    ordering = ("-created_at",)
    list_per_page = 30

    # ── 상세 화면(편집) 그룹핑 ─────────────────────────
    fieldsets = (
        ("분석 대상", {
            "fields": ("target_type", "target_id"),
        }),
        ("분석기 정보", {
            "fields": ("method", "model_version"),
        }),
        ("결과 점수", {
            "fields": ("score", "label", "ai_probability", "confidence", "is_dangerous"),
        }),
        ("매칭 근거", {
            "classes": ("collapse",),  # 기본 접힘
            "fields": ("positive_hits", "negative_hits", "danger_hits"),
        }),
        ("원본 응답(FastAPI)", {
            "classes": ("collapse",),
            "fields": ("raw_response", "raw_response_pretty"),
        }),
        ("검수 큐", {
            "fields": ("needs_review", "reviewed"),
        }),
        ("타임스탬프", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    # ── 커스텀 표시 메서드 ─────────────────────────────
    @admin.display(description="분석 대상")
    def target_display(self, obj: SentimentResult) -> str:
        """GFK target 을 '앱.모델 #ID' 형태로 보여줌."""
        try:
            ct = obj.target_type
            return f"{ct.app_label}.{ct.model} #{obj.target_id}"
        except Exception:
            return f"#{obj.target_id}"

    @admin.display(description="라벨", ordering="label")
    def label_badge(self, obj: SentimentResult) -> str:
        """label 을 색깔 배지로 표시 (긍정=초록, 부정=빨강, 중립=회색, 에러=주황)."""
        colors = {
            "positive": "#28a745",
            "negative": "#dc3545",
            "neutral": "#6c757d",
            "error": "#fd7e14",
        }
        color = colors.get(obj.label, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_label_display(),
        )

    @admin.display(description="원본 응답 (보기 좋게)")
    def raw_response_pretty(self, obj: SentimentResult) -> str:
        """raw_response JSON 을 들여쓰기해서 보여줌."""
        if not obj.raw_response:
            return "(비어있음)"
        try:
            pretty = json.dumps(obj.raw_response, indent=2, ensure_ascii=False)
            return format_html("<pre style='white-space:pre-wrap;'>{}</pre>", pretty)
        except Exception:
            return str(obj.raw_response)
