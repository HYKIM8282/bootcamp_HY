from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RealEstateAgentViewSet,
    EBBrokerViewSet,        # ✅ 추가
    broker_list_view,
    broker_detail_view,
)

router = DefaultRouter()
router.register("agents", RealEstateAgentViewSet, basename="realestateagent")
router.register("eb-brokers", EBBrokerViewSet, basename="eb-broker")  # ✅ 추가

urlpatterns = [
    # 템플릿 화면
    path("", broker_list_view, name="agent_list"),
    path("<int:pk>/", broker_detail_view, name="broker-detail"),
    # API
    path("api/", include(router.urls)),
]