/**
 * community/board.js
 * - 게시판 목록/작성/상세/수정/삭제/좋아요 (ViewSet 연동)
 * - 로그인 없이도 목록은 조회 가능. 글쓰기는 로그인 필요.
 */
(function () {
  // ─────────────────────────────────────────────────────
  // 설정값
  // ─────────────────────────────────────────────────────
  const cfgEl = document.getElementById('boardConfig');
  if (!cfgEl) return;
  const CFG = JSON.parse(cfgEl.textContent);

  const $ = (id) => document.getElementById(id);

  // ─────────────────────────────────────────────────────
  // 상태
  // ─────────────────────────────────────────────────────
  const state = {
    page: 1,
    pageSize: 10,
    total: 0,
    category: '',
    items: [],
    mode: 'create',   // 'create' | 'edit'
    editId: null,
    currentDetail: null,
  };

  // ─────────────────────────────────────────────────────
  // 유틸
  // ─────────────────────────────────────────────────────
  function getCsrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return (m && m[1]) || CFG.csrfToken || '';
  }

  async function api(url, opts = {}) {
    // 1차: Django 세션 인증 우선 사용 (로그인 폼 흐름)
    //   - 만료된 JWT 가 localStorage 에 남아 있으면 401 을 유발하므로
    //     세션 쿠키 + CSRF 만으로 먼저 시도한다.
    const baseHeaders = {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrf(),
      ...(opts.headers || {}),
    };

    let res = await fetch(url, {
      credentials: 'same-origin',
      ...opts,
      headers: baseHeaders,
    });

    // 세션 인증이 실패했을 때만 JWT 로 폴백 (있을 경우)
    if (res.status === 401) {
      const access = localStorage.getItem('access_token');
      if (access) {
        res = await fetch(url, {
          credentials: 'same-origin',
          ...opts,
          headers: { ...baseHeaders, Authorization: 'Bearer ' + access },
        });
        // JWT 도 만료/무효라면 정리
        if (res.status === 401) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }
    }

    let data = null;
    try { data = await res.json(); } catch (_) {}
    return { ok: res.ok, status: res.status, data };
  }

  function fmtDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${d.getFullYear()}-${mm}-${dd}`;
  }

  function escapeHtml(s) {
    return String(s ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // ─────────────────────────────────────────────────────
  // 목록 렌더링 (빈 행은 7행까지 채움 — 이미지 형식)
  // ─────────────────────────────────────────────────────
  function render() {
    const tbody = $('boardTbody');
    tbody.innerHTML = '';

    const rows = state.items.slice(0, state.pageSize);
    const startNo = state.total - (state.page - 1) * state.pageSize;

    rows.forEach((p, i) => {
      const tr = document.createElement('tr');
      tr.className = 'board-row board-row--data';
      tr.dataset.id = p.id;
      tr.innerHTML = `
        <td class="col-no">${startNo - i}</td>
        <td class="col-title">${escapeHtml(p.title)}</td>
        <td class="col-author">${escapeHtml(p.author_name)}</td>
        <td class="col-date">${fmtDate(p.created_at)}</td>
        <td class="col-view">${p.view_count}</td>
        <td class="col-like">${p.like_count}</td>
      `;
      tr.addEventListener('click', () => openDetail(p.id));
      tbody.appendChild(tr);
    });

    // 7행까지 빈 행 채우기
    const pad = Math.max(0, 7 - rows.length);
    for (let i = 0; i < pad; i++) {
      const tr = document.createElement('tr');
      tr.className = 'board-row board-row--empty';
      tr.innerHTML = `<td>&nbsp;</td><td></td><td></td><td></td><td></td><td></td>`;
      tbody.appendChild(tr);
    }

    const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
    $('boardPageInfo').textContent = `${state.page} / ${totalPages}`;
    $('boardPrev').disabled = state.page <= 1;
    $('boardNext').disabled = state.page >= totalPages;
  }

  // ─────────────────────────────────────────────────────
  // 목록 가져오기
  // ─────────────────────────────────────────────────────
  async function loadList() {
    const url = new URL(CFG.listUrl, window.location.origin);
    url.searchParams.set('page', state.page);
    if (state.category) url.searchParams.set('category', state.category);

    const { ok, data } = await api(url.toString());
    if (!ok || !data || !data.success) {
      $('boardTbody').innerHTML =
        `<tr class="board-row board-row--empty"><td colspan="6">불러오기 실패</td></tr>`;
      return;
    }
    state.items    = data.data || [];
    state.total    = (data.meta && data.meta.total) || 0;
    state.pageSize = (data.meta && data.meta.page_size) || 10;
    render();
  }

  // ─────────────────────────────────────────────────────
  // 모달
  // ─────────────────────────────────────────────────────
  function openModal({ mode, post }) {
    state.mode = mode;
    state.editId = post ? post.id : null;

    const isForm   = mode === 'create' || mode === 'edit';
    const isDetail = mode === 'detail';

    $('boardForm').style.display   = isForm ? 'block' : 'none';
    $('boardDetail').style.display = isDetail ? 'block' : 'none';
    $('boardModalTitle').textContent =
      mode === 'create' ? '새 글 작성' :
      mode === 'edit'   ? '글 수정'     : '글 상세보기';

    if (isForm) {
      $('bfTitle').value    = post ? post.title : '';
      $('bfCategory').value = post ? post.category : 'latest';
      $('bfNickname').value = post ? (post.nickname || '') : '';
      $('bfContent').value  = post ? post.content : '';
      $('bfFeedback').textContent = '';
    }

    $('boardModal').classList.add('is-open');
  }

  function closeModal() {
    $('boardModal').classList.remove('is-open');
    state.editId = null;
    state.currentDetail = null;
  }

  // ─────────────────────────────────────────────────────
  // 글쓰기 버튼
  // ─────────────────────────────────────────────────────
  $('boardWriteBtn').addEventListener('click', () => {
    if (!CFG.isAuthenticated) {
      alert('글쓰기는 로그인이 필요합니다.');
      window.location.href = CFG.loginUrl;
      return;
    }
    openModal({ mode: 'create' });
  });

  // ─────────────────────────────────────────────────────
  // 등록 / 수정 제출
  // ─────────────────────────────────────────────────────
  $('bfSubmit').addEventListener('click', async () => {
    const payload = {
      title:    $('bfTitle').value.trim(),
      category: $('bfCategory').value,
      nickname: $('bfNickname').value.trim(),
      content:  $('bfContent').value.trim(),
    };
    if (!payload.title)   { $('bfFeedback').textContent = '제목을 입력하세요.'; return; }
    if (!payload.content) { $('bfFeedback').textContent = '내용을 입력하세요.'; return; }

    let url, method;
    if (state.mode === 'edit' && state.editId) {
      url    = CFG.listUrl + state.editId + '/';
      method = 'PATCH';
    } else {
      url    = CFG.listUrl;
      method = 'POST';
    }

    const { ok, status, data } = await api(url, { method, body: JSON.stringify(payload) });

    if (status === 401) {
      $('bfFeedback').textContent = '로그인이 만료됐어요. 다시 로그인합니다…';
      setTimeout(() => { window.location.href = CFG.loginUrl; }, 800);
      return;
    }
    if (!ok || !data || !data.success) {
      const msg = (data && data.error && data.error.message) || '저장 실패';
      $('bfFeedback').textContent = msg;
      return;
    }
    closeModal();
    state.page = 1;
    await loadList();
  });

  // ─────────────────────────────────────────────────────
  // 상세
  // ─────────────────────────────────────────────────────
  async function openDetail(id) {
    const { ok, data } = await api(CFG.listUrl + id + '/');
    if (!ok || !data || !data.success) return alert('글을 불러올 수 없습니다.');
    const p = data.data;
    state.currentDetail = p;

    $('bdCategory').textContent = p.category_display || p.category;
    $('bdAuthor').textContent   = p.author_name;
    $('bdDate').textContent     = fmtDate(p.created_at);
    $('bdView').textContent     = p.view_count;
    $('bdLike').textContent     = p.like_count;
    $('bdTitle').textContent    = p.title;
    $('bdContent').textContent  = p.content;

    const isMine = CFG.isAuthenticated && (p.author_name === CFG.currentUser || (p.nickname === '' && p.author && CFG.currentUser));
    $('bdEditBtn').style.display   = isMine ? 'inline-block' : 'none';
    $('bdDeleteBtn').style.display = isMine ? 'inline-block' : 'none';

    openModal({ mode: 'detail', post: p });
  }

  $('bdEditBtn').addEventListener('click', () => {
    if (!state.currentDetail) return;
    openModal({ mode: 'edit', post: state.currentDetail });
  });

  $('bdDeleteBtn').addEventListener('click', async () => {
    if (!state.currentDetail) return;
    if (!confirm('정말 삭제하시겠습니까?')) return;
    const { ok, data } = await api(CFG.listUrl + state.currentDetail.id + '/', { method: 'DELETE' });
    if (!ok || !data || !data.success) return alert((data && data.error && data.error.message) || '삭제 실패');
    closeModal();
    await loadList();
  });

  $('bdLikeBtn').addEventListener('click', async () => {
    if (!CFG.isAuthenticated) {
      alert('좋아요는 로그인이 필요합니다.');
      window.location.href = CFG.loginUrl;
      return;
    }
    if (!state.currentDetail) return;
    const { ok, data } = await api(CFG.listUrl + state.currentDetail.id + '/like/', { method: 'POST' });
    if (ok && data && data.success) {
      $('bdLike').textContent = data.data.like_count;
      state.currentDetail.like_count = data.data.like_count;
      loadList();
    }
  });

  // ─────────────────────────────────────────────────────
  // 페이저 / 카테고리 / 닫기
  // ─────────────────────────────────────────────────────
  $('boardPrev').addEventListener('click', () => {
    if (state.page > 1) { state.page -= 1; loadList(); }
  });
  $('boardNext').addEventListener('click', () => {
    const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
    if (state.page < totalPages) { state.page += 1; loadList(); }
  });
  $('boardCategory').addEventListener('change', (e) => {
    state.category = e.target.value;
    state.page = 1;
    loadList();
  });
  document.querySelectorAll('[data-board-close]').forEach((el) =>
    el.addEventListener('click', closeModal)
  );

  // 초기 로드
  loadList();
})();
