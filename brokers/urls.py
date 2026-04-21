# brokers/urls.py
from .views import (
    # ... 기존 ...
    OfficeWithBrokersView,
    VWorldBothProxyView,
    VWorldSequentialSyncView,
)

urlpatterns = [
    # ... 기존 ...
    path("offices/<str:jurirno>/full/", OfficeWithBrokersView.as_view()),  # 3번
    path("vworld/both/",               VWorldBothProxyView.as_view()),     # 1번
    path("vworld/sync/",               VWorldSequentialSyncView.as_view()), # 4번
]