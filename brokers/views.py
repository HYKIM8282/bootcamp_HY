from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views import View

from .models import RealEstateAgent, EBBrokerInfo
from .serializers import (
    RealEstateAgentSerializer,
    EBBrokerInfoSerializer,
    EBBrokerSearchParamSerializer,
)
from .management.commands.fetch_broker2 import EBBrokerAPIClient, EBBrokerRequestParams


# ── API용 ViewSet ──────────────────────────────────────────────

class RealEstateAgentViewSet(viewsets.ModelViewSet):
    queryset = RealEstateAgent.objects.all().order_by("-regist_de")
    serializer_class = RealEstateAgentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "bsnm_cmpnm",
        "brkr_nm",
        "jurirno",
        "ld_code_nm",
        "rdnmadr",
        "mnnmadr",
    ]
    ordering_fields = [
        "last_updt_dt",
        "ld_code_nm",
        "brkr_nm",
    ]

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        ld_code    = request.query_params.get("ldcode")
        bsnm_cmpnm = request.query_params.get("bsnm_cmpnm")
        jurirno    = request.query_params.get("jurirno")
        sttus      = request.query_params.get("sttus")

        if ld_code:
            qs = qs.filter(ld_code__icontains=ld_code)
        if bsnm_cmpnm:
            qs = qs.filter(bsnm_cmpnm__icontains=bsnm_cmpnm)
        if jurirno:
            qs = qs.filter(jurirno__icontains=jurirno)
        if sttus:
            qs = qs.filter(sttus_se_code=sttus)

        serializer = self.get_serializer(qs, many=True)
        return Response({"count": qs.count(), "results": serializer.data})

    @action(detail=False, methods=["post"], url_path="sync")
    def sync(self, request):
        from django.core.management import call_command
        call_command("fetch_broker")
        count = RealEstateAgent.objects.count()
        return Response({"message": "sync complete", "total": count})

class EBBrokerViewSet(viewsets.ModelViewSet):
    """
    부동산중개업자 ViewSet

    GET  /api/eb-brokers/         → list()   DB 목록 조회
    GET  /api/eb-brokers/search/  → search() V-World API 실시간 조회
    POST /api/eb-brokers/sync/    → sync()   API → DB upsert
    """

    queryset = EBBrokerInfo.objects.all()
    serializer_class = EBBrokerInfoSerializer

    # ── GET /api/eb-brokers/ (필터 적용) ──────────────────────
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()

        ld_code    = request.query_params.get("ld_code")
        brkr_nm    = request.query_params.get("brkr_nm")
        bsnm_cmpnm = request.query_params.get("bsnm_cmpnm")

        if ld_code:
            qs = qs.filter(ld_code__startswith=ld_code)
        if brkr_nm:
            qs = qs.filter(brkr_nm__icontains=brkr_nm)
        if bsnm_cmpnm:
            qs = qs.filter(bsnm_cmpnm__icontains=bsnm_cmpnm)

        serializer = self.get_serializer(qs, many=True)
        return Response({"count": qs.count(), "results": serializer.data})

    # ── GET /api/eb-brokers/search/ ───────────────────────────
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        """V-World API 실시간 조회 (DB 저장 없음)"""
        param_serializer = EBBrokerSearchParamSerializer(data=request.query_params)
        if not param_serializer.is_valid():
            return Response(param_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated  = param_serializer.validated_data
        api_params = EBBrokerRequestParams(
            ld_code     = validated.get("ld_code"),
            bsnm_cmpnm  = validated.get("bsnm_cmpnm"),
            brkr_nm     = validated.get("brkr_nm"),
            jurirno     = validated.get("jurirno"),
            num_of_rows = validated.get("num_of_rows", 10),
            page_no     = validated.get("page_no", 1),
        )

        client       = EBBrokerAPIClient()
        api_response = client.fetch(api_params)

        if api_response.has_error:
            return Response(
                {"error": api_response.error_code, "message": api_response.error_message},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "totalCount": api_response.total_count,
                "pageNo":     api_response.page_no,
                "numOfRows":  api_response.num_of_rows,
                "items": [
                    {
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
                    for item in api_response.items
                ],
            }
        )

    # ── POST /api/eb-brokers/sync/ ────────────────────────────
    @action(detail=False, methods=["post"], url_path="sync")
    def sync(self, request):
        """V-World API 조회 결과를 DB에 저장 (upsert)"""
        param_serializer = EBBrokerSearchParamSerializer(data=request.data)
        if not param_serializer.is_valid():
            return Response(param_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated  = param_serializer.validated_data
        api_params = EBBrokerRequestParams(
            ld_code     = validated.get("ld_code"),
            bsnm_cmpnm  = validated.get("bsnm_cmpnm"),
            brkr_nm     = validated.get("brkr_nm"),
            jurirno     = validated.get("jurirno"),
            num_of_rows = 1000,
        )

        client    = EBBrokerAPIClient()
        all_items = client.fetch_all(api_params)

        created_count = 0
        updated_count = 0

        for item in all_items:
            _, created = EBBrokerInfo.objects.update_or_create(
                jurirno = item.jurirno,
                ld_code = item.ld_code,
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
            {
                "synced":  len(all_items),
                "created": created_count,
                "updated": updated_count,
            },
            status=status.HTTP_200_OK,
        )


# ── 템플릿용 화면 뷰 ───────────────────────────────────────────




class BrokerListView(View):
    def get(self, request):
        agents = RealEstateAgent.objects.all().order_by("-regist_de")

        ldcode     = request.GET.get("ldcode", "").strip()
        bsnm_cmpnm = request.GET.get("bsnm_cmpnm", "").strip()
        jurirno    = request.GET.get("jurirno", "").strip()
        sttus      = request.GET.get("sttus", "").strip()

        if ldcode:
            agents = agents.filter(ld_code__icontains=ldcode)
        if bsnm_cmpnm:
            agents = agents.filter(bsnm_cmpnm__icontains=bsnm_cmpnm)
        if jurirno:
            agents = agents.filter(jurirno__icontains=jurirno)
        if sttus:
            agents = agents.filter(sttus_se_code=sttus)

        paginator   = Paginator(agents, 10)
        page_number = request.GET.get("page")
        page_obj    = paginator.get_page(page_number)

        return render(request, "brokers/agent_list.html", {"page_obj": page_obj})


class BrokerDetailView(View):
    def get(self, request, pk):
        agent = get_object_or_404(RealEstateAgent, pk=pk)
        return render(request, "brokers/detail.html", {"agent": agent})


class Broker2ListView(View):
    def get(self, request):
        qs = EBBrokerInfo.objects.all().order_by("ld_code_nm")

        ld_code    = request.GET.get("ld_code", "").strip()
        brkr_nm    = request.GET.get("brkr_nm", "").strip()
        bsnm_cmpnm = request.GET.get("bsnm_cmpnm", "").strip()

        if ld_code:
            qs = qs.filter(ld_code__startswith=ld_code)
        if brkr_nm:
            qs = qs.filter(brkr_nm__icontains=brkr_nm)
        if bsnm_cmpnm:
            qs = qs.filter(bsnm_cmpnm__icontains=bsnm_cmpnm)

        paginator   = Paginator(qs, 10)
        page_number = request.GET.get("page")
        page_obj    = paginator.get_page(page_number)

        return render(request, "brokers/broker2_list.html", {"page_obj": page_obj})


from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views import View

from .models import RealEstateAgent, EBBrokerInfo
from .serializers import (
    RealEstateAgentSerializer,
    EBBrokerInfoSerializer,
    EBBrokerSearchParamSerializer,
)
from .management.commands.fetch_broker2 import EBBrokerAPIClient, EBBrokerRequestParams


# ── API용 ViewSet ──────────────────────────────────────────────

class RealEstateAgentViewSet(viewsets.ModelViewSet):
    queryset = RealEstateAgent.objects.all().order_by("-regist_de")
    serializer_class = RealEstateAgentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "bsnm_cmpnm",
        "brkr_nm",
        "jurirno",
        "ld_code_nm",
        "rdnmadr",
        "mnnmadr",
    ]
    ordering_fields = [
        "last_updt_dt",
        "ld_code_nm",
        "brkr_nm",
    ]


class EBBrokerViewSet(viewsets.ModelViewSet):
    """
    부동산중개업자 ViewSet

    GET  /api/eb-brokers/         → list()   DB 목록 조회
    GET  /api/eb-brokers/search/  → search() V-World API 실시간 조회
    POST /api/eb-brokers/sync/    → sync()   API → DB upsert
    """

    queryset = EBBrokerInfo.objects.all()
    serializer_class = EBBrokerInfoSerializer

    # ── GET /api/eb-brokers/ (필터 적용) ──────────────────────
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()

        ld_code    = request.query_params.get("ld_code")
        brkr_nm    = request.query_params.get("brkr_nm")
        bsnm_cmpnm = request.query_params.get("bsnm_cmpnm")

        if ld_code:
            qs = qs.filter(ld_code__startswith=ld_code)
        if brkr_nm:
            qs = qs.filter(brkr_nm__icontains=brkr_nm)
        if bsnm_cmpnm:
            qs = qs.filter(bsnm_cmpnm__icontains=bsnm_cmpnm)

        serializer = self.get_serializer(qs, many=True)
        return Response({"count": qs.count(), "results": serializer.data})

    # ── GET /api/eb-brokers/search/ ───────────────────────────
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        """V-World API 실시간 조회 (DB 저장 없음)"""
        param_serializer = EBBrokerSearchParamSerializer(data=request.query_params)
        if not param_serializer.is_valid():
            return Response(param_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated  = param_serializer.validated_data
        api_params = EBBrokerRequestParams(
            ld_code     = validated.get("ld_code"),
            bsnm_cmpnm  = validated.get("bsnm_cmpnm"),
            brkr_nm     = validated.get("brkr_nm"),
            jurirno     = validated.get("jurirno"),
            num_of_rows = validated.get("num_of_rows", 10),
            page_no     = validated.get("page_no", 1),
        )

        client       = EBBrokerAPIClient()
        api_response = client.fetch(api_params)

        if api_response.has_error:
            return Response(
                {"error": api_response.error_code, "message": api_response.error_message},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {
                "totalCount": api_response.total_count,
                "pageNo":     api_response.page_no,
                "numOfRows":  api_response.num_of_rows,
                "items": [
                    {
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
                    for item in api_response.items
                ],
            }
        )

    # ── POST /api/eb-brokers/sync/ ────────────────────────────
    @action(detail=False, methods=["post"], url_path="sync")
    def sync(self, request):
        """V-World API 조회 결과를 DB에 저장 (upsert)"""
        param_serializer = EBBrokerSearchParamSerializer(data=request.data)
        if not param_serializer.is_valid():
            return Response(param_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated  = param_serializer.validated_data
        api_params = EBBrokerRequestParams(
            ld_code     = validated.get("ld_code"),
            bsnm_cmpnm  = validated.get("bsnm_cmpnm"),
            brkr_nm     = validated.get("brkr_nm"),
            jurirno     = validated.get("jurirno"),
            num_of_rows = 1000,
        )

        client    = EBBrokerAPIClient()
        all_items = client.fetch_all(api_params)

        created_count = 0
        updated_count = 0

        for item in all_items:
            _, created = EBBrokerInfo.objects.update_or_create(
                jurirno = item.jurirno,
                ld_code = item.ld_code,
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
            {
                "synced":  len(all_items),
                "created": created_count,
                "updated": updated_count,
            },
            status=status.HTTP_200_OK,
        )


# ── 템플릿용 화면 뷰 ───────────────────────────────────────────




class BrokerListView(View):
    def get(self, request):
        agents = RealEstateAgent.objects.all().order_by("-regist_de")

        ldcode     = request.GET.get("ldcode", "").strip()
        bsnm_cmpnm = request.GET.get("bsnm_cmpnm", "").strip()
        jurirno    = request.GET.get("jurirno", "").strip()
        sttus      = request.GET.get("sttus", "").strip()

        if ldcode:
            agents = agents.filter(ld_code__icontains=ldcode)
        if bsnm_cmpnm:
            agents = agents.filter(bsnm_cmpnm__icontains=bsnm_cmpnm)
        if jurirno:
            agents = agents.filter(jurirno__icontains=jurirno)
        if sttus:
            agents = agents.filter(sttus_se_code=sttus)

        paginator   = Paginator(agents, 10)
        page_number = request.GET.get("page")
        page_obj    = paginator.get_page(page_number)

        return render(request, "brokers/agent_list.html", {"page_obj": page_obj})


class BrokerDetailView(View):
    def get(self, request, pk):
        agent = get_object_or_404(RealEstateAgent, pk=pk)
        return render(request, "brokers/detail.html", {"agent": agent})


class Broker2ListView(View):
    def get(self, request):
        qs = EBBrokerInfo.objects.all().order_by("ld_code_nm")

        ld_code    = request.GET.get("ld_code", "").strip()
        brkr_nm    = request.GET.get("brkr_nm", "").strip()
        bsnm_cmpnm = request.GET.get("bsnm_cmpnm", "").strip()

        if ld_code:
            qs = qs.filter(ld_code__startswith=ld_code)
        if brkr_nm:
            qs = qs.filter(brkr_nm__icontains=brkr_nm)
        if bsnm_cmpnm:
            qs = qs.filter(bsnm_cmpnm__icontains=bsnm_cmpnm)

        paginator   = Paginator(qs, 10)
        page_number = request.GET.get("page")
        page_obj    = paginator.get_page(page_number)

        return render(request, "brokers/broker2_list.html", {"page_obj": page_obj})
        
