from django.contrib import admin
from .models import Review, Image


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    # ✅ 목록에 표시할 컬럼
    list_display = [
        'id',
        'agent',
        'author',
        'score',
        'content_preview',  # 내용 미리보기
        'created_at',
    ]

    # ✅ 오른쪽 필터 패널
    list_filter = [
        'score',        # 별점 필터
        'created_at',   # 날짜 필터
    ]

    # ✅ 검색 기능
    search_fields = [
        'agent__bsnm_cmpnm',   # 상호명 검색
        'author__username',    # 작성자 검색
        'content',             # 내용 검색
    ]

    # ✅ 읽기 전용 필드
    readonly_fields = ['created_at', 'updated_at']

    # ✅ 최신순 정렬
    ordering = ['-created_at']

    # ✅ 내용 미리보기 (30자 이상이면 ... 처리)
    def content_preview(self, obj):
        if len(obj.content) > 30:
            return obj.content[:30] + '...'
        return obj.content
    content_preview.short_description = '내용 미리보기'


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    """범용 이미지(GFK) 관리. 대상 모델/객체ID로 필터·검색."""

    list_display  = ['id', 'content_type', 'object_id', 'is_primary', 'uploaded_by', 'uploaded_at']
    list_filter   = ['content_type', 'is_primary', 'uploaded_at']
    search_fields = ['caption', 'object_id']
    readonly_fields = ['uploaded_at']
    ordering      = ['-uploaded_at']