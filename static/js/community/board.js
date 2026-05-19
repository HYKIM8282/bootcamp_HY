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
    pendingFiles: [],          // 작성/수정 모달에서 등록 대기 중인 이미지 파일들 (누적)
    pendingObjectUrls: [],     // 미리보기용 ObjectURL — 모달 닫을 때 일괄 revoke
    existingImages: [],        // 수정 모달에서 보여줄 기존 첨부 ({id, image_url, caption}[])
    lightboxImages: [],        // 라이트박스에 표시할 사진 배열
    lightboxIndex: 0,          // 현재 라이트박스 인덱스
    selectedExistingIds: new Set(),  // 다중 선택: 기존 사진 id
    selectedNewIdxs: new Set(),      // 다중 선택: 새 파일 인덱스
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

  // multipart 업로드 전용 — Content-Type 헤더는 브라우저가 boundary 포함해 자동 설정 (수동 설정 금지)
  async function apiUpload(url, formData) {
    const baseHeaders = { 'X-CSRFToken': getCsrf() };
    let res = await fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      body: formData,
      headers: baseHeaders,
    });
    if (res.status === 401) {
      const access = localStorage.getItem('access_token');
      if (access) {
        res = await fetch(url, {
          method: 'POST',
          credentials: 'same-origin',
          body: formData,
          headers: { ...baseHeaders, Authorization: 'Bearer ' + access },
        });
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
  // 첨부 이미지 — 누적 선택 + 미리보기 + 제거
  // (파일 input은 매번 value 비워서 같은 파일도 다시 추가 가능하게)
  // ─────────────────────────────────────────────────────
  function revokePendingObjectUrls() {
    state.pendingObjectUrls.forEach((url) => URL.revokeObjectURL(url));
    state.pendingObjectUrls = [];
  }

  function clearPendingFiles() {
    revokePendingObjectUrls();
    state.pendingFiles = [];
    state.existingImages = [];
    state.selectedExistingIds = new Set();
    state.selectedNewIdxs = new Set();
    const preview = $('bfImagePreview');
    if (preview) preview.innerHTML = '';
    updateSelectionBar();
  }

  function renderImagePreview() {
    const preview = $('bfImagePreview');
    if (!preview) return;
    revokePendingObjectUrls();
    preview.innerHTML = '';

    // 1) 기존 사진 — 클릭 또는 드래그로 선택, 일괄 삭제는 액션바
    state.existingImages.forEach((img) => {
      const wrap = document.createElement('div');
      wrap.className = 'bf-preview-item bf-preview-item--existing';
      wrap.dataset.existingId = img.id;
      if (state.selectedExistingIds.has(String(img.id))) wrap.classList.add('is-selected');
      wrap.innerHTML = `
        <img src="${escapeHtml(img.image_url)}" alt="${escapeHtml(img.caption || '')}">
        <div class="bf-preview-check" aria-hidden="true"></div>
      `;
      preview.appendChild(wrap);
    });

    // 2) 새로 첨부할 파일
    state.pendingFiles.forEach((file, idx) => {
      const url = URL.createObjectURL(file);
      state.pendingObjectUrls.push(url);
      const wrap = document.createElement('div');
      wrap.className = 'bf-preview-item bf-preview-item--new';
      wrap.dataset.newIdx = idx;
      if (state.selectedNewIdxs.has(idx)) wrap.classList.add('is-selected');
      wrap.innerHTML = `
        <img src="${url}" alt="${escapeHtml(file.name)}">
        <div class="bf-preview-check" aria-hidden="true"></div>
      `;
      preview.appendChild(wrap);
    });

    updateSelectionBar();
  }

  function updateSelectionBar() {
    const bar = $('bfImagePreviewBar');
    const cnt = $('bfImagePreviewCount');
    if (!bar) return;
    const total = state.selectedExistingIds.size + state.selectedNewIdxs.size;
    if (total === 0) {
      bar.hidden = true;
    } else {
      bar.hidden = false;
      if (cnt) cnt.textContent = `선택 ${total}장`;
    }
  }

  function toggleItemSelection(item) {
    const isSelected = item.classList.toggle('is-selected');
    if (item.dataset.existingId !== undefined) {
      const id = String(item.dataset.existingId);
      if (isSelected) state.selectedExistingIds.add(id);
      else state.selectedExistingIds.delete(id);
    } else if (item.dataset.newIdx !== undefined) {
      const idx = Number(item.dataset.newIdx);
      if (isSelected) state.selectedNewIdxs.add(idx);
      else state.selectedNewIdxs.delete(idx);
    }
    updateSelectionBar();
  }

  async function deleteSelectedImages() {
    const existingIds = Array.from(state.selectedExistingIds);
    const newIdxs     = Array.from(state.selectedNewIdxs);
    const total       = existingIds.length + newIdxs.length;
    if (total === 0) return;

    const msg = existingIds.length > 0
      ? `선택한 ${total}장(이미 저장된 ${existingIds.length}장 포함)을 정말 삭제할까요?`
      : `선택한 ${total}장을 삭제할까요?`;
    if (!confirm(msg)) return;

    // 새 파일 — 클라이언트 상태에서만 제거 (큰 인덱스부터 splice)
    newIdxs.sort((a, b) => b - a).forEach((i) => state.pendingFiles.splice(i, 1));

    // 기존 — DELETE API 차례 호출
    const failed = [];
    for (const id of existingIds) {
      if (!state.editId) break;
      const url = CFG.listUrl + state.editId + '/images/' + id + '/';
      const { ok, data } = await api(url, { method: 'DELETE' });
      if (ok && data && data.success) {
        state.existingImages = state.existingImages.filter((x) => String(x.id) !== String(id));
      } else {
        failed.push(id);
      }
    }

    state.selectedExistingIds = new Set();
    state.selectedNewIdxs     = new Set();
    renderImagePreview();
    if (failed.length > 0) alert(`${failed.length}장 삭제 실패 (나머지는 정상 삭제)`);
  }

  function onImageInputChange(event) {
    const picked = Array.from(event.target.files || []);
    if (picked.length === 0) return;
    state.pendingFiles = state.pendingFiles.concat(picked);
    event.target.value = '';
    renderImagePreview();
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
      // 파일 input 및 누적 미리보기 초기화 (이전 선택 잔존 방지)
      if ($('bfImages')) $('bfImages').value = '';
      clearPendingFiles();
      // 수정 모달이면 기존 첨부 사진을 미리보기에 함께 표시
      if (mode === 'edit' && post && Array.isArray(post.images) && post.images.length > 0) {
        state.existingImages = post.images.slice();
        renderImagePreview();
      }
    }

    $('boardModal').classList.add('is-open');
  }

  function closeModal() {
    $('boardModal').classList.remove('is-open');
    state.editId = null;
    state.currentDetail = null;
    clearPendingFiles();             // 미리보기 ObjectURL 누수 방지 + 다음 모달 깨끗하게
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

    // 글 저장 성공 후 누적된 첨부 이미지가 있으면 차례로 업로드
    const savedPost = data.data;
    if (savedPost && state.pendingFiles.length > 0) {
      const total = state.pendingFiles.length;
      $('bfFeedback').textContent = `이미지 업로드 중… (0/${total})`;
      let done = 0;
      for (const file of state.pendingFiles) {
        const fd = new FormData();
        fd.append('image', file);
        const up = await apiUpload(CFG.listUrl + savedPost.id + '/upload_image/', fd);
        done += 1;
        $('bfFeedback').textContent = `이미지 업로드 중… (${done}/${total})`;
        if (!up.ok || !up.data || !up.data.success) {
          $('bfFeedback').textContent = (up.data && up.data.error && up.data.error.message) || '이미지 업로드 일부 실패';
          // 부분 실패해도 글은 이미 저장됨 — 계속 진행
        }
      }
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

    renderImages(p);
    openModal({ mode: 'detail', post: p });
  }

  // 상세 보기 갤러리 — 사진 표시 + 클릭 시 라이트박스 확대 (삭제는 수정 모달에서)
  function renderImages(post) {
    const gallery = $('bdImages');
    if (!gallery) return;
    gallery.innerHTML = '';
    const imgs = (post && post.images) || [];
    if (imgs.length === 0) return;

    imgs.forEach((img, idx) => {
      const item = document.createElement('div');
      item.className = 'bd-image-item';
      const safeUrl     = escapeHtml(img.image_url || '');
      const safeCaption = escapeHtml(img.caption || '');
      item.innerHTML = `<img src="${safeUrl}" alt="${safeCaption}">`;
      item.addEventListener('click', () => openLightbox(imgs, idx));
      gallery.appendChild(item);
    });
  }

  // 라이트박스 — 사진 배열 + 현재 인덱스로 띄움. ← → 로 넘김.
  function openLightbox(images, index) {
    const lb = $('boardLightbox');
    if (!lb || !Array.isArray(images) || images.length === 0) return;
    state.lightboxImages = images;
    state.lightboxIndex  = Math.max(0, Math.min(index || 0, images.length - 1));
    showLightboxImage();
    lb.classList.add('is-open');
  }
  function closeLightbox() {
    const lb  = $('boardLightbox');
    const img = $('boardLightboxImg');
    if (!lb) return;
    lb.classList.remove('is-open');
    if (img) img.src = '';
    state.lightboxImages = [];
  }
  function showLightboxImage() {
    const img     = $('boardLightboxImg');
    const counter = $('boardLightboxCount');
    const prev    = $('boardLightboxPrev');
    const next    = $('boardLightboxNext');
    const cur = state.lightboxImages[state.lightboxIndex];
    if (img && cur) img.src = cur.image_url;
    const total = state.lightboxImages.length;
    if (counter) counter.textContent = total > 1 ? `${state.lightboxIndex + 1} / ${total}` : '';
    // 한 장이면 네비 숨김
    if (prev) prev.style.display = total > 1 ? 'flex' : 'none';
    if (next) next.style.display = total > 1 ? 'flex' : 'none';
  }
  function lightboxPrev() {
    const total = state.lightboxImages.length;
    if (total === 0) return;
    state.lightboxIndex = (state.lightboxIndex - 1 + total) % total;
    showLightboxImage();
  }
  function lightboxNext() {
    const total = state.lightboxImages.length;
    if (total === 0) return;
    state.lightboxIndex = (state.lightboxIndex + 1) % total;
    showLightboxImage();
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
  // 카테고리 탭 — 클릭 시 해당 카테고리만 필터링 + active 표시
  $('boardTabs').addEventListener('click', (e) => {
    const btn = e.target.closest('.board-tab');
    if (!btn) return;
    document.querySelectorAll('.board-tab').forEach((b) => {
      const active = b === btn;
      b.classList.toggle('is-active', active);
      b.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    state.category = btn.dataset.cat || '';
    state.page = 1;
    loadList();
  });
  document.querySelectorAll('[data-board-close]').forEach((el) =>
    el.addEventListener('click', closeModal)
  );

  // 파일 input: 선택할 때마다 누적 + 미리보기 갱신
  const imagesInput = $('bfImages');
  if (imagesInput) imagesInput.addEventListener('change', onImageInputChange);

  // 미리보기 다중 선택 — 클릭 토글 + 마우스 드래그 박스 선택 + 일괄 삭제
  const previewEl = $('bfImagePreview');
  const deleteSelectedBtn = $('bfImagePreviewDelete');
  if (deleteSelectedBtn) deleteSelectedBtn.addEventListener('click', deleteSelectedImages);

  let dragState = null;
  if (previewEl) {
    previewEl.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return;
      const rect = previewEl.getBoundingClientRect();
      dragState = {
        startClientX: e.clientX,
        startClientY: e.clientY,
        rect,
        dragging: false,
        target: e.target.closest('.bf-preview-item'),
        boxEl: null,
      };
      e.preventDefault();   // 드래그 중 텍스트 선택 방지
    });
  }
  document.addEventListener('mousemove', (e) => {
    if (!dragState) return;
    const dx = Math.abs(e.clientX - dragState.startClientX);
    const dy = Math.abs(e.clientY - dragState.startClientY);
    if (!dragState.dragging) {
      if (dx + dy < 5) return;             // 임계점 미만이면 클릭 후보 유지
      dragState.dragging = true;
      const box = document.createElement('div');
      box.className = 'bf-drag-box';
      previewEl.appendChild(box);
      dragState.boxEl = box;
    }
    const rect = previewEl.getBoundingClientRect();
    const x1 = Math.min(dragState.startClientX, e.clientX) - rect.left;
    const y1 = Math.min(dragState.startClientY, e.clientY) - rect.top;
    const x2 = Math.max(dragState.startClientX, e.clientX) - rect.left;
    const y2 = Math.max(dragState.startClientY, e.clientY) - rect.top;
    dragState.boxEl.style.left   = x1 + 'px';
    dragState.boxEl.style.top    = y1 + 'px';
    dragState.boxEl.style.width  = (x2 - x1) + 'px';
    dragState.boxEl.style.height = (y2 - y1) + 'px';
    // 박스와 교차하는 썸네일 선택
    previewEl.querySelectorAll('.bf-preview-item').forEach((item) => {
      const ir = item.getBoundingClientRect();
      const ix1 = ir.left   - rect.left;
      const iy1 = ir.top    - rect.top;
      const ix2 = ir.right  - rect.left;
      const iy2 = ir.bottom - rect.top;
      const intersects = !(ix2 < x1 || ix1 > x2 || iy2 < y1 || iy1 > y2);
      const id  = item.dataset.existingId;
      const idx = item.dataset.newIdx;
      if (intersects) {
        item.classList.add('is-selected');
        if (id !== undefined)  state.selectedExistingIds.add(String(id));
        if (idx !== undefined) state.selectedNewIdxs.add(Number(idx));
      } else {
        item.classList.remove('is-selected');
        if (id !== undefined)  state.selectedExistingIds.delete(String(id));
        if (idx !== undefined) state.selectedNewIdxs.delete(Number(idx));
      }
    });
    updateSelectionBar();
  });
  document.addEventListener('mouseup', () => {
    if (!dragState) return;
    if (dragState.dragging) {
      if (dragState.boxEl && dragState.boxEl.parentNode) dragState.boxEl.parentNode.removeChild(dragState.boxEl);
    } else if (dragState.target) {
      // 임계점 못 넘기면 클릭으로 처리 — 썸네일 토글
      toggleItemSelection(dragState.target);
    }
    dragState = null;
  });

  // 라이트박스: 배경/✕ 클릭 + ESC/← → 키
  document.querySelectorAll('[data-lightbox-close]').forEach((el) =>
    el.addEventListener('click', closeLightbox)
  );
  const lbEl = $('boardLightbox');
  if (lbEl) lbEl.addEventListener('click', (e) => {
    if (e.target === lbEl) closeLightbox();     // 배경 클릭 시 닫기 (이미지/버튼은 안 닫힘)
  });
  const lbPrev = $('boardLightboxPrev');
  const lbNext = $('boardLightboxNext');
  if (lbPrev) lbPrev.addEventListener('click', (e) => { e.stopPropagation(); lightboxPrev(); });
  if (lbNext) lbNext.addEventListener('click', (e) => { e.stopPropagation(); lightboxNext(); });
  document.addEventListener('keydown', (e) => {
    if (!lbEl || !lbEl.classList.contains('is-open')) return;
    if (e.key === 'Escape')          closeLightbox();
    else if (e.key === 'ArrowLeft')  lightboxPrev();
    else if (e.key === 'ArrowRight') lightboxNext();
  });

  // 초기 로드
  loadList();
})();
