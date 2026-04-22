from rest_framework import serializers
from .models import RealEstateAgent, EBBrokerInfo

#부동산중개업사무소정보조회
class RealEstateAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealEstateAgent
        fields = "__all__"

class RealEstateAgentSearchParamSerializer(serializers.Serializer):
    """부동산중개업사무소정보조회 API 검색 요청 파라미터 유효성 검사용"""

    ld_code = serializers.CharField(
        max_length=5,
        min_length=2,
        required=False,
        help_text="시군구코드 (2~5자리)",
    )
    bsnm_cmpnm = serializers.CharField(
        max_length=100,
        required=False,
        help_text="사업자상호",
    )
    brkr_nm = serializers.CharField(
        max_length=50,
        required=False,
        help_text="중개업자명",
    )
    jurirno = serializers.CharField(
        max_length=20,
        required=False,
        help_text="등록번호",
    )
    sttus_se_code = serializers.CharField(
        max_length=5,
        required=False,
        help_text="상태구분코드",
    )
    num_of_rows = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=1000,
        help_text="검색건수 (최대 1000)",
    )
    page_no = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="페이지번호",
    )

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


#부동산중개업자정보조회
class EBBrokerInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EBBrokerInfo
        fields = "__all__"
        read_only_fields = ("id", "fetched_at")


class EBBrokerSearchParamSerializer(serializers.Serializer):
    """API 검색 요청 파라미터 유효성 검사용"""

    ld_code = serializers.CharField(
        max_length=5,
        min_length=2,
        required=False,
        help_text="시군구코드 (2~5자리)",
    )
    bsnm_cmpnm = serializers.CharField(
        max_length=200,
        required=False,
        help_text="사업자상호",
    )
    brkr_nm = serializers.CharField(
        max_length=100,
        required=False,
        help_text="중개업자명",
    )
    jurirno = serializers.CharField(
        max_length=50,
        required=False,
        help_text="법인등록번호",
    )
    num_of_rows = serializers.IntegerField(
        default=10,
        min_value=1,
        max_value=1000,
        help_text="검색건수 (최대 1000)",
    )
    page_no = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="페이지번호",
    )

    def validate(self, attrs):
        # 최소 하나의 검색 조건 필요
        search_fields = ["ld_code", "bsnm_cmpnm", "brkr_nm", "jurirno"]
        if not any(attrs.get(f) for f in search_fields):
            raise serializers.ValidationError(
                "ldCode, bsnmCmpnm, brkrNm, jurirno 중 하나 이상 입력하세요."
            )
        return attrs