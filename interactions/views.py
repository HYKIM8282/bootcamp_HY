from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework import viewsets, permissions
from rest_framework.response import Response

from brokers.models import RealEstateAgent
from .models import Review
from .forms import ReviewForm
from .serializers import ReviewSerializer


# ────────────────────────────────────────────────
# DRF API ViewSet (선택 - API 용도)
# ────────────────────────────────────────────────

class ReviewViewSet(viewsets.ModelViewSet):
    """리뷰 API ViewSet"""

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # ✅ agent_pk 기준으로 필터링
        return Review.objects.filter(
            agent_id=self.kwargs.get('agent_pk')
        )

    def perform_create(self, serializer):
        agent = get_object_or_404(
            RealEstateAgent,
            pk=self.kwargs.get('agent_pk')
        )
        # ✅ 작성자, 중개업소 자동 저장
        serializer.save(author=self.request.user, agent=agent)


# ────────────────────────────────────────────────
# 템플릿 뷰 (화면용)
# ────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def review_create(request, agent_pk):
    """리뷰 작성"""
    agent = get_object_or_404(RealEstateAgent, pk=agent_pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.agent  = agent   # ✅ 중개업소 자동 연결
            review.author = request.user  # ✅ 작성자 자동 연결
            review.save()
            return redirect('brokers:broker1_detail', pk=agent_pk)
    else:
        form = ReviewForm()

    return render(request, 'interactions/review_form.html', {
        'form': form,
        'agent': agent,
    })


@login_required(login_url='/accounts/login/')
def review_delete(request, review_pk):
    """리뷰 삭제 (본인만 가능)"""
    review = get_object_or_404(Review, pk=review_pk)

    # ✅ 본인 리뷰만 삭제 가능
    if review.author == request.user:
        agent_pk = review.agent.pk
        review.delete()
        return redirect('brokers:broker1_detail', pk=agent_pk)

    return redirect('brokers:broker1_detail', pk=review.agent.pk)