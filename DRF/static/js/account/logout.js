/**
 * logout.js
 * 경로: static/js/account/logout.js
 *
 * 헤더의 로그아웃 버튼이 호출하는 JWT 로그아웃 함수.
 * 로그인된 사용자가 있을 때만 header.html 에서 로드됨.
 */
async function jwtLogout() {
  const access  = localStorage.getItem('access_token');
  const refresh = localStorage.getItem('refresh_token') || '';
  const headers = { 'Content-Type': 'application/json' };
  if (access) headers['Authorization'] = 'Bearer ' + access;
  try {
    await fetch('/accounts/api/logout/', {
      method: 'POST',
      headers,
      body: JSON.stringify({ refresh }),
    });
  } catch {}
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('username');
  window.location.href = '/accounts/login/';
}
