from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  # 내 옆에 있는 views.py를 불러옴

from .views import (
    RealEstateAgentViewSet,
    EBBrokerViewSet,
    BrokerListView,
    BrokerDetailView,
    Broker2ListView,
    BrokerImageUploadView,
    BrokerImageDeleteView,
    dashboard,
)

app_name = "brokers"

router = DefaultRouter()
router.register("agents", RealEstateAgentViewSet, basename="realestateagent")
router.register("eb-brokers", EBBrokerViewSet, basename="eb-broker")

urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),   # [추가]

    path("broker1/", BrokerListView.as_view(), name="broker1_list"),
    path("broker2/", Broker2ListView.as_view(), name="broker2_list"),

    path("detail1/<int:pk>/", BrokerDetailView.as_view(), name="broker1_detail"),
    path("detail2/<int:pk>/", BrokerDetailView.as_view(), name="broker2_detail"),

    path(
        "detail1/<int:pk>/images/upload/",
        BrokerImageUploadView.as_view(),
        name="broker_image_upload",
    ),
    
    path(
        "images/<int:image_pk>/delete/",
        BrokerImageDeleteView.as_view(),
        name="broker_image_delete",
    ),

    path("api/", include(router.urls)),
]