/**
 * signup.js — JWT 회원가입
 * POST /accounts/api/signup/ → 토큰 저장 → 대시보드 이동
 */
document.addEventListener('DOMContentLoaded', function () {
  const form    = document.getElementById('signupForm');
  const errorEl = document.getElementById('signupError');
  const btn     = document.getElementById('signupBtn');
  if (!form) return;

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    clearErrors();

    const payload = {
      username:  document.getElementById('id_username').value.trim(),
      email:     document.getElementById('id_email').value.trim(),
      password1: document.getElementById('id_password1').value,
      password2: document.getElementById('id_password2').value,
    };

    btn.disabled    = true;
    btn.textContent = '처리 중...';

    try {
      const res  = await fetch('/accounts/api/signup/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (res.ok && data.access) {
        localStorage.setItem('access_token',  data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('username',      data.username);
        window.location.href = '/brokers/dashboard/';
      } else if (data.errors) {
        showFieldErrors(data.errors);
      } else {
        showError(data.error || '회원가입에 실패했습니다.');
      }
    } catch {
      showError('서버 오류가 발생했습니다.');
    } finally {
      btn.disabled    = false;
      btn.textContent = '가입하기';
    }
  });

  function clearErrors() {
    ['username', 'email', 'password1', 'password2'].forEach(function (f) {
      const el = document.getElementById('err_' + f);
      if (el) { el.textContent = ''; el.style.display = 'none'; }
    });
    errorEl.style.display = 'none';
  }

  function showFieldErrors(errors) {
    Object.keys(errors).forEach(function (field) {
      const el = document.getElementById('err_' + field);
      if (el) {
        el.textContent   = errors[field][0];
        el.style.display = 'block';
      }
    });
  }

  function showError(msg) {
    errorEl.textContent   = msg;
    errorEl.style.display = 'block';
  }

  function getCsrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
  }
});
