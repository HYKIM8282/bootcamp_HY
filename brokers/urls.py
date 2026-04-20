from django.urls import path
from . import views

app_name = "brokers"

urlpatterns = [
    path("", views.agent_list, name="agent_list"),
]