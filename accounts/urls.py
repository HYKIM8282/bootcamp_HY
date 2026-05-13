from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # HTML 페이지
    path('signup/', views.signup_view,  name='signup'),
    path('login/',  views.login_view,   name='login'),
    path('logout/', views.logout_view,  name='logout'),

    # JWT API (JSON)
    path('api/login/',         views.LoginAPIView.as_view(),  name='api_login'),
    path('api/signup/',        views.SignupAPIView.as_view(), name='api_signup'),
    path('api/logout/',        views.LogoutAPIView.as_view(), name='api_logout'),
    path('api/token/refresh/', TokenRefreshView.as_view(),   name='token_refresh'),
]
