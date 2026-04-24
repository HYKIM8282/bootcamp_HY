from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):

    # ✅ 작성자 이름 읽기 전용
    author_name = serializers.CharField(
        source='author.username',
        read_only=True
    )

    # ✅ 별점 텍스트 읽기 전용
    score_display = serializers.CharField(
        source='get_score_display',
        read_only=True
    )

    class Meta:
        model  = Review
        fields = [
            'id',
            'agent',
            'author',
            'author_name',
            'score',
            'score_display',
            'content',
            'created_at',
            'updated_at',
        ]
        # ✅ author, agent 는 자동 처리 (직접 입력 불필요)
        read_only_fields = ['author', 'agent', 'created_at', 'updated_at']