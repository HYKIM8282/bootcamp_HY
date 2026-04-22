from django.contrib import admin
from .models import RealEstateAgent


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
