from django.contrib import admin
from .models import BrokerOffice, Broker


class BrokerInline(admin.TabularInline):
    model            = Broker
    extra            = 0
    fields           = ("brkr_nm", "ofcps_se_code_nm", "brkr_asort_code_nm",
                         "crqfc_no", "crqfc_acqdt")
    show_change_link = True


@admin.register(BrokerOffice)
class BrokerOfficeAdmin(admin.ModelAdmin):
    list_display    = ("jurirno", "bsnm_cmpnm", "brkr_nm",
                        "ld_code_nm", "sttus_se_code_nm",
                        "regist_de", "estbs_begin_de", "estbs_end_de")
    list_filter     = ("sttus_se_code", "ld_code_nm")
    search_fields   = ("jurirno", "bsnm_cmpnm", "brkr_nm", "rdnmadr")
    readonly_fields = ("created_at", "updated_at")
    inlines         = [BrokerInline]


@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display    = ("brkr_nm", "ofcps_se_code_nm", "brkr_asort_code_nm",
                        "crqfc_no", "bsnm_cmpnm")
    list_filter     = ("ofcps_se_code", "brkr_asort_code")
    search_fields   = ("brkr_nm", "crqfc_no", "jurirno", "bsnm_cmpnm")
    readonly_fields = ("created_at", "updated_at")