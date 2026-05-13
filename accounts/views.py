from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import SignUpForm


# ── HTML 렌더링 뷰 (GET 전용) ────────────────────────────────────

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('brokers:dashboard')
    return render(request, 'accounts/signup.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('brokers:dashboard')
    next_url = request.GET.get('next', '')
    return render(request, 'accounts/login.html', {'next': next_url})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


# ── JWT API 뷰 (JSON POST) ───────────────────────────────────────

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response(
                {'error': '아이디와 비밀번호를 입력하세요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {'error': '아이디 또는 비밀번호가 틀렸습니다.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)  # Django 세션도 함께 생성 (@login_required 호환)
        refresh = RefreshToken.for_user(user)
        return Response({
            'access':   str(refresh.access_token),
            'refresh':  str(refresh),
            'username': user.username,
        })


class SignupAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        form = SignUpForm(request.data)
        if not form.is_valid():
            return Response(
                {'errors': form.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = form.save()
        login(request, user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'access':   str(refresh.access_token),
            'refresh':  str(refresh),
            'username': user.username,
        }, status=status.HTTP_201_CREATED)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # refresh 토큰이 전달되면 만료 처리
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass
        logout(request)
        return Response({'message': '로그아웃 되었습니다.'})
