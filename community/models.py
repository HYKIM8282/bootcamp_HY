from django.conf import settings
from django.db import models


class Post(models.Model):
    """커뮤니티 게시글 — 제목·본문·카테고리·좋아요·조회수.

    역할: 사용자가 작성하는 커뮤니티 글.
    영향:
    - community/PostLike 와 1:N (좋아요)
    - community/views.py PostViewSet 에서 CRUD
    - templates/community/board.html 에서 렌더링

    향후 확장: 댓글 모델 추가, 공유링크 필드 추가 검토 중
    """

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
    nickname = models.CharField(
        max_length=30,
        blank=True,
        default="",
        verbose_name="익명 닉네임",
        help_text="입력 시 이 닉네임으로 표시. 비우면 회원 username 사용.",
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


class PostLike(models.Model):
    """글 좋아요 — 1인 1회 제한을 DB 레벨에서 보장."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="게시글",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_likes",
        verbose_name="사용자",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")

    class Meta:
        db_table        = "community_post_like"
        unique_together = [("post", "user")]  # ★ 1인 1좋아요
        verbose_name        = "글 좋아요"
        verbose_name_plural = "글 좋아요 목록"

    def __str__(self):
        return f"{self.user} → {self.post_id}"
