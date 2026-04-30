from rest_framework import serializers

from interactions.serializers import ReviewSerializer
from .models import RealEstateAgent, EBBrokerInfo


class RealEstateAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealEstateAgent
        fields = "__all__"


class RealEstateAgentSearchParamSerializer(serializers.Serializer):
    ld_code = serializers.CharField(max_length=5, min_length=2, required=False)
    bsnm_cmpnm = serializers.CharField(max_length=100, required=False)
    brkr_nm = serializers.CharField(max_length=50, required=False)
    jurirno = serializers.CharField(max_length=20, required=False)
    sttus_se_code = serializers.CharField(max_length=5, required=False)
    num_of_rows = serializers.IntegerField(default=10, min_value=1, max_value=1000)
    page_no = serializers.IntegerField(default=1, min_value=1)

    def validate_ld_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("시군구코드는 숫자만 입력하세요.")
        return value

    def validate(self, attrs):
        search_fields = ["ld_code", "bsnm_cmpnm", "brkr_nm", "jurirno"]
        if not any(attrs.get(f) for f in search_fields):
            raise serializers.ValidationError(
                "ldCode, bsnmCmpnm, brkrNm, jurirno 중 하나 이상 입력하세요."
            )
        return attrs


class EBBrokerInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EBBrokerInfo
        fields = "__all__"
        read_only_fields = ("id", "fetched_at")


class EBBrokerSearchParamSerializer(serializers.Serializer):
    ld_code = serializers.CharField(max_length=5, min_length=2, required=False)
    bsnm_cmpnm = serializers.CharField(max_length=200, required=False)
    brkr_nm = serializers.CharField(max_length=100, required=False)
    jurirno = serializers.CharField(max_length=50, required=False)
    num_of_rows = serializers.IntegerField(default=10, min_value=1, max_value=1000)
    page_no = serializers.IntegerField(default=1, min_value=1)

    def validate(self, attrs):
        search_fields = ["ld_code", "bsnm_cmpnm", "brkr_nm", "jurirno"]
        if not any(attrs.get(f) for f in search_fields):
            raise serializers.ValidationError(
                "ldCode, bsnmCmpnm, brkrNm, jurirno 중 하나 이상 입력하세요."
            )
        return attrs


class RealEstateAgentDetailSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    avg_score = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = RealEstateAgent
        fields = [
            "id",
            "ld_code",
            "ld_code_nm",
            "jurirno",
            "bsnm_cmpnm",
            "brkr_nm",
            "sttus_se_code",
            "sttus_se_code_nm",
            "regist_de",
            "estbs_begin_de",
            "estbs_end_de",
            "mnnmadr",
            "rdnmadr",
            "last_updt_dt",
            "avg_score",
            "review_count",
            "reviews",
        ]

    def get_avg_score(self, obj):
        reviews = obj.reviews.all()
        if not reviews.exists():
            return 0
        return round(sum(r.score for r in reviews) / reviews.count(), 1)

    def get_review_count(self, obj):
        return obj.reviews.count()


class RealEstateAgentMapSerializer(serializers.ModelSerializer):
    # [수정] 지도 표시/필터링에 필요한 필드 유지
    class Meta:
        model = RealEstateAgent
        fields = [
            "id",
            "bsnm_cmpnm",
            "rdnmadr",
            "ld_code_nm",
            "lat",
            "lng",
            "sttus_se_code",
        ]