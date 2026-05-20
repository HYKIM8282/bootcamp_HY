from django.contrib import admin
from .models import RealEstateAgent, EBBrokerInfo



@admin.register(RealEstateAgent)
class RealEstateAgentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "jurirno",
        "bsnm_cmpnm",
        "brkr_nm",
        "ld_code",
        "ld_code_nm",
        "sttus_se_code",
        "sttus_se_code_nm",
        "regist_de",
        "last_updt_dt",
    )

    search_fields = (
        "jurirno",
        "bsnm_cmpnm",
        "brkr_nm",
        "ld_code",
        "ld_code_nm",
        "rdnmadr",
        "mnnmadr",
    )

    list_filter = (
        "sttus_se_code",
        "sttus_se_code_nm",
        "ld_code_nm",
        "regist_de",
        "last_updt_dt",
    )

    ordering = ("-regist_de",)
    list_per_page = 20

    readonly_fields = (
        "regist_de",
        "last_updt_dt",
    )

    fieldsets = (
        (
            "기본 정보",
            {
                "fields": (
                    "jurirno",
                    "bsnm_cmpnm",
                    "brkr_nm",
                    "sttus_se_code",
                    "sttus_se_code_nm",
                )
            },
        ),
        (
            "지역 정보",
            {
                "fields": (
                    "ld_code",
                    "ld_code_nm",
                    "rdnmadr_code",
                    "rdnmadr",
                    "mnnmadr",
                )
            },
        ),
        (
            "일자 정보",
            {
                "fields": (
                    "regist_de",
                    "estbs_begin_de",
                    "estbs_end_de",
                    "last_updt_dt",
                )
            },
        ),
    )


@admin.register(EBBrokerInfo)
class EBBrokerInfoAdmin(admin.ModelAdmin):
    # 목록 화면
    list_display = (
        "ld_code",
        "ld_code_nm",
        "jurirno",
        "bsnm_cmpnm",
        "brkr_nm",
        "brkr_asort_code_nm",
        "ofcps_se_code_nm",
        "last_updt_dt",
        "fetched_at",
    )
    list_filter = (
        "brkr_asort_code_nm",
        "ofcps_se_code_nm",
        "ld_code_nm",
        "last_updt_dt",
    )
    search_fields = (
        "jurirno",
        "bsnm_cmpnm",
        "brkr_nm",
        "ld_code",
        "ld_code_nm",
        "crqfc_no",
    )
    readonly_fields = ("fetched_at",)
    ordering = ("-fetched_at",)
    date_hierarchy = "fetched_at"

    # 상세 화면 필드 그룹
    fieldsets = (
        ("지역 정보", {
            "fields": ("ld_code", "ld_code_nm"),
        }),
        ("업체 정보", {
            "fields": ("jurirno", "bsnm_cmpnm"),
        }),
        ("중개업자 정보", {
            "fields": ("brkr_nm", "brkr_asort_code", "brkr_asort_code_nm"),
        }),
        ("자격증 정보", {
            "fields": ("crqfc_no", "crqfc_acqdt"),
        }),
        ("직위 정보", {
            "fields": ("ofcps_se_code", "ofcps_se_code_nm"),
        }),
        ("메타 정보", {
            "fields": ("last_updt_dt", "fetched_at"),
        }),
    )
