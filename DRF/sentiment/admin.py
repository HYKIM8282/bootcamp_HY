# ─────────────────────────────────────────────────────────
# sentiment/admin.py: Django Admin 등록
# ─────────────────────────────────────────────────────────
# 역할: SentimentResult 를 관리자 페이지에서 검수 가능하게 함
# 영향: /admin/sentiment/sentimentresult/
# 주의: 검수 큐(needs_review) 항목 필터링 기능 제공
# ─────────────────────────────────────────────────────────

from django.contrib import admin

from .models import SentimentResult


@admin.register(SentimentResult)
class SentimentResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "method",
        "score",
        "is_dangerous",
        "needs_review",
        "reviewed",
        "created_at",
    )
    list_filter = ("method", "is_dangerous", "needs_review", "reviewed")
    search_fields = ("positive_hits", "negative_hits", "danger_hits")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
