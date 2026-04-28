from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect 
from django.http import HttpResponseForbidden  
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from interactions.models import Review
from interactions.forms import ReviewForm

from .models import RealEstateAgent, EBBrokerInfo, BrokerImage      # BrokerImage 추가
from .forms import BrokerImageForm   
from .serializers import (
    RealEstateAgentSerializer,
    EBBrokerInfoSerializer,
    EBBrokerSearchParamSerializer,
    RealEstateAgentDetailSerializer,
)
from .management.commands.fetch_broker2 import EBBrokerAPIClient, EBBrokerRequestParams


# ────────────────────────────────────────────────
# API1 ViewSets (DRF)
# ────────────────────────────────────────────────

class RealEstateAgentViewSet(viewsets.ModelViewSet):
    queryset = RealEstateAgent.objects.all().order_by("-regist_de")
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["bsnm_cmpnm", "brkr_nm", "jurirno", "ld_code_nm", "rdnmadr", "mnnmadr"]
    ordering_fields = ["last_updt_dt", "ld_code_nm", "brkr_nm"]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RealEstateAgentDetailSerializer
        return RealEstateAgentSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if v := request.query_params.get("ldcode"):
            qs = qs.filter(ld_code__icontains=v)
        if v := request.query_params.get("bsnm_cmpnm"):
            qs = qs.filter(bsnm_cmpnm__icontains=v)
        if v := request.query_params.get("jurirno"):
            qs = qs.filter(jurirno__icontains=v)
        if v := request.query_params.get("sttus"):
            qs = qs.filter(sttus_se_code=v)
        serializer = self.get_serializer(qs, many=True)
        return Response({"count": qs.count(), "results": serializer.data})

    @action(detail=False, methods=["post"], url_path="sync")
    def sync(self, request):
        from django.core.management import call_command
        call_command("fetch_broker")
        return Response({"message": "sync complete", "total": RealEstateAgent.objects.count()})


# ────────────────────────────────────────────────
# API2 ViewSets (DRF)
# ────────────────────────────────────────────────

class EBBrokerViewSet(viewsets.ModelViewSet):
    queryset = EBBrokerInfo.objects.all()
    serializer_class = EBBrokerInfoSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if v := request.query_params.get("ld_code"):
            qs = qs.filter(ld_code__startswith=v)
        if v := request.query_params.get("brkr_nm"):
            qs = qs.filter(brkr_nm__icontains=v)
        if v := request.query_params.get("bsnm_cmpnm"):
            qs = qs.filter(bsnm_cmpnm__icontains=v)
        serializer = self.get_serializer(qs, many=True)
        return Response({"count": qs.count(), "results": serializer.data})

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        param_serializer = EBBrokerSearchParamSerializer(data=request.query_params)
        if not param_serializer.is_valid():
            return Response(param_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        api_response = self._call_api(param_serializer.validated_data)
        if api_response.has_error:
            return Response(
                {"error": api_response.error_code, "message": api_response.error_message},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({
            "totalCount": api_response.total_count,
            "pageNo":     api_response.page_no,
            "numOfRows":  api_response.num_of_rows,
            "items":      [self._serialize_item(item) for item in api_response.items],
        })

    @action(detail=False, methods=["post"], url_path="sync")
    def sync(self, request):
        param_serializer = EBBrokerSearchParamSerializer(data=request.data)
        if not param_serializer.is_valid():
            return Response(param_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated = param_serializer.validated_data
        api_params = EBBrokerRequestParams(
            ld_code=validated.get("ld_code"),
            bsnm_cmpnm=validated.get("bsnm_cmpnm"),
            brkr_nm=validated.get("brkr_nm"),
            jurirno=validated.get("jurirno"),
            num_of_rows=1000,
        )
        all_items = EBBrokerAPIClient().fetch_all(api_params)
        created_count = updated_count = 0
        for item in all_items:
            _, created = EBBrokerInfo.objects.update_or_create(
                jurirno=item.jurirno,
                ld_code=item.ld_code,
                defaults={
                    "ld_code_nm":         item.ld_code_nm,
                    "bsnm_cmpnm":         item.bsnm_cmpnm,
                    "brkr_nm":            item.brkr_nm,
                    "brkr_asort_code":    item.brkr_asort_code,
                    "brkr_asort_code_nm": item.brkr_asort_code_nm,
                    "crqfc_no":           item.crqfc_no,
                    "crqfc_acqdt":        item.crqfc_acqdt,
                    "ofcps_se_code":      item.ofcps_se_code,
                    "ofcps_se_code_nm":   item.ofcps_se_code_nm,
                    "last_updt_dt":       item.last_updt_dt,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        return Response(
            {"synced": len(all_items), "created": created_count, "updated": updated_count},
            status=status.HTTP_200_OK,
        )

    def _call_api(self, validated: dict):
        params = EBBrokerRequestParams(
            ld_code=validated.get("ld_code"),
            bsnm_cmpnm=validated.get("bsnm_cmpnm"),
            brkr_nm=validated.get("brkr_nm"),
            jurirno=validated.get("jurirno"),
            num_of_rows=validated.get("num_of_rows", 10),
            page_no=validated.get("page_no", 1),
        )
        return EBBrokerAPIClient().fetch(params)

    @staticmethod
    def _serialize_item(item) -> dict:
        return {
            "ldCode":          item.ld_code,
            "ldCodeNm":        item.ld_code_nm,
            "jurirno":         item.jurirno,
            "bsnmCmpnm":       item.bsnm_cmpnm,
            "brkrNm":          item.brkr_nm,
            "brkrAsortCode":   item.brkr_asort_code,
            "brkrAsortCodeNm": item.brkr_asort_code_nm,
            "crqfcNo":         item.crqfc_no,
            "crqfcAcqdt":      item.crqfc_acqdt,
            "ofcpsSecode":     item.ofcps_se_code,
            "ofcpsSeCodeNm":   item.ofcps_se_code_nm,
            "lastUpdtDt":      item.last_updt_dt,
        }


# ────────────────────────────────────────────────
# 템플릿 뷰1
# ────────────────────────────────────────────────

# ❌ 삭제: BrokerListView(View) 중복 선언 제거
# ✅ LoginRequiredMixin 버전 하나만 유지
class BrokerListView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        qs = RealEstateAgent.objects.all().order_by("-regist_de")
        if v := request.GET.get("ldcode", "").strip():
            qs = qs.filter(ld_code__icontains=v)
        if v := request.GET.get("bsnm_cmpnm", "").strip():
            qs = qs.filter(bsnm_cmpnm__icontains=v)
        if v := request.GET.get("jurirno", "").strip():
            qs = qs.filter(jurirno__icontains=v)
        if v := request.GET.get("sttus", "").strip():
            qs = qs.filter(sttus_se_code=v)
        page_obj = Paginator(qs, 10).get_page(request.GET.get("page"))
        return render(request, "brokers/broker1_list.html", {"page_obj": page_obj})


# ────────────────────────────────────────────────
# 상세 뷰
# ────────────────────────────────────────────────
class BrokerDetailView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request, pk):
        agent   = get_object_or_404(RealEstateAgent, pk=pk)
        reviews = Review.objects.filter(agent=agent).select_related('author')
        images  = BrokerImage.objects.filter(agent=agent)        # ← 추가

        avg_score = 0
        if reviews.exists():
            avg_score = round(
                sum(r.score for r in reviews) / reviews.count(), 1
            )

        return render(request, 'brokers/detail.html', {
            'agent':        agent,
            'reviews':      reviews,
            'avg_score':    avg_score,
            'review_count': reviews.count(),
            'form':         ReviewForm(),
            'image_form':   BrokerImageForm(),   # ← 추가
            'images':       images,              # ← 추가
        })


# ────────────────────────────────────────────────
# 템플릿 뷰2
# ────────────────────────────────────────────────

# ❌ 삭제: Broker2ListView(View) 중복 선언 제거
# ✅ LoginRequiredMixin 버전 하나만 유지
class Broker2ListView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def get(self, request):
        qs = EBBrokerInfo.objects.all().order_by("ld_code_nm")
        if v := request.GET.get("ld_code", "").strip():
            qs = qs.filter(ld_code__startswith=v)
        if v := request.GET.get("brkr_nm", "").strip():
            qs = qs.filter(brkr_nm__icontains=v)
        if v := request.GET.get("bsnm_cmpnm", "").strip():
            qs = qs.filter(bsnm_cmpnm__icontains=v)
        page_obj = Paginator(qs, 10).get_page(request.GET.get("page"))
        return render(request, "brokers/broker2_list.html", {"page_obj": page_obj})
    

# ─────────────────────────────────────────────
# 이미지 업로드 뷰
# ─────────────────────────────────────────────

class BrokerImageUploadView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, pk):
        agent = get_object_or_404(RealEstateAgent, pk=pk)
        form  = BrokerImageForm(request.POST, request.FILES)
        if form.is_valid():
            img             = form.save(commit=False)
            img.agent       = agent
            img.uploaded_by = request.user
            img.save()
        return redirect('brokers:broker1_detail', pk=pk)


# ─────────────────────────────────────────────
# 이미지 삭제 뷰
# ─────────────────────────────────────────────

class BrokerImageDeleteView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request, image_pk):
        img = get_object_or_404(BrokerImage, pk=image_pk)

        # 업로드한 본인 또는 관리자만 삭제 가능
        if img.uploaded_by != request.user and not request.user.is_staff:
            return HttpResponseForbidden()

        agent_pk = img.agent.pk
        img.image.delete(save=False)   # 디스크에서도 파일 삭제
        img.delete()
        return redirect('brokers:broker1_detail', pk=agent_pk)