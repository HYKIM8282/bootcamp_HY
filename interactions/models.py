from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from brokers.models import RealEstateAgent


class Review(models.Model):
    """중개사 리뷰 — 별점(1~5) + 텍스트 + 작성자.

    역할: 사용자가 부동산 중개업소(RealEstateAgent)에 남기는 평가.
    영향:
    - brokers/RealEstateAgent 와 FK 연결 (agent_id)
    - brokers/views.py BrokerDetailView 에서 표시
    - brokers/serializers.py RealEstateAgentDetailSerializer 에 nested 포함
    """

    # 별점 선택지
    SCORE_CHOICES = [
        (1, '⭐ 1점'),
        (2, '⭐⭐ 2점'),
        (3, '⭐⭐⭐ 3점'),
        (4, '⭐⭐⭐⭐ 4점'),
        (5, '⭐⭐⭐⭐⭐ 5점'),
    ]

    # ✅ 어떤 중개업소에 대한 리뷰인지 (broker pk 연동)
    agent    = models.ForeignKey(
        RealEstateAgent,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    # ✅ 누가 작성했는지
    author   = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    # ✅ 별점 (1~5)
    score    = models.PositiveSmallIntegerField(choices=SCORE_CHOICES)

    # ✅ 리뷰 내용
    content  = models.TextField()

    # ✅ 리뷰 이미지 (선택)
    image = models.ImageField(
        upload_to='reviews/%Y/%m/',
        null=True, blank=True,
        verbose_name='리뷰 이미지',
    )

    # ✅ 작성일 / 수정일
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # 최신순 정렬

    def __str__(self):
        return f"[{self.score}점] {self.agent.bsnm_cmpnm} - {self.author.username}"


class Image(models.Model):
    """범용 이미지 첨부 모델.

    GenericForeignKey(GFK)로 어떤 모델에든 붙음. 예: 중개업소(RealEstateAgent),
    리뷰(Review), 커뮤니티 글(Post). 도메인별로 분산된 이미지 코드를 한곳으로 통합.
    """

    # 어느 모델의 어느 객체에 붙는지
    content_type   = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='대상 모델')
    object_id      = models.PositiveIntegerField(verbose_name='대상 PK')
    content_object = GenericForeignKey('content_type', 'object_id')

    # 이미지 본체
    image      = models.ImageField(upload_to='images/%Y/%m/', verbose_name='이미지')
    caption    = models.CharField(max_length=200, blank=True, verbose_name='설명')
    is_primary = models.BooleanField(default=False, verbose_name='대표 이미지')

    # 메타
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='업로더',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='업로드일시')

    class Meta:
        db_table = 'interactions_image'
        ordering = ['-is_primary', '-uploaded_at']
        indexes  = [models.Index(fields=['content_type', 'object_id'], name='idx_image_target')]
        verbose_name        = '이미지'
        verbose_name_plural = '이미지 목록'

    def __str__(self):
        return f"Image {self.pk} → {self.content_type}({self.object_id})"

    def save(self, *args, **kwargs):
        # 같은 대상에서 is_primary=True 인 이미지는 1장만 유지 (BrokerImage 버그 흡수 수정)
        if self.is_primary:
            type(self).objects.filter(
                content_type=self.content_type,
                object_id=self.object_id,
                is_primary=True,
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)