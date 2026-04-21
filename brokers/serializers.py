from rest_framework import serializers
from .models import BrokerOffice, Broker


class BrokerSerializer(serializers.ModelSerializer):
    asort_label = serializers.CharField(source="get_brkr_asort_code_display", read_only=True)
    ofcps_label = serializers.CharField(source="get_ofcps_se_code_display",   read_only=True)
    class Meta:
        model  = Broker
        fields = ["id","ld_code","ld_code_nm","jurirno","bsnm_cmpnm","brkr_nm",
                  "brkr_asort_code","asort_label","brkr_asort_code_nm",
                  "crqfc_no","crqfc_acqdt",
                  "ofcps_se_code","ofcps_label","ofcps_se_code_nm",
                  "last_updt_dt","created_at","updated_at"]
        read_only_fields = ("id","created_at","updated_at")


class BrokerOfficeListSerializer(serializers.ModelSerializer):
    sttus_label  = serializers.CharField(source="get_sttus_se_code_display", read_only=True)
    broker_count = serializers.SerializerMethodField()
    class Meta:
        model  = BrokerOffice
        fields = ["id","ld_code","ld_code_nm","jurirno","bsnm_cmpnm","brkr_nm",
                  "sttus_se_code","sttus_label","sttus_se_code_nm",
                  "regist_de","estbs_begin_de","estbs_end_de",
                  "mnnmadr","rdnmadr","rdnmadrcode",
                  "last_updt_dt","broker_count"]
    def get_broker_count(self, obj):
        return obj.brokers.count()


class BrokerOfficeDetailSerializer(BrokerOfficeListSerializer):
    brokers = BrokerSerializer(many=True, read_only=True)
    class Meta(BrokerOfficeListSerializer.Meta):
        fields = BrokerOfficeListSerializer.Meta.fields + ["brokers","created_at","updated_at"]


# ── 이미지3: 사무소 VWorld 원본 파싱 ──────────────────────
class VWorldOfficeRawSerializer(serializers.Serializer):
    ldCode        = serializers.CharField()
    ldCodeNm      = serializers.CharField()
    jurirno       = serializers.CharField()
    bsnmCmpnm     = serializers.CharField()
    brkrNm        = serializers.CharField()
    sttusSeCode   = serializers.CharField()
    sttusSeCodeNm = serializers.CharField()
    registDe      = serializers.DateField(input_formats=["%Y-%m-%d","%Y%m%d"],
                        allow_null=True, required=False)
    estbsBeginDe  = serializers.DateField(input_formats=["%Y-%m-%d","%Y%m%d"],
                        allow_null=True, required=False)
    estbsEndDe    = serializers.DateField(input_formats=["%Y-%m-%d","%Y%m%d"],
                        allow_null=True, required=False)
    lastUpdtDt    = serializers.DateField(input_formats=["%Y-%m-%d","%Y%m%d"],
                        allow_null=True, required=False)
    mnnmadr       = serializers.CharField(allow_blank=True, required=False, default="")
    rdnmadr       = serializers.CharField(allow_blank=True, required=False, default="")
    rdnmadrcode   = serializers.CharField(allow_blank=True, required=False, default="")

    def save(self):
        d = self.validated_data
        office, _ = BrokerOffice.objects.update_or_create(
            jurirno=d["jurirno"],
            defaults={
                "ld_code": d["ldCode"], "ld_code_nm": d["ldCodeNm"],
                "bsnm_cmpnm": d["bsnmCmpnm"], "brkr_nm": d["brkrNm"],
                "sttus_se_code": d["sttusSeCode"],
                "sttus_se_code_nm": d["sttusSeCodeNm"],
                "regist_de": d.get("registDe"),
                "estbs_begin_de": d.get("estbsBeginDe"),
                "estbs_end_de": d.get("estbsEndDe"),
                "last_updt_dt": d.get("lastUpdtDt"),
                "mnnmadr": d.get("mnnmadr",""),
                "rdnmadr": d.get("rdnmadr",""),
                "rdnmadrcode": d.get("rdnmadrcode",""),
            })
        return office


# ── 이미지2: 중개업자 VWorld 원본 파싱 ──────────────────────
class VWorldBrokerRawSerializer(serializers.Serializer):
    ldCode          = serializers.CharField()
    ldCodeNm        = serializers.CharField()
    jurirno         = serializers.CharField()
    bsnmCmpnm       = serializers.CharField()
    brkrNm          = serializers.CharField()
    brkrAsortCode   = serializers.CharField()
    brkrAsortCodeNm = serializers.CharField()
    crqfcNo         = serializers.CharField(allow_blank=True, required=False, default="")
    crqfcAcqdt      = serializers.DateField(input_formats=["%Y-%m-%d","%Y%m%d"],
                          allow_null=True, required=False)
    ofcpsSeCode     = serializers.CharField()
    ofcpsSeCodeNm   = serializers.CharField()
    lastUpdtDt      = serializers.DateField(input_formats=["%Y-%m-%d","%Y%m%d"],
                          allow_null=True, required=False)

    def save(self):
        d      = self.validated_data
        office = BrokerOffice.objects.filter(jurirno=d["jurirno"]).first()
        broker, _ = Broker.objects.update_or_create(
            jurirno=d["jurirno"], brkr_nm=d["brkrNm"], ofcps_se_code=d["ofcpsSeCode"],
            defaults={
                "office": office, "ld_code": d["ldCode"], "ld_code_nm": d["ldCodeNm"],
                "bsnm_cmpnm": d["bsnmCmpnm"],
                "brkr_asort_code": d["brkrAsortCode"],
                "brkr_asort_code_nm": d["brkrAsortCodeNm"],
                "crqfc_no": d.get("crqfcNo",""),
                "crqfc_acqdt": d.get("crqfcAcqdt"),
                "ofcps_se_code_nm": d["ofcpsSeCodeNm"],
                "last_updt_dt": d.get("lastUpdtDt"),
            })