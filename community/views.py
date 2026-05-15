from rest_framework import permissions, status
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404

from .models import Post
from .serializers import PostSerializer


# =========================================================
# 글 목록 + 작성  (GET / POST)
# Content-Type : application/json  (form 전송 X)
# =========================================================

class PostListCreateView(APIView):
    """
    GET   /community/posts/        → 최신글 목록 (page=1 부터, 페이지당 10개)
    POST  /community/posts/        → 새 글 작성 (JSON)
    """
    parser_classes = [JSONParser]   # ★ JSON 만 받음

    PAGE_SIZE = 10

    def get_permissions(self):
        # 글쓰기는 로그인 필요, 목록은 누구나 조회 가능
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get(self, request):
        category = request.query_params.get("category", "").strip()
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except (TypeError, ValueError):
            page = 1

        qs = Post.objects.all().select_related("author")
        if category:
            qs = qs.filter(category=category)

        total = qs.count()
        start = (page - 1) * self.PAGE_SIZE
        end   = start + self.PAGE_SIZE
        items = qs[start:end]

        return Response({
            "success":  True,
            "results":  PostSerializer(items, many=True).data,
            "page":     page,
            "page_size": self.PAGE_SIZE,
            "total":    total,
            "has_next": end < total,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if not serializer.is_valid():
            # ErrorDict → 첫 메시지 한 줄로 정리 (JS 표시용)
            first_err = next(iter(serializer.errors.values()), ["유효성 검사 실패"])
            msg = first_err[0] if isinstance(first_err, list) and first_err else str(first_err)
            return Response(
                {"success": False, "error": str(msg)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        post = serializer.save(author=request.user)
        return Response(
            {"success": True, "post": PostSerializer(post).data},
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# 글 삭제 (DELETE)
# =========================================================

class PostDeleteView(APIView):
    """DELETE /community/posts/<pk>/delete/  → 본인 글만 삭제"""

    parser_classes     = [JSONParser]
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)

        if post.author != request.user and not request.user.is_staff:
            return Response(
                {"success": False, "error": "삭제 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        post.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)
