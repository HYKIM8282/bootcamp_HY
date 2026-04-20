from django.db import models


class RealEstateAgent(models.Model):
    """부동산 중개업소 모델"""

    ld_code = models.CharField(
        max_length=10,
        verbose_name="시군구코드"
    )
    ld_code_nm = models.CharField(
        max_length=50,
        verbose_name="시군구명"
    )
    jurirno = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="등록번호"
    )
    bsnm_cmpnm = models.CharField(
        max_length=100,
        verbose_name="사업자상호"
    )
    brkr_nm = models.CharField(
        max_length=50,
        verbose_name="중개업자명"
    )
    sttus_se_code = models.CharField(
        max_length=5,
        verbose_name="상태구분코드"
    )
    sttus_se_code_nm = models.CharField(
        max_length=20,
        verbose_name="상태구분명"
    )
    regist_de = models.DateField(
        verbose_name="등록일자"
    )
    estbs_begin_de = models.DateField(
        null=True,
        blank=True,
        verbose_name="보증설정시작일"
    )
    estbs_end_de = models.DateField(
        null=True,
        blank=True,
        verbose_name="보증설정종료일"
    )
    last_updt_dt = models.DateField(
        verbose_name="데이터기준일자"
    )
    mnnmadr = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="지번주소"
    )
    rdnmadr = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="도로명주소"
    )
    rdnmadr_code = models.CharField(
        max_length=25,
        blank=True,
        verbose_name="도로명주소코드"
    )

    class Meta:
        db_table = "real_estate_agent"
        verbose_name = "부동산 중개업소"
        verbose_name_plural = "부동산 중개업소 목록"
        ordering = ["-regist_de"]

    def __str__(self):
        return f"[{self.jurirno}] {self.bsnm_cmpnm}"