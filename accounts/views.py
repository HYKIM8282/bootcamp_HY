from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm

# ✅ 회원가입
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('brokers:broker1_list')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)          # 가입 후 자동 로그인
            return redirect('brokers:dashboard')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

# ✅ 로그인
def login_view(request):
    if request.user.is_authenticated:
        return redirect('brokers:dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('brokers:broker1_list')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

# ✅ 로그아웃
def logout_view(request):
    logout(request)
    return redirect('accounts:login')