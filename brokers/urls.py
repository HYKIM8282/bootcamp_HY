from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RealEstateAgentViewSet,
    EBBrokerViewSet,        # ✅ 추가
    BrokerListView,         # 클래스 이름으로 변경
    BrokerDetailView,
    Broker2ListView,    #broker_list_view,

)

router = DefaultRouter()
router.register("agents", RealEstateAgentViewSet, basename="realestateagent")
router.register("eb-brokers", EBBrokerViewSet, basename="eb-broker")  

urlpatterns = [
    path("broker1/",   BrokerListView.as_view(),   name="broker1_list"),   # .as_view() 추가
    path("broker2/",   Broker2ListView.as_view(),  name="broker2_list"),
    path("detail1/<int:pk>/",  BrokerDetailView.as_view(), name="broker1_detail"),
    path("detail2/<int:pk>/",  BrokerDetailView.as_view(), name="broker2_detail"),
]



# 상단       링크 