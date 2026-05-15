from django.conf import settings
from django.db import models


class Post(models.Model):
    """커뮤니티 글 — 포켓메뉴에서 등록·조회"""

    CATEGORY_CHOICES = [
        ("latest", "최신글"),
        ("hot",    "인기글"),
        ("region", "관심동네"),
    ]

    title    = models.CharField(max_length=80,  verbose_name="제목")
    content  = models.TextField(verbose_name="본문")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="latest",
        verbose_name="카테고리",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="작성자",
    )
    like_count = models.PositiveIntegerField(default=0, verbose_name="좋아요수")
    view_count = models.PositiveIntegerField(default=0, verbose_name="조회수")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")
    updated_at = models.DateTimeField(auto_now=True,     verbose_name="수정일")

    class Meta:
        db_table            = "community_post"
        ordering            = ["-created_at"]   # ★ 최신글이 항상 상위
        verbose_name        = "커뮤니티 글"
        verbose_name_plural = "커뮤니티 글 목록"

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"
