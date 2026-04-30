from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from interactions.forms import ReviewForm
from interactions.models import Review

from .forms import BrokerImageForm
from .management.commands.fetch_broker2 import EBBrokerAPIClient, EBBrokerRequestParams
from .models import BrokerImage, EBBrokerInfo, RealEstateAgent
from .serializers import (
    EBBrokerInfoSerializer,
    EBBrokerSearchParamSerializer,
    RealEstateAgentDetailSerializer,
    RealEstateAgentMapSerializer,
    RealEstateAgentSerializer,
)


# =========================================================
# API ViewSets
# =========================================================

class RealEstateAgentViewSet(viewsets.ModelViewSet):
    queryset = RealEstateAgent.objects.all().order_by("-regist_de")
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["bsnm_cmpnm", "brkr_nm", "jurirno", "ld_code_nm", "rdnmadr", "mnnmadr"]
    ordering_fields = ["last_updt_dt", "ld_code_nm", "brkr_nm"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RealEstateAgentDetailSerializer
        if self.request.query_params.get("map_only"):
            return RealEstateAgentMapSerializer
        return RealEstateAgentSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()

        if v := request.query_params.get("ldcode", "").strip():
            qs = qs.filter(ld_code__icontains=v)

        if v := request.query_params.get("bsnm_cmpnm", "").strip():
            qs = qs.filter(bsnm_cmpnm__icontains=v)

        if v := request.query_params.get("jurirno", "").strip():
            qs = qs.filter(jurirno__icontains=v)

        if v := request.query_params.get("sttus", "").strip():
            qs = qs.filter(sttus_se_code=v)

        # [수정] 지도 클릭 지역 필터를 주소 필드까지 함께 보도록 보강
        if v := request.query_params.get("ld_code_nm", "").strip():
            qs = qs.filter(
                Q(ld_code_nm__icontains=v) |
                Q(rdnmadr__icontains=v) |
                Q(mnnmadr__icontains=v)
            )

        # [수정] 지도 전용 데이터 요청 시 좌표 있는 데이터만
        if request.query_params.get("map_only"):
            qs = qs.filter(lat__isnull=False, lng__isnull=False)

        serializer = self.get_serializer(qs, many=True)
        return Response({
            "count": qs.count(),
            "results": serializer.data,
        })

    @action(detail=False, methods=["post"], url_path="sync")
    def sync(self, request):
        from django.core.management import call_command
        call_command("fetch_broker")
        return Response({
            "message": "sync complete",
            "total": RealEstateAgent.objects.count(),
        })


class EBBrokerViewSet(viewsets.ModelViewSet):
    queryset = EBBrokerInfo.objects.all()
    serializer_class = EBBrokerInfoSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()

        if v := request.query_params.get("ld_code", "").strip():
            qs = qs.filter(ld_code__startswith=v)

        if v := request.query_params.get("brkr_nm", "").strip():
            qs = qs.filter(brkr_nm__icontains=v)

        if v := request.query_params.get("bsnm_cmpnm", "").strip():
            qs = qs.filter(bsnm_cmpnm__icontains=v)

        serializer = self.get_serializer(qs, many=True)
        return Response({
            "count": qs.count(),
            "results": serializer.data,
        })

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        param_serializer = EBBrokerSearchParamSerializer(data=request.query_params)
        if not param_serializer.is_valid():
            return Response(param_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        api_response = self._call_api(param_serializer.validated_data)
        if api_response.has_error:
            return Response(
                {
                    "error": api_response.error_code,
                    "message": api_response.error_message,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            "totalCount": api_response.total_count,
            "pageNo": api_response.page_no,
            "numOfRows": api_response.num_of_rows,
            "items": [self._serialize_item(item) for item in api_response.items],
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
        created_count = 0
        updated_count = 0

        for item in all_items:
            _, created = EBBrokerInfo.objects.update_or_create(
                jurirno=item.jurirno,
                ld_code=item.ld_code,
                defaults={
                    "ld_code_nm": item.ld_code_nm,
                    "bsnm_cmpnm": item.bsnm_cmpnm,
                    "brkr_nm": item.brkr_nm,
                    "brkr_asort_code": item.brkr_asort_code,
                    "brkr_asort_code_nm": item.brkr_asort_code_nm,
                    "crqfc_no": item.crqfc_no,
                    "crqfc_acqdt": item.crqfc_acqdt,
                    "ofcps_se_code": item.ofcps_se_code,
                    "ofcps_se_code_nm": item.ofcps_se_code_nm,
                    "last_updt_dt": item.last_updt_dt,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        return Response(
            {
                "synced": len(all_items),
                "created": created_count,
                "updated": updated_count,
            },
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
            "ldCode": item.ld_code,
            "ldCodeNm": item.ld_code_nm,
            "jurirno": item.jurirno,
            "bsnmCmpnm": item.bsnm_cmpnm,
            "brkrNm": item.brkr_nm,
            "brkrAsortCode": item.brkr_asort_code,
            "brkrAsortCodeNm": item.brkr_asort_code_nm,
            "crqfcNo": item.crqfc_no,
            "crqfcAcqdt": item.crqfc_acqdt,
            "ofcpsSecode": item.ofcps_se_code,
            "ofcpsSeCodeNm": item.ofcps_se_code_nm,
            "lastUpdtDt": item.last_updt_dt,
        }


# =========================================================
# 목록 View
# =========================================================

class BrokerListView(LoginRequiredMixin, View):
    login_url = "/login/"
    paginate_by = 10

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

        # [수정] 지도 클릭 후 넘어온 구/군명 필터
        selected_region = request.GET.get("ld_code_nm", "").strip()
        if selected_region:
            qs = qs.filter(
                Q(ld_code_nm__icontains=selected_region) |
                Q(rdnmadr__icontains=selected_region) |
                Q(mnnmadr__icontains=selected_region)
            )

        page_obj = Paginator(qs, self.paginate_by).get_page(request.GET.get("page"))

        # [수정] 지도 마커용 데이터도 같은 필터 결과를 기준으로 보냄
        map_agents = list(
            qs.filter(lat__isnull=False, lng__isnull=False).values(
                "id",
                "bsnm_cmpnm",
                "rdnmadr",
                "ld_code_nm",
                "lat",
                "lng",
                "sttus_se_code",
            )
        )

        context = {
            "page_obj": page_obj,
            "map_agents_json": map_agents,
            "selected_region": selected_region,
        }
        return render(request, "brokers/broker1_list.html", context)


# =========================================================
# 상세 View
# =========================================================

class BrokerDetailView(LoginRequiredMixin, View):
    login_url = "/login/"

    def get(self, request, pk):
        agent = get_object_or_404(RealEstateAgent, pk=pk)
        reviews = Review.objects.filter(agent=agent).select_related("author")
        images = BrokerImage.objects.filter(agent=agent)
        review_count = reviews.count()

        avg_raw = reviews.aggregate(avg=Avg("score"))["avg"]
        avg_score = round(avg_raw, 1) if avg_raw else 0

        score_distribution = []
        for score in [5, 4, 3, 2, 1]:
            cnt = reviews.filter(score=score).count()
            pct = round(cnt / review_count * 100) if review_count else 0
            score_distribution.append({
                "score": score,
                "count": cnt,
                "percent": pct,
            })

        return render(
            request,
            "brokers/detail.html",
            {
                "agent": agent,
                "reviews": reviews,
                "avg_score": avg_score,
                "review_count": review_count,
                "form": ReviewForm(),
                "image_form": BrokerImageForm(),
                "images": images,
                "score_distribution": score_distribution,
            },
        )


# =========================================================
# 목록 View 2
# =========================================================

class Broker2ListView(LoginRequiredMixin, View):
    login_url = "/login/"

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


# =========================================================
# 이미지 업로드 View
# =========================================================

class BrokerImageUploadView(LoginRequiredMixin, View):
    login_url = "/login/"

    def post(self, request, pk):
        agent = get_object_or_404(RealEstateAgent, pk=pk)
        form = BrokerImageForm(request.POST, request.FILES)

        if form.is_valid():
            old_images = BrokerImage.objects.filter(agent=agent)
            for old in old_images:
                old.image.delete(save=False)
                old.delete()

            img = form.save(commit=False)
            img.agent = agent
            img.uploaded_by = request.user
            img.is_primary = True
            img.save()

        return redirect("brokers:broker1_detail", pk=pk)


# =========================================================
# 이미지 삭제 View
# =========================================================

class BrokerImageDeleteView(LoginRequiredMixin, View):
    login_url = "/login/"

    def post(self, request, image_pk):
        img = get_object_or_404(BrokerImage, pk=image_pk)

        if img.uploaded_by != request.user and not request.user.is_staff:
            return HttpResponseForbidden()

        agent_pk = img.agent.pk
        img.image.delete(save=False)
        img.delete()
        return redirect("brokers:broker1_detail", pk=agent_pk)
