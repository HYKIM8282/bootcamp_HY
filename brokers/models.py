from django.db import models
from django.conf import settings as django_settings

class RealEstateAgent(models.Model):
    ld_code = models.CharField(
        max_length=10,
        verbose_name="시군구코드",
    )
    ld_code_nm = models.CharField(
        max_length=50,
        verbose_name="시군구명",
    )
    jurirno = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="등록번호",
    )
    bsnm_cmpnm = models.CharField(
        max_length=100,
        verbose_name="사업자상호",
    )
    brkr_nm = models.CharField(
        max_length=50,
        verbose_name="중개업자명",
    )
    sttus_se_code = models.CharField(
        max_length=5,
        verbose_name="상태구분코드",
    )
    sttus_se_code_nm = models.CharField(
        max_length=20,
        verbose_name="상태구분명",
    )
    regist_de = models.DateField(
        verbose_name="등록일자",
    )
    estbs_begin_de = models.DateField(
        blank=True,
        null=True,
        verbose_name="보증설정시작일",
    )
    estbs_end_de = models.DateField(
        blank=True,
        null=True,
        verbose_name="보증설정종료일",
    )
    last_updt_dt = models.DateField(
        verbose_name="데이터기준일자",
    )
    mnnmadr = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="지번주소",
    )
    rdnmadr = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="도로명주소",
    )
    rdnmadr_code = models.CharField(
        max_length=25,
        blank=True,
        verbose_name="도로명주소코드",
    )

    class Meta:
        db_table = "real_estate_agent"
        verbose_name = "부동산 중개업소"
        verbose_name_plural = "부동산 중개업소 목록"
        ordering = ["-regist_de"]

    def __str__(self):
        return f"{self.bsnm_cmpnm} / {self.brkr_nm}"


class EBBrokerInfo(models.Model):
    """
    부동산중개업자정보조회 API (V-World) 응답 모델
    요청주소: https://api.vworld.kr/ned/data/getEBBrokerInfo
    """

    # 지역 정보
    ld_code = models.CharField(
        max_length=10,
        verbose_name="시군구코드",
        db_index=True,
    )
    ld_code_nm = models.CharField(
        max_length=100,
        verbose_name="시군구명",
        blank=True,
        default="",
    )

    # 업체 정보
    jurirno = models.CharField(
        max_length=50,
        verbose_name="등록번호",
        blank=True,
        default="",
        db_index=True,
    )
    bsnm_cmpnm = models.CharField(
        max_length=200,
        verbose_name="사업자상호",
        blank=True,
        default="",
    )

    # 중개업자 정보
    brkr_nm = models.CharField(
        max_length=100,
        verbose_name="중개업자명",
        blank=True,
        default="",
    )
    brkr_asort_code = models.CharField(
        max_length=10,
        verbose_name="중개업자종별코드",
        blank=True,
        default="",
    )
    brkr_asort_code_nm = models.CharField(
        max_length=50,
        verbose_name="중개업자종별명",
        blank=True,
        default="",
    )

    # 자격증 정보
    crqfc_no = models.CharField(
        max_length=50,
        verbose_name="자격증번호",
        blank=True,
        default="",
    )
    crqfc_acqdt = models.DateField(
        verbose_name="자격증취득일",
        null=True,
        blank=True,
    )

    # 직위 정보
    ofcps_se_code = models.CharField(
        max_length=10,
        verbose_name="직위구분코드",
        blank=True,
        default="",
    )
    ofcps_se_code_nm = models.CharField(
        max_length=50,
        verbose_name="직위구분명",
        blank=True,
        default="",
    )

    # 메타 정보
    last_updt_dt = models.DateField(
        verbose_name="데이터기준일자",
        null=True,
        blank=True,
    )
    fetched_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="수집일시",
    )

    class Meta:
        db_table = "eb_broker_info"
        verbose_name = "부동산중개업자정보"
        verbose_name_plural = "부동산중개업자정보 목록"
        indexes = [
            models.Index(fields=["ld_code", "brkr_nm"], name="idx_broker_code_name"),
            models.Index(fields=["bsnm_cmpnm"], name="idx_broker_company"),
        ]

    def __str__(self):
        return f"[{self.ld_code_nm}] {self.bsnm_cmpnm} - {self.brkr_nm}"
    

class BrokerImage(models.Model):
    """중개업소 pk에 연결되는 이미지 모델"""

    agent = models.ForeignKey(
        RealEstateAgent,
        on_delete=models.CASCADE,
        related_name='images',        # agent.images.all() 로 접근
        verbose_name='중개업소',
    )
    uploaded_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='업로더',
    )
    image = models.ImageField(
        upload_to='brokers/%Y/%m/',   # media/brokers/2026/04/ 폴더에 저장
        verbose_name='이미지',
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='사진 설명',
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name='대표이미지',
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='업로드일시',
    )

    class Meta:
        db_table = 'broker_image'
        verbose_name = '중개업소 이미지'
        verbose_name_plural = '중개업소 이미지 목록'
        ordering = ['-is_primary', '-uploaded_at']

    def __str__(self):
        return f"{self.agent.bsnm_cmpnm} - 이미지 {self.pk}"