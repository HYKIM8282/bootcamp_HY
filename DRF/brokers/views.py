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

from django.contrib.contenttypes.models import ContentType

from interactions.forms import ReviewForm
from interactions.models import Image, Review
from interactions.serializers import ImageSerializer

from .management.commands.fetch_broker2 import EBBrokerAPIClient, EBBrokerRequestParams
from .models import EBBrokerInfo, RealEstateAgent
from .serializers import (
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
    # ✅ 구 이름 → { code, dongs } 매핑.
    #   - ld_code_nm 이 "서울특별시 송파구" / "송파구" 등으로 섞여도
    #     "XX구" 토큰만 추출해 키 불일치 방지.
    #   - 같은 JSON 안에 ld_code 도 담아 JS 에서 한 번에 조회.
    info_by_gu = {}
    rows = (
        RealEstateAgent.objects
        .exclude(mnnmadr="")
        .exclude(ld_code_nm="")
        .values_list("ld_code_nm", "mnnmadr", "ld_code")
    )
    for gu_name_raw, addr, ld_code in rows:
        # "서울특별시 송파구" → "송파구" 정규화 (마지막 "구" 토큰)
        gu_name = None
        for token in gu_name_raw.split():
            if token.endswith("구"):
                gu_name = token
        if not gu_name:
            continue

        info = info_by_gu.setdefault(gu_name, {"code": ld_code, "dongs": set()})

        parts = addr.split()
        if len(parts) >= 3 and parts[2].endswith("동"):
            info["dongs"].add(parts[2])

    # set → 정렬된 list 로 직렬화 가능하게
    info_by_gu = {
        gu: {"code": info["code"], "dongs": sorted(info["dongs"])}
        for gu, info in info_by_gu.items()
    }

    return render(request, "brokers/dashboard.html", {
        "total_count":  RealEstateAgent.objects.count(),
        "active_count": RealEstateAgent.objects.filter(sttus_se_code="1").count(),
        "closed_count": RealEstateAgent.objects.filter(sttus_se_code="2").count(),
        "info_by_gu":   info_by_gu,
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

        # ✅ [추가] 동(읍·면·동) 필터 — 지번주소(mnnmadr) 의 "동" 부분 매칭
        selected_dong = request.GET.get("dong", "").strip()
        if selected_dong:
            qs = qs.filter(mnnmadr__icontains=selected_dong)

        # ✅ [추가] 현재 선택된 구에 속한 동 목록 — UI 버튼 렌더용
        #   지번주소 형식: "서울특별시 송파구 송파동 143-6" → split[2] 가 동
        #   ldcode(코드) 또는 ld_code_nm(이름) 어느 쪽으로 들어와도 처리
        dong_list       = []
        selected_ldcode = request.GET.get("ldcode", "").strip()
        if selected_ldcode:
            base_qs = RealEstateAgent.objects.filter(ld_code=selected_ldcode)
        elif selected_region:
            base_qs = RealEstateAgent.objects.filter(ld_code_nm__icontains=selected_region)
        else:
            base_qs = None

        if base_qs is not None:
            addresses = (
                base_qs.exclude(mnnmadr="")
                       .values_list("mnnmadr", flat=True)
            )
            dong_set = set()
            for addr in addresses:
                parts = addr.split()
                if len(parts) >= 3 and parts[2].endswith("동"):
                    dong_set.add(parts[2])
            dong_list = sorted(dong_set)

        # ✅ [추가] 전체 구별 동 매핑 — JS 가 시군구 변경 시 동 드롭다운 즉시 갱신용
        #   { "11710": ["가락동", ...], "11680": [...], ... }
        dongs_by_code = {}
        for code, addr in (
            RealEstateAgent.objects
            .exclude(mnnmadr="").exclude(ld_code="")
            .values_list("ld_code", "mnnmadr")
        ):
            parts = addr.split()
            if len(parts) >= 3 and parts[2].endswith("동"):
                dongs_by_code.setdefault(code, set()).add(parts[2])
        dongs_by_code = {c: sorted(d) for c, d in dongs_by_code.items()}

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
            "dong_list":            dong_list,
            "selected_dong":        selected_dong,
            "dongs_by_code":        dongs_by_code,
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
        reviews      = list(
            Review.objects.filter(agent=agent).select_related("author")
        )
        # 통합 Image(GFK) — RealEstateAgent.images = GenericRelation('interactions.Image')
        images       = agent.images.all()
        review_count = len(reviews)

        avg_raw   = (
            sum(r.score for r in reviews) / review_count if review_count else None
        )
        avg_score = round(avg_raw, 1) if avg_raw else 0

        score_distribution = [
            {
                "score": s,
                "count": (cnt := sum(1 for r in reviews if r.score == s)),
                "pct":   round(cnt / review_count * 100) if review_count else 0,
            }
            for s in [5, 4, 3, 2, 1]
        ]

        # ─── 감정분석 결과 합산 (8단계) ────────────────────────────
        from sentiment.models import SentimentResult
        from sentiment.services import calc_trust_score

        review_ct = ContentType.objects.get_for_model(Review)
        sentiment_qs = (
            SentimentResult.objects
            .filter(target_type=review_ct, target_id__in=[r.id for r in reviews])
            .exclude(label="error")
            .order_by("-created_at")
        )
        # target_id 별 최신 1건만 (재분석 히스토리 중 최신)
        sentiment_map = {}
        for sr in sentiment_qs:
            if sr.target_id not in sentiment_map:
                sentiment_map[sr.target_id] = sr

        # Review 각각에 .sentiment attach (template 에서 review.sentiment 접근)
        for r in reviews:
            r.sentiment = sentiment_map.get(r.id)

        # 평균 감정점수 (-1 ~ +1)
        scores = [sr.score for sr in sentiment_map.values()]
        avg_sentiment = round(sum(scores) / len(scores), 3) if scores else None

        # 종합 신뢰점수 (0~100)
        trust_score = calc_trust_score(avg_raw, avg_sentiment)
        # ───────────────────────────────────────────────────────────

        return render(
            request,
            "brokers/broker_detail.html",
            {
                "agent":              agent,
                "reviews":            reviews,
                "avg_score":          avg_score,
                "review_count":       review_count,
                "form":               ReviewForm(),
                "images":             images,
                "score_distribution": score_distribution,
                "avg_sentiment":      avg_sentiment,
                "trust_score":        trust_score,
                "analyzed_count":     len(sentiment_map),
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
    """POST /detail1/<pk>/images/upload/ — 중개업소 이미지 업로드.

    요청: multipart/form-data (image, caption, is_primary)
    응답: 201 + { success, id, image_url, caption, is_primary, uploaded_by, uploaded_at }
    검증(파일 형식·크기)은 ImageSerializer 가 담당 — DRF 단일 검증 흐름.
    """

    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser]

    def post(self, request, pk):
        agent = get_object_or_404(RealEstateAgent, pk=pk)

        serializer = ImageSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # 기존 이미지 전부 교체 (기존 동작 유지)
        for old in agent.images.all():
            old.image.delete(save=False)
            old.delete()

        # GFK 필드(content_type/object_id) 와 uploaded_by 는 뷰에서 주입
        img = serializer.save(
            content_type=ContentType.objects.get_for_model(RealEstateAgent),
            object_id=agent.pk,
            uploaded_by=request.user,
        )

        # 저장된 객체를 다시 직렬화해 read 필드(image_url 등) 포함 응답
        out = ImageSerializer(img, context={"request": request})
        return Response(
            {"success": True, **out.data},
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
        # 통합 Image(GFK) 모델 사용 — 어떤 도메인 이미지든 같은 엔드포인트로 삭제
        img = get_object_or_404(Image, pk=image_pk)

        # ── 권한 검사 ─────────────────────────────────────
        if img.uploaded_by != request.user and not request.user.is_staff:
            return Response(
                {"success": False, "error": "삭제 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        img.image.delete(save=False)
        img.delete()
        return Response({"success": True}, status=status.HTTP_200_OK)
