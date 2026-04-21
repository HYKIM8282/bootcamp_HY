
# brokers/models.py
class BrokerOffice(models.Model):
    jurirno    = models.CharField(max_length=50, unique=True, verbose_name="등록번호")
    bsnm_cmpnm = models.CharField(max_length=200, verbose_name="사업자상호")
    # ... 나머지 필드


class Broker(models.Model):
    # ── FK로 사무소와 연결 ─────────────────────────
    office = models.ForeignKey(
        BrokerOffice,
        on_delete=models.CASCADE,
        related_name="brokers",     # office.brokers.all() 로 소속 중개업자 조회
        null=True, blank=True,
        verbose_name="소속 사무소",
    )
    jurirno = models.CharField(max_length=50, verbose_name="등록번호", db_index=True)
    brkr_nm = models.CharField(max_length=100, verbose_name="중개업자명")
    # ... 나머지 필드


# 사용 예시
office  = BrokerOffice.objects.get(jurirno="가123456-789")
brokers = office.brokers.all()          # 소속 중개업자 전체
rep     = office.brokers.filter(ofcps_se_code="01").first()  # 대표만