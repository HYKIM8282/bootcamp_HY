from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from interactions.forms import ReviewForm
from interactions.models import Review

from .forms import BrokerImageForm
from .management.commands.fetch_broker2 import EBBrokerAPIClient, EBBrokerRequestParams
from .models import BrokerImage, EBBrokerInfo, RealEstateAgent
from .serializers import (
    BrokerImageSerializer,
    EBBrokerInfoSerializer,
    EBBrokerSearchParamSerializer,
    RealEstateAgentDetailSerializer,
    RealEstateAgentMapSerializer,
    RealEstateAgentSerializer,
)


# =========================================================
# 대시보드
# =========================================================

@login_required(login_url="/accounts/login/")
def dashboard(request):
    return render(request, "brokers/dashboard.html", {
        "total_count":  RealEstateAgent.objects.count(),
        "active_count": RealEstateAgent.objects.filter(sttus_se_code="1").count(),
        "closed_count": RealEstateAgent.objects.filter(sttus_se_code="2").count(),
    })


# =========================================================
# API ViewSets
# =========================================================

class RealEstateAgentViewSet(viewsets.ModelViewSet):
    queryset        = RealEstateAgent.objects.all().order_by("-regist_de")
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields   = ["bsnm_cmpnm", "brkr_nm", "jurirno", "ld_code_nm", "rdnmadr", "mnnmadr"]
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
        if v := request.query_params.get("ld_code_nm", "").strip():
            qs = qs.filter(
                Q(ld_code_nm__icontains=v) | Q(rdnmadr__icontains=v) | Q(mnnmadr__icontains=v)
            )
        if request.query_params.get("map_only"):
            qs = qs.filter(lat__isnull=False, lng__isnull=False)
        serializer = self.get_serializer(qs, many=True)
        return Response({"count": qs.count(), "results": serializer.data})

    @action(detail=False, methods=["post"], url_path="sync")
    def sync(self, request):
        from django.core.management import call_command
        call_command("fetch_broker")
        return Response({"message": "sync complete", "total": RealEstateAgent.objects.count()})


class EBBrokerViewSet(viewsets.ModelViewSet):
    queryset         = EBBrokerInfo.objects.all()
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
            "items":      [self._serialize_item(i) for i in api_response.items],
        })

    @action(detail=False, methods=["post"], url_path="sync")
    def sync(self, request):
        param_serializer = EBBrokerSearchParamSerializer(data=request.data)
        if not param_serializer.is_valid():
            return Response(param_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        validated  = param_serializer.validated_data
        api_params = EBBrokerRequestParams(
            ld_code=validated.get("ld_code"), bsnm_cmpnm=validated.get("bsnm_cmpnm"),
            brkr_nm=validated.get("brkr_nm"), jurirno=validated.get("jurirno"),
            num_of_rows=1000,
        )
        all_items = EBBrokerAPIClient().fetch_all(api_params)
        created_count = updated_count = 0
        for item in all_items:
            _, created = EBBrokerInfo.objects.update_or_create(
                jurirno=item.jurirno, ld_code=item.ld_code,
                defaults={
                    "ld_code_nm": item.ld_code_nm, "bsnm_cmpnm": item.bsnm_cmpnm,
                    "brkr_nm": item.brkr_nm, "brkr_asort_code": item.brkr_asort_code,
                    "brkr_asort_code_nm": item.brkr_asort_code_nm,
                    "crqfc_no": item.crqfc_no, "crqfc_acqdt": item.crqfc_acqdt,
                    "ofcps_se_code": item.ofcps_se_code,
                    "ofcps_se_code_nm": item.ofcps_se_code_nm,
                    "last_updt_dt": item.last_updt_dt,
                },
            )
            if created: created_count += 1
            else:       updated_count += 1
        return Response(
            {"synced": len(all_items), "created": created_count, "updated": updated_count},
            status=status.HTTP_200_OK,
        )

    def _call_api(self, validated: dict):
        return EBBrokerAPIClient().fetch(EBBrokerRequestParams(
            ld_code=validated.get("ld_code"), bsnm_cmpnm=validated.get("bsnm_cmpnm"),
            brkr_nm=validated.get("brkr_nm"), jurirno=validated.get("jurirno"),
            num_of_rows=validated.get("num_of_rows", 10),
            page_no=validated.get("page_no", 1),
        ))

    @staticmethod
    def _serialize_item(item) -> dict:
        return {
            "ldCode": item.ld_code, "ldCodeNm": item.ld_code_nm, "jurirno": item.jurirno,
            "bsnmCmpnm": item.bsnm_cmpnm, "brkrNm": item.brkr_nm,
            "brkrAsortCode": item.brkr_asort_code, "brkrAsortCodeNm": item.brkr_asort_code_nm,
            "crqfcNo": item.crqfc_no, "crqfcAcqdt": item.crqfc_acqdt,
            "ofcpsSecode": item.ofcps_se_code, "ofcpsSeCodeNm": item.ofcps_se_code_nm,
            "lastUpdtDt": item.last_updt_dt,
        }


# =========================================================
# 목록 View
# =========================================================

class BrokerListView(LoginRequiredMixin, View):
    login_url   = "/accounts/login/"
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

        selected_region = request.GET.get("ld_code_nm", "").strip()
        if selected_region:
            qs = qs.filter(
                Q(ld_code_nm__icontains=selected_region) |
                Q(rdnmadr__icontains=selected_region) |
                Q(mnnmadr__icontains=selected_region)
            )

        page_obj = Paginator(qs, self.paginate_by).get_page(request.GET.get("page"))

        # 그룹 A: DB에 좌표 있음 → 즉시 마커
        map_agents = list(
            qs.filter(lat__isnull=False, lng__isnull=False).values(
                "id", "bsnm_cmpnm", "rdnmadr", "ld_code_nm", "lat", "lng", "sttus_se_code",
            )
        )
        # 그룹 B: 좌표 없음 → JS 가 Kakao 지오코딩 후 마커 (최대 500건)
        map_agents_addr = list(
            qs.filter(lat__isnull=True)
              .exclude(rdnmadr__isnull=True)
              .exclude(rdnmadr="")
              .values("id", "bsnm_cmpnm", "rdnmadr", "ld_code_nm", "sttus_se_code")[:500]
        )

        return render(request, "brokers/broker1_list.html", {
            "page_obj":             page_obj,
            "map_agents_json":      map_agents,
            "map_agents_addr_json": map_agents_addr,
            "selected_region":      selected_region,
        })


# =========================================================
# 상세 View
# ─────────────────────────────────────────────────────────
# [수정] 템플릿 경로: "brokers/detail.html"
#                  → "brokers/broker_detail.html"
#
# 이유: CSS(broker_detail.css) / JS(broker_detail.js) 와
#       파일명을 "broker_detail" 로 통일
# =========================================================

class BrokerDetailView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"

    def get(self, request, pk):
        agent        = get_object_or_404(RealEstateAgent, pk=pk)
        reviews      = Review.objects.filter(agent=agent).select_related("author")
        images       = BrokerImage.objects.filter(agent=agent)
        review_count = reviews.count()

        avg_raw   = reviews.aggregate(avg=Avg("score"))["avg"]
        avg_score = round(avg_raw, 1) if avg_raw else 0

        score_distribution = [
            {
                "score": s,
                "count": (cnt := reviews.filter(score=s).count()),
                "pct":   round(cnt / review_count * 100) if review_count else 0,
            }
            for s in [5, 4, 3, 2, 1]
        ]

        return render(
            request,
            "brokers/broker_detail.html",   # ★ [수정] detail.html → broker_detail.html
            {
                "agent":              agent,
                "reviews":            reviews,
                "avg_score":          avg_score,
                "review_count":       review_count,
                "form":               ReviewForm(),
                "image_form":         BrokerImageForm(),
                "images":             images,
                "score_distribution": score_distribution,
            },
        )


# =========================================================
# 목록 View 2
# =========================================================

class Broker2ListView(LoginRequiredMixin, View):
    login_url = "/accounts/login/"

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
# ─────────────────────────────────────────────────────────
# [변경] Django View + redirect() → DRF APIView + Response
#        axios FormData 방식 대응
#        BrokerImageSerializer 로 응답 직렬화
# =========================================================

class BrokerImageUploadView(APIView):
    """
    POST  /detail/<pk>/images/upload/
    Content-Type : multipart/form-data  (axios FormData)

    요청 필드:
        image      : 파일 (필수)
        caption    : 설명 (선택)
        is_primary : 대표 이미지 여부 (기본 true)

    성공 응답 201:
        { success, id, image_url, caption, is_primary, uploaded_by }
    """

    permission_classes = [IsAuthenticated]
    # ★ MultiPartParser: FormData(파일) 파싱
    # ★ FormParser     : 일반 POST 폼 필드 파싱
    parser_classes     = [MultiPartParser, FormParser]

    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    MAX_SIZE      = 5 * 1024 * 1024   # 5 MB

    def post(self, request, pk):
        agent      = get_object_or_404(RealEstateAgent, pk=pk)
        image_file = request.FILES.get("image")

        # ── 유효성 검사 ───────────────────────────────────
        if not image_file:
            return Response(
                {"success": False, "error": "이미지 파일이 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if image_file.content_type not in self.ALLOWED_TYPES:
            return Response(
                {"success": False, "error": "JPG·PNG·WEBP·GIF 형식만 업로드 가능합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if image_file.size > self.MAX_SIZE:
            return Response(
                {"success": False, "error": "파일 크기는 5 MB 이하여야 합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── BrokerImageForm 2차 검증 ──────────────────────
        form = BrokerImageForm(request.POST, request.FILES)
        if not form.is_valid():
            return Response(
                {"success": False, "error": form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_primary = request.data.get("is_primary", "true").lower() == "true"

        # ── 기존 이미지 전부 교체 ─────────────────────────
        for old in BrokerImage.objects.filter(agent=agent):
            old.image.delete(save=False)
            old.delete()

        # ── 저장 ──────────────────────────────────────────
        img             = form.save(commit=False)
        img.agent       = agent
        img.uploaded_by = request.user
        img.is_primary  = is_primary
        img.save()

        # ── Serializer 로 응답 ────────────────────────────
        serializer = BrokerImageSerializer(img, context={"request": request})
        return Response(
            {"success": True, **serializer.data},
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# 이미지 삭제 View
# ─────────────────────────────────────────────────────────
# [변경] Django View (POST) + redirect()
#      → DRF APIView (DELETE) + Response(JSON)
#        axios apiClient.delete() 방식 대응
# =========================================================

class BrokerImageDeleteView(APIView):
    """
    DELETE  /brokers/images/<image_pk>/delete/
    Content-Type : application/json  (axios apiClient)

    성공 응답 200:
        { success: true }
    """

    permission_classes = [IsAuthenticated]
    parser_classes     = [JSONParser]

    def delete(self, request, image_pk):
        img = get_object_or_404(BrokerImage, pk=image_pk)

        # ── 권한 검사 ─────────────────────────────────────
        if img.uploaded_by != request.user and not request.user.is_staff:
            return Response(
                {"success": False, "error": "삭제 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        img.image.delete(save=False)
        img.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)
