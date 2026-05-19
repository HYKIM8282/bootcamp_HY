from rest_framework import serializers
from .models import Review, Image


class ImageSerializer(serializers.ModelSerializer):
    """범용 Image(GFK) 시리얼라이저 — 입력 검증과 응답 직렬화를 모두 담당.

    write 필드: image, caption, is_primary
    read 필드 : id, image_url, caption, is_primary, uploaded_by, uploaded_at
    GFK 필드(content_type, object_id) 와 uploaded_by 는 뷰에서 .save(**kwargs)로 주입.
    응답 필드는 기존 BrokerImageSerializer와 호환 → 프론트엔드 JS 변경 없이 전환.
    """

    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    MAX_SIZE      = 5 * 1024 * 1024  # 5MB

    image_url   = serializers.SerializerMethodField()
    uploaded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model  = Image
        fields = ["id", "image", "image_url", "caption", "is_primary", "uploaded_by", "uploaded_at"]
        read_only_fields = ["id", "image_url", "uploaded_by", "uploaded_at"]
        extra_kwargs = {
            "image":      {"write_only": True, "required": True},
            "caption":    {"required": False},
            "is_primary": {"required": False},
        }

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None

    def validate_image(self, value):
        if value.content_type not in self.ALLOWED_TYPES:
            raise serializers.ValidationError("JPG·PNG·WEBP·GIF 형식만 업로드 가능합니다.")
        if value.size > self.MAX_SIZE:
            raise serializers.ValidationError("파일 크기는 5MB 이하여야 합니다.")
        return value


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

    # ✅ 통합 이미지(GFK) — 리뷰에 붙은 사진들 (다중 가능). 응답 전용.
    images = ImageSerializer(many=True, read_only=True)

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
            'images',
            'created_at',
            'updated_at',
        ]
        # ✅ author, agent 는 자동 처리 (직접 입력 불필요)
        read_only_fields = ['author', 'agent', 'created_at', 'updated_at']