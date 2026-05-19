from django.utils.timesince import timesince
from rest_framework import serializers

from .models import Post


class PostSerializer(serializers.ModelSerializer):
    """커뮤니티 글 직렬화 — JSON 응답 전용"""

    author_name      = serializers.SerializerMethodField()
    category_display = serializers.CharField(source="get_category_display",    read_only=True)
    time_ago         = serializers.SerializerMethodField()

    class Meta:
        model  = Post
        fields = [
            "id",
            "title",
            "content",
            "category",
            "category_display",
            "author",
            "author_name",
            "nickname",
            "like_count",
            "view_count",
            "created_at",
            "updated_at",
            "time_ago",
        ]
        read_only_fields = [
            "author",
            "like_count",
            "view_count",
            "created_at",
            "updated_at",
        ]

    def get_author_name(self, obj):
        # 닉네임을 입력했으면 닉네임, 비웠으면 회원 username
        if obj.nickname:
            return obj.nickname
        return obj.author.username if obj.author else "익명"

    def get_time_ago(self, obj):
        # 예) "1분", "3시간", "2일" 뒤에 "전" 부가
        return f"{timesince(obj.created_at).split(',')[0]} 전"

    def validate_title(self, value):
        v = (value or "").strip()
        if not v:
            raise serializers.ValidationError("제목을 입력해주세요.")
        if len(v) > 80:
            raise serializers.ValidationError("제목은 80자 이내여야 합니다.")
        return v

    def validate_content(self, value):
        v = (value or "").strip()
        if not v:
            raise serializers.ValidationError("내용을 입력해주세요.")
        if len(v) > 1000:
            raise serializers.ValidationError("본문은 1,000자 이내여야 합니다.")
        return v
