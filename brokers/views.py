from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin 

from .models import RealEstateAgent, EBBrokerInfo
from .serializers import (
    RealEstateAgentSerializer,
    EBBrokerInfoSerializer,
    EBBrokerSearchParamSerializer,
)
from .management.commands.fetch_broker2 import EBBrokerAPIClient, EBBrokerRequestParams


# ────────────────────────────────────────────────
# API1 ViewSets (DRF)
# ────────────────────────────────────────────────

class RealEstateAgentViewSet(viewsets.ModelViewSet):
    """공인중개사 CRUD + 검색·정렬 + DB 동기화"""

    queryset = RealEstateAgent.objects.all().order_by("-regist_de")
    serializer_class = RealEstateAgentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["bsnm_cmpnm", "brkr_nm", "jurirno", "ld_code_nm", "rdnmadr", "mnnmadr"]
    ordering_fields = ["last_updt_dt", "ld_code_nm", "brkr_nm"]

    def list(self, request, *args, **kwargs):
        """쿼리 파라미터로 필터링 후 목록 반환"""
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
        """관리 커맨드 실행 → DB 동기화"""
        from django.core.management import call_command
        call_command("fetch_broker")
        return Response({"message": "sync complete", "total": RealEstateAgent.objects.count()})


# ────────────────────────────────────────────────
# API2 ViewSets (DRF)
# ────────────────────────────────────────────────

class EBBrokerViewSet(viewsets.ModelViewSet):
    """
    부동산중개업자 ViewSet

    GET  /api/eb-brokers/         → list()   DB 목록 조회
    GET  /api/eb-brokers/search/  → search() V-World API 실시간 조회
    POST /api/eb-brokers/sync/    → sync()   API → DB upsert
    """

    queryset = EBBrokerInfo.objects.all()
    serializer_class = EBBrokerInfoSerializer

    def list(self, request, *args, **kwargs):
        """쿼리 파라미터로 필터링 후 DB 목록 반환"""
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
        """V-World API 실시간 조회 (DB 저장 없음)"""
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
        """V-World API 결과를 DB에 upsert"""
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

    # ── 내부 헬퍼 ──────────────────────────────────────────────

    def _call_api(self, validated: dict):
        """validated_data → EBBrokerAPIClient.fetch() 호출"""
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
        """API 응답 단일 항목을 camelCase dict으로 변환"""
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
# 템플릿 뷰1 (Django View)
# ────────────────────────────────────────────────

class BrokerListView(View):
    """공인중개사 목록 화면 (페이지네이션 + 필터)"""

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
    
class BrokerListView(LoginRequiredMixin, View):  # ✅ LoginRequiredMixin 추가
    login_url = '/accounts/login/'               # ✅ 추가

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
#디테일 CLASS추가
# ────────────────────────────────────────────────


class BrokerDetailView(View):
    """공인중개사 상세 화면"""

    def get(self, request, pk):
        agent = get_object_or_404(RealEstateAgent, pk=pk)
        return render(request, "brokers/detail.html", {"agent": agent})
    
# 수정 후: LoginRequiredMixin 추가 → 비로그인 시 /accounts/login/ 으로 자동 이동
class BrokerDetailView(LoginRequiredMixin, View):  # ✅ LoginRequiredMixin 추가
    login_url = '/accounts/login/'                 # ✅ 추가

    def get(self, request, pk):
        agent = get_object_or_404(RealEstateAgent, pk=pk)
        return render(request, "brokers/detail.html", {"agent": agent})


# ────────────────────────────────────────────────
# 템플릿 뷰2 (Django View)
# ────────────────────────────────────────────────

class Broker2ListView(View):
    """부동산중개업자(API2) 목록 화면 (페이지네이션 + 필터)"""

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
    
# 수정 후: LoginRequiredMixin 추가 → 비로그인 시 /accounts/login/ 으로 자동 이동
class Broker2ListView(LoginRequiredMixin, View):  # ✅ LoginRequiredMixin 추가
    login_url = '/accounts/login/'                # ✅ 추가

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

# ────────────────────────────────────────────────
#디테일 CLASS추가
# ────────────────────────────────────────────────
