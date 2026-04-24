from django.db import models
from django.contrib.auth.models import User
from brokers.models import RealEstateAgent


class Review(models.Model):

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

    # ✅ 작성일 / 수정일
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # 최신순 정렬

    def __str__(self):
        return f"[{self.score}점] {self.agent.bsnm_cmpnm} - {self.author.username}"