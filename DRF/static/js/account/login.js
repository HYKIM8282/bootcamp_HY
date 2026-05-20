/**
 * login.js — JWT 로그인
 * POST /accounts/api/login/ → access/refresh 토큰 localStorage 저장 → 리다이렉트
 */
document.addEventListener('DOMContentLoaded', function () {
  var form    = document.getElementById('loginForm');
  var errorEl = document.getElementById('loginError');
  var btn     = document.getElementById('loginBtn');
  if (!form) return;

  form.addEventListener('submit', async function (e) {
    e.preventDefault();

    var username = document.getElementById('id_username').value.trim();
    var password = document.getElementById('id_password').value;

    errorEl.style.display = 'none';
    btn.disabled    = true;
    btn.textContent = '로그인 중...';

    var next = form.dataset.next || '/community/';

    try {
      const res  = await fetch('/accounts/api/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();

      if (res.ok && data.access) {
        localStorage.setItem('access_token',  data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('username',      data.username);
        window.location.href = next;
      } else {
        showError(data.error || '로그인에 실패했습니다.');
      }
    } catch {
      showError('서버 오류가 발생했습니다.');
    }
  });

  function showError(msg) {
    errorEl.textContent   = msg;
    errorEl.style.display = 'block';
    btn.disabled          = false;
    btn.textContent       = '로그인';
  }

  function getCsrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : '';
  }
});
