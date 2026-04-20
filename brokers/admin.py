from django.contrib import admin
from .models import RealEstateAgent


@admin.register(RealEstateAgent)
class RealEstateAgentAdmin(admin.ModelAdmin):

    # 목록 페이지에서 보여줄 컬럼
    list_display = [
        'jurirno',
        'bsnm_cmpnm',
        'brkr_nm',
        'ld_code_nm',
        'sttus_se_code_nm',
        'regist_de',
        'last_updt_dt',
    ]

    # 오른쪽 필터 패널
    list_filter = [
        'sttus_se_code_nm',
        'ld_code_nm',
        'regist_de',
    ]

    # 상단 검색창 (검색 가능한 필드)
    search_fields = [
        'bsnm_cmpnm',
        'brkr_nm',
        'jurirno',
        'rdnmadr',
        'mnnmadr',
    ]

    # 읽기 전용 필드 (수정 불가)
    readonly_fields = [
        'jurirno',
        'last_updt_dt',
        'regist_de',
    ]

    # 상세 페이지 섹션 구분
    fieldsets = [
        ('기본 정보', {
            'fields': [
                'jurirno',
                'bsnm_cmpnm',
                'brkr_nm',
            ]
        }),
        ('지역 정보', {
            'fields': [
                'ld_code',
                'ld_code_nm',
                'mnnmadr',
                'rdnmadr',
                'rdnmadr_code',
            ]
        }),
        ('상태 정보', {
            'fields': [
                'sttus_se_code',
                'sttus_se_code_nm',
                'regist_de',
            ]
        }),
        ('보증 정보', {
            'fields': [
                'estbs_begin_de',
                'estbs_end_de',
            ],
            'classes': ['collapse'],  # 기본 접혀있음
        }),
        ('데이터 기준', {
            'fields': [
                'last_updt_dt',
            ]
        }),
    ]

    # 한 페이지에 보여줄 데이터 수
    list_per_page = 20

    # 목록에서 클릭 시 이동할 필드
    list_display_links = ['jurirno', 'bsnm_cmpnm']