from django.core.paginator import Paginator
from django.shortcuts import render
from .models import RealEstateAgent


def agent_list(request):
    qs = RealEstateAgent.objects.all()

    # 필터
    if ldcode := request.GET.get("ldcode"):
        qs = qs.filter(ld_code__icontains=ldcode)
    if bsnm := request.GET.get("bsnm_cmpnm"):
        qs = qs.filter(bsnm_cmpnm__icontains=bsnm)
    if jurirno := request.GET.get("jurirno"):
        qs = qs.filter(jurirno__icontains=jurirno)
    if sttus := request.GET.get("sttus"):
        qs = qs.filter(sttus_se_code=sttus)

    paginator = Paginator(qs, 10)
    page_obj  = paginator.get_page(request.GET.get("page", 1))

    return render(request, "brokers/agent_list.html", {"page_obj": page_obj})
