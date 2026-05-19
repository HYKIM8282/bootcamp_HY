from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.db.models import F
from django.shortcuts import render

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from interactions.models import Image
from interactions.serializers import ImageSerializer

from .models import Post, PostLike
from .serializers import PostSerializer


# =========================================================
# 커뮤니티 게시판 페이지 (HTML 렌더링) — 로그인 없이 접근 가능
# =========================================================

def board_view(request):
    """커뮤니티 게시판 페이지: /community/ — 로그인 없이도 목록 조회 가능."""
    return render(request, "community/board.html")


# =========================================================
# Post ViewSet — CRUD 전체 제공
#   - 목록/상세 조회: 누구나 가능 (AllowAny)
#   - 작성/수정/삭제: 로그인 필요 (IsAuthenticated) + 본인 글만 수정/삭제
# =========================================================

class PostViewSet(viewsets.ModelViewSet):
    """
    /community/api/posts/         GET   목록
    /community/api/posts/         POST  작성 (로그인 필요)
    /community/api/posts/<pk>/    GET   상세 (조회수 +1)
    /community/api/posts/<pk>/    PATCH 수정 (작성자 본인만)
    /community/api/posts/<pk>/    DELETE 삭제 (작성자 본인만)
    /community/api/posts/<pk>/like/   POST 좋아요 +1 (로그인 필요)
    """
    queryset           = Post.objects.all().select_related("author")
    serializer_class   = PostSerializer
    parser_classes     = [JSONParser]

    PAGE_SIZE = 10

    # ─────────────────────────────────────────────────────
    # 권한: 읽기는 누구나, 쓰기는 로그인 필요
    # ─────────────────────────────────────────────────────
    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    # ─────────────────────────────────────────────────────
    # 목록: ?category=&page= 파라미터 + 페이지네이션
    # 응답 형식은 CLAUDE.md API 표준에 맞춤
    # ─────────────────────────────────────────────────────
    def list(self, request, *args, **kwargs):
        category = request.query_params.get("category", "").strip()
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except (TypeError, ValueError):
            page = 1

        qs = self.get_queryset()
        if category:
            qs = qs.filter(category=category)

        total = qs.count()
        start = (page - 1) * self.PAGE_SIZE
        end   = start + self.PAGE_SIZE
        items = qs[start:end]

        return Response({
            "success": True,
            "data": PostSerializer(items, many=True).data,
            "meta": {
                "total":     total,
                "page":      page,
                "page_size": self.PAGE_SIZE,
                "has_next":  end < total,
            },
        }, status=status.HTTP_200_OK)

    # ─────────────────────────────────────────────────────
    # 상세: 조회수 +1
    # ─────────────────────────────────────────────────────
    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        Post.objects.filter(pk=post.pk).update(view_count=F("view_count") + 1)
        post.refresh_from_db()
        return Response(
            {"success": True, "data": PostSerializer(post).data},
            status=status.HTTP_200_OK,
        )

    # ─────────────────────────────────────────────────────
    # 작성: author = 로그인 사용자, nickname은 요청 데이터에서
    # ─────────────────────────────────────────────────────
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "VALIDATION", "message": _first_error(serializer.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        post = serializer.save(author=request.user)
        return Response(
            {"success": True, "data": PostSerializer(post).data},
            status=status.HTTP_201_CREATED,
        )

    # ─────────────────────────────────────────────────────
    # 수정/삭제: 본인 글만 가능
    # ─────────────────────────────────────────────────────
    def update(self, request, *args, **kwargs):
        del args, kwargs  # DRF router 호환용 시그니처 — 본문은 직접 처리
        post = self.get_object()
        if not self._is_owner(request.user, post):
            return Response(
                {"success": False, "error": {"code": "FORBIDDEN", "message": "수정 권한이 없습니다."}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(post, data=request.data, partial=False)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "VALIDATION", "message": _first_error(serializer.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(
            {"success": True, "data": PostSerializer(post).data},
            status=status.HTTP_200_OK,
        )

    def partial_update(self, request, *args, **kwargs):
        del args, kwargs  # DRF router 호환용 시그니처 — 본문은 직접 처리
        post = self.get_object()
        if not self._is_owner(request.user, post):
            return Response(
                {"success": False, "error": {"code": "FORBIDDEN", "message": "수정 권한이 없습니다."}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(post, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "VALIDATION", "message": _first_error(serializer.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        post.refresh_from_db()
        return Response(
            {"success": True, "data": PostSerializer(post).data},
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        if not self._is_owner(request.user, post):
            return Response(
                {"success": False, "error": {"code": "FORBIDDEN", "message": "삭제 권한이 없습니다."}},
                status=status.HTTP_403_FORBIDDEN,
            )
        post.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)

    # ─────────────────────────────────────────────────────
    # 좋아요 토글 — 1인 1회 (DB 유니크 제약으로 보장)
    #   처음 누르면 +1, 같은 사람이 다시 누르면 -1
    # ─────────────────────────────────────────────────────
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        user = request.user

        with transaction.atomic():
            try:
                PostLike.objects.create(post=post, user=user)
                Post.objects.filter(pk=post.pk).update(like_count=F("like_count") + 1)
                liked = True
            except IntegrityError:
                # 이미 좋아요를 누른 사용자 → 취소(언라이크)
                PostLike.objects.filter(post=post, user=user).delete()
                Post.objects.filter(pk=post.pk, like_count__gt=0).update(
                    like_count=F("like_count") - 1
                )
                liked = False

        post.refresh_from_db()
        return Response(
            {"success": True, "data": {"like_count": post.like_count, "liked": liked}},
            status=status.HTTP_200_OK,
        )

    # ─────────────────────────────────────────────────────
    # 이미지 업로드 — 게시글에 사진 첨부 (다중 가능)
    #   POST /community/api/posts/<pk>/upload_image/
    #   Content-Type: multipart/form-data (image, caption?, is_primary?)
    #   본인 글만 첨부 가능
    # ─────────────────────────────────────────────────────
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_image(self, request, pk=None):
        post = self.get_object()
        if not self._is_owner(request.user, post):
            return Response(
                {"success": False, "error": {"code": "FORBIDDEN", "message": "이미지 추가 권한이 없습니다."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ImageSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": {"code": "VALIDATION", "message": _first_error(serializer.errors)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        img = serializer.save(
            content_type=ContentType.objects.get_for_model(Post),
            object_id=post.pk,
            uploaded_by=request.user,
        )
        return Response(
            {"success": True, "data": ImageSerializer(img, context={"request": request}).data},
            status=status.HTTP_201_CREATED,
        )

    # ─────────────────────────────────────────────────────
    # 이미지 삭제
    #   DELETE /community/api/posts/<pk>/images/<image_pk>/
    #   본인 글의 이미지만 삭제 가능
    # ─────────────────────────────────────────────────────
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"images/(?P<image_pk>[^/.]+)",
        permission_classes=[permissions.IsAuthenticated],
        parser_classes=[JSONParser],
    )
    def delete_image(self, request, pk=None, image_pk=None):
        post = self.get_object()
        if not self._is_owner(request.user, post):
            return Response(
                {"success": False, "error": {"code": "FORBIDDEN", "message": "이미지 삭제 권한이 없습니다."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        img = Image.objects.filter(
            pk=image_pk,
            content_type=ContentType.objects.get_for_model(Post),
            object_id=post.pk,
        ).first()
        if not img:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "이미지를 찾을 수 없습니다."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        img.image.delete(save=False)
        img.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)

    # ─────────────────────────────────────────────────────
    @staticmethod
    def _is_owner(user, post):
        return post.author_id == user.id or user.is_staff


def _first_error(errors):
    """DRF errors dict → 첫 번째 메시지 한 줄로."""
    first = next(iter(errors.values()), ["유효성 검사 실패"])
    if isinstance(first, list) and first:
        return str(first[0])
    return str(first)
